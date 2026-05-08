---
description: Reads all 6 worker files and produces backend/agents/tools.py with correct Claude SDK tool definitions and a dispatch function
---

# tools-writer

Single output: `backend/agents/tools.py`

## Step 1 — Read these files in order

```
backend/workers/discovery.py
backend/workers/auditor.py
backend/workers/site_generator.py
backend/workers/video_recorder.py
backend/workers/message_composer.py
backend/workers/whatsapp_sender.py
backend/config.py
```

## Step 2 — Produce `TOOLS` list

Six tool definitions. One per worker's primary callable. Exact names, exact types.

| Tool name | Worker function to call | Notes |
|---|---|---|
| `search_businesses` | `fetch_google_places` (primary), `fetch_serpapi` (fallback) | dispatch checks `settings.is_real("google_places_api_key")` |
| `audit_website` | `score_website` | returns float, tool returns `{"score": float, "url": str}` |
| `generate_site` | `generate_site_openai` (primary), `generate_site_mock` (fallback) | dispatch checks `settings.is_real("openai_api_key")` |
| `record_video` | `record_site_video` | dispatch constructs `video_path` from `settings.videos_dir` |
| `compose_message` | `compose_with_openai` (primary), `compose_mock` (fallback) | dispatch checks `settings.is_real("openai_api_key")` |
| `send_whatsapp` | `send_via_twilio` (primary), `simulate_send` (fallback) | dispatch checks `settings.is_real("twilio_account_sid")` |

## Step 3 — Handle the Lead ORM mismatch

`generate_site_openai`, `generate_site_mock`, `compose_with_openai`, `compose_mock` take a SQLAlchemy `Lead` ORM object, not a dict. The Claude tool call sends a dict.

Fix with `types.SimpleNamespace`:
```python
from types import SimpleNamespace
lead_ns = SimpleNamespace(**lead_dict)
result = await generate_site_openai(lead_ns)
```

## Step 4 — `dispatch(tool_name, tool_input)` function

```python
async def dispatch(tool_name: str, tool_input: dict) -> any:
    # one elif branch per tool_name
    # no try/except — let orchestrator.py handle errors
    # for generate_site and compose_message: construct SimpleNamespace from tool_input dict
    # for record_video: auto-build video_path as:
    #   Path(settings.videos_dir) / f"lead_{tool_input['lead_id']}.webm"
```

## Step 5 — File structure

```python
"""
agents/tools.py — Claude SDK tool definitions wrapping backend/workers/
"""
from types import SimpleNamespace
from pathlib import Path
from backend.config import settings
from backend.workers.discovery import fetch_google_places, fetch_serpapi
from backend.workers.auditor import score_website
from backend.workers.site_generator import generate_site_openai, generate_site_mock
from backend.workers.video_recorder import record_site_video
from backend.workers.message_composer import compose_with_openai, compose_mock
from backend.workers.whatsapp_sender import send_via_twilio, simulate_send

TOOLS: list[dict] = [ ... ]

async def dispatch(tool_name: str, tool_input: dict) -> any:
    ...
```

## Do not

- Modify any worker file
- Add business logic to dispatch
- Create any other file
- Import anthropic inside tools.py
