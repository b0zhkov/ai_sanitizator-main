"""
Google Cloud Vision OCR service.

Reads credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON_B64 env var,
builds an ImageAnnotatorClient in-memory (no filesystem writes — Vercel-safe),
and exposes a single function to extract text from raw image bytes.
"""

import base64
import json
import logging
import os
from functools import lru_cache

from google.cloud import vision
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# scopes required by the Vision API
_VISION_SCOPES = ["https://www.googleapis.com/auth/cloud-vision"]


class OCRError(Exception):
    """Raised when the Vision API call fails or returns an error."""


@lru_cache(maxsize=1)
def _get_client() -> vision.ImageAnnotatorClient:
    """Build and cache a Vision API client from base64-encoded credentials."""

    b64_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON_B64")
    if not b64_creds:
        raise OCRError(
            "GOOGLE_APPLICATION_CREDENTIALS_JSON_B64 is not set. "
            "Please configure it with your base64-encoded service-account JSON."
        )

    try:
        raw_json = base64.b64decode(b64_creds)
        info = json.loads(raw_json)
    except Exception as exc:
        raise OCRError(f"Failed to decode credentials: {exc}") from exc

    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=_VISION_SCOPES
    )

    return vision.ImageAnnotatorClient(credentials=credentials)


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    Send raw image bytes to Google Cloud Vision and return the extracted text.

    Uses document_text_detection (optimised for dense text / documents).
    Falls back to text_annotations[0].description when full_text_annotation
    is empty.  Returns an empty string when no text is detected.

    Raises OCRError on API-level failures.
    """

    client = _get_client()

    image = vision.Image(content=image_bytes)

    try:
        response = client.document_text_detection(image=image)
    except Exception as exc:
        raise OCRError(f"Vision API request failed: {exc}") from exc

    # the API may attach an error object to the response itself
    if response.error and response.error.message:
        raise OCRError(f"Vision API error: {response.error.message}")

    # prefer the structured full-text annotation (best for documents)
    if response.full_text_annotation and response.full_text_annotation.text:
        return response.full_text_annotation.text.strip()

    # fallback: first entry in the simple text_annotations list
    if response.text_annotations:
        return response.text_annotations[0].description.strip()

    return ""
