import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)

# make sure the project root is on sys.path so cross-folder imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(current_dir)
sys.path.insert(0, _project_root)

# _paths registers all sub-package directories onto sys.path
import _paths
try:
    from text_sanitization import document_loading
    from text_sanitization.changes_log import build_changes_log
except ImportError as e:
    logging.error(f"Error importing core text processing modules: {e}")
    raise e

from web_app.database import init_db
from web_app.routes_auth import router as auth_router
from web_app.routes_history import router as history_router
from web_app.routes_process import router as process_router

# lifespan runs once on startup (before the yield) and once on shutdown (after)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables if they don't exist yet
    init_db()
    
    if os.getenv("AUTH_SECRET") is None:
        import warnings
        warnings.warn(
            "AUTH_SECRET not set! Using insecure fallback. Set AUTH_SECRET in production to prevent security vulnerabilities.",
            stacklevel=2,
            category=RuntimeWarning
        )
        
    yield

app = FastAPI(lifespan=lifespan)


# register API routes before static files so /api/* paths take priority
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(process_router)

app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# serve the SPA — all non-API GET requests land here
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(current_dir, 'static', 'index.html'))