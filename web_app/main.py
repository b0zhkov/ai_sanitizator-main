from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import json
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import shutil
import tempfile
from typing import List, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'text_sanitization'))
sys.path.insert(0, os.path.join(project_root, 'text_sanitization', 'changes-log'))
sys.path.insert(0, os.path.join(project_root, 'text-analysis'))
sys.path.insert(0, os.path.join(project_root, 'text-rewriting'))

try:
    from changes_log import build_changes_log, Change
    import llm_validator
    from rewriting_agent import rewriting_agent
    from post_humanizer import humanize
    import document_loading
except ImportError as e:
    print(f"Error importing modules: {e}")
    pass

app = FastAPI()

app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(current_dir, 'static', 'index.html'))

@app.post("/api/process")
async def process_text(action: str = Form(...), text: str = Form(...), strength: str = Form("medium")):
    try:
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        clean_text_val, changes = await asyncio.to_thread(build_changes_log, text)
        
        changes_list = [
            {
                "description": c.description,
                "text_before": c.text_before if hasattr(c, 'text_before') else "", 
                "text_after": c.text_after if hasattr(c, 'text_after') else ""
            } 
            for c in changes
        ]

        if action == "clean":
            return JSONResponse({
                "clean_text": clean_text_val,
                "changes": changes_list
            })

        elif action == "rewrite":
            async def rewrite_stream_generator():
                import time
                t0 = time.time()
                print(f"[TIMING] Start processing...")

                yield json.dumps({
                    "type": "stage", 
                    "data": {
                        "step": "clean",
                        "clean_text": clean_text_val
                    }
                }) + "\n"

                t1 = time.time()
                stats = await asyncio.to_thread(llm_validator.collect_stats, clean_text_val)
                print(f"[TIMING] Stats collection took: {time.time() - t1:.2f}s")

                critique_task = asyncio.create_task(
                    asyncio.to_thread(llm_validator.get_llm_critique, clean_text_val, stats)
                )

                analysis_for_rewrite = {"statistical_metrics": stats, "llm_critique": None}
                
                yield json.dumps({
                    "type": "stage",
                    "data": { "step": "analyzed" }
                }) + "\n"

                rewritten_chunks_gen = []
                t2 = time.time()
                try:
                    for chunk in rewriting_agent.stream_rewrite(clean_text_val, analysis_for_rewrite):
                        if chunk and isinstance(chunk, str):
                            rewritten_chunks_gen.append(chunk)
                            yield json.dumps({"type": "chunk", "data": chunk}) + "\n"
                except Exception as e:
                    print(f"Rewrite error: {e}")
                    yield json.dumps({"type": "error", "data": str(e)}) + "\n"
                
                print(f"[TIMING] Rewriting (Streaming) took: {time.time() - t2:.2f}s")
                    
                raw_rewritten_text = "".join(rewritten_chunks_gen)

                yield json.dumps({
                    "type": "stage",
                    "data": { "step": "humanizing" }
                }) + "\n"

                t3 = time.time()
                rewritten_text_final = await asyncio.to_thread(humanize, raw_rewritten_text, strength)
                print(f"[TIMING] Humanization (Post-processing) took: {time.time() - t3:.2f}s")

                yield json.dumps({
                    "type": "stage",
                    "data": { "step": "verifying" }
                }) + "\n"

                t4 = time.time()
                rewritten_analysis = await asyncio.to_thread(
                    llm_validator.verify_metrics_only, rewritten_text_final
                )
                print(f"[TIMING] Verification (Metrics) took: {time.time() - t4:.2f}s")

                t5 = time.time()
                try:
                    llm_critique = await critique_task
                except Exception:
                    llm_critique = {}
                ai_score = llm_critique.get("ai_score", 0.0)
                print(f"[TIMING] LLM Critique waited: {time.time() - t5:.2f}s")

                print(f"[TIMING] Total Process took: {time.time() - t0:.2f}s")

                final_changes = list(changes_list)
                final_changes.append({
                    "description": "Applied AI Rewriting (Clean + Rewrite)  ",
                    "text_before": clean_text_val,
                    "text_after": rewritten_text_final
                })

                yield json.dumps({
                    "type": "done",
                    "data": {
                        "clean_text": clean_text_val,
                        "rewritten_text": rewritten_text_final,
                        "changes": final_changes,
                        "original_text_ai_score": ai_score,
                        "rewritten_metrics": rewritten_analysis.get("statistical_metrics", {})
                    }
                }) + "\n"

            return StreamingResponse(rewrite_stream_generator(), media_type="application/x-ndjson")
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            tmp_path = tmp.name

        def save_upload_file():
            with open(tmp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        await asyncio.to_thread(save_upload_file)
            
        try:
            content = await asyncio.to_thread(document_loading.load_file_content, tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        return {"content": content}
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")