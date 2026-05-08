"""
workers/auditor.py — Module 2: Website Quality Auditor
Checks if a business website exists and evaluates its quality.
"""
import asyncio
import logging
import random
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from models import Job, Lead
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def check_website_exists(url: str) -> bool:
    """Check if a URL is reachable."""
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.head(url)
            return resp.status_code < 500
    except Exception:
        return False


async def score_website(url: str) -> float:
    """
    Score a website's quality (0–100).
    Uses heuristics in absence of Lighthouse (which requires Node.js).
    Real Lighthouse integration can replace this.
    """
    if not url:
        return 0.0

    score = 50.0  # Base score

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text.lower()

            # Penalize free website builders / low-quality indicators
            low_quality_signals = [
                "business.site", "wix.com", "weebly.com", "wordpress.com",
                "blogspot.com", "jimdo.com", "yolasite.com", "site123.com"
            ]
            for signal in low_quality_signals:
                if signal in url.lower():
                    score -= 25
                    break

            # Penalize missing metadata
            if "<meta name=\"description\"" not in html:
                score -= 10
            if "<title>" not in html:
                score -= 10

            # Penalize if site is very short (low content)
            if len(html) < 2000:
                score -= 15

            # Penalize if not HTTPS
            if not url.startswith("https"):
                score -= 10

            # Check for mobile viewport
            if "viewport" not in html:
                score -= 10

    except Exception as e:
        logger.warning(f"Failed to score website {url}: {e}")
        score = 20.0  # Assume poor if unreachable

    return max(0.0, min(100.0, score))


async def run_audit(job_id: int) -> int:
    """
    Step 2: Audit websites for all discovered leads.
    Returns the number of leads that need a website.
    """
    logger.info(f"[Job {job_id}] Starting website audit")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Lead).where(Lead.job_id == job_id, Lead.status == "discovered")
        )
        leads = result.scalars().all()
        lead_ids = [l.id for l in leads]

    qualified = 0

    for lead_id in lead_ids:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                continue

            if lead.existing_website:
                exists = await check_website_exists(lead.existing_website)
                if exists:
                    score = await score_website(lead.existing_website)
                else:
                    score = 0.0
                    lead.existing_website = None  # Treat as no website
            else:
                score = 0.0

            lead.website_score = score
            threshold = settings.website_quality_threshold

            if score < threshold or not lead.existing_website:
                lead.needs_website = True
                qualified += 1
            else:
                lead.needs_website = False

            lead.status = "audited"
            await db.commit()

        logger.debug(f"[Job {job_id}] Lead {lead_id}: score={score:.1f}, needs_website={lead.needs_website}")

    # Update job stats
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one()
        job.qualified_leads = qualified
        await db.commit()

    logger.info(f"[Job {job_id}] Audit complete — {qualified} leads need a website")
    return qualified
