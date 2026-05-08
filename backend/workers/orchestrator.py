"""
workers/orchestrator.py — Master pipeline runner
Chains all 6 steps and handles errors per step.
"""
import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable
from sqlalchemy import select

from models import Job
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)

STEPS = [
    ("discovery",   "🔍 Discovering businesses..."),
    ("audit",       "🌐 Auditing websites..."),
    ("generation",  "✨ Generating AI websites..."),
    ("recording",   "🎬 Recording video tours..."),
    ("messaging",   "💬 Composing messages..."),
    ("sending",     "📤 Sending WhatsApp messages..."),
]


async def orchestrate(
    job_id: int,
    broadcast: Callable[[int, dict], Awaitable[None]],
):
    """Run all pipeline steps for a given job."""
    logger.info(f"[Orchestrator] Starting pipeline for job {job_id}")

    async def emit(event_type: str, message: str, data: dict | None = None):
        await broadcast(job_id, {
            "type": event_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **(data or {}),
        })

    async def update_job(step: str | None, status: str, error: str | None = None):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                if step:
                    job.current_step = step
                job.status = status
                if error:
                    job.error_message = error
                await db.commit()

    await update_job(None, "running")
    await emit("started", f"🚀 Pipeline started for job {job_id}")

    try:
        # ─── Step 1: Discovery ─────────────────────────────────────────────
        await update_job("discovery", "running")
        await emit("step", "🔍 Step 1/6 — Discovering businesses...", {"step": "discovery"})
        from workers.discovery import run_discovery
        found = await run_discovery(job_id)
        await emit("step_done", f"✅ Discovery complete — {found} businesses found", {"step": "discovery", "count": found})

        # ─── Step 2: Audit ─────────────────────────────────────────────────
        await update_job("audit", "running")
        await emit("step", "🌐 Step 2/6 — Auditing websites...", {"step": "audit"})
        from workers.auditor import run_audit
        qualified = await run_audit(job_id)
        await emit("step_done", f"✅ Audit complete — {qualified} businesses need a website", {"step": "audit", "count": qualified})

        if qualified == 0:
            await update_job(None, "completed")
            await emit("done", "✅ Pipeline complete — no businesses qualify for outreach")
            return

        # ─── Step 3: Site Generation ───────────────────────────────────────
        await update_job("generation", "running")
        await emit("step", "✨ Step 3/6 — Generating AI website previews...", {"step": "generation"})
        from workers.site_generator import run_site_generation
        generated = await run_site_generation(job_id)
        await emit("step_done", f"✅ Generation complete — {generated} sites created", {"step": "generation", "count": generated})

        # ─── Step 4: Video Recording ───────────────────────────────────────
        await update_job("recording", "running")
        await emit("step", "🎬 Step 4/6 — Recording video tours...", {"step": "recording"})
        from workers.video_recorder import run_video_recording
        recorded = await run_video_recording(job_id)
        await emit("step_done", f"✅ Recording complete — {recorded} videos created", {"step": "recording", "count": recorded})

        # ─── Step 5: Message Composition ───────────────────────────────────
        await update_job("messaging", "running")
        await emit("step", "💬 Step 5/6 — Composing personalized messages...", {"step": "messaging"})
        from workers.message_composer import run_message_composition
        composed = await run_message_composition(job_id)
        await emit("step_done", f"✅ Messages composed — {composed} ready to send", {"step": "messaging", "count": composed})

        # ─── Step 6: WhatsApp Sending ──────────────────────────────────────
        await update_job("sending", "running")
        await emit("step", "📤 Step 6/6 — Sending WhatsApp messages...", {"step": "sending"})
        from workers.whatsapp_sender import run_whatsapp_sending
        sent = await run_whatsapp_sending(job_id)
        await emit("step_done", f"✅ Sending complete — {sent} messages delivered", {"step": "sending", "count": sent})

        # ─── Done ──────────────────────────────────────────────────────────
        await update_job(None, "completed")
        await emit("done", f"🎉 Pipeline complete! {sent} businesses reached on WhatsApp.")

    except Exception as e:
        logger.error(f"[Orchestrator] Job {job_id} failed: {e}", exc_info=True)
        await update_job(None, "failed", error=str(e))
        await emit("error", f"❌ Pipeline failed: {str(e)}", {"error": str(e)})
