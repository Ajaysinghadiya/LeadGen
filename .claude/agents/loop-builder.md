---
description: Writes backend/agents/orchestrator.py — the Claude SDK agentic loop that replaces workers/orchestrator.py
---

# loop-builder

Single output: `backend/agents/orchestrator.py`
Also create: `backend/agents/__init__.py` (empty)

## Read first (in this order)

1. `CLAUDE.md` — SDK loop pattern (exact code to follow), decision thresholds, SSE event shape
2. `backend/agents/tools.py` — TOOLS list and dispatch() signature
3. `backend/agents/prompts/system.md` — system prompt text to load
4. `backend/models.py` — Lead and Job ORM models
5. `backend/config.py` — settings object, website_quality_threshold

## Produce these two functions

### `async run_agent(lead: Lead, emit_fn: Callable, db: AsyncSession) -> None`

Processes a single lead through the Claude SDK loop.

```
1. Read lead.website_score and compare against thresholds from CLAUDE.md
   - If lead has no website (website_url is None or empty): score = 0, proceed as low
   - score > SEO_THRESHOLD (60): call emit_fn("skip", ...), update lead.status="skipped", return
   - Otherwise: enter Claude SDK loop

2. Build messages list:
   user_message = (
       f"Process this lead:\n"
       f"Name: {lead.business_name}\n"
       f"Category: {lead.category}, City: {lead.city}\n"
       f"Website: {lead.website_url or 'None'}\n"
       f"Website score: {lead.website_score}\n"
       f"Score thresholds: build_site if < {settings.website_quality_threshold}, "
       f"seo_pitch if {settings.website_quality_threshold}–60, skip if > 60\n"
       f"Lead ID: {lead.id}"
   )

3. Run the SDK loop from CLAUDE.md exactly — use the break-after-tool-call pattern

4. After loop completes: update lead.status = "processed" in DB, await db.commit()
```

**emit_fn signature:** `async def emit_fn(event_type: str, lead_id: str, content: str) -> None`

### `async run_job(job_id: int, db: AsyncSession, sse_queue: asyncio.Queue) -> None`

Processes all leads in a job sequentially.

```python
async def run_job(job_id: int, db: AsyncSession, sse_queue: asyncio.Queue) -> None:
    # 1. Query all leads for job_id where status = "qualified" or "discovered"
    # 2. Update Job.steps_total = len(leads)
    # 3. For each lead:
    #    a. Define emit_fn that puts event dict onto sse_queue
    #    b. await run_agent(lead, emit_fn, db)
    #    c. Job.steps_done += 1, await db.commit()
    # 4. Update Job.status = "completed", await db.commit()
    # 5. Put sentinel {"type": "done", "lead_id": "", "content": "", "timestamp": time.time()} onto queue
```

## emit_fn implementation

```python
async def _make_emit(lead_id: int, queue: asyncio.Queue):
    async def emit(event_type: str, lead_id_str: str, content: str) -> None:
        await queue.put({
            "type": event_type,
            "lead_id": str(lead_id),
            "content": content,
            "timestamp": time.time(),
        })
    return emit
```

## Imports

```python
import asyncio, json, time
from pathlib import Path
from typing import Callable
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.config import settings
from backend.models import Job, Lead
from backend.agents.tools import TOOLS, dispatch
```

Load system prompt at module level:
```python
_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
MODEL = "claude-sonnet-4-6"
SEO_THRESHOLD = 60
```

## Do not

- Import from `backend/routers/`
- Create FastAPI routes
- Call any worker directly — all worker calls go through `dispatch()`
- Use `time.sleep()` — use `asyncio.sleep()` if needed
