"""
agents/orchestrator.py — Claude SDK agentic loop with cost controls.

For each lead in a job, runs an Anthropic tool-use loop:
  - The agent reasons (text blocks become 'thought' SSE events)
  - The agent calls tools (become 'action' SSE events)
  - Tool results become 'result' SSE events
  - Errors become 'error' SSE events
  - Strong-website / dedup skips become 'skip' SSE events
  - Cache hits / dedup hits become 'cost_saved' SSE events

Cost controls (run_job, before agent loop):
  - 24h TTL on discovery: skip API call if same (city,category) ran recently
  - Phone dedup: drop leads whose phone exists in any earlier job
  - max_leads cap: slice the lead list before paying Anthropic per-lead
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Awaitable

import anthropic
from sqlalchemy import select, func

from config import settings
from database import AsyncSessionLocal
from models import Job, Lead
from agents.tools import TOOLS, dispatch, LAST_CACHE_HIT


_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
MODEL = "claude-sonnet-4-6"
SEO_THRESHOLD = 60
MAX_TURNS = 12
DISCOVERY_TTL_HOURS = 24


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

    # Pre-flight skip — already audited as strong site
    # (Phone dedup is handled at run_job level so we never pay Anthropic per dup.)
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
    cache_read_total = 0
    cache_write_total = 0

    for _ in range(MAX_TURNS):
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            # Cache breakpoint on system → covers tools + system (~1.2K tokens).
            # Cache write = 1.25× input price ONCE; reads = 0.10× thereafter.
            # 5-min TTL refreshes on every hit, so sequential leads stay warm.
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            tools=TOOLS,
            messages=messages,
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            cache_write_total += getattr(usage, "cache_creation_input_tokens", 0) or 0
            cache_read_total += getattr(usage, "cache_read_input_tokens", 0) or 0

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
                    # Cache-hit telemetry: emit cost_saved when template cache served the request.
                    if block.name in ("generate_site", "compose_message"):
                        if LAST_CACHE_HIT.get(block.name) is True:
                            await _emit(
                                broadcast, job_id, lead_id_str, "result",
                                f"💰 cost_saved: {block.name} served from template cache (no AI call)"
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
                break

        if response.stop_reason == "end_turn" and not tool_call_made:
            if not sent:
                skipped = True
            break

        if response.stop_reason == "max_tokens":
            await _emit(broadcast, job_id, lead_id_str, "error", "max_tokens reached")
            break
    else:
        await _emit(broadcast, job_id, lead_id_str, "error",
                    f"agent loop hit MAX_TURNS={MAX_TURNS}")

    if cache_read_total or cache_write_total:
        # Cost delta: cached read at $0.30/M vs uncached at $3/M  → save $2.70/M.
        saved_usd = (cache_read_total * 2.70) / 1_000_000
        await _emit(
            broadcast, job_id, lead_id_str, "result",
            f"💰 prompt_cache: write={cache_write_total} read={cache_read_total} tok "
            f"(~${saved_usd:.4f} saved this lead)"
        )

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead.id))
        db_lead = result.scalar_one_or_none()
        if db_lead:
            if sent:
                db_lead.status = "message_sent"
            elif skipped:
                db_lead.status = "skipped"
            await db.commit()


async def _maybe_reuse_recent_leads(job: Job, broadcast, job_id: int) -> bool:
    """24h TTL: if same (city,category) ran recently and was not force_refreshed,
    clone the prior job's leads into this job and skip the discovery API call.
    Returns True if we reused (and therefore should skip run_discovery)."""
    if job.force_refresh:
        return False

    cutoff = datetime.utcnow() - timedelta(hours=DISCOVERY_TTL_HOURS)
    async with AsyncSessionLocal() as db:
        prior_q = await db.execute(
            select(Job).where(
                Job.id != job.id,
                Job.city == job.city,
                Job.category == job.category,
                Job.created_at >= cutoff,
                Job.total_found > 0,
            ).order_by(Job.created_at.desc()).limit(1)
        )
        prior = prior_q.scalar_one_or_none()
        if not prior:
            return False

        leads_q = await db.execute(select(Lead).where(Lead.job_id == prior.id))
        prior_leads = list(leads_q.scalars().all())
        if not prior_leads:
            return False

        for pl in prior_leads:
            db.add(Lead(
                job_id=job.id,
                business_name=pl.business_name,
                phone=pl.phone, email=pl.email, address=pl.address,
                city=pl.city, category=pl.category,
                existing_website=pl.existing_website,
                website_score=pl.website_score,
                needs_website=pl.needs_website,
                status="audited",
            ))

        cur = await db.execute(select(Job).where(Job.id == job.id))
        j = cur.scalar_one_or_none()
        if j:
            j.total_found = len(prior_leads)
            j.current_step = "reused_cache"
        await db.commit()

    age_hours = (datetime.utcnow() - prior.created_at).total_seconds() / 3600
    await _emit(
        broadcast, job_id, "", "result",
        f"💰 cost_saved: reusing {len(prior_leads)} leads from job #{prior.id} "
        f"({age_hours:.1f}h ago). Skipping discovery API call. "
        f"Toggle 'Force refresh' to override."
    )
    return True


async def _phone_dedup(job_id: int, broadcast) -> int:
    """Mark leads as 'duplicate' when phone matches any earlier Lead in another job.
    Returns count of dedup hits."""
    skipped = 0
    async with AsyncSessionLocal() as db:
        cur = await db.execute(
            select(Lead).where(Lead.job_id == job_id, Lead.phone.isnot(None))
        )
        my_leads = list(cur.scalars().all())

        for lead in my_leads:
            dup_q = await db.execute(
                select(func.count(Lead.id)).where(
                    Lead.phone == lead.phone,
                    Lead.job_id != job_id,
                )
            )
            count = dup_q.scalar_one()
            if count > 0:
                lead.status = "duplicate"
                skipped += 1

        await db.commit()

    if skipped > 0:
        await _emit(
            broadcast, job_id, "", "result",
            f"💰 cost_saved: {skipped} duplicate phone(s) skipped before agent loop. "
            f"Saved ~{skipped} Anthropic agent runs."
        )
    return skipped


async def run_job(job_id: int,
                  broadcast: Callable[[int, dict], Awaitable[None]]) -> None:
    """Pipeline entry point. Phases: discover (or reuse), audit, dedup, cap, agent loop, finalize."""

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return
        job.status = "running"
        job.current_step = "agent_loop"
        await db.commit()
        # Snapshot job state we need after session close
        job_snap = SimpleNamespace(
            id=job.id, city=job.city, category=job.category,
            max_leads=job.max_leads, force_refresh=job.force_refresh,
        )

    # ─── Phase 1 — discovery (with 24h TTL short-circuit) ───────────────────
    try:
        async with AsyncSessionLocal() as db:
            cur = await db.execute(select(Job).where(Job.id == job_id))
            job = cur.scalar_one_or_none()

        reused = await _maybe_reuse_recent_leads(job, broadcast, job_id)

        if not reused:
            from workers.discovery import run_discovery
            await broadcast(job_id, {
                "type": "thought", "lead_id": "",
                "content": f"Discovering businesses in {job_snap.city} for category '{job_snap.category}'...",
                "timestamp": time.time(),
            })
            await run_discovery(job_id)

            from workers.auditor import run_audit
            await broadcast(job_id, {
                "type": "thought", "lead_id": "",
                "content": "Auditing existing websites...",
                "timestamp": time.time(),
            })
            await run_audit(job_id)
    except Exception as e:
        async with AsyncSessionLocal() as db:
            cur = await db.execute(select(Job).where(Job.id == job_id))
            job = cur.scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = f"discovery/audit failed: {e}"
                await db.commit()
        await broadcast(job_id, {
            "type": "error", "lead_id": "", "content": str(e), "timestamp": time.time()
        })
        return

    # ─── Phase 2 — phone dedup (drops repeat targets BEFORE Anthropic loop) ──
    await _phone_dedup(job_id, broadcast)

    # ─── Phase 3 — apply max_leads cap ──────────────────────────────────────
    async with AsyncSessionLocal() as db:
        cur = await db.execute(
            select(Lead).where(
                Lead.job_id == job_id,
                Lead.status.in_(["discovered", "audited"]),
            ).order_by(Lead.website_score.asc().nulls_first(), Lead.id.asc())
        )
        eligible = list(cur.scalars().all())

        cap = max(1, int(job_snap.max_leads or 25))
        capped = eligible[:cap]
        dropped = eligible[cap:]

        for d in dropped:
            d.status = "over_cap"
        await db.commit()

    if dropped:
        await _emit(
            broadcast, job_id, "", "result",
            f"💰 cost_saved: lead cap = {cap}. Dropped {len(dropped)} extra lead(s) "
            f"to control API spend. Increase 'Max leads' on the next job to widen."
        )

    leads_snapshot = [
        SimpleNamespace(
            id=l.id, job_id=l.job_id, business_name=l.business_name,
            category=l.category, city=l.city, address=l.address,
            phone=l.phone, existing_website=l.existing_website,
            website_score=l.website_score, needs_website=l.needs_website,
            generated_site_path=l.generated_site_path, video_path=l.video_path,
            status=l.status,
        )
        for l in capped
    ]

    # ─── Phase 4 — run agent loop per (capped, deduped) lead ────────────────
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

    # ─── Phase 5 — finalize counters ────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        cur = await db.execute(select(Job).where(Job.id == job_id))
        job = cur.scalar_one_or_none()
        if job:
            job.status = "completed"
            job.current_step = None

            sent_q = await db.execute(
                select(func.count(Lead.id)).where(
                    Lead.job_id == job_id, Lead.status == "message_sent"
                )
            )
            job.outreach_sent = int(sent_q.scalar_one() or 0)

            skip_q = await db.execute(
                select(func.count(Lead.id)).where(
                    Lead.job_id == job_id,
                    Lead.status.in_(["skipped", "duplicate", "over_cap"]),
                )
            )
            job.skipped_count = int(skip_q.scalar_one() or 0)

            qual_q = await db.execute(
                select(func.count(Lead.id)).where(
                    Lead.job_id == job_id, Lead.needs_website == True   # noqa: E712
                )
            )
            job.qualified_leads = int(qual_q.scalar_one() or 0)

            await db.commit()

    await broadcast(job_id, {
        "type": "done",
        "lead_id": "",
        "content": "Pipeline complete",
        "timestamp": time.time(),
    })
