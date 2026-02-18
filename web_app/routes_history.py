from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from web_app.database import get_db
from web_app.models import User, HistoryEntry
from web_app.auth import get_optional_user


router = APIRouter(prefix="/api", tags=["history"])

MAX_HISTORY_PER_USER = 50


class BulkHistoryItem(BaseModel):
    action_type: str
    input_text: str
    output_text: str
    created_at: Optional[str] = None


def _enforce_history_limit(db: Session, user_id: int):
    count = db.query(HistoryEntry).filter(HistoryEntry.user_id == user_id).count()

    if count <= MAX_HISTORY_PER_USER:
        return

    overflow = count - MAX_HISTORY_PER_USER
    oldest = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.user_id == user_id)
        .order_by(HistoryEntry.created_at.asc())
        .limit(overflow)
        .all()
    )

    for entry in oldest:
        db.delete(entry)

    db.flush()


def save_history_entry(
    db: Session, user_id: int, action_type: str, input_text: str, output_text: str
):
    entry = HistoryEntry(
        user_id=user_id,
        action_type=action_type,
        input_text=input_text,
        output_text=output_text,
    )
    db.add(entry)
    db.flush()

    _enforce_history_limit(db, user_id)
    db.commit()


@router.get("/history")
def get_history(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    entries = (
        db.query(HistoryEntry)
        .filter(HistoryEntry.user_id == user.id)
        .order_by(desc(HistoryEntry.created_at))
        .limit(MAX_HISTORY_PER_USER)
        .all()
    )

    return JSONResponse([
        {
            "id": e.id,
            "action_type": e.action_type,
            "input_text": e.input_text,
            "output_text": e.output_text,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ])


@router.delete("/history/{entry_id}")
def delete_history_entry(
    entry_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    entry = db.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(entry)
    db.commit()

    return JSONResponse({"status": "deleted"})


@router.post("/history/bulk")
def bulk_save_history(
    items: List[BulkHistoryItem],
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    for item in items:
        created = None
        if item.created_at:
            try:
                created = datetime.fromisoformat(item.created_at)
            except ValueError:
                created = None

        entry = HistoryEntry(
            user_id=user.id,
            action_type=item.action_type,
            input_text=item.input_text,
            output_text=item.output_text,
            created_at=created or datetime.now(timezone.utc),
        )
        db.add(entry)

    db.flush()
    _enforce_history_limit(db, user.id)
    db.commit()

    return JSONResponse({"status": "saved", "count": len(items)})
