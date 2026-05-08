"""
agents/tools.py — Claude SDK tool definitions wrapping backend/workers/

Two exports:
  TOOLS    — list[dict] of Anthropic tool schemas
  dispatch — async (tool_name, tool_input) -> result

dispatch is a thin adapter only. All business logic lives in workers/.
Lead ORM mismatch (workers expecting Lead ORM but Claude tool calls send dicts)
is handled with a SimpleNamespace adapter.
"""
from types import SimpleNamespace
from pathlib import Path

from config import settings
from workers.discovery import fetch_google_places, fetch_serpapi
from workers.auditor import score_website
from workers.site_generator import generate_site_openai, generate_site_mock
from workers.video_recorder import record_site_video
from workers.message_composer import compose_with_openai, compose_mock
from workers.whatsapp_sender import send_via_twilio, simulate_send


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
            "Send a WhatsApp message via Twilio (or simulate if Twilio is not configured). "
            "Returns a dict with sid and status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "E.164 phone number, e.g. '+919876543210'"},
                "message": {"type": "string"},
                "video_url": {"type": "string"},
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
        lead_ns = SimpleNamespace(
            id=tool_input["lead_id"],
            business_name=tool_input["business_name"],
            category=tool_input["category"],
            city=tool_input["city"],
            address=tool_input.get("address"),
            phone=tool_input.get("phone"),
        )
        if settings.is_real("openai_api_key"):
            html = await generate_site_openai(lead_ns)
        else:
            html = generate_site_mock(lead_ns)
        sites_dir = Path(settings.generated_sites_dir)
        sites_dir.mkdir(parents=True, exist_ok=True)
        site_path = sites_dir / f"lead_{lead_ns.id}.html"
        site_path.write_text(html, encoding="utf-8")
        return str(site_path)

    if tool_name == "record_video":
        videos_dir = Path(settings.videos_dir)
        videos_dir.mkdir(parents=True, exist_ok=True)
        video_path = str(videos_dir / f"lead_{tool_input['lead_id']}.webm")
        ok = await record_site_video(
            html_path=tool_input["html_path"],
            video_path=video_path,
            business_name=tool_input["business_name"],
        )
        return {"success": bool(ok), "video_path": video_path if ok else None}

    if tool_name == "compose_message":
        lead_ns = SimpleNamespace(
            id=tool_input["lead_id"],
            business_name=tool_input["business_name"],
            category=tool_input["category"],
            city=tool_input["city"],
            approach=tool_input["approach"],
        )
        if settings.is_real("openai_api_key"):
            return await compose_with_openai(lead_ns)
        return compose_mock(lead_ns)

    if tool_name == "send_whatsapp":
        phone = tool_input["phone"]
        message = tool_input["message"]
        video_url = tool_input.get("video_url")
        if settings.is_real("twilio_account_sid") and settings.is_real("twilio_auth_token"):
            return await send_via_twilio(phone=phone, message=message, video_url=video_url)
        return await simulate_send(phone=phone, message=message)

    raise ValueError(f"Unknown tool: {tool_name}")
