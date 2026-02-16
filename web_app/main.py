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
    import document_loading
except ImportError as e:
    print(f"Error importing modules: {e}")
    pass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(current_dir, 'static', 'index.html'))

@app.post("/api/process")
async def process_text(action: str = Form(...), text: str = Form(...)):
    try:
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        clean_text_val, changes = build_changes_log(text)
        
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
                # Emit Clean Event
                yield json.dumps({
                    "type": "stage", 
                    "data": {
                        "step": "clean",
                        "clean_text": clean_text_val
                    }
                }) + "\n"

                # 2. Analyze
                analysis = await asyncio.to_thread(llm_validator.validate_text, clean_text_val)
                
                yield json.dumps({
                    "type": "stage",
                    "data": { "step": "analyzed" }
                }) + "\n"

                # 3. Rewrite Stream
                rewritten_chunks_gen = []
                try:
                    for chunk in rewriting_agent.stream_rewrite(clean_text_val, analysis):
                        if chunk and isinstance(chunk, str):
                            rewritten_chunks_gen.append(chunk)
                            yield json.dumps({"type": "chunk", "data": chunk}) + "\n"
                except Exception as e:
                    print(f"Rewrite error: {e}")
                    yield json.dumps({"type": "error", "data": str(e)}) + "\n"
                    
                rewritten_text_final = "".join(rewritten_chunks_gen)
                
                llm_critique = analysis.get("llm_critique", {})
                ai_score = llm_critique.get("ai_score", 0.0)
                
                # Calculate score for rewritten text
                yield json.dumps({
                    "type": "stage",
                    "data": { "step": "verifying" }
                }) + "\n"

                rewritten_analysis = await asyncio.to_thread(llm_validator.validate_text, rewritten_text_final)
                rewritten_score = rewritten_analysis.get("llm_critique", {}).get("ai_score", 0.0)

                final_changes = list(changes_list)
                final_changes.append({
                    "description": "Applied AI Rewriting (Clean + Rewrite)",
                    "text_before": clean_text_val,
                    "text_after": rewritten_text_final
                })

                # Final Event
                yield json.dumps({
                    "type": "done", 
                    "data": {
                        "clean_text": clean_text_val,
                        "rewritten_text": rewritten_text_final,
                        "changes": final_changes,
                        "original_text_ai_score": ai_score,
                        "rewritten_text_ai_score": rewritten_score
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
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        try:
            content = document_loading.load_file_content(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")