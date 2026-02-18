import hashlib
import hmac
import json
import base64
import secrets
import time
import os
from typing import Optional

from fastapi import Request, Depends
from sqlalchemy.orm import Session

from web_app.database import get_db
from web_app.models import User


AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-fallback-secret-change-in-production")
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days


def generate_salt() -> str:
    return secrets.token_hex(32)


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    ).hex()


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    computed = hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(text: str) -> bytes:
    padding = 4 - len(text) % 4
    return base64.urlsafe_b64decode(text + "=" * padding)


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64_encode(payload_bytes)

    signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def decode_token(token: str) -> Optional[int]:
    try:
        payload_b64, signature = token.rsplit(".", 1)
    except ValueError:
        return None

    expected_sig = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        return None

    try:
        payload = json.loads(_b64_decode(payload_b64))
    except (json.JSONDecodeError, Exception):
        return None

    if payload.get("exp", 0) < time.time():
        return None

    return payload.get("user_id")


def get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    user_id = decode_token(token)

    if user_id is None:
        return None

    return db.query(User).filter(User.id == user_id).first()
