import logging
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.database import init_db
from backend.routes.jobs import router as jobs_router
from backend.routes.characters import router as characters_router
from backend.routes.scenes import router as scenes_router
from backend.routes.episodes import router as episodes_router
from backend.routes.ai_assist import router as ai_assist_router
from backend.pipeline.orchestrator import get_script

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="Novel2Scenario",
    description="AI-powered novel-to-script conversion tool",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, # type: ignore[arg-type]
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(characters_router)
app.include_router(scenes_router)
app.include_router(episodes_router)
app.include_router(ai_assist_router)


@app.get("/api/jobs/{job_id}/script")
async def download_script(job_id: int, format: str = Query("json", pattern="^(json|yaml)$")):
    script = get_script(job_id)
    if format == "yaml":
        yaml_str = yaml.dump(script, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return PlainTextResponse(content=yaml_str, media_type="application/x-yaml")
    return script
