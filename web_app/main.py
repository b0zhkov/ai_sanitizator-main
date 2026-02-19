import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
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
    print(f"Error importing modules: {e}")
    # Fail hard on import error as per critique
    raise e

from web_app.database import init_db
from web_app.routes_auth import router as auth_router
from web_app.routes_history import router as history_router
from web_app.routes_process import router as process_router

app = FastAPI()


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router)
app.include_router(history_router)
app.include_router(process_router)

# Mount static files
current_dir = _current_dir
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(current_dir, 'static', 'index.html'))