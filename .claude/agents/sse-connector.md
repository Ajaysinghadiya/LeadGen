---
description: Adds agent thoughts SSE pipe to backend/routers/jobs.py — minimum changes only
---

# sse-connector

Modifies: `backend/routers/jobs.py`
Imports from: `backend.agents.orchestrator` (run_job)

**Read the entire `backend/routers/jobs.py` before touching it.**
Make minimum changes. Do not rewrite existing routes.

## What to add

### 1. Module-level queue registry

Add at the top of the file, after existing imports:
```python
import asyncio
from backend.agents.orchestrator import run_job

job_queues: dict[str, asyncio.Queue] = {}
```

### 2. Replace background task call in POST /jobs

Find where the existing background task is started (it calls workers/orchestrator.py).
Replace that call with:
```python
job_queues[str(job.id)] = asyncio.Queue()
background_tasks.add_task(run_job, job.id, db, job_queues[str(job.id)])
```

Remove the import of the old `orchestrate` function from `workers/orchestrator.py`.

### 3. Update GET /jobs/{id}/stream SSE route

The existing SSE route streams events. Update it to pull from `job_queues[job_id]`:

```python
@router.get("/{job_id}/stream")
async def stream_job_events(job_id: str, request: Request):
    async def event_generator():
        queue = job_queues.get(job_id)
        if not queue:
            return

        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                if event.get("type") == "done":
                    break
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"   # SSE comment keeps connection alive

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

If `json` is not already imported in jobs.py, add `import json`.

## What not to change

- Route paths
- Job creation logic
- Lead querying logic
- Any other existing route
- The `get_sse_queues()` or `broadcast_event()` functions if they exist — check first

## Verify

After editing, run:
```bash
cd backend && python -c "from routers.jobs import router; print('OK')"
```
If it fails, fix the import error before finishing.
