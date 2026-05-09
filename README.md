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
1. Land on dashboard → WhatsAppGate blocks UI → scan QR with phone → pair
   (or click "Continue in simulate mode" to bypass for dev/demo)
2. Form: city + max_leads (5–25). NO business category — system auto-sweeps.
      ↓
[lead_finder] → parallel SerpAPI/Google Places sweep across 8 boring SMB
                categories: sweet shop, dhaba, saree shop, local jeweller,
                bakery, tailor boutique, printing press, handicraft shop
      ↓
      → filters: rating ≥ 3.8, reviews ∈ [5, 100], phone present
      ↓
      → if < 5 qualified leads → expand to nearest city (no filter loosening)
      ↓
[Claude Agent per lead] → audits each existing website (0–100 score)
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
| AI generates a site **per lead** — 30 leads = 30 OpenAI calls | Sites: 6 archetype templates (no AI). Messages: 2 locked templates with `{name}` substitution (no AI) |
| Re-uploads system prompt + tool schemas every API call | **Prompt caching** on (system + tools) — first call writes, rest read at 90% off |
| Twilio-only send (paid, business approval) | Personal WhatsApp via QR bridge (free) — Twilio fallback |
| Step events only | thought / action / result / error / skip / **cost_saved** events |
| Zero reasoning visible | Agent Thoughts panel streams chain-of-thought |

v1 is preserved at `backend/workers/orchestrator.py` for reference but is no longer wired in.

### Cost controls (added 2026-05)

Four layers protect API spend, in this order:

1. **24h discovery TTL** — `_maybe_reuse_recent_leads` in orchestrator. If the same `(city, category)` ran in the last 24h, clone its leads instead of refetching from SerpAPI. Toggleable per job via `force_refresh`.
2. **Phone dedup** — `_phone_dedup` runs after discovery, before the agent loop. Marks leads `status="duplicate"` when the phone matches any earlier `Lead.phone` in any other job. Saves Anthropic tokens (the most expensive part).
3. **`max_leads` cap** — slices the eligible-lead list to the per-job cap before the agent loop. UI shows `Max Leads` dropdown on dashboard. Lower cap → less spend.
4. **Prompt caching** (added 2026-05-09) — `cache_control: {"type": "ephemeral"}` on the system prompt creates a single cache breakpoint covering both tools (~600 tok) and system prompt (~600 tok). First call writes at 1.25× input price; every subsequent call reads at 0.10× (90% off). 5-min TTL refreshes on each hit, so sequential leads stay warm. Saves ~40% of the per-job Anthropic bill (e.g. $0.09 / 5 leads, $19 / 1k leads). Per-lead totals emitted as `💰 prompt_cache: write=X read=Y tok (~$Z saved this lead)` SSE events.

All four emit `cost_saved` / `prompt_cache` SSE events into the Agent Thoughts panel so you can see what each layer saved per job.

**Template cache (`agents/template_cache.py`):**
- **Site templates** — `render_site` uses the archetype path by default (free, deterministic). Legacy AI/mock path kept behind `LEADGEN_USE_LEGACY_TEMPLATE=1` for fallback; cached at `data/site_templates/{category}.html`.
- **Message templates** (locked 2026-05-09) — `render_message` returns one of two **hardcoded** templates (`BUILD_SITE_TEMPLATE`, `SEO_PITCH_TEMPLATE`) with `{name}` substituted. NO AI call ever; price ₹5,000 hardcoded; ~40-50 words each for WhatsApp readability. Edit the constants at the top of `template_cache.py` to change wording.

---

## Job Lifecycle Controls (added 2026-05-09)

### Stop a running job

`POST /jobs/{id}/stop` flips `Job.status="stopped"`. The orchestrator polls this between leads — when it sees `stopped`, the current lead finishes (so no half-sent WhatsApp / half-recorded video) and the agent loop exits. Finalize phase preserves the `stopped` status instead of overwriting to `completed`.

UI: `⏹ Stop` button appears on each `JobCard` on the dashboard AND in the job-detail page header. Both fire `POST /jobs/{id}/stop` after a confirm dialog. Returns 409 if the job is already done/failed.

### Delete a job

`DELETE /jobs/{id}` cascade-deletes the job's leads + outreach rows. **Files on disk are NOT removed** (HTML / videos persist for manual cleanup if you want them).

UI: `✕` icon on each `JobCard` (top-right). Confirm dialog. Allowed even on running jobs — but recommend stopping first to avoid the orchestrator writing to a deleted `job_id`.

### Tool-output persistence (bug fix)

Earlier the orchestrator only updated `Lead.status`. Tool outputs (generated site path, video path, message text, send result) were lost — the dashboard rendered `site=[no] video=[no]` even when the agent had successfully generated everything. The orchestrator now captures each tool's return value and writes:

| Tool | Persisted to |
|---|---|
| `generate_site` | `Lead.generated_site_path` |
| `record_video` | `Lead.video_path` (when `success=true`) |
| `compose_message` | `Outreach.message_text` (on send) |
| `send_whatsapp` | `Outreach.whatsapp_status` + `twilio_sid` + `sent_at` |

### Bridge send — loud failures only

If the WhatsApp bridge reports `ready=true` but `/send` raises (e.g. puppeteer "detached Frame" bug, expired session, recipient not on WhatsApp), `tools.py:send_whatsapp` now **raises** instead of silently falling through to `simulate_send`. The agent surfaces this as an `error` SSE event and the lead does NOT flip to `message_sent`. Previously this fallback masked real bridge bugs as fake "successes".

The simulate path is still reachable when the bridge reports `ready=false` (down or unpaired) — that's the legitimate dev/demo escape hatch.

---

## Boring-Categories Auto-Sweep (added 2026-05-09)

### Targeting thesis

We target **under-served Indian SMBs that nobody is pitching**: real local businesses with demand but weak/no online presence, in categories that digital agencies overlook because they're "boring" — not gyms, not salons, not cafés.

### What the user enters

Just two fields:
- **City** (e.g. `Jaipur`)
- **Max Leads** — number input, restricted **5–25** (UI + Pydantic both enforce)

No category input. The system sweeps a curated list automatically.

### Curated boring-category list

| Category | Why included |
|---|---|
| `sweet shop` (mithai, halwai) | High spend potential, no online ambition baked in |
| `dhaba` (small family restaurants) | Real-money business, agencies skip them |
| `saree shop` (silk, sari, cloth) | Cash-flow positive, mostly walk-in only |
| `local jeweller` (small gold shops) | Decent margins, often on amateur Wix sites |
| `bakery` (local, not Theobroma-tier) | Reorders + footfall, nobody pitches |
| `tailor boutique` (small fashion) | Repeat customers, weak digital |
| `printing press` (digital print + design) | B2B steady cash, no online presence |
| `handicraft shop` (textile, local crafts) | Tourist-driven, online undermarketed |

Deliberately excluded: kiraana stores (margin too thin for ₹5k spend), gyms/salons/cafés (over-pitched), mechanics/electricians (don't pay for marketing).

### Qualification filters

Applied during discovery, BEFORE the agent loop touches a lead:

| Signal | Threshold | Reason |
|---|---|---|
| `rating` | ≥ 3.8 | Below = customer-experience problem, not website problem |
| `reviews` | 5 ≤ count ≤ 100 | < 5 = too thin, > 100 = already pitched by competitors |
| `phone` | required | No phone = can't WhatsApp |
| Listings missing rating/reviews data | dropped | No signal of demand |

### Sweep mechanics

1. Fan out 8 SerpAPI / Google Places queries in **parallel** via `asyncio.gather` (~3s vs ~24s sequential)
2. Apply filters to each category result set
3. Dedup by phone across all 8 categories (a sweet shop might also list under bakery)
4. If primary city yields **< 5 qualified leads**, expand to nearest city — **filters never loosen, only geography widens**

Nearest-city map covers 25 Indian metros + tier-2 cities. Examples:
- Jaipur → Ajmer, Jodhpur, Kishangarh
- Mumbai → Thane, Navi Mumbai, Kalyan
- Delhi → Gurgaon, Noida, Ghaziabad
- Pune → Pimpri-Chinchwad, Satara, Nashik

If user's city isn't in the map and yields < 5 leads, the job completes with whatever was found — no silent loosening of standards.

### Cost

| Provider | Calls per job | Cost per job |
|---|---|---|
| Google Places (priority 1) | 8 | $0.00 (free tier ample) |
| SerpAPI (fallback) | 8 | $0.08 (paid: $50/5000) |
| Free tier alone (100/mo) | 8 | ~12 jobs/month before quota hit |

### Files

```
backend/agents/lead_finder.py        # NEW — sweep + filter + nearest-city
backend/agents/orchestrator.py       # imports run_discovery from lead_finder
backend/schemas.py                   # JobCreate.category Optional, max_leads 5–25
backend/routers/jobs.py              # stores SWEEP_TAG="auto_boring_sweep"
frontend/app/page.js                 # 2-field form, JobCard renders "Local SMB sweep"
frontend/lib/api.js                  # createJob(city, opts) — no category
```

### Storage convention

`Job.category` is set to the synthetic value `"auto_boring_sweep"` for v2 jobs. The 24h TTL reuse logic still works because city + sentinel match across runs. Per-lead `Lead.category` holds the actual matched boring category (e.g. `"sweet shop"`) — that drives archetype routing and per-lead messaging.

---

## WhatsApp Gate + Locked Outreach (added 2026-05-09)

### QR-first hard gate

`frontend/app/components/WhatsAppGate.js` blocks every page (except `/whatsapp` itself) until WhatsApp is paired. States:

| Bridge state | Gate shows |
|---|---|
| `bridge_down` (port 8001 unreachable) | Full-screen panel with `cd whatsapp-bridge && npm start` instructions |
| `hasQr=true` | Big QR + "WhatsApp → Settings → Linked Devices → Link a Device" hint |
| `ready=true` | Auto-dismiss; dashboard renders |

Bypass: **"Continue in simulate mode →"** button writes `localStorage.leadgen_wa_skip_simulate=1`. Persists across reloads. Useful for dev/demo when bridge is down. To re-enable gate: `localStorage.removeItem('leadgen_wa_skip_simulate')`.

`frontend/app/components/AppShell.js` is the layout wrapper that exempts `/whatsapp` from gating (would deadlock otherwise) and applies the gate to every other route.

### Locked WhatsApp outreach templates

Replaced the old AI-composed message path with two hardcoded templates in `agents/template_cache.py`:

```python
BUILD_SITE_TEMPLATE = (
    "Hi there! I've created a demo website for {name} after seeing your great "
    "feedback on Google — see a test video. Your brand deserves a top-tier site! "
    "I can finalize and launch this for you in 48 hours for just ₹5,000. Interested?"
)

SEO_PITCH_TEMPLATE = (
    "Hi there! Saw your existing site for {name} — strong reviews on Google but "
    "missing key SEO basics hurting your ranking. I can fix metadata, mobile speed, "
    "and structure in 48 hours for just ₹5,000. Interested?"
)
```

Properties:
- ~40-50 words each (WhatsApp readability — long messages don't get read)
- `{name}` is the only variable; price `₹5,000` is hardcoded
- `compose_message` tool returns `(template, cache_hit=True)` — no AI cost ever
- `build_site` is the default; `seo_pitch` is selected via `lead_dict["approach"]`

### Human-readable artifact filenames

Generated HTML and recorded videos now use sanitized business names instead of `lead_<id>.{html,webm}`:

| Lead | HTML | Video |
|---|---|---|
| `Bussy Sweet Shop` (id=5) | `Bussy_Sweet_Shop_demo_5.html` | `Bussy_Sweet_Shop_recording_demo_5.webm` |
| `M/s Bassi & Co.` (id=12) | `Ms_Bassi_&_Co._demo_12.html` | `Ms_Bassi_&_Co._recording_demo_12.webm` |

`agents/tools.py:_safe_filename` strips Windows-illegal chars (`\ / : * ? " < > |` + control chars), replaces whitespace with underscore, caps name at 80 chars, and appends `<suffix>_<lead_id>` to prevent duplicate-name collisions.

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
│   │   ├── orchestrator.py              # run_agent + run_job (SDK loop, dedup pre-flight, prompt cache)
│   │   ├── lead_finder.py               # boring-category sweep + filters + nearest-city
│   │   ├── tools.py                     # 6 tool defs + dispatch (bridge→twilio→simulate)
│   │   ├── template_cache.py            # archetype-first sites; LOCKED message templates
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
│   │   ├── layout.js                    # Wraps body in <AppShell>
│   │   ├── page.js                      # Dashboard
│   │   ├── jobs/[id]/page.js            # Two-column: leads + Agent Thoughts panel
│   │   ├── leads/page.js                # Lead explorer
│   │   ├── whatsapp/page.js             # QR pairing UI + status + disconnect
│   │   └── components/
│   │       ├── AppShell.js              # Wrapper — exempts /whatsapp, gates rest
│   │       └── WhatsAppGate.js          # Full-screen QR gate + simulate-skip
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

**Pair via the gate.** When the bridge is up, opening `http://localhost:3000/` shows a full-screen QR (WhatsAppGate). Scan with your phone (WhatsApp → Settings → Linked Devices → Link a Device); the gate auto-dismisses on pair. Session is persisted in `whatsapp-bridge/.wwebjs_auth/` (gitignored), so you only scan once per machine.

If the QR rotates faster than you can scan or "couldn't link to device" pops up, kill the bridge, wipe `whatsapp-bridge/.wwebjs_auth/`, restart `node server.js` — the protocol resets cleanly. If still broken, bump `whatsapp-web.js` to `@latest` (WhatsApp protocol changes occasionally lag the lib).

When paired, the agent's `send_whatsapp` tool routes through the bridge automatically. If you'd rather skip pairing for dev/demo, click "Continue in simulate mode →" on the gate. If the bridge is down or unpaired during a real run, it falls back to Twilio (if configured), then to simulation.

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
- [x] `frontend/app/components/WhatsAppGate.js` + `AppShell.js` — QR-first hard gate (added 2026-05-09)
- [x] `backend/agents/lead_finder.py` — boring-category auto-sweep + rating/review filters + nearest-city fallback (added 2026-05-09)
- [x] `frontend/app/page.js` — simplified to city + max_leads (5–25); category input removed (added 2026-05-09)
- [x] Orchestrator persists tool outputs — `lead.generated_site_path`, `lead.video_path`, `Outreach` row created on send (fixed 2026-05-09)
- [x] Bridge send loud-fail — when bridge says `ready=true` but send 500s, raise instead of silently falling to `simulate_send` (fixed 2026-05-09)
- [x] Stop running job — `POST /jobs/{id}/stop` + ⏹ Stop button on dashboard cards and job page header. Graceful — current lead finishes (added 2026-05-09)
- [x] Delete job — `DELETE /jobs/{id}` cascades to leads + outreach. ✕ icon on JobCard with confirm dialog (added 2026-05-09)
- [x] `frontend/components/Sidebar.js` — live WhatsApp status dot
- [x] Anthropic prompt caching wired (`cache_control` on system → covers tools + system) — added 2026-05-09
- [x] Locked WhatsApp templates in `template_cache.py` — `BUILD_SITE_TEMPLATE` + `SEO_PITCH_TEMPLATE` (added 2026-05-09)
- [x] Human-readable artifact filenames — `<Business_Name>_demo_<id>.html` / `_recording_demo_<id>.webm` (added 2026-05-09)
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

### Cost estimate (recorded 2026-05-09)

For a 5-lead run with all real APIs (SerpAPI + Anthropic + WhatsApp bridge), expected per-run spend:

```
SerpAPI discovery        : 1 call             $0.010
Anthropic agent loop     : ~30 messages       $0.215  (no caching)
                                              $0.130  (with prompt caching, ~40% off)
OpenAI message templates : 0 (locked)         $0.000
OpenAI site templates    : 0 (archetype)      $0.000
WhatsApp send            : bridge             $0.000
─────────────────────────────────────────────────────
Total per 5 leads        :                    ~$0.13–$0.23
Per-lead                 :                    ~$0.03–$0.05
Scaling to 1000 leads    :                    ~$25–$45 with caching
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
