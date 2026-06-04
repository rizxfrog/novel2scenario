import json
from fastapi import APIRouter
from backend.models import EpisodeResponse, EpisodeUpdate
from backend.pipeline.orchestrator import get_episodes, update_episodes

router = APIRouter(prefix="/api/jobs/{job_id}/episodes", tags=["episodes"])


@router.get("", response_model=list[EpisodeResponse])
async def list_episodes(job_id: int):
    episodes = get_episodes(job_id)
    result = []
    for row in episodes:
        chapters = row.get("novel_chapters", [])
        if isinstance(chapters, str):
            chapters = json.loads(chapters)
        result.append(EpisodeResponse(
            id=row["id"], job_id=row["job_id"], number=row["number"],
            title=row.get("title"), summary=row.get("summary"),
            novel_chapters=chapters, scene_ids=row.get("scene_ids", []),
        ))
    return result


@router.put("", response_model=list[EpisodeResponse])
async def save_episodes(job_id: int, data: list[EpisodeUpdate]):
    episodes = [d.model_dump(exclude_none=True) for d in data]
    update_episodes(job_id, episodes)
    return await list_episodes(job_id)
