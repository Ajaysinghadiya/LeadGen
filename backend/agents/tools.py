"""
agents/tools.py — Claude SDK tool definitions wrapping backend/workers/

Two exports:
  TOOLS    — list[dict] of Anthropic tool schemas
  dispatch — async (tool_name, tool_input) -> result

dispatch is a thin adapter only. All business logic lives in workers/.
Lead ORM mismatch (workers expecting Lead ORM but Claude tool calls send dicts)
is handled with a SimpleNamespace adapter.
"""
import os
import re
from pathlib import Path

import httpx

from config import settings
from workers.discovery import fetch_google_places, fetch_serpapi
from workers.auditor import score_website
from workers.video_recorder import record_site_video
from workers.whatsapp_sender import send_via_twilio, simulate_send
from agents.template_cache import render_site, render_message

# Surface last cache hit to the orchestrator so it can emit a cost_saved SSE event.
LAST_CACHE_HIT: dict = {"generate_site": None, "compose_message": None}


def _safe_filename(business_name: str | None, lead_id: int, suffix: str, ext: str) -> str:
    """Build a cross-platform safe filename: <Business_Name>_<suffix>_<lead_id>.<ext>

    - Strips Windows-illegal chars (\\ / : * ? " < > |) and control chars
    - Replaces whitespace runs with single underscore
    - Caps the business-name portion at 80 chars
    - lead_id suffix prevents collisions when two leads share a business name
    """
    raw = (business_name or "lead").strip()
    raw = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", raw)   # illegal + control
    raw = re.sub(r"\s+", "_", raw)                    # spaces → underscore
    raw = re.sub(r"_+", "_", raw).strip("_")          # collapse repeats
    if not raw:
        raw = "lead"
    raw = raw[:80]
    return f"{raw}_{suffix}_{lead_id}.{ext}"

# WhatsApp Web bridge (Node sidecar running whatsapp-web.js)
WHATSAPP_BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", "http://localhost:8001")


async def _bridge_status() -> dict:
    """Returns {ready: bool, hasQr: bool, me: dict|None} or {error: ...}."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{WHATSAPP_BRIDGE_URL}/status")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"error": str(e), "ready": False}


async def _bridge_send(phone: str, message: str, media_path: str | None = None) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(
            f"{WHATSAPP_BRIDGE_URL}/send",
            json={"phone": phone, "message": message, "mediaPath": media_path},
        )
        r.raise_for_status()
        return r.json()


TOOLS: list[dict] = [
    {
        "name": "search_businesses",
        "description": (
            "Discover local businesses for a given city and category using Google "
            "Places (preferred) or SerpAPI fallback. Returns a list of businesses "
            "with name, phone, email, address, and existing_website."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Jaipur'"},
                "category": {"type": "string", "description": "Business category, e.g. 'sweet shop'"},
            },
            "required": ["city", "category"],
        },
    },
    {
        "name": "audit_website",
        "description": (
            "Score a website's quality from 0 to 100 using heuristics "
            "(metadata, HTTPS, mobile viewport, free-builder detection, content size)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL of the website to audit"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "generate_site",
        "description": (
            "Generate a single-page HTML website for a business that has no website "
            "or a low-quality one. Writes the file to disk and returns the path."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "integer"},
                "business_name": {"type": "string"},
                "category": {"type": "string"},
                "city": {"type": "string"},
                "address": {"type": "string"},
                "phone": {"type": "string"},
            },
            "required": ["lead_id", "business_name", "category", "city"],
        },
    },
    {
        "name": "record_video",
        "description": (
            "Record a video tour of a generated HTML site using a headless browser. "
            "Returns the video path on success."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "integer"},
                "html_path": {"type": "string", "description": "Path to the generated HTML file"},
                "business_name": {"type": "string"},
            },
            "required": ["lead_id", "html_path", "business_name"],
        },
    },
    {
        "name": "compose_message",
        "description": (
            "Compose a personalized WhatsApp outreach message. Use approach='build_site' "
            "when offering a free website, or approach='seo_pitch' when proposing SEO "
            "improvements to an existing low-scoring site."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "integer"},
                "business_name": {"type": "string"},
                "category": {"type": "string"},
                "city": {"type": "string"},
                "approach": {
                    "type": "string",
                    "enum": ["build_site", "seo_pitch"],
                },
            },
            "required": ["lead_id", "business_name", "category", "city", "approach"],
        },
    },
    {
        "name": "send_whatsapp",
        "description": (
            "Send a WhatsApp message. Routing priority: (1) personal WhatsApp via Web bridge "
            "if QR-paired, (2) Twilio if configured, (3) simulation. Pass video_path for "
            "media attachments via the bridge."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "E.164 phone number, e.g. '+919876543210'"},
                "message": {"type": "string"},
                "video_url": {"type": "string", "description": "Public URL to video (Twilio path)"},
                "video_path": {"type": "string", "description": "Local file path to video (bridge path)"},
            },
            "required": ["phone", "message"],
        },
    },
]


async def dispatch(tool_name: str, tool_input: dict):
    """Route a Claude tool call to the matching worker. No try/except — let the
    orchestrator surface errors as 'error' SSE events."""

    if tool_name == "search_businesses":
        city = tool_input["city"]
        category = tool_input["category"]
        if settings.is_real("google_places_api_key"):
            return await fetch_google_places(city, category)
        if settings.is_real("serpapi_key"):
            return await fetch_serpapi(city, category)
        from workers.discovery import MOCK_BUSINESSES
        return [{**b, "city": city, "category": category, "email": None} for b in MOCK_BUSINESSES]

    if tool_name == "audit_website":
        url = tool_input["url"]
        score = await score_website(url)
        return {"score": float(score), "url": url}

    if tool_name == "generate_site":
        # Cache-first: AI generates ONE template per category, code substitutes per lead.
        html, cache_hit = await render_site(tool_input)
        LAST_CACHE_HIT["generate_site"] = cache_hit
        sites_dir = Path(settings.generated_sites_dir).resolve()
        sites_dir.mkdir(parents=True, exist_ok=True)
        # Human-readable filename: <Business_Name>_demo_<lead_id>.html
        fname = _safe_filename(
            tool_input.get("business_name"),
            int(tool_input["lead_id"]),
            "demo",
            "html",
        )
        site_path = sites_dir / fname
        site_path.write_text(html, encoding="utf-8")
        # Return absolute path — the WhatsApp bridge runs from a different CWD
        # and needs to resolve this file via fs.existsSync().
        return str(site_path)

    if tool_name == "record_video":
        videos_dir = Path(settings.videos_dir).resolve()
        videos_dir.mkdir(parents=True, exist_ok=True)
        # Human-readable filename: <Business_Name>_recording_demo_<lead_id>.webm
        fname = _safe_filename(
            tool_input.get("business_name"),
            int(tool_input["lead_id"]),
            "recording_demo",
            "webm",
        )
        video_path = str(videos_dir / fname)
        ok = await record_site_video(
            html_path=tool_input["html_path"],
            video_path=video_path,
            business_name=tool_input["business_name"],
        )
        # Absolute path so the bridge (different CWD) can find it for media attachment.
        return {"success": bool(ok), "video_path": video_path if ok else None}

    if tool_name == "compose_message":
        # Cache-first: AI generates ONE message template per (category, approach).
        message, cache_hit = await render_message(tool_input)
        LAST_CACHE_HIT["compose_message"] = cache_hit
        return message

    if tool_name == "send_whatsapp":
        phone = tool_input["phone"]
        message = tool_input["message"]
        video_url = tool_input.get("video_url")
        media_path = tool_input.get("video_path") or tool_input.get("media_path")

        # Priority 1: Node WhatsApp Web bridge (personal WhatsApp via QR pairing)
        status = await _bridge_status()
        if status.get("ready"):
            # Bridge claims paired — a send failure here is a real problem
            # (puppeteer detached frame, expired session, recipient not on WA).
            # Raise instead of silently falling back to simulate, otherwise
            # the dashboard shows "message_sent" while nothing actually went out.
            try:
                result = await _bridge_send(phone, message, media_path=media_path)
                return {
                    "sid": result.get("id", "WA_BRIDGE"),
                    "status": result.get("status", "sent"),
                    "via": "whatsapp_bridge",
                }
            except Exception as e:
                raise RuntimeError(f"WhatsApp bridge send failed: {e}") from e

        bridge_error = status.get("error", "bridge not connected")

        # Priority 2: Twilio (if configured)
        if settings.is_real("twilio_account_sid") and settings.is_real("twilio_auth_token"):
            return await send_via_twilio(phone=phone, message=message, video_url=video_url)

        # Priority 3: simulation
        result = await simulate_send(phone=phone, message=message)
        result["bridge_error"] = bridge_error
        return result

    raise ValueError(f"Unknown tool: {tool_name}")
