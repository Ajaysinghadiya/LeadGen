# LeadGen 2.0

> **Agentic Lead Generation & Automated Outreach for Local Businesses**

AI-powered system that finds local businesses without websites, generates custom site previews, records video tours, and sends personalized WhatsApp pitches — all orchestrated by a Claude SDK agent that reasons through each lead independently.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-orange)](https://anthropic.com)
[![Status](https://img.shields.io/badge/v2-shipped-success)](#build-status)

---

## What It Does

```
City + Category
      ↓
[Claude Agent] → searches Google Places / SerpAPI for local businesses
      ↓
      → audits each existing website (0–100 score)
      ↓
      → reasons: "Does this business need help, and what kind?"
      ↓
      → branches:
          score < 30  → generate site → record video → pitch "build_site" → WhatsApp
          30 ≤ s ≤ 60 → pitch "seo_pitch" → WhatsApp
          score > 60  → skip with explanation
      ↓
Live Agent Thoughts panel streams reasoning + tool calls per lead.
```

The agent is **not** a fixed pipeline. It reasons per lead, picks the right branch, and explains skips. Every text block becomes a "thought" event; every tool call becomes an "action" event; every result/error becomes a labeled SSE event for the dashboard.

---

## Architecture

### v2 — Agentic Layer (shipped)

```
POST /jobs ─► routers/jobs.py ─► run_pipeline (background task)
                                        │
                                        ▼
                       agents/orchestrator.py  (Claude SDK loop)
                                        │
            ┌───────────────────────────┼─────────────────────────────┐
            ▼                           ▼                             ▼
    agents/prompts/              agents/tools.py            mcp_servers/
    system.md                    (TOOLS + dispatch)         (external API wrappers)
    persona + branching          adapter to workers/        whatsapp_mcp.py
                                        │                  serp_mcp.py
                                        ▼
                            backend/workers/  (locked, pure execution)
                            discovery / auditor / site_generator /
                            video_recorder / message_composer / whatsapp_sender

    SSE event shape: {type, lead_id, content, timestamp}
    Types: thought | action | result | error | skip | done
```

### Design rules

- `workers/` is locked. Pure execution. Zero Anthropic imports.
- `agents/tools.py` is a thin adapter only. `SimpleNamespace` shim for Lead-ORM functions.
- MCP servers exist for **external** APIs only (Twilio, Google Places/SerpAPI). Internal Python is plain Claude SDK tools — no MCP overhead.
- Background tasks create their own `AsyncSessionLocal()`. Request session is closed before the task runs.
- SSE infrastructure (`_sse_queues`, `broadcast_event`) is reused — no second queue dict.

### v1 vs v2

| v1 (linear `workers/orchestrator.py`) | v2 (`agents/orchestrator.py`) |
|---|---|
| Fixed order: discover → audit → generate → record → compose → send | Claude branches per lead based on score |
| Every business gets identical treatment | Strong sites are skipped; medium pivots to SEO |
| Step events only | thought / action / result / error / skip events |
| Zero reasoning visible | Agent Thoughts panel streams chain-of-thought |

v1 is preserved at `backend/workers/orchestrator.py` for reference but is no longer wired in.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Orchestration** | [Anthropic Claude SDK](https://github.com/anthropics/anthropic-sdk-python) | Agentic loop, reasoning, tool dispatch |
| **AI Model** | `claude-sonnet-4-6` | Per-lead orchestration |
| **Site Generation** | OpenAI GPT-4o-mini → template fallback | Generate HTML site previews |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) + async SQLAlchemy 2.0 | REST + SSE streaming |
| **Database** | SQLite (`aiosqlite`) | Jobs, leads, outreach |
| **Browser Automation** | [Playwright](https://playwright.dev/python/) | Headless video recording |
| **WhatsApp** | [Twilio](https://twilio.com) → simulation fallback | Outreach delivery |
| **Discovery** | Google Places → SerpAPI → mock fallback | Find businesses by city + category |
| **Frontend** | Next.js 15 (App Router) | Dashboard, job monitor, leads explorer |
| **Protocol** | MCP (Model Context Protocol) | Standardize external API tools |
| **Dev Loop** | Claude Code subagents + skills + hooks | See `.claude/` |

---

## Directory Structure

```
LeadGen/
├── backend/
│   ├── agents/                          # Claude SDK agentic layer (v2)
│   │   ├── __init__.py
│   │   ├── orchestrator.py              # run_agent + run_job (SDK loop)
│   │   ├── tools.py                     # 6 tool defs + dispatch()
│   │   └── prompts/
│   │       └── system.md                # Orchestrator persona + branching rules
│   │
│   ├── workers/                         # Pure execution (locked)
│   │   ├── orchestrator.py              # v1 linear pipeline (kept for reference)
│   │   ├── discovery.py                 # Google Places / SerpAPI / mock
│   │   ├── auditor.py                   # HTTP check + heuristic score (0–100)
│   │   ├── site_generator.py            # GPT-4o-mini or template HTML
│   │   ├── video_recorder.py            # Playwright headless WEBM recording
│   │   ├── message_composer.py          # Hinglish/English pitch
│   │   └── whatsapp_sender.py           # Twilio or simulated send
│   │
│   ├── mcp_servers/                     # FastMCP wrappers for external APIs only
│   │   ├── __init__.py
│   │   ├── whatsapp_mcp.py              # send_whatsapp_message tool
│   │   └── serp_mcp.py                  # search_businesses tool
│   │
│   ├── routers/
│   │   ├── jobs.py                      # Job CRUD + SSE stream + run_pipeline
│   │   └── leads.py                     # Lead explorer + site/video preview
│   │
│   ├── tests/
│   │   └── test_agent_decisions.py      # 3-lead branching test (mocked)
│   │
│   ├── main.py · models.py · schemas.py · config.py · database.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.js                      # Dashboard
│   │   ├── jobs/[id]/page.js            # Two-column: leads + Agent Thoughts panel
│   │   └── leads/page.js                # Lead explorer
│   ├── components/Sidebar.js
│   └── lib/api.js                       # apiFetch + watchJob (EventSource)
│
├── .claude/                             # Claude Code config
│   ├── agents/                          # Subagent specs (one per output file)
│   │   ├── prompt-engineer.md
│   │   ├── tools-writer.md
│   │   ├── loop-builder.md
│   │   ├── mcp-builder.md
│   │   ├── sse-connector.md
│   │   └── panel-builder.md
│   ├── skills/                          # /skill verification routines
│   │   ├── audit-workers/SKILL.md
│   │   ├── wrap-worker/SKILL.md
│   │   ├── test-decisions/SKILL.md
│   │   └── sse-check/SKILL.md
│   ├── hooks/
│   │   ├── guard_workers.py             # PreToolUse — blocks edits to locked files
│   │   └── lint_agents.sh               # PostToolUse — auto-ruff new agents/ files
│   └── settings.json
│
├── CLAUDE.md                            # Project brain — loaded every session
├── data/                                # Runtime (gitignored): leadgen.db, sites, videos
├── docker-compose.yml
└── README.md
```

---

## Data Models (actual schema)

```
Job
 ├── id, city, category
 ├── status            (pending | running | completed | failed)
 ├── current_step
 ├── total_found, qualified_leads, outreach_sent
 ├── error_message, created_at, updated_at
 └── leads[]

Lead
 ├── id, job_id
 ├── business_name, phone, email, address, city, category
 ├── existing_website, website_score (0–100), needs_website
 ├── generated_site_path, video_path
 ├── status (discovered | audited | site_generated | video_recorded |
 │          message_sent | failed | skipped)
 └── outreach (1:1)

Outreach
 ├── lead_id, message_text, video_url
 ├── whatsapp_status (pending | sent | delivered | read | failed)
 ├── twilio_sid, sent_at
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for Redis if you re-enable RQ)

### 1. Environment (`.env`)

| Key | Source | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | **Yes** — orchestrator |
| `GOOGLE_PLACES_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) | No — mock fallback |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | No — secondary fallback |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | No — template fallback |
| `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | [console.twilio.com](https://console.twilio.com) | No — simulation mode |

Without `ANTHROPIC_API_KEY` the agent loop returns 401 on first turn. Workers' OpenAI/Twilio/Google fallbacks still work standalone.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
playwright install chromium

uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:3000

### 4. (Optional) MCP servers as standalone

```bash
python -m mcp_servers.whatsapp_mcp     # stdio MCP for Twilio
python -m mcp_servers.serp_mcp         # stdio MCP for Google Places / SerpAPI
```

---

## Usage

1. Open http://localhost:3000
2. Create a job: city (e.g. `Jaipur`) + category (e.g. `sweet shop`)
3. Open the job page — left column shows leads, right column shows **Agent Thoughts**:
   - 💭 yellow rows = reasoning (text blocks)
   - ⚙️ blue rows = tool calls (mono)
   - ✓ green rows = tool results (truncated 150 chars)
   - ⚠ red rows = errors
   - ↷ gray rows = skips (strong sites)
4. Watch the agent decide per lead. Skip → SEO pitch → full build are all visible live.
5. Generated HTML and WEBM tours are linked off the leads explorer.

---

## Running the decision test

Mocks `dispatch` and Anthropic — no API calls, no DB writes.

```bash
cd backend
python tests/test_agent_decisions.py
```

Asserts:
- Lead A (score 0):  `generate_site → record_video → compose(build_site) → send_whatsapp`
- Lead B (score 35): `compose(seo_pitch) → send_whatsapp` (no site, no video)
- Lead C (score 85): pre-flight skip event, zero tool calls

---

## Claude Code Tooling

This repo is built with Claude Code subagents/skills/hooks under `.claude/`.

| Subagent | Output |
|---|---|
| `prompt-engineer` | `backend/agents/prompts/system.md` |
| `tools-writer` | `backend/agents/tools.py` |
| `loop-builder` | `backend/agents/orchestrator.py` |
| `mcp-builder` | `backend/mcp_servers/whatsapp_mcp.py` + `serp_mcp.py` |
| `sse-connector` | one-line swap in `backend/routers/jobs.py` |
| `panel-builder` | `frontend/app/jobs/[id]/page.js` |

| Skill | Verifies |
|---|---|
| `/audit-workers` | Worker signatures match `tools.py` |
| `/wrap-worker` | Single-worker tool wrap procedure |
| `/test-decisions` | 3-lead branching (mocked) — implemented at `backend/tests/test_agent_decisions.py` |
| `/sse-check` | SSE endpoint emits expected event types |

| Hook | Trigger | Purpose |
|---|---|---|
| `guard_workers.py` | PreToolUse Write/Edit | Block edits to locked layer (workers, models, routers core) |
| `lint_agents.sh` | PostToolUse Write/Edit | Auto-ruff new files in `agents/` and `mcp_servers/` |

`CLAUDE.md` is loaded every session — it pins exact worker signatures, decision thresholds, SSE event shape, and the Claude SDK loop pattern.

---

## Build Status

v2 agentic layer: **shipped**.

- [x] `backend/agents/__init__.py` + `agents/prompts/system.md`
- [x] `backend/agents/tools.py` (6 tools, dispatch with SimpleNamespace adapter)
- [x] `backend/agents/orchestrator.py` (run_agent + run_job, break-after-tool-call loop)
- [x] `backend/mcp_servers/whatsapp_mcp.py` + `serp_mcp.py`
- [x] `backend/routers/jobs.py` swap to `agents.orchestrator.run_job`
- [x] `frontend/app/jobs/[id]/page.js` two-column layout + Agent Thoughts panel
- [x] `backend/tests/test_agent_decisions.py` — 10/10 decision checks pass

---

## Contributing

1. Fork
2. Branch: `git checkout -b feature/my-feature`
3. Commit (hooks block edits to locked layer — that's intentional)
4. PR

---

## License

MIT
