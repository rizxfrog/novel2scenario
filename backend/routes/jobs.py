from fastapi import APIRouter, HTTPException
from backend.models import JobCreate, JobResponse, RetryRequest
from backend.pipeline.orchestrator import create_job, get_job, advance_pipeline, list_jobs, delete_job, retry_pipeline, get_stage_statuses, get_chapters

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
async def list_all_jobs(q: str | None = None, status: str | None = None):
    jobs = list_jobs(search=q, status_filter=status)
    return [JobResponse(**j) for j in jobs]


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


@router.delete("/{job_id}", status_code=204)
async def delete_job_endpoint(job_id: int):
    try:
        get_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    delete_job(job_id)


@router.get("/{job_id}/stages")
async def get_stages(job_id: int):
    try:
        get_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    return get_stage_statuses(job_id)


@router.get("/{job_id}/chapters")
async def get_chapters_endpoint(job_id: int):
    try:
        get_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    return get_chapters(job_id)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: int, data: RetryRequest):
    try:
        get_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        job = await retry_pipeline(job_id, data.from_stage, data.rerun_stages)
        return JobResponse(**job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
