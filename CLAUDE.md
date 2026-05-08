# LeadGen 2.0 — Claude Code Brain File

## Project state

**Complete and locked — never modify these:**
- `backend/workers/` — all 6 workers built, real API + mock fallback both work
- `backend/routers/jobs.py`, `routers/leads.py` — CRUD + SSE stream complete
- `backend/models.py`, `schemas.py`, `database.py`, `config.py`, `main.py` — complete

**Being built — the agentic layer:**
- `backend/agents/prompts/system.md`
- `backend/agents/tools.py`
- `backend/agents/orchestrator.py`
- `backend/mcp_servers/whatsapp_mcp.py`
- `backend/mcp_servers/serp_mcp.py`
- `backend/routers/jobs.py` → add agent thoughts SSE pipe
- `frontend/app/jobs/[id]/page.js` → Agent Thoughts panel

---

## Exact worker function signatures (read-only)

These are the real signatures from the codebase. Do not invent different ones.

```python
# discovery.py
async def fetch_google_places(city: str, category: str) -> list[dict]
# returns: [{business_name, phone, email, address, existing_website}]

async def fetch_serpapi(city: str, category: str) -> list[dict]
# returns: same shape as fetch_google_places

# auditor.py
async def score_website(url: str) -> float
# returns: float 0.0–100.0

# site_generator.py — both take Lead ORM object, not a dict
async def generate_site_openai(lead: Lead) -> str   # returns raw HTML string
def generate_site_mock(lead: Lead) -> str            # returns raw HTML string

# video_recorder.py
async def record_site_video(html_path: str, video_path: str, business_name: str) -> bool

# message_composer.py — both take Lead ORM object
async def compose_with_openai(lead: Lead) -> str
def compose_mock(lead: Lead) -> str

# whatsapp_sender.py
async def send_via_twilio(phone: str, message: str, video_url: str | None = None) -> dict
# returns: {sid: str, status: str}
async def simulate_send(phone: str, message: str) -> dict
# returns: {sid: str, status: str}
```

**Lead ORM object key attributes:**
`lead.business_name`, `lead.category`, `lead.city`, `lead.address`, `lead.phone`, `lead.needs_website`, `lead.website_score`, `lead.site_html_path`, `lead.video_path`

**How tools.py must handle Lead ORM mismatch:**
Workers taking `lead: Lead` cannot accept dicts from Claude tool calls.
`tools.py` must create a `types.SimpleNamespace` adapter:
```python
from types import SimpleNamespace
mock_lead = SimpleNamespace(**lead_dict)  # lead_dict from DB query
```

---

## Decision thresholds

```python
LOW_QUALITY   = 30   # settings.website_quality_threshold — from config.py
SEO_THRESHOLD = 60   # second threshold for pivot logic

score < LOW_QUALITY   → full pipeline: generate_site → record_video → compose("build_site") → send
LOW_QUALITY <= score <= SEO_THRESHOLD → seo_pitch: compose("seo_pitch") → send
score > SEO_THRESHOLD → skip, emit reason, next lead
```

`LOW_QUALITY` comes from `settings.website_quality_threshold`. Read it — don't hardcode 30.

---

## SSE event shape

All agent events must match this exactly:
```python
{
    "type": "thought" | "action" | "result" | "error" | "skip",
    "lead_id": str,          # str(lead.id)
    "content": str,
    "timestamp": float       # time.time()
}
```

Formatted for SSE wire: `f"data: {json.dumps(event)}\n\n"`

---

## Claude SDK loop pattern — follow exactly

```python
import anthropic
from backend.agents.tools import TOOLS, dispatch

client = anthropic.AsyncAnthropic()
MODEL = "claude-sonnet-4-6"

messages = [{"role": "user", "content": f"Process this lead: {lead_dict}"}]

while True:
    response = await client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,   # loaded from agents/prompts/system.md
        tools=TOOLS,
        messages=messages,
    )
    for block in response.content:
        if block.type == "text":
            await emit("thought", lead_id, block.text)
        elif block.type == "tool_use":
            await emit("action", lead_id, f"{block.name} ← {json.dumps(block.input)}")
            try:
                result = await dispatch(block.name, block.input)
                await emit("result", lead_id, str(result)[:300])
            except Exception as e:
                await emit("error", lead_id, str(e))
                result = {"error": str(e)}
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": block.id, "content": str(result)}]
            })
            break   # re-enter loop after each tool call
    if response.stop_reason == "end_turn":
        break
```

---

## Hard rules

- No Claude SDK / Anthropic imports inside `workers/` — ever
- `tools.py` is a thin wrapper layer only — zero business logic
- All new code in `agents/` and `mcp_servers/` is async — no `time.sleep()`
- Never modify worker function signatures
- `settings.is_real("twilio_account_sid")` → use Twilio; else `simulate_send()`
- `settings.is_real("openai_api_key")` → use OpenAI workers; else mock
- MCP servers only for Twilio and Google Places/SerpAPI — nothing else gets MCP
- Agent thoughts SSE uses the existing `job_queues` dict in `routers/jobs.py`
