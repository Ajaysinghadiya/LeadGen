# LeadGen 2.0

> **Agentic Lead Generation & Automated Outreach for Local Businesses**

An AI-powered system that finds local businesses without websites, generates custom site previews, records video tours, and sends personalized WhatsApp pitches — all orchestrated by a Claude AI agent that reasons through each lead independently.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-orange)](https://anthropic.com)

---

## What It Does

```
City + Category
      ↓
[Claude Agent] → searches Google Maps for businesses without websites
      ↓
      → reasons: "Does this business actually need help?"
      ↓
      → generates a custom website preview (HTML/Tailwind)
      ↓
      → records a 10-second video tour via Playwright
      ↓
      → writes a personalized Hinglish/English pitch
      ↓
      → sends via WhatsApp (Twilio or simulation)
```

The agent isn't just a pipeline runner — it makes decisions. If a business already has a decent website, it skips them or pivots the pitch to "SEO Optimization." Every reasoning step streams live to the dashboard.

---

## Architecture

### The Agentic Layer (v2 — what we're building)

```
POST /jobs  ──►  agents/orchestrator.py  (Claude SDK loop)
                        │
              ┌─────────┼──────────────────────────┐
              │         │                          │
         tools.py   workers/ (execution)    mcp_servers/ (external APIs)
              │         │                          │
        wraps each   discovery.py             whatsapp_mcp.py
        worker as    auditor.py               serp_mcp.py
        Claude tool  site_generator.py
                     video_recorder.py
                     message_composer.py
                     whatsapp_sender.py
```

**Key design decision:** Workers are pure execution functions. The Claude SDK loop in `agents/orchestrator.py` wraps them as tools — no worker code changes needed. MCP servers only for external APIs (WhatsApp, Google Places) since those are portable integrations worth standardizing.

### vs. v1 (Linear Pipeline)

| v1 | v2 |
|---|---|
| Fixed order: discover → audit → generate → record → send | Claude decides what to do next per lead |
| OpenAI for text tasks only | Claude handles orchestration + reasoning |
| Fails silently on API errors | Agent retries, pivots to fallback, or skips |
| Every business gets identical treatment | Agent skips good websites, pivots pitch for SEO plays |
| No visibility into decisions | Agent Thoughts panel streams chain-of-thought live |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Orchestration** | [Anthropic Claude SDK](https://github.com/anthropics/anthropic-sdk-python) | Agentic loop, reasoning, tool dispatch |
| **AI Model** | `claude-sonnet-4-6` / `claude-opus-4-7` | Sonnet for speed, Opus for complex reasoning |
| **Site Generation** | Claude + GPT-4o-mini fallback | Generate HTML/Tailwind website previews |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) + [SQLAlchemy](https://sqlalchemy.org) | REST API, async DB, SSE streaming |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Jobs, leads, outreach records |
| **Task Queue** | Redis + background tasks | Async pipeline execution |
| **Browser Automation** | [Playwright](https://playwright.dev/python/) | Headless recording of website tours |
| **WhatsApp** | [Twilio](https://twilio.com) / simulation | Outreach message delivery |
| **Business Discovery** | Google Places API / [SerpAPI](https://serpapi.com) | Find businesses in a city + category |
| **Frontend** | [Next.js 15](https://nextjs.org) | Dashboard, job monitor, lead explorer |
| **Protocol** | MCP (Model Context Protocol) | Standardized interface for external APIs |

---

## Directory Structure

```
LeadGen/
├── backend/
│   ├── agents/                        # Claude SDK agentic layer (v2)
│   │   ├── orchestrator.py            # Main Claude loop + tool dispatch
│   │   ├── tools.py                   # Tool definitions wrapping workers/
│   │   └── prompts/
│   │       ├── system.md              # Orchestrator system prompt
│   │       └── outreach.md            # Outreach specialist persona
│   │
│   ├── workers/                       # Pure execution modules
│   │   ├── orchestrator.py            # v1 linear pipeline (kept for reference)
│   │   ├── discovery.py               # Google Places / SerpAPI / mock fallback
│   │   ├── auditor.py                 # HTTP check + quality score (0–100)
│   │   ├── site_generator.py          # HTML/Tailwind site generation
│   │   ├── video_recorder.py          # Playwright headless MP4 recording
│   │   ├── message_composer.py        # Hinglish/English message drafting
│   │   └── whatsapp_sender.py         # Twilio send or simulation
│   │
│   ├── mcp_servers/                   # MCP servers for external APIs only
│   │   ├── whatsapp_mcp.py            # Twilio WhatsApp MCP server
│   │   └── serp_mcp.py                # Google Places / SERP MCP server
│   │
│   ├── routers/
│   │   ├── jobs.py                    # Job CRUD + SSE event stream
│   │   └── leads.py                   # Lead explorer + site/video preview
│   │
│   ├── main.py                        # FastAPI app entry point
│   ├── models.py                      # ORM: Job, Lead, Outreach
│   ├── schemas.py                     # Pydantic request/response schemas
│   ├── config.py                      # Settings from .env
│   ├── database.py                    # Async SQLAlchemy setup
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.js                    # Dashboard home
│   │   ├── jobs/[id]/page.js          # Job monitor + Agent Thoughts panel
│   │   └── leads/page.js              # Lead explorer
│   ├── components/
│   │   └── Sidebar.js
│   └── lib/
│       └── api.js                     # API client
│
├── data/                              # Runtime data (gitignored)
│   ├── leadgen.db
│   ├── generated_sites/
│   └── videos/
│
├── .env                               # Environment config (template — no real keys)
├── docker-compose.yml                 # Redis service
└── README.md
```

---

## Data Models

```
Job
 ├── id, city, category, status
 ├── steps_total, steps_done
 ├── created_at, updated_at
 └── leads[]
       ├── id, name, phone, address
       ├── website_url, website_score (0–100)
       ├── site_html_path, video_path
       └── outreach
             ├── message_text
             ├── status (pending/sent/failed/simulated)
             └── twilio_sid
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for Redis)

### 1. Environment

```bash
# .env is already in the repo as a template — fill in your keys
```

| Key | Get It From | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com) | Yes (orchestrator) |
| `GOOGLE_PLACES_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) | No (mock fallback) |
| `SERPAPI_KEY` | [SerpAPI](https://serpapi.com) | No (alternative to Google Places) |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com) | No (template fallback) |
| `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | [Twilio Console](https://console.twilio.com) | No (simulation mode) |

### 2. Redis

```bash
docker-compose up -d redis
# or: install Redis via WSL / Chocolatey / Scoop on Windows
```

### 3. Backend

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

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:3000

---

## Usage

1. Open the dashboard at http://localhost:3000
2. Click **New Job** → enter a city (e.g. `Ahmedabad`) and category (e.g. `sweet shop`)
3. Watch the **Agent Thoughts** panel as Claude reasons through each lead
4. Explore generated sites and videos in the **Leads** tab

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Roadmap (v2 Build Order)

- [ ] `backend/agents/prompts/system.md` — orchestrator system prompt
- [ ] `backend/agents/tools.py` — wrap workers as Claude SDK tool definitions
- [ ] `backend/agents/orchestrator.py` — Claude SDK agentic loop
- [ ] `backend/mcp_servers/whatsapp_mcp.py` — Twilio MCP server
- [ ] `backend/mcp_servers/serp_mcp.py` — Google Places MCP server
- [ ] `backend/routers/jobs.py` — pipe agent thoughts through SSE stream
- [ ] `frontend/app/jobs/[id]/page.js` — Agent Thoughts panel

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a pull request

---

## License

MIT
