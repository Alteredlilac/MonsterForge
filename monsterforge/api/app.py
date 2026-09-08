"""
FastAPI app wiring for the MonsterForge JSON API.

A separate app from ui/app.py, not a router mounted on it: the JSON API
and the human-facing web UI are independent branches of the pipeline,
forking after serialization/ (see PIPELINE_ARCHITECTURE.md decision 6)
and sharing only the layers underneath them (pipeline/, db/,
validation/) -- run and deployed as two separate services, potentially
on two separate hosts, rather than one process serving both.

Just the app instance, startup (lifespan()), and the two route routers
(api/reads.py, api/creation.py) -- every actual route handler lives in
one of those modules. title= is the only thing making the automatic
Swagger UI at /docs (and the OpenAPI schema at /openapi.json, no extra
code required for either) show something more useful than the generic
"FastAPI" default.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from monsterforge.api.creation import router as creation_router
from monsterforge.api.reads import router as reads_router
from monsterforge.db.session import init_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Same startup sequence as ui/app.py's own lifespan() -- each app
    starts up independently, but both need the database tables created
    and reference rows seeded before serving a single request (see
    db/session.py::init_database())."""
    init_database()
    yield


app = FastAPI(title="MonsterForge API", lifespan=lifespan)
app.include_router(reads_router)
app.include_router(creation_router)

# Same favicon file as ui/app.py, for the same reason -- the browser
# tab icon on /docs (and any other page this app serves) otherwise
# falls back to a blank default.
FAVICON_PATH = Path(__file__).resolve().parents[1] / "docs" / "images" / "Web" / "favicon.png"


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)
