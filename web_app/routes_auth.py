from typing import Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from web_app.auth import (
    create_token,
    generate_salt,
    get_optional_user,
    hash_password,
    verify_password,
)
from web_app.database import get_db
from web_app.models import User


router = APIRouter(prefix="/api", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


def _validate_credentials(email: str, password: str):

    blocked_domains = ['admin.com', 'test.com', 'example.com', 'dummy.com', 'mailinator.com']

    domain_part = email.split('@')[-1].lower() if '@' in email else ''

    if domain_part in blocked_domains:
        raise HTTPException(status_code=400, detail=f"Domain '{domain_part}' is not allowed for registration")

    try:
        valid = validate_email(email, check_deliverability=True)
        email = valid.normalized
        
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(password) < 6:
        raise HTTPException(
            status_code=400, detail="Password must be at least 6 characters"
        )
    return email

@router.post("/register")
def register(body: AuthRequest, db: Session = Depends(get_db)):
    valid_email = _validate_credentials(body.email, body.password)

    existing = db.query(User).filter(User.email == valid_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    salt = generate_salt()
    hashed = hash_password(body.password, salt)

    user = User(email=valid_email, password_hash=hashed, salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return JSONResponse({"token": token, "email": user.email})

@router.post("/login")
def login(body: AuthRequest, db: Session = Depends(get_db)):
    try:
        # Normalize email for login, but skip deliverability check
        valid = validate_email(body.email, check_deliverability=False)
        normalized_email = valid.normalized
    except EmailNotValidError:
        # If the email is fundamentally invalid, it won't be in our DB
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = db.query(User).filter(User.email == normalized_email).first()

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
