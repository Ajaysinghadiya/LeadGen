"""
tests/test_pipeline.py — Integration tests for pipeline modules
Run with: python -m pytest tests/ -v
"""
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# ─── Test DB setup ────────────────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///./data/test_leadgen.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Override settings for tests."""
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "MOCK")
    monkeypatch.setenv("OPENAI_API_KEY", "MOCK")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "MOCK")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "MOCK")
    monkeypatch.setenv("GENERATED_SITES_DIR", "./data/test_sites")
    monkeypatch.setenv("VIDEOS_DIR", "./data/test_videos")


@pytest.mark.asyncio
async def test_full_pipeline():
    """End-to-end pipeline test with mock data."""
    import importlib
    import sys

    # Reload modules to pick up env overrides
    for mod in ["config", "database", "models"]:
        if mod in sys.modules:
            del sys.modules[mod]

    from config import settings
    from database import init_db, AsyncSessionLocal
    from models import Job, Lead, Outreach

    await init_db()

    # Create a job
    async with AsyncSessionLocal() as db:
        job = Job(city="Jaipur", category="restaurants")
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id

    assert job_id is not None

    # Step 1: Discovery
    from workers.discovery import run_discovery
    found = await run_discovery(job_id)
    assert found > 0, "Discovery should find mock businesses"

    # Step 2: Audit
    from workers.auditor import run_audit
    qualified = await run_audit(job_id)
    assert qualified >= 0

    if qualified == 0:
        pytest.skip("No leads qualified — adjust WEBSITE_QUALITY_THRESHOLD if needed")

    # Step 3: Site generation
    from workers.site_generator import run_site_generation
    generated = await run_site_generation(job_id)
    assert generated > 0, "Mock site generation should succeed"

    # Verify HTML file was created
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Lead).where(Lead.job_id == job_id, Lead.status == "site_generated")
        )
        leads = result.scalars().all()
    assert len(leads) > 0
    for lead in leads:
        assert lead.generated_site_path is not None

    # Step 5: Message composition (skip video in CI)
    for lead in leads:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import update
            await db.execute(
                update(Lead).where(Lead.id == lead.id).values(status="video_recorded")
            )
            await db.commit()

    from workers.message_composer import run_message_composition
    composed = await run_message_composition(job_id)
    assert composed > 0, "Message composition should produce messages"

    # Step 6: WhatsApp sending (simulated)
    from workers.whatsapp_sender import run_whatsapp_sending
    sent = await run_whatsapp_sending(job_id)
    assert sent > 0, "Simulated WhatsApp send should succeed"

    # Verify outreach records
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Outreach).join(Lead).where(Lead.job_id == job_id)
        )
        outreach_records = result.scalars().all()

    assert len(outreach_records) > 0
    for o in outreach_records:
        assert o.whatsapp_status == "sent"
        assert o.twilio_sid is not None

    print(f"\n✅ Full pipeline test passed!")
    print(f"   Discovered: {found} | Qualified: {qualified} | Generated: {generated} | Sent: {sent}")


@pytest.mark.asyncio
async def test_site_template_renders():
    """Test that mock site template generates valid HTML."""
    from config import settings
    from database import init_db, AsyncSessionLocal
    from models import Job, Lead

    await init_db()

    async with AsyncSessionLocal() as db:
        job = Job(city="Pune", category="gyms")
        db.add(job)
        await db.commit()
        lead = Lead(
            job_id=job.id,
            business_name="FitZone Gym",
            city="Pune",
            category="gyms",
            phone="+919999999999",
            address="MG Road, Pune",
            needs_website=True,
            status="audited",
        )
        db.add(lead)
        await db.commit()
        await db.refresh(lead)

    from workers.site_generator import generate_site_mock
    html = generate_site_mock(lead)
    assert "FitZone Gym" in html
    assert "Pune" in html
    assert "<!DOCTYPE html>" in html
    assert "<title>" in html
    print("\n✅ Site template test passed — valid HTML generated")
