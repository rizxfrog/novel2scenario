import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes.jobs import router as jobs_router
from backend.routes.characters import router as characters_router
from backend.routes.scenes import router as scenes_router
from backend.routes.episodes import router as episodes_router
from backend.pipeline.orchestrator import get_script

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Novel2Scenario",
    description="AI-powered novel-to-script conversion tool",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(characters_router)
app.include_router(scenes_router)
app.include_router(episodes_router)


@app.get("/api/jobs/{job_id}/script")
async def download_script(job_id: int):
    return get_script(job_id)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Database initialized")
