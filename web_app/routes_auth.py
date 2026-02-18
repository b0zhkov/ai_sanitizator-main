import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from web_app.database import get_db
from web_app.models import User
from web_app.auth import (
    generate_salt,
    hash_password,
    verify_password,
    create_token,
    get_optional_user,
)


router = APIRouter(prefix="/api", tags=["auth"])

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class AuthRequest(BaseModel):
    email: str
    password: str


def _validate_credentials(email: str, password: str):
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    if len(password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters"
        )


@router.post("/register")
def register(body: AuthRequest, db: Session = Depends(get_db)):
    _validate_credentials(body.email, body.password)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    salt = generate_salt()
    hashed = hash_password(body.password, salt)

    user = User(email=body.email, password_hash=hashed, salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return JSONResponse({"token": token, "email": user.email})


@router.post("/login")
def login(body: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not verify_password(body.password, user.salt, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.id)
    return JSONResponse({"token": token, "email": user.email})


@router.get("/me")
def get_me(user: Optional[User] = Depends(get_optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return JSONResponse({
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })
