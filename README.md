# LeadGen 2.0

> **Agentic Lead Generation & Automated Outreach for Local Businesses**

AI-powered system that finds local businesses without websites, generates custom site previews, records video tours, and sends personalized WhatsApp pitches **from your personal WhatsApp number via QR pairing** — all orchestrated by a Claude SDK agent that reasons through each lead independently.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-orange)](https://anthropic.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Web%20Bridge-25D366)](https://github.com/pedroslopez/whatsapp-web.js)
[![Status](https://img.shields.io/badge/v2-shipped-success)](#build-status)

---

## What It Does

```
1. Open /whatsapp → scan QR with phone → pair personal WhatsApp
2. City + Category form
      ↓
[Claude Agent] → searches Google Places / SerpAPI for local businesses
      ↓
      → audits each existing website (0–100 score)
      ↓
      → dedup check: skip leads whose phone already received outreach
      ↓
      → reasons: "Does this business need help, and what kind?"
      ↓
      → branches:
          score < 30  → generate site → record video → pitch "build_site" → WhatsApp
          30 ≤ s ≤ 60 → pitch "seo_pitch" → WhatsApp
          score > 60  → skip with explanation
      ↓
Messages send from YOUR WhatsApp number via the Node bridge.
Live Agent Thoughts panel streams reasoning + tool calls per lead.
```

The agent is **not** a fixed pipeline. It reasons per lead, picks the right branch, and explains skips. Every text block becomes a "thought" event; every tool call becomes an "action" event; every result/error becomes a labeled SSE event for the dashboard.

**Outreach uses your personal WhatsApp** via a Node sidecar running [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js). Pair once with a QR scan, and the agent sends from your number — no Twilio account, no business approval, no per-message fees. Twilio fallback still works if you prefer that route.

---

## Architecture

### v2 — Agentic Layer + WhatsApp Bridge (shipped)

```
              Browser :3000               Backend :8000               Bridge :8001
                  │                            │                            │
   POST /jobs ───►│                            │                            │
                  │── /api/jobs ──────────────►│                            │
                  │                            ▼                            │
                  │              routers/jobs.py → run_pipeline             │
                  │                            ▼                            │
                  │              agents/orchestrator.py                     │
                  │              (Claude SDK loop, dedup pre-flight)        │
                  │                ┌───────────┼───────────┐                │
                  │                ▼           ▼           ▼                │
                  │      agents/prompts/   agents/      mcp_servers/        │
                  │      system.md         tools.py     whatsapp_mcp.py     │
                  │                        │            serp_mcp.py         │
                  │                        ▼                                │
                  │      backend/workers/ (locked execution)                │
                  │      discovery / auditor / site_generator /             │
                  │      video_recorder / message_composer / whatsapp_sender│
                  │                            │                            │
                  │                            │  send_whatsapp tool        │
                  │                            └──── HTTP /send ───────────►│
                  │                                                         │
                  │◄── /api/whatsapp/qr ────── proxy ──── GET /qr ──────────│
                  │◄── /api/whatsapp/status ── proxy ──── GET /status ──────│
                  │                                                         │
                  │                          whatsapp-web.js + LocalAuth ───┘
                  │                          Node sidecar — personal WhatsApp via QR

    SSE event shape: {type, lead_id, content, timestamp}
    Types: thought | action | result | error | skip | done
```

### Design rules

- `workers/` is locked. Pure execution. Zero Anthropic imports.
- `agents/tools.py` is a thin adapter only. `SimpleNamespace` shim for Lead-ORM functions.
- WhatsApp send priority: **(1) bridge if paired → (2) Twilio if configured → (3) simulation**. Decided per-call in `tools.py` `send_whatsapp` dispatch.
- Dedup runs as orchestrator pre-flight #1: phone-based `Outreach` lookup across all jobs blocks repeat messages.
- MCP servers exist for **external** APIs only (Twilio, Google Places/SerpAPI). Internal Python is plain Claude SDK tools — no MCP overhead.
- Background tasks create their own `AsyncSessionLocal()`. Request session is closed before the task runs.
- SSE infrastructure (`_sse_queues`, `broadcast_event`) is reused — no second queue dict.
- `WHATSAPP_BRIDGE_URL` is read from `os.environ` (NOT pydantic Settings — config.py is locked, and Settings forbids extras). Defaults to `http://localhost:8001`.

### v1 vs v2

| v1 (linear `workers/orchestrator.py`) | v2 (`agents/orchestrator.py`) |
|---|---|
| Fixed order: discover → audit → generate → record → compose → send | Claude branches per lead based on score |
| Every business gets identical treatment | Strong sites are skipped; medium pivots to SEO |
| No dedup — same number could get hit on repeat jobs | Phone dedup runs **before** agent loop (no Anthropic spend on duplicates) |
| Re-discovery on every run — wasted SerpAPI calls | 24h TTL reuses leads from a recent matching job — `force_refresh` to override |
| No lead cap — pipeline burns through whatever the API returned | `max_leads` per-job cap (UI dropdown 10/20/25/30/35/50, default 25) |
| AI generates a site **per lead** — 30 leads = 30 OpenAI calls | AI generates **one template per category**; code substitutes per lead. Same for message templates |
| Twilio-only send (paid, business approval) | Personal WhatsApp via QR bridge (free) — Twilio fallback |
| Step events only | thought / action / result / error / skip / **cost_saved** events |
| Zero reasoning visible | Agent Thoughts panel streams chain-of-thought |

v1 is preserved at `backend/workers/orchestrator.py` for reference but is no longer wired in.

### Cost controls (added 2026-05)

Three layers protect API spend, in this order:

1. **24h discovery TTL** — `_maybe_reuse_recent_leads` in orchestrator. If the same `(city, category)` ran in the last 24h, clone its leads instead of refetching from SerpAPI. Toggleable per job via `force_refresh`.
2. **Phone dedup** — `_phone_dedup` runs after discovery, before the agent loop. Marks leads `status="duplicate"` when the phone matches any earlier `Lead.phone` in any other job. Saves Anthropic tokens (the most expensive part).
3. **`max_leads` cap** — slices the eligible-lead list to the per-job cap before the agent loop. UI shows `Max Leads` dropdown on dashboard. Lower cap → less spend.

All three emit `cost_saved` SSE events into the Agent Thoughts panel so you can see what each layer saved per job.

**Template cache (`agents/template_cache.py`):**
- `data/site_templates/{category}.html` — one HTML template per category, generated once via OpenAI with `__BIZ_NAME__` / `__BIZ_CITY__` etc. placeholders. Subsequent leads in the same category use simple `str.replace` substitution. Zero AI cost on cache hits.
- `data/message_templates/{category}__{approach}.txt` — same pattern for outreach text. Cache key = `(category, approach)`.
- Wipe `data/site_templates/` or `data/message_templates/` to force regeneration (e.g., when prompt changes).

---

## Site Archetypes (added 2026-05-08)

The single generic Inter+orange template was replaced by **6 distinctive archetype templates**, each with its own font pair, palette pool, headline pool, and signature design move. Routing is automatic: `lead.category` → archetype → palette variation picked from `hash(business_name)`.

**Why this exists.** I analyzed 29 reference sites in `data/Sample_Webages/` and found that ~90% converged on `Cormorant Garamond + Montserrat + cream-bg-with-gold-accent`. That convergence IS the AI-slop baseline. To stand out, archetypes deliberately avoid those choices.

| Archetype | Categories | Display + Body Font | Signature move |
|---|---|---|---|
| `playful_mithai` | sweets, mithai, farsan, halwai, bakery | Yeseva One + Quicksand | Floating SVG paisley orbs, "Made fresh daily" marquee strip |
| `luxury_textile` | silk, saree, sari, patola, handloom | Italiana + Spectral | Vertical Roman-numeral ticker w/ cross-dissolve animation |
| `modern_salon_boutique` | salon, parlour, boutique, tailor, fashion (default) | Fraunces (var opsz) + DM Sans | Diagonal-clip image column, gold underline-on-hover |
| `artisan_craft` | pattachitra, thanka, painter, sculptor, handicraft | Cormorant Infant + Crimson Pro | Hand-drawn SVG ornament corners, kerned all-caps eyebrow |
| `event_occasion` | mehndi, henna, wedding, academy, courses | Tenor Sans + Italiana + DM Sans | Radial gold pulse behind name, henna-pattern SVG underline animating in |
| `luxury_jewellery` | jeweller, gold, diamond, bridal jewellery | Marcellus + Outfit | 16-ray sun-burst SVG behind name, gold cursor-dot follower |

**Per-lead variation.** Each archetype carries 3 palette pools + 5 headline alts + 5 lede alts. `seed = sum(ord(c) for c in business_name) % pool_size` picks one slot. Two sweet shops in the same city render with different palette + headline + lede — no twin pages.

**Routing.** `agents/archetype_router.py` matches keywords on word-prefix boundaries (so `jewell` catches `jewellery`, `jeweller`, etc.). Fallback: `modern_salon_boutique`. 15/15 sanity examples pass.

**Files.**
```
backend/agents/site_archetypes/
├── __init__.py                # registry + render_for_lead(archetype, lead)
├── _common.py                 # variation_seed, render_template helper, grain SVG
├── playful_mithai.py
├── luxury_textile.py
├── modern_salon_boutique.py
├── artisan_craft.py
├── event_occasion.py
└── luxury_jewellery.py
backend/agents/archetype_router.py    # category → archetype + EXAMPLES table
backend/scripts/render_archetype_demos.py   # render demo HTML per archetype
docs/design_archetypes.md             # full spec + sample-cluster analysis
```

**Pipeline integration.** `template_cache.render_site` defaults to the archetype path — free, deterministic, distinctive. The legacy AI/mock path is kept behind `LEADGEN_USE_LEGACY_TEMPLATE=1` for fallback.

**Render demos.** `python backend/scripts/render_archetype_demos.py` writes one demo HTML per archetype to `data/generated_sites/demo_{archetype}.html`. Open in browser to compare.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Orchestration** | [Anthropic Claude SDK](https://github.com/anthropics/anthropic-sdk-python) | Agentic loop, reasoning, tool dispatch |
| **AI Model** | `claude-sonnet-4-6` | Per-lead orchestration |
| **Site Generation** | 6 archetype templates → OpenAI fallback | Distinctive per-category HTML site previews |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) + async SQLAlchemy 2.0 | REST + SSE streaming |
| **Database** | SQLite (`aiosqlite`) | Jobs, leads, outreach |
| **Browser Automation** | [Playwright](https://playwright.dev/python/) | Headless video recording |
| **WhatsApp (primary)** | [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) Node sidecar | Personal WhatsApp via QR pairing — free, no business approval |
| **WhatsApp (fallback)** | [Twilio](https://twilio.com) → simulation | Used if bridge not paired |
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
│   │   ├── orchestrator.py              # run_agent + run_job (SDK loop, dedup pre-flight)
│   │   ├── tools.py                     # 6 tool defs + dispatch (bridge→twilio→simulate)
│   │   ├── template_cache.py            # archetype-first; legacy AI/mock fallback
│   │   ├── archetype_router.py          # category → archetype slug
│   │   ├── site_archetypes/             # 6 distinctive site templates
│   │   │   ├── __init__.py              # registry + render_for_lead
│   │   │   ├── _common.py               # variation_seed + render helpers
│   │   │   ├── playful_mithai.py        # sweets · Yeseva One + Quicksand
│   │   │   ├── luxury_textile.py        # silk/saree · Italiana + Spectral
│   │   │   ├── modern_salon_boutique.py # salon/boutique · Fraunces + DM Sans
│   │   │   ├── artisan_craft.py         # artist/craft · Cormorant Infant + Crimson Pro
│   │   │   ├── event_occasion.py        # mehndi/event · Tenor Sans + Italiana
│   │   │   └── luxury_jewellery.py      # jewellery · Marcellus + Outfit
│   │   └── prompts/
│   │       └── system.md                # Orchestrator persona + branching rules
│   │
│   ├── scripts/
│   │   └── render_archetype_demos.py    # Render one demo per archetype
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
│   │   ├── leads.py                     # Lead explorer + site/video preview
│   │   └── whatsapp.py                  # Proxy /whatsapp/{status,qr,logout} → bridge
│   │
│   ├── tests/
│   │   └── test_agent_decisions.py      # 3-lead branching test (mocked)
│   │
│   ├── main.py · models.py · schemas.py · config.py · database.py
│   └── requirements.txt
│
├── whatsapp-bridge/                     # Node sidecar — whatsapp-web.js
│   ├── server.js                        # Express + LocalAuth + /qr /send /status /logout
│   ├── package.json                     # whatsapp-web.js, express, qrcode, cors
│   └── .wwebjs_auth/                    # Persisted session (gitignored)
│
├── frontend/
│   ├── app/
│   │   ├── page.js                      # Dashboard
│   │   ├── jobs/[id]/page.js            # Two-column: leads + Agent Thoughts panel
│   │   ├── leads/page.js                # Lead explorer
│   │   └── whatsapp/page.js             # QR pairing UI + status + disconnect
│   ├── components/Sidebar.js            # Nav + live WhatsApp status dot
│   └── lib/api.js                       # apiFetch + watchJob + getWhatsAppStatus
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
├── docs/
│   └── design_archetypes.md             # 6-archetype spec + sample-cluster analysis
├── data/                                # Runtime (gitignored): leadgen.db, sites, videos
│   └── Sample_Webages/                  # Reference HTML files used for archetype DNA
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
- Chromium (auto-installed by Playwright + whatsapp-web.js)

### 1. Environment (`.env`)

The `.env` file lives at the repo root **and** is copied to `backend/.env` (config.py reads from CWD, which is `backend/` when uvicorn runs).

| Key | Source | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | **Yes** — orchestrator |
| `GOOGLE_PLACES_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) | No — mock fallback |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | No — secondary discovery source |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | No — template fallback for site generation |
| `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | [console.twilio.com](https://console.twilio.com) | No — only used if WhatsApp bridge is not paired |

> **Bridge URL:** Defaults to `http://localhost:8001`. To override, set `WHATSAPP_BRIDGE_URL` as a **shell** env var **before** starting uvicorn — do not put it in `.env` (pydantic Settings forbids extras since `config.py` is locked).

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

### 4. WhatsApp bridge (Node sidecar)

```bash
cd whatsapp-bridge
npm install                # First time only
npm start                  # Listens on :8001
```

Pair once at **http://localhost:3000/whatsapp** — scan the QR with your phone (WhatsApp → Settings → Linked Devices → Link a Device). Session is persisted in `whatsapp-bridge/.wwebjs_auth/` (gitignored), so you only scan once per machine.

When paired, the agent's `send_whatsapp` tool routes through the bridge automatically. If the bridge is down or unpaired, it falls back to Twilio (if configured), then to simulation.

### 5. (Optional) MCP servers as standalone

```bash
python -m mcp_servers.whatsapp_mcp     # stdio MCP for Twilio
python -m mcp_servers.serp_mcp         # stdio MCP for Google Places / SerpAPI
```

---

## Usage

1. Boot all 3 servers (backend :8000, frontend :3000, bridge :8001).
2. Open **http://localhost:3000/whatsapp** — scan the QR with your phone (WhatsApp → Settings → Linked Devices → Link a Device). The sidebar dot turns green when paired.
3. Go to dashboard → create a job: city (e.g. `Jaipur`) + category (e.g. `sweet shop`).
4. Open the job page — left column shows leads, right column shows **Agent Thoughts**:
   - 💭 yellow rows = reasoning (text blocks)
   - ⚙️ blue rows = tool calls (mono)
   - ✓ green rows = tool results (truncated 150 chars)
   - ⚠ red rows = errors
   - ↷ gray rows = skips (strong sites OR phone already contacted)
5. Watch the agent decide per lead. Skip → SEO pitch → full build are all visible live.
6. Messages send from your personal WhatsApp. Generated HTML and WEBM tours are linked off the leads explorer.

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

v2 agentic layer + WhatsApp Web bridge + cost controls: **shipped**.

- [x] `backend/agents/__init__.py` + `agents/prompts/system.md`
- [x] `backend/agents/tools.py` (6 tools, dispatch with SimpleNamespace adapter, bridge-first send routing, template-cache integration)
- [x] `backend/agents/orchestrator.py` (Claude SDK loop + 24h TTL + phone dedup + max_leads cap + cost_saved SSE)
- [x] `backend/agents/template_cache.py` — archetype-first site rendering; AI/mock cache for messages
- [x] `backend/agents/site_archetypes/` — 6 distinctive archetype templates (Yeseva/Italiana/Fraunces/Cormorant Infant/Tenor Sans/Marcellus)
- [x] `backend/agents/archetype_router.py` — category → archetype routing (15/15 examples pass)
- [x] `backend/mcp_servers/whatsapp_mcp.py` + `serp_mcp.py`
- [x] `backend/routers/jobs.py` swap to `agents.orchestrator.run_job`, accepts `max_leads` + `force_refresh`
- [x] `backend/routers/whatsapp.py` — `/whatsapp/{status,qr,logout}` proxy to bridge
- [x] `backend/models.py` — `max_leads`, `force_refresh`, `skipped_count` on Job
- [x] `whatsapp-bridge/` — Node sidecar (whatsapp-web.js + LocalAuth + Express)
- [x] `frontend/app/page.js` — Max Leads dropdown + Force-refresh checkbox
- [x] `frontend/app/jobs/[id]/page.js` — two-column layout + Agent Thoughts panel
- [x] `frontend/app/whatsapp/page.js` — QR pairing UI + status polling
- [x] `frontend/components/Sidebar.js` — live WhatsApp status dot
- [x] `backend/tests/test_agent_decisions.py` — 10/10 decision checks pass

### Smoke test (recorded 2026-05-08)

```
Job 1: Pune / gym, max_leads=15
  → SerpAPI returned 20 leads, capped to 15 (5 dropped as over_cap)
Job 2: Pune / gym, max_leads=15 (re-run within 24h)
  → TTL reuse: cloned 20 leads from Job 1 (zero SerpAPI calls)
  → Phone dedup: 18/20 leads matched Job 1 phones → marked duplicate
  → 18 Anthropic agent runs avoided. Net cost on a duplicate run: ~zero.
```

---

## Contributing

1. Fork
2. Branch: `git checkout -b feature/my-feature`
3. Commit (hooks block edits to locked layer — that's intentional)
4. PR

---

## License

MIT
