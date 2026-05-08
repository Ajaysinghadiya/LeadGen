---
description: Verifies the SSE pipe works end-to-end — creates a real job and reads first 10 agent events
---

## Step 1 — Check backend is running

```bash
curl -s http://localhost:8000/docs > /dev/null && echo "UP" || echo "DOWN"
```

If DOWN: stop here and print:
```
Backend is not running.
Start it with: cd backend && uvicorn main:app --reload --port 8000
```

## Step 2 — Create a test job

```bash
curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"city": "Jaipur", "category": "sweet shop"}'
```

Save `job_id` from the response JSON. If the request fails, print the error and stop.

## Step 3 — Read the SSE stream

Connect to `GET http://localhost:8000/jobs/{job_id}/stream` and read events.
Use Python's `httpx` with streaming to collect events:

```python
import httpx, json, asyncio, time

async def read_events(job_id: str, max_events: int = 10, timeout_sec: int = 30):
    events = []
    deadline = time.time() + timeout_sec
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"http://localhost:8000/jobs/{job_id}/stream") as r:
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    events.append(event)
                    print(f"[{event['type']:8}] lead_{event['lead_id']}: {event['content'][:80]}")
                    if len(events) >= max_events:
                        break
                if time.time() > deadline:
                    print("Timeout reached")
                    break
    return events
```

Print each event as it arrives.

## Step 4 — Verify

After collecting events, check:

| Check | Result |
|---|---|
| At least 1 `thought` event received | ✓/✗ |
| At least 1 `action` event received | ✓/✗ |
| Each event has keys: type, lead_id, content, timestamp | ✓/✗ |
| `type` value is one of: thought/action/result/error/skip/done | ✓/✗ |

If any check fails: print the raw event that failed and the reason.

Stop after 10 events — do not wait for the full job to complete.

## Step 5 — Report

```
Job ID:    <job_id>
Events:    <count> received in <elapsed>s
Schema:    PASS / FAIL
thought:   SEEN / NOT SEEN
action:    SEEN / NOT SEEN
Overall:   PASS / FAIL
```
