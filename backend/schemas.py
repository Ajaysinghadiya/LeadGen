"""
schemas.py — Pydantic request/response schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Job Schemas ─────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    city: str
    # category is no longer collected from the user — agents/lead_finder.py auto-sweeps
    # 8 "boring" categories. Kept as Optional + default for backwards-compat with
    # any external API caller still sending it; payload value is ignored.
    category: Optional[str] = None
    max_leads: int = Field(default=25, ge=5, le=25,
                           description="Cap on leads passed to the agent loop. Range 5–25 (UI-enforced).")
    force_refresh: bool = Field(default=False,
                                description="If True, bypass the 24h discovery cache and refetch from the source API.")


class JobResponse(BaseModel):
    id: int
    city: str
    category: str
    status: str
    current_step: Optional[str]
    max_leads: int
    force_refresh: bool
    total_found: int
    qualified_leads: int
    outreach_sent: int
    skipped_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Lead Schemas ─────────────────────────────────────────────────────────────

class LeadResponse(BaseModel):
    id: int
    job_id: int
    business_name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: str
    category: str
    existing_website: Optional[str]
    website_score: Optional[float]
    needs_website: bool
    generated_site_path: Optional[str]
    video_path: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OutreachResponse(BaseModel):
    id: int
    lead_id: int
    message_text: str
    video_url: Optional[str]
    whatsapp_status: str
    twilio_sid: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadDetailResponse(LeadResponse):
    outreach: Optional[OutreachResponse] = None


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedLeads(BaseModel):
    items: list[LeadDetailResponse]
    total: int
    page: int
    page_size: int


class PaginatedJobs(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int


# ─── Generic ──────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    job_id: Optional[int] = None
