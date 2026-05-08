---
description: Tests orchestrator decision logic against three mock leads — verifies correct pipeline branch per score
---

Do not call any real API. Do not start the server. Mock the dispatch function.

## Step 1 — Read these files

```
backend/agents/orchestrator.py
backend/agents/tools.py
backend/config.py
```

## Step 2 — Create three test leads as SimpleNamespace

```python
from types import SimpleNamespace
import time

lead_a = SimpleNamespace(
    id=1, business_name="Bassi Sweets", category="sweet shop",
    city="Jaipur", address="MI Road", phone="+91-9876543210",
    existing_website=None, website_score=0.0, needs_website=True,
    generated_site_path=None, video_path=None, status="discovered", job_id=1
)

lead_b = SimpleNamespace(
    id=2, business_name="Sharma Dhaba", category="restaurant",
    city="Ahmedabad", address="CG Road", phone="+91-9876543211",
    existing_website="http://sharmadhabaold.wordpress.com", website_score=35.0,
    needs_website=False, generated_site_path=None, video_path=None, status="audited", job_id=1
)

lead_c = SimpleNamespace(
    id=3, business_name="Taj Hotel", category="hotel",
    city="Mumbai", address="Colaba", phone="+91-2222222222",
    existing_website="https://tajhotels.com", website_score=85.0,
    needs_website=False, generated_site_path=None, video_path=None, status="audited", job_id=1
)
```

## Step 3 — Mock dispatch and emit

```python
events = []

async def mock_dispatch(tool_name, tool_input):
    events.append({"call": tool_name, "input": tool_input})
    # Return plausible mock results per tool
    if tool_name == "generate_site": return "/data/generated_sites/test.html"
    if tool_name == "record_video": return True
    if tool_name == "compose_message": return "Namaste! Aapki dukaan ke liye..."
    if tool_name == "send_whatsapp": return {"sid": "SM_MOCK_00001", "status": "simulated"}
    if tool_name == "audit_website": return {"score": float(tool_input.get("score", 50)), "url": ""}
    return {}

# Patch dispatch in agents.orchestrator
import backend.agents.orchestrator as orch
orch.dispatch = mock_dispatch
```

## Step 4 — Run run_agent for each lead with a mock emit_fn

Collect all emitted events. Print them as a table:

```
Lead A (score=0):
  [thought]  "I see Bassi Sweets has no website..."
  [action]   generate_site ← {...}
  [result]   /data/generated_sites/test.html
  [action]   record_video ← {...}
  ...

Lead B (score=35):
  [thought]  "Sharma Dhaba has a website but it scores 35..."
  [action]   compose_message ← {approach: "seo_pitch", ...}
  [action]   send_whatsapp ← {...}

Lead C (score=85):
  [skip]     "Taj Hotel has a strong website (score 85). Skipping."
```

## Step 5 — Verify

| Check | Lead A | Lead B | Lead C |
|---|---|---|---|
| `generate_site` called | ✓ | ✗ | ✗ |
| `record_video` called | ✓ | ✗ | ✗ |
| `compose_message(approach=build_site)` | ✓ | ✗ | ✗ |
| `compose_message(approach=seo_pitch)` | ✗ | ✓ | ✗ |
| `send_whatsapp` called | ✓ | ✓ | ✗ |
| Skip event emitted | ✗ | ✗ | ✓ |

If any check fails: print the actual events that were emitted and flag the discrepancy.
