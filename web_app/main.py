import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(current_dir)
sys.path.insert(0, _project_root)
import _paths 

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.responses import FileResponse

try:
    from changes_log import build_changes_log, Change
    import llm_validator
    from rewriting_agent import rewriting_agent
    from post_humanizer import humanize
    import document_loading
except ImportError as e:
    logging.error(f"Error importing modules: {e}")
    raise e

from web_app.database import init_db
from web_app.routes_auth import router as auth_router
from web_app.routes_history import router as history_router
from web_app.routes_process import router as process_router

import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)


app.include_router(auth_router)
app.include_router(history_router)
app.include_router(process_router)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(current_dir, 'static', 'index.html'))