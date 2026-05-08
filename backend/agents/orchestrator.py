"""
agents/orchestrator.py — Claude SDK agentic loop.

Replaces the linear workers/orchestrator.py.
For each lead in a job, runs an Anthropic tool-use loop:
  - The agent reasons (text blocks become 'thought' SSE events)
  - The agent calls tools (become 'action' SSE events)
  - Tool results become 'result' SSE events
  - Errors become 'error' SSE events
  - Strong-website skips become 'skip' SSE events
"""
import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Awaitable

import anthropic
from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal
from models import Job, Lead, Outreach
from agents.tools import TOOLS, dispatch


_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
MODEL = "claude-sonnet-4-6"
SEO_THRESHOLD = 60
MAX_TURNS = 12   # safety cap on tool-use loop


async def _emit(broadcast: Callable[[int, dict], Awaitable[None]],
                job_id: int, lead_id: str, event_type: str, content: str):
    await broadcast(job_id, {
        "type": event_type,
        "lead_id": lead_id,
        "content": content,
        "timestamp": time.time(),
    })


async def run_agent(lead: Lead, job_id: int,
                    broadcast: Callable[[int, dict], Awaitable[None]]) -> None:
    """Process a single lead through the Claude SDK loop."""
    lead_id_str = str(lead.id)
    score = lead.website_score if lead.existing_website else 0.0
    score = score or 0.0

    # Pre-flight skip #1 — phone already messaged in any prior job (dedup)
    if lead.phone:
        async with AsyncSessionLocal() as db:
            dup = await db.execute(
                select(Lead).join(Outreach, Outreach.lead_id == Lead.id).where(
                    Lead.phone == lead.phone,
                    Lead.id != lead.id,
                    Outreach.whatsapp_status.in_(["sent", "delivered", "read"]),
                )
            )
            if dup.scalars().first():
                await _emit(
                    broadcast, job_id, lead_id_str, "skip",
                    f"{lead.business_name} ({lead.phone}) already contacted in earlier outreach. Skipping."
                )
                cur = await db.execute(select(Lead).where(Lead.id == lead.id))
                db_lead = cur.scalar_one_or_none()
                if db_lead:
                    db_lead.status = "skipped"
                    await db.commit()
                return

    # Pre-flight skip #2 — already audited as strong site
    if score > SEO_THRESHOLD:
        await _emit(
            broadcast, job_id, lead_id_str, "skip",
            f"{lead.business_name} already has a strong website (score {score:.0f}). Skipping outreach."
        )
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead.id))
            db_lead = result.scalar_one_or_none()
            if db_lead:
                db_lead.status = "skipped"
                await db.commit()
        return

    threshold = settings.website_quality_threshold

    user_message = (
        f"Process this lead:\n"
        f"Name: {lead.business_name}\n"
        f"Category: {lead.category}, City: {lead.city}\n"
        f"Address: {lead.address or 'Unknown'}\n"
        f"Phone: {lead.phone or 'Unknown'}\n"
        f"Website: {lead.existing_website or 'None'}\n"
        f"Website score: {score}\n"
        f"Score thresholds: build_site if < {threshold}, "
        f"seo_pitch if {threshold}–{SEO_THRESHOLD}, skip if > {SEO_THRESHOLD}\n"
        f"Lead ID: {lead.id}"
    )

    client = anthropic.AsyncAnthropic()
    messages = [{"role": "user", "content": user_message}]

    sent = False
    skipped = False

    for _ in range(MAX_TURNS):
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_call_made = False
        for block in response.content:
            if block.type == "text":
                text = block.text.strip()
                if text:
                    await _emit(broadcast, job_id, lead_id_str, "thought", text)
            elif block.type == "tool_use":
                tool_call_made = True
                await _emit(
                    broadcast, job_id, lead_id_str, "action",
                    f"{block.name} ← {json.dumps(block.input)}"
                )
                try:
                    result = await dispatch(block.name, block.input)
                    await _emit(
                        broadcast, job_id, lead_id_str, "result",
                        str(result)[:300]
                    )
                    if block.name == "send_whatsapp":
                        sent = True
                except Exception as e:
                    await _emit(broadcast, job_id, lead_id_str, "error", str(e))
                    result = {"error": str(e)}

                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }],
                })
                break  # break-after-tool-call — re-enter loop

        if response.stop_reason == "end_turn" and not tool_call_made:
            # Agent decided not to act — likely a high-score skip
            if not sent:
                skipped = True
            break

        if response.stop_reason == "max_tokens":
            await _emit(broadcast, job_id, lead_id_str, "error", "max_tokens reached")
            break
    else:
        await _emit(broadcast, job_id, lead_id_str, "error",
                    f"agent loop hit MAX_TURNS={MAX_TURNS}")

    # Persist final lead status
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead.id))
        db_lead = result.scalar_one_or_none()
        if db_lead:
            if sent:
                db_lead.status = "message_sent"
            elif skipped:
                db_lead.status = "skipped"
            await db.commit()


async def run_job(job_id: int,
                  broadcast: Callable[[int, dict], Awaitable[None]]) -> None:
    """Process all leads in a job sequentially. Called as a FastAPI background task —
    creates its own DB session because the request session is closed by the time we run."""

    # Phase 1 — discover leads if not already discovered, then mark job running
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return
        job.status = "running"
        job.current_step = "agent_loop"
        await db.commit()

    # Run discovery + audit via existing workers (these handle their own sessions)
    try:
        from workers.discovery import run_discovery
        from workers.auditor import run_audit

        await broadcast(job_id, {
            "type": "thought", "lead_id": "",
            "content": f"Discovering businesses in {job.city} for category '{job.category}'...",
            "timestamp": time.time(),
        })
        await run_discovery(job_id)

        await broadcast(job_id, {
            "type": "thought", "lead_id": "",
            "content": "Auditing existing websites...",
            "timestamp": time.time(),
        })
        await run_audit(job_id)
    except Exception as e:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = f"discovery/audit failed: {e}"
                await db.commit()
        await broadcast(job_id, {
            "type": "error", "lead_id": "", "content": str(e), "timestamp": time.time()
        })
        return

    # Phase 2 — fetch leads ready for the agent loop
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Lead).where(
                Lead.job_id == job_id,
                Lead.status.in_(["discovered", "audited"]),
            )
        )
        leads = list(result.scalars().all())
        # Snapshot ORM attrs to plain objects so the loop can use them after the
        # session closes (lazy-load would otherwise raise).
        leads_snapshot = [
            SimpleNamespace(
                id=l.id, job_id=l.job_id, business_name=l.business_name,
                category=l.category, city=l.city, address=l.address,
                phone=l.phone, existing_website=l.existing_website,
                website_score=l.website_score, needs_website=l.needs_website,
                generated_site_path=l.generated_site_path, video_path=l.video_path,
                status=l.status,
            )
            for l in leads
        ]

    # Phase 3 — run the agent loop per lead
    for lead in leads_snapshot:
        try:
            await run_agent(lead, job_id, broadcast)
        except Exception as e:
            await broadcast(job_id, {
                "type": "error",
                "lead_id": str(getattr(lead, "id", "")),
                "content": f"agent failed: {e}",
                "timestamp": time.time(),
            })

    # Phase 4 — finalize job
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.status = "completed"
            job.current_step = None
            sent_count_q = await db.execute(
                select(Lead).where(Lead.job_id == job_id, Lead.status == "message_sent")
            )
            job.outreach_sent = len(list(sent_count_q.scalars().all()))
            await db.commit()

    await broadcast(job_id, {
        "type": "done",
        "lead_id": "",
        "content": "Pipeline complete",
        "timestamp": time.time(),
    })


