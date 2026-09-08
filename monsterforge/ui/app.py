"""
FastAPI app wiring for the MonsterForge web UI.

Just the app instance, startup (lifespan()), the three route routers
(ui/routes/convert.py, review.py, library.py), and a favicon route --
every actual GET/POST handler lives in one of those router modules now.
Helpers shared across more than one of them (form/context parsing,
hidden-field (de)serialization, building an HTTP response from a
resolved state) live in their own modules alongside routes/ (context.py,
hidden_fields.py, responses.py), imported by whichever router needs
them rather than by this file.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from monsterforge.db.session import create_all_tables, get_session
from monsterforge.db.seed import seed_reference_data
from monsterforge.ui.routes.convert import router as convert_router
from monsterforge.ui.routes.library import router as library_router
from monsterforge.ui.routes.review import router as review_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create the database tables and seed reference rows once, at
    startup — this project has no migration tool, so table creation
    must be triggered explicitly rather than happening on import (see
    db/session.py::create_all_tables())."""
    create_all_tables()
    session = get_session()
    try:
        seed_reference_data(session)
    finally:
        session.close()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(convert_router)
app.include_router(review_router)
app.include_router(library_router)

FAVICON_PATH = Path(__file__).resolve().parents[1] / "docs" / "images" / "Web" / "favicon.png"


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)
