"""
OCR endpoint — accepts an image upload and returns extracted text.

POST /api/ocr
  Input:  multipart/form-data  file=<image>
  Output: JSON {"content": "...", "engine": "google_vision", "language_hint": "en"}

Validates MIME type and file size before calling the Vision API.
"""

import logging
import os
import time

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from web_app.services.ocr_google import OCRError, extract_text_from_image_bytes

logger = logging.getLogger(__name__)

router = APIRouter()

_ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
_DEFAULT_MAX_MB = 10


def _max_image_bytes() -> int:
    """Read the upload-size cap from env (default 10 MB)."""
    try:
        return int(os.getenv("OCR_MAX_IMAGE_MB", _DEFAULT_MAX_MB)) * 1024 * 1024
    except ValueError:
        return _DEFAULT_MAX_MB * 1024 * 1024


@router.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...)):

    if file.content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported image type '{file.content_type}'. "
                f"Allowed: {', '.join(sorted(_ALLOWED_MIME_TYPES))}"
            ),
        )

    image_bytes = await file.read()
    size_mb = len(image_bytes) / (1024 * 1024)
    max_bytes = _max_image_bytes()

    if len(image_bytes) > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Image too large ({size_mb:.1f} MB). Maximum allowed is {max_mb:.0f} MB.",
        )

    logger.info("OCR request — file=%s  size=%.2f MB", file.filename, size_mb)

    t0 = time.time()
    try:
        text = extract_text_from_image_bytes(image_bytes)
    except OCRError as exc:
        logger.error("OCR failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    elapsed = time.time() - t0
    logger.info(
        "OCR complete — latency=%.2fs  chars=%d  empty=%s",
        elapsed,
        len(text),
        not text,
    )

    return JSONResponse({
        "content": text,
        "engine": "google_vision",
    })
