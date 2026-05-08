---
description: Wires agents/orchestrator.py into routers/jobs.py — replaces workers/orchestrator call with run_job
---

# sse-connector

Modifies: `backend/routers/jobs.py`

**Read the entire `backend/routers/jobs.py` before touching it.**

## What already exists (do not touch)

- `_sse_queues: dict[int, list[asyncio.Queue]]` — already there
- `get_sse_queues()` — already there
- `broadcast_event(job_id, event)` — already there, pushes to all listeners
- `GET /{job_id}/stream` — already correct, reads from `_sse_queues`
- `StreamingResponse` with keepalive — already correct

The SSE infrastructure is complete. Do not rewrite it. Do not add a second queue dict.

## One change only: replace the background task call

In `run_pipeline(job_id: int)` at the bottom of jobs.py:

**Current:**
```python
async def run_pipeline(job_id: int):
    from workers.orchestrator import orchestrate
    await orchestrate(job_id, broadcast_event)
```

**Replace with:**
```python
async def run_pipeline(job_id: int):
    from agents.orchestrator import run_job
    await run_job(job_id, broadcast_event)
```

That's the entire change. One import swap. `broadcast_event` already has the right signature:
`async def broadcast_event(job_id: int, event: dict)` — which matches what `run_job` expects.

## Verify

After the edit, run:
```bash
cd backend && python -c "from routers.jobs import router; print('OK')"
```

If it fails with ImportError on `agents.orchestrator`, it means `agents/orchestrator.py`
hasn't been built yet — that's expected. The import is inside the function body,
so it won't fail at import time.

## Do not

- Add a new `job_queues` dict
- Modify `create_job`, `list_jobs`, `get_job`, or `stream_job_events`
- Change the SSE event format or the StreamingResponse
- Add new routes
