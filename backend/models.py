"""
models.py — SQLAlchemy ORM models
"""
from datetime import datetime
from sqlalchemy import (
    Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Status: pending | running | completed | failed
    current_step: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Steps: discovery | audit | generation | recording | messaging | sending

    # Cost controls
    max_leads: Mapped[int] = mapped_column(Integer, default=25)
    force_refresh: Mapped[bool] = mapped_column(Boolean, default=False)

    total_found: Mapped[int] = mapped_column(Integer, default=0)
    qualified_leads: Mapped[int] = mapped_column(Integer, default=0)
    outreach_sent: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="job", lazy="selectin")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Business info
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)

    # Website audit
    existing_website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_website: Mapped[bool] = mapped_column(Boolean, default=False)

    # Generated assets
    generated_site_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Pipeline status
    # discovered | audited | site_generated | video_recorded | message_sent | failed | skipped
    status: Mapped[str] = mapped_column(String(30), default="discovered")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    job: Mapped["Job"] = relationship("Job", back_populates="leads")
    outreach: Mapped["Outreach | None"] = relationship("Outreach", back_populates="lead", uselist=False, lazy="selectin")


class Outreach(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)

    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # pending | sent | delivered | read | failed
    whatsapp_status: Mapped[str] = mapped_column(String(20), default="pending")
    twilio_sid: Mapped[str | None] = mapped_column(String(200), nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    lead: Mapped["Lead"] = relationship("Lead", back_populates="outreach")
