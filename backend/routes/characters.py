import json
from fastapi import APIRouter
from backend.models import CharacterResponse, CharacterUpdate, CharacterRelationship
from backend.pipeline.orchestrator import get_characters, update_characters

router = APIRouter(prefix="/api/jobs/{job_id}/characters", tags=["characters"])


@router.get("", response_model=list[CharacterResponse])
async def list_characters(job_id: int):
    chars = get_characters(job_id)
    result = []
    for row in chars:
        traits = row.get("traits", [])
        if isinstance(traits, str):
            traits = json.loads(traits)
        result.append(CharacterResponse(
            id=row["id"], job_id=row["job_id"], name=row["name"],
            role=row.get("role"), traits=traits,
            description=row.get("description"),
            first_appearance=row.get("first_appearance"),
            relationships=[CharacterRelationship(**r) if isinstance(r, dict) else r for r in row.get("relationships", [])],
        ))
    return result


@router.put("", response_model=list[CharacterResponse])
async def save_characters(job_id: int, data: list[CharacterUpdate]):
    chars = [d.model_dump(exclude_none=True) for d in data]
    update_characters(job_id, chars)
    return await list_characters(job_id)
