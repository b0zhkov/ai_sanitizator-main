from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import shutil
import tempfile
from typing import List, Optional

# --- Path Setup ---
# Calculate the project root (d:\projects\ai_sanitizator-main)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add paths to sys.path to mimic the desktop app environment
# 1. Project Root
sys.path.insert(0, project_root)
# 2. text_sanitization (for document_loading.py)
sys.path.insert(0, os.path.join(project_root, 'text_sanitization'))
# 3. changes-log (for changes_log.py)
sys.path.insert(0, os.path.join(project_root, 'text_sanitization', 'changes-log'))
# 4. text-analysis
sys.path.insert(0, os.path.join(project_root, 'text-analysis'))
# 5. text-rewriting
sys.path.insert(0, os.path.join(project_root, 'text-rewriting'))

# --- Imports ---
try:
    from changes_log import build_changes_log, Change # From text_sanitization/changes-log
    import llm_validator # From text-analysis
    from rewriting_agent import rewriting_agent # From text-rewriting
    import document_loading # From text_sanitization
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Continue to allow app to start, but endpoints will fail
    pass

app = FastAPI()

# Add CORS for development (Vercel handles this differently in prod but good for local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves static files (styles, js, images)
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(current_dir, 'static', 'index.html'))

@app.post("/api/process")
async def process_text(action: str = Form(...), text: str = Form(...)):
    """
    Unified endpoint for processing text.
    action: "clean" or "rewrite"
    """
    try:
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        # 1. Always Clean First
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
                "changes": changes_list,
                "ai_score": None
            })

        elif action == "rewrite":
            # 2. Analyze
            analysis = llm_validator.validate_text(clean_text_val)
            if "error" in analysis:
                 # If validation/analysis fails, return error but maybe still return clean text?
                 # ideally fail gracefully
                 pass 

            # 3. Rewrite
            # Collect stream into full text for response
            rewritten_chunks = []
            try:
                for chunk in rewriting_agent.stream_rewrite(clean_text_val, analysis):
                     if chunk and isinstance(chunk, str):
                         rewritten_chunks.append(chunk)
            except Exception as e:
                # Fallback if AI fails
                print(f"Rewrite error: {e}")
                
            rewritten_text_val = "".join(rewritten_chunks)
            
            # Get AI Score
            llm_critique = analysis.get("llm_critique", {})
            ai_score = llm_critique.get("ai_score", 0.0)
            
            # Add rewrite step to changes log
            changes_list.append({
                "description": "Applied AI Rewriting (Clean + Rewrite)",
                "text_before": clean_text_val,
                "text_after": rewritten_text_val
            })

            return JSONResponse({
                "clean_text": clean_text_val, # Intermediate
                "rewritten_text": rewritten_text_val, # Final
                "changes": changes_list,
                "ai_score": ai_score
            })
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Create a temporary file to save uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        # Use document loading logic
        try:
            content = document_loading.load_file_content(tmp_path)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")
