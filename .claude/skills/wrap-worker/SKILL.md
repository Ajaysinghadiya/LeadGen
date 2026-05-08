---
description: Produces the Claude SDK tool definition + dispatch case for a single worker — output ready to paste into tools.py
---

Worker to wrap: $ARGUMENTS

## Step 1 — Read the file

Read `backend/workers/$ARGUMENTS.py` in full.

## Step 2 — Identify the primary callable

Use this mapping:

| $ARGUMENTS | Primary function | Fallback |
|---|---|---|
| `discovery` | `fetch_google_places` | `fetch_serpapi` |
| `auditor` | `score_website` | none |
| `site_generator` | `generate_site_openai` | `generate_site_mock` |
| `video_recorder` | `record_site_video` | `create_mock_video` |
| `message_composer` | `compose_with_openai` | `compose_mock` |
| `whatsapp_sender` | `send_via_twilio` | `simulate_send` |

## Step 3 — Output Block A: tool definition

```python
{
    "name": "<tool_name>",
    "description": "<one sentence: what the function does>. <one sentence: when the orchestrator agent should call this tool>.",
    "input_schema": {
        "type": "object",
        "properties": {
            "<param_name>": {
                "type": "<json_type>",  # string/number/boolean/array/object
                "description": "<what this param means>"
            },
            # ... one entry per parameter
        },
        "required": ["<all params without defaults>"]
    }
}
```

**If the function takes a `lead` parameter (Lead ORM object):** Expand it as flat fields in `properties`:
- `business_name: string`
- `category: string`
- `city: string`
- `address: string | null`
- `phone: string | null`
- `lead_id: integer` (needed for video path construction)

## Step 4 — Output Block B: dispatch case

```python
elif tool_name == "<tool_name>":
    # If input has lead fields: construct SimpleNamespace
    # from types import SimpleNamespace
    # lead_ns = SimpleNamespace(**{k: tool_input[k] for k in ["business_name", "category", "city", "address", "phone"]})
    # result = await primary_function(lead_ns)
    #
    # For video_recorder: build video_path from settings.videos_dir
    # video_path = str(Path(settings.videos_dir) / f"lead_{tool_input['lead_id']}.webm")
    #
    # Check settings.is_real() for API-dependent workers to route primary vs fallback
    return <result>
```

Output only Block A and Block B. No explanation. Ready to paste into `backend/agents/tools.py`.
