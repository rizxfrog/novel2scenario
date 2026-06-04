from fastapi import APIRouter, HTTPException
from backend.models import JobCreate, JobResponse
from backend.pipeline.orchestrator import create_job, get_job, advance_pipeline

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_new_job(data: JobCreate):
    job = create_job(
        novel_text=data.novel_text,
        title=data.title,
        author=data.author,
    )
    return JobResponse(**job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: int):
    try:
        job = get_job(job_id)
        return JobResponse(**job)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/{job_id}/continue", response_model=JobResponse)
async def continue_pipeline(job_id: int):
    try:
        job = await advance_pipeline(job_id)
        return JobResponse(**job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
