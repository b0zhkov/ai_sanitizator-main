import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# Vercel has a read-only filesystem, so the DB goes in /tmp there
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    _DB_PATH = "/tmp/sanitizator.db"
else:
    _DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanitizator.db")

_DATABASE_URL = f"sqlite:///{_DB_PATH}"

# check_same_thread=False is needed because FastAPI handles requests across threads
engine = create_engine(_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db():
    from web_app.models import User, HistoryEntry  # noqa: F401
    Base.metadata.create_all(bind=engine)


# FastAPI dependency — yields a session per request and ensures cleanup
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()