"""
routers/jobs.py — /jobs endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import json

from database import get_db
from models import Job, Lead, Outreach
from schemas import JobCreate, JobResponse, MessageResponse, PaginatedJobs

router = APIRouter(prefix="/jobs", tags=["jobs"])

# SSE event bus: job_id -> list of queues
_sse_queues: dict[int, list[asyncio.Queue]] = {}


def get_sse_queues():
    return _sse_queues


async def broadcast_event(job_id: int, event: dict):
    """Push SSE event to all listeners of a job."""
    queues = _sse_queues.get(job_id, [])
    for q in queues:
        await q.put(event)


@router.post("/", response_model=MessageResponse, status_code=202)
async def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new lead generation job."""
    # Category input has been removed from the UI — agents/lead_finder.py auto-sweeps
    # the curated boring-categories list. Job.category stores the SWEEP_TAG sentinel
    # so 24h-TTL reuse / dedup still match across sweep jobs in the same city.
    from agents.lead_finder import SWEEP_TAG
    job = Job(
        city=payload.city.strip(),
        category=SWEEP_TAG,
        max_leads=payload.max_leads,
        force_refresh=payload.force_refresh,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Run pipeline in background
    background_tasks.add_task(run_pipeline, job.id)

    return MessageResponse(message="Job started", job_id=job.id)


@router.get("/", response_model=PaginatedJobs)
async def list_jobs(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    total_result = await db.execute(select(func.count()).select_from(Job))
    total = total_result.scalar_one()
    result = await db.execute(
        select(Job).order_by(Job.created_at.desc()).offset(offset).limit(page_size)
    )
    jobs = result.scalars().all()
    return PaginatedJobs(items=jobs, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/stream")
async def stream_job_events(job_id: int, db: AsyncSession = Depends(get_db)):
    """Server-Sent Events endpoint for real-time job progress."""
    # Verify job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    queue: asyncio.Queue = asyncio.Queue()
    _sse_queues.setdefault(job_id, []).append(queue)

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") == "done":
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
        finally:
            _sse_queues[job_id].remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def run_pipeline(job_id: int):
    """Background task: run the agentic pipeline for a job."""
    # Import here to avoid circular imports
    from agents.orchestrator import run_job
    await run_job(job_id, broadcast_event)


@router.post("/{job_id}/stop", response_model=MessageResponse)
async def stop_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a running job as stopped. The orchestrator polls Job.status between
    leads and breaks early when it sees 'stopped' — graceful, not abrupt.
    The current lead being processed will finish first to avoid half-sent
    WhatsApp messages or half-recorded videos."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("running", "pending"):
        raise HTTPException(status_code=409, detail=f"Job is {job.status}, cannot stop")

    job.status = "stopped"
    await db.commit()

    # Notify any open SSE listeners so the UI updates immediately.
    await broadcast_event(job_id, {
        "type": "result",
        "lead_id": "",
        "content": "⏹ Stop requested — finishing current lead, then halting.",
        "timestamp": __import__("time").time(),
    })
    return MessageResponse(message="Stop requested", job_id=job_id)


@router.delete("/{job_id}", response_model=MessageResponse)
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a job and all its leads + outreach records.
    Generated HTML / video files on disk are NOT removed (manual cleanup if needed)."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Cascade: leads → outreach → job
    leads_q = await db.execute(select(Lead).where(Lead.job_id == job_id))
    leads = list(leads_q.scalars().all())
    for lead in leads:
        out_q = await db.execute(select(Outreach).where(Outreach.lead_id == lead.id))
        for o in out_q.scalars().all():
            await db.delete(o)
        await db.delete(lead)

    await db.delete(job)
    await db.commit()
    return MessageResponse(message=f"Deleted job {job_id} ({len(leads)} leads)", job_id=job_id)
