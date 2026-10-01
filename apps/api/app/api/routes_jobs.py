import asyncio
import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.errors import JobNotFoundError
from app.core.rate_limit import limiter
from app.schemas.job import CreateJobRequest, CreateJobResponse, JobProgressEvent
from app.security.ssrf import validate_url_ssrf
from app.services.queue_service import queue_service
from app.workers.job_worker import JobWorker

router = APIRouter(prefix="/api/jobs", tags=["Job Management"])
settings = get_settings()


@router.post("", response_model=CreateJobResponse)
async def create_job(payload: CreateJobRequest, request: Request):
    client_ip = limiter.get_client_ip(request)
    limiter.check(f"jobs:{client_ip}", max_requests=settings.RATE_LIMIT_JOBS_PER_MIN)

    # Validate SSRF
    _ = validate_url_ssrf(payload.url)

    job_id = str(uuid.uuid4())
    job_event = JobProgressEvent(
        job_id=job_id,
        status="QUEUED",
        progress=0.0,
        downloaded_bytes=0,
        total_bytes=0,
        speed=0.0,
        eta=0,
        stage_message="Job queued for processing...",
        filename="media_download",
    )
    await queue_service.save_job_state(job_event)

    # Launch background worker task
    asyncio.create_task(JobWorker.process_job(job_id, payload))

    return CreateJobResponse(
        success=True,
        job_id=job_id,
        status="QUEUED",
        message="Job scheduled successfully.",
    )


@router.get("/{job_id}", response_model=JobProgressEvent)
async def get_job_status(job_id: str):
    job = await queue_service.get_job_state(job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found.")
    return job


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    job = await queue_service.get_job_state(job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found.")

    async def event_generator():
        async for event in queue_service.subscribe_events(job_id):
            payload = json.dumps(event.model_dump())
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    job = await queue_service.get_job_state(job_id)
    if not job:
        raise JobNotFoundError(f"Job {job_id} not found.")

    job.status = "CANCELLED"
    job.stage_message = "Cancelled by user."
    await queue_service.save_job_state(job)
    return {"success": True, "job_id": job_id, "status": "CANCELLED"}
