"""
routers/leads.py — /leads endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pathlib import Path
import os

from database import get_db
from models import Lead
from schemas import LeadDetailResponse, PaginatedLeads

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/", response_model=PaginatedLeads)
async def list_leads(
    page: int = 1,
    page_size: int = 50,
    city: str | None = None,
    category: str | None = None,
    status: str | None = None,
    needs_website: bool | None = None,
    job_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead)

    if city:
        query = query.where(Lead.city.ilike(f"%{city}%"))
    if category:
        query = query.where(Lead.category.ilike(f"%{category}%"))
    if status:
        query = query.where(Lead.status == status)
    if needs_website is not None:
        query = query.where(Lead.needs_website == needs_website)
    if job_id:
        query = query.where(Lead.job_id == job_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Lead.created_at.desc()).offset(offset).limit(page_size)
    )
    leads = result.scalars().all()
    return PaginatedLeads(items=leads, total=total, page=page, page_size=page_size)


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/{lead_id}/preview")
async def get_lead_preview(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the AI-generated HTML site preview."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.generated_site_path:
        raise HTTPException(status_code=404, detail="No generated site for this lead")

    path = Path(lead.generated_site_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Generated site file not found")

    return FileResponse(path, media_type="text/html")


@router.get("/{lead_id}/video")
async def get_lead_video(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the recorded video for this lead."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.video_path:
        raise HTTPException(status_code=404, detail="No video for this lead")

    path = Path(lead.video_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(path, media_type="video/mp4")
