"""
agents/template_cache.py — AI-once-per-category caching layer.

Pattern: AI generates ONE template per (category[, approach]) with {{placeholders}}.
Code substitutes per business. AI does the creative work once; code repeats it for free.

Caches:
  data/site_templates/{category_slug}.html
  data/message_templates/{category_slug}__{approach}.txt

Two functions:
  render_site(lead_dict)      -> returns HTML (cached or freshly generated + cached)
  render_message(lead_dict)   -> returns message text (cached or freshly generated + cached)

These intercept what would otherwise be per-lead OpenAI calls.
Cache is filesystem-based — wipe `data/site_templates/` and `data/message_templates/`
to force regeneration.
"""
import os
import re
import logging
import tempfile
from pathlib import Path
from types import SimpleNamespace

from config import settings
from workers.site_generator import generate_site_openai, generate_site_mock
from workers.message_composer import compose_with_openai, compose_mock
from agents.archetype_router import route as route_archetype
from agents.site_archetypes import (
    render_for_lead as render_archetype_for_lead,
    variation_seed,
)

logger = logging.getLogger(__name__)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "unknown").lower()).strip("_")


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically: write to tmp file in same dir, then rename.
    Prevents TOCTOU races when concurrent callers regenerate the same template.
    On Windows os.replace is atomic; on POSIX rename is atomic within same filesystem."""
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _site_template_dir() -> Path:
    p = Path(settings.data_dir) / "site_templates"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _message_template_dir() -> Path:
    p = Path(settings.data_dir) / "message_templates"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ─── Site templates ──────────────────────────────────────────────────────────

# Placeholder tokens — chosen so they survive any HTML AI may produce
SITE_PLACEHOLDERS = {
    "business_name": "__BIZ_NAME__",
    "category": "__BIZ_CATEGORY__",
    "city": "__BIZ_CITY__",
    "address": "__BIZ_ADDRESS__",
    "phone": "__BIZ_PHONE__",
}


async def _generate_site_template(category: str) -> str:
    """Generate ONE site template per category with placeholder tokens.

    We pass a placeholder Lead through the regular generator, then collect the
    output. Code-side render() will substitute __BIZ_*__ tokens for each real lead.
    """
    placeholder_lead = SimpleNamespace(
        id=0,
        business_name=SITE_PLACEHOLDERS["business_name"],
        category=category,
        city=SITE_PLACEHOLDERS["city"],
        address=SITE_PLACEHOLDERS["address"],
        phone=SITE_PLACEHOLDERS["phone"],
    )

    if settings.is_real("openai_api_key"):
        try:
            html = await generate_site_openai(placeholder_lead)
            return html
        except Exception as e:
            logger.warning(f"OpenAI site template generation failed for '{category}': {e}. Using mock.")

    return generate_site_mock(placeholder_lead)


def _substitute_site(template: str, lead_dict: dict) -> str:
    out = template
    out = out.replace(SITE_PLACEHOLDERS["business_name"], str(lead_dict.get("business_name", "")))
    out = out.replace(SITE_PLACEHOLDERS["category"],      str(lead_dict.get("category", "")))
    out = out.replace(SITE_PLACEHOLDERS["city"],          str(lead_dict.get("city", "")))
    out = out.replace(SITE_PLACEHOLDERS["address"],       str(lead_dict.get("address") or ""))
    out = out.replace(SITE_PLACEHOLDERS["phone"],         str(lead_dict.get("phone") or ""))
    return out


async def render_site(lead_dict: dict) -> tuple[str, bool]:
    """Returns (html, cache_hit).

    Archetype path (default): pick archetype from category, pick palette
    variation from hash(business_name), substitute. No AI cost. cache_hit=True.

    Legacy AI/mock path: kept behind LEADGEN_USE_LEGACY_TEMPLATE=1 so
    existing tests / cache-fallback behaviour is preserved.
    """
    if not os.environ.get("LEADGEN_USE_LEGACY_TEMPLATE"):
        archetype = route_archetype(lead_dict.get("category"))
        html, _palette_idx = render_archetype_for_lead(archetype, lead_dict)
        return html, True  # archetype render is deterministic & free — counts as a hit

    # ── Legacy path ────────────────────────────────────────────────
    category = lead_dict.get("category") or "default"
    cache_path = _site_template_dir() / f"{_slug(category)}.html"

    if cache_path.exists():
        template = cache_path.read_text(encoding="utf-8")
        return _substitute_site(template, lead_dict), True

    template = await _generate_site_template(category)
    _atomic_write(cache_path, template)
    return _substitute_site(template, lead_dict), False


# ─── Message templates (LOCKED — no AI freestyle) ───────────────────────────
#
# Two fixed templates. compose_message tool returns one of these verbatim with
# {name} substituted. Locked at ~40-50 words for WhatsApp readability.
# Price ₹5,000 hardcoded — change here if pricing ever changes.

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


async def render_message(lead_dict: dict) -> tuple[str, bool]:
    """Returns (message, cache_hit=True). No AI call — message is locked template
    with business_name substituted. approach picks build_site vs seo_pitch wording."""
    name = lead_dict.get("business_name") or "your business"
    approach = lead_dict.get("approach") or "build_site"
    template = SEO_PITCH_TEMPLATE if approach == "seo_pitch" else BUILD_SITE_TEMPLATE
    return template.format(name=name), True
