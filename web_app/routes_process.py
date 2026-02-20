from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import os
import shutil
import tempfile
import json
import time
import traceback

from web_app.database import get_db
from web_app.auth import get_optional_user
from web_app.routes_history import save_history_entry

from web_app.services.rate_limiter import check_rate_limit, update_usage, anonymous_rewrite_limiter
from web_app.services.rewrite_pipeline import rewrite_stream_generator

from changes_log import build_changes_log
import document_loading

router = APIRouter()

@router.post("/api/process")
async def process_text(
    request: Request,
    action: str = Form(...),
    text: str = Form(..., min_length=1),
    strength: str = Form("medium"),
    db: Session = Depends(get_db),
):
    try:

        clean_text_val, changes = await asyncio.to_thread(build_changes_log, text)
        
        changes_list = [
            {
                "description": c.description,
                "text_before": c.text_before, 
                "text_after": c.text_after
            } 
            for c in changes
        ]

        user = get_optional_user(request, db)

        if action == "clean":
            if user:
                save_history_entry(db, user.id, "clean", text, clean_text_val)

            return JSONResponse({
                "clean_text": clean_text_val,
                "changes": changes_list
            })

        elif action == "rewrite":
            t0 = time.time()

            if user:
                is_allowed, error_msg = check_rate_limit(user, db, len(clean_text_val))
                if not is_allowed:
                    async def error_generator():
                         yield json.dumps({"type": "error", "data": error_msg}) + "\n"
                    return StreamingResponse(error_generator(), media_type="application/x-ndjson")

                update_usage(user, db, len(clean_text_val))
            else:
                is_allowed, error_msg = anonymous_rewrite_limiter.check(request)
                if not is_allowed:
                    async def error_generator():
                         yield json.dumps({"type": "error", "data": error_msg}) + "\n"
                    return StreamingResponse(error_generator(), media_type="application/x-ndjson")

            return StreamingResponse(
                rewrite_stream_generator(clean_text_val, request, db, user, changes_list, t0, strength),
                media_type="application/x-ndjson"
            )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/upload")
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