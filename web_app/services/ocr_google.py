"""
Google Cloud Vision OCR service (REST transport).

Reads credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON_B64 env var,
authenticates via google-auth, and calls the Vision REST API directly
with httpx — no grpc dependency (Vercel-safe).

Exposes a single function to extract text from raw image bytes.
"""

import base64
import json
import logging
import os
from functools import lru_cache

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

_VISION_SCOPES = ["https://www.googleapis.com/auth/cloud-vision"]
_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


class OCRError(Exception):
    """Raised when the Vision API call fails or returns an error."""


@lru_cache(maxsize=1)
def _get_credentials() -> service_account.Credentials:
    """Build and cache Google credentials from base64-encoded service-account JSON."""

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

    return service_account.Credentials.from_service_account_info(
        info, scopes=_VISION_SCOPES
    )


def _get_access_token() -> str:
    """Return a valid access token, refreshing if needed."""
    creds = _get_credentials()
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def _call_vision_api(image_b64: str, feature_type: str) -> dict:
    """Send a single-feature annotate request and return the response dict."""

    payload = {
        "requests": [
            {
                "image": {"content": image_b64},
                "features": [{"type": feature_type}],
            }
        ]
    }

    token = _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    resp = httpx.post(_VISION_URL, json=payload, headers=headers, timeout=60)

    if resp.status_code != 200:
        raise OCRError(
            f"Vision API HTTP {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    responses = data.get("responses", [])
    if not responses:
        raise OCRError("Vision API returned no responses")

    annotation = responses[0]
    if "error" in annotation:
        err = annotation["error"]
        raise OCRError(
            f"Vision API error {err.get('code')}: {err.get('message')}"
        )

    return annotation


def _extract_text_from_annotation(annotation: dict) -> str:
    """Pull text from a Vision API annotation dict."""

    # Prefer fullTextAnnotation (best for documents / dense text)
    full = annotation.get("fullTextAnnotation", {})
    if full.get("text"):
        return full["text"].strip()

    # Fallback: first entry in textAnnotations
    text_anns = annotation.get("textAnnotations", [])
    if text_anns:
        return text_anns[0].get("description", "").strip()

    return ""


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    Send raw image bytes to Google Cloud Vision and return the extracted text.

    Uses DOCUMENT_TEXT_DETECTION (optimised for dense text / documents).
    Falls back to TEXT_DETECTION when the first attempt returns no text.
    Returns an empty string when no text is detected.

    Raises OCRError on API-level failures.
    """

    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    # Primary attempt — document text detection
    try:
        annotation = _call_vision_api(image_b64, "DOCUMENT_TEXT_DETECTION")
        text = _extract_text_from_annotation(annotation)
        if text:
            return text
    except Exception as exc:
        if isinstance(exc, OCRError):
            raise
        logger.warning("DOCUMENT_TEXT_DETECTION failed: %s", exc)

    # Fallback — plain text detection (better for sparse text)
    try:
        annotation = _call_vision_api(image_b64, "TEXT_DETECTION")
        text = _extract_text_from_annotation(annotation)
        if text:
            return text
    except Exception as exc:
        if isinstance(exc, OCRError):
            raise
        logger.error("TEXT_DETECTION fallback failed: %s", exc)
        raise OCRError(f"Vision API fallback request failed: {exc}") from exc

    return ""
