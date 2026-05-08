---
description: Checks all 6 workers are ready to be wrapped as Claude SDK tools — reads and reports, no modifications
---

Read each file below in full, then answer the four questions for each worker:

```
backend/workers/discovery.py      → function: fetch_google_places
backend/workers/auditor.py        → function: score_website
backend/workers/site_generator.py → functions: generate_site_openai, generate_site_mock
backend/workers/video_recorder.py → function: record_site_video
backend/workers/message_composer.py → functions: compose_with_openai, compose_mock
backend/workers/whatsapp_sender.py  → functions: send_via_twilio, simulate_send
```

## Four questions per worker

1. **Async?** — Is the primary callable `async def`? (Required — sync blocks the event loop in the agent)
2. **Type hints?** — Do all parameters have type annotations? (Required for `input_schema` in tools.py)
3. **Return type** — What does it return? Is it JSON-serializable (str, dict, list, float, bool)?
4. **Fallback path?** — Does it have a mock/simulation path that works without external APIs?

## Output format

Print a table:

| Worker | Function | Async | Type hints | Return type | JSON-safe | Fallback |
|---|---|---|---|---|---|---|
| discovery | fetch_google_places | ✓ | ✓ | list[dict] | ✓ | ✓ (mock) |
| ... | | | | | | |

Then flag any worker that needs attention before tools.py can be built.

**Known issue to check:** `generate_site_openai`, `generate_site_mock`, `compose_with_openai`, `compose_mock` take a `Lead` ORM object as `lead` parameter. This is NOT JSON-serializable by Claude. Flag these and confirm that tools.py will use `SimpleNamespace` adapter (see CLAUDE.md).

Do not modify any worker file. Read and report only.
