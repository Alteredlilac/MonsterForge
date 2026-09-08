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
one of those modules.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
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


app = FastAPI(lifespan=lifespan)
app.include_router(reads_router)
app.include_router(creation_router)
