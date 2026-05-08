---
description: Writes backend/agents/orchestrator.py — the Claude SDK agentic loop that replaces workers/orchestrator.py
---

# loop-builder

Single output: `backend/agents/orchestrator.py`
Also create: `backend/agents/__init__.py` (empty)

## Read first (in this order)

1. `CLAUDE.md` — SDK loop pattern, decision thresholds, SSE event shape, Lead/Job attribute names
2. `backend/agents/tools.py` — TOOLS list and dispatch() signature
3. `backend/agents/prompts/system.md` — system prompt text to load
4. `backend/models.py` — Lead and Job ORM models (exact field names)
5. `backend/config.py` — settings object, website_quality_threshold
6. `backend/routers/jobs.py` — broadcast_event() signature (this is how SSE events get sent)

## Produce these two functions

### `async run_agent(lead: Lead, job_id: int, broadcast: Callable) -> None`

Processes a single lead through the Claude SDK loop.

```
1. Read lead.website_score. If lead.existing_website is None or empty: treat score as 0.
   - score > SEO_THRESHOLD (60): call broadcast(job_id, skip_event), update lead.status="skipped", return
   - Otherwise: enter Claude SDK loop

2. Build user message:
   user_message = (
       f"Process this lead:\n"
       f"Name: {lead.business_name}\n"
       f"Category: {lead.category}, City: {lead.city}\n"
       f"Website: {lead.existing_website or 'None'}\n"
       f"Website score: {lead.website_score or 0}\n"
       f"Score thresholds: build_site if < {settings.website_quality_threshold}, "
       f"seo_pitch if {settings.website_quality_threshold}–60, skip if > 60\n"
       f"Lead ID: {lead.id}"
   )

3. Run the SDK loop from CLAUDE.md — break-after-tool-call pattern

4. After loop completes: open a new AsyncSessionLocal(), update lead.status = "message_sent",
   await db.commit(), await db.close()
   (Use "message_sent" — exact value from models.py status enum)
```

**broadcast signature** (from routers/jobs.py):
```python
async def broadcast(job_id: int, event: dict) -> None
# event shape: {"type": str, "lead_id": str, "content": str, "timestamp": float}
```

### `async run_job(job_id: int, broadcast: Callable) -> None`

Processes all leads in a job sequentially. This is the function called as a background task.

```python
async def run_job(job_id: int, broadcast: Callable) -> None:
    # IMPORTANT: Create own AsyncSessionLocal() — never receive db as parameter.
    # The request session is closed before background tasks run.

    async with AsyncSessionLocal() as db:
        # 1. Set job.status = "running", await db.commit()
        # 2. Query all leads for job_id where status IN ("discovered", "audited")
        # 3. Update job.total_found = len(leads), await db.commit()

    # 4. For each lead: await run_agent(lead, job_id, broadcast)

    async with AsyncSessionLocal() as db:
        # 5. Set job.status = "completed"
        # 6. Count leads with status="message_sent" → job.outreach_sent
        # 7. await db.commit()

    # 8. Broadcast done sentinel:
    await broadcast(job_id, {"type": "done", "lead_id": "", "content": "Pipeline complete", "timestamp": time.time()})
```

## Imports

```python
import asyncio, json, time
from pathlib import Path
from typing import Callable
import anthropic
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Job, Lead
from agents.tools import TOOLS, dispatch
```

Note: imports use relative-style module names (`from database import ...`, `from models import ...`)
matching the existing workers pattern, not `from backend.database import ...`.

Load system prompt at module level:
```python
_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
MODEL = "claude-sonnet-4-6"
SEO_THRESHOLD = 60
```

## Do not

- Accept `db: AsyncSession` as a parameter to `run_job` or `run_agent`
- Use `Job.steps_total` or `Job.steps_done` — these fields don't exist
- Set `lead.status = "processed"` — use `"message_sent"` (exact value from models.py)
- Import from `routers/` — only import `broadcast_event` pattern, don't import the function
- Create FastAPI routes
- Call any worker directly — all worker calls go through `dispatch()`
- Use `time.sleep()` — use `asyncio.sleep()` if needed
