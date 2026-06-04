import json
from fastapi import APIRouter
from backend.models import SceneResponse, SceneUpdate, SceneBeatResponse, SceneSetting
from backend.pipeline.orchestrator import get_scenes, update_scenes

router = APIRouter(prefix="/api/jobs/{job_id}/scenes", tags=["scenes"])


@router.get("", response_model=list[SceneResponse])
async def list_scenes(job_id: int):
    scenes = get_scenes(job_id)
    result = []
    for row in scenes:
        setting = row.get("setting", {})
        if isinstance(setting, str):
            setting = json.loads(setting)
        chars = row.get("characters_present", [])
        if isinstance(chars, str):
            chars = json.loads(chars)
        result.append(SceneResponse(
            id=row["id"], job_id=row["job_id"], chapter_id=row["chapter_id"],
            number=row["number"], heading=row.get("heading"),
            setting=SceneSetting(**setting) if setting else None,
            summary=row.get("summary"), characters_present=chars,
            beats=[SceneBeatResponse(**b) for b in row.get("beats", [])],
            chapter_title=row.get("chapter_title"),
        ))
    return result


@router.put("", response_model=list[SceneResponse])
async def save_scenes(job_id: int, data: list[SceneUpdate]):
    scenes = [d.model_dump(exclude_none=True) for d in data]
    update_scenes(job_id, scenes)
    return await list_scenes(job_id)
