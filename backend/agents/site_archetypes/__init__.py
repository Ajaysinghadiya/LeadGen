"""
Site archetype registry.

Each archetype module exposes:
  PALETTE_POOL   : list[dict]
  HEADLINE_POOL  : list[str]
  LEDE_POOL      : list[str]
  TEMPLATE       : str  (HTML w/ __BIZ_*__, __BG__, __INK__, __ACCENT__, __HEADLINE__, __LEDE__ tokens)

Two public functions:
  render_for_lead(archetype_slug, lead_dict) -> (html, palette_idx)
      — Substitutes per-lead values; picks variation via hash(business_name).
  render_template_cached(archetype_slug, palette_idx) -> str
      — Returns the same archetype rendered with palette_idx selected, but
        with __BIZ_*__ + __HEADLINE__ + __LEDE__ left as placeholders so the
        template_cache can substitute per-lead later. Used for cache files.
"""
from __future__ import annotations
from typing import Tuple

from . import (
    luxury_textile,
    modern_salon_boutique,
    playful_mithai,
    artisan_craft,
    event_occasion,
    luxury_jewellery,
)
from ._common import variation_seed, pick, render_template

ARCHETYPES = {
    "luxury_textile": luxury_textile,
    "modern_salon_boutique": modern_salon_boutique,
    "playful_mithai": playful_mithai,
    "artisan_craft": artisan_craft,
    "event_occasion": event_occasion,
    "luxury_jewellery": luxury_jewellery,
}


def list_archetypes() -> list[str]:
    return list(ARCHETYPES.keys())


def render_for_lead(archetype: str, lead: dict) -> Tuple[str, int]:
    """Render a fully-substituted page for one lead. Returns (html, palette_idx)."""
    mod = ARCHETYPES.get(archetype)
    if mod is None:
        mod = ARCHETYPES["modern_salon_boutique"]  # safe fallback

    seed = variation_seed(str(lead.get("business_name", "")))
    palette = pick(seed, mod.PALETTE_POOL)
    headline = pick(seed, mod.HEADLINE_POOL)
    lede = pick(seed, mod.LEDE_POOL)

    # __BIZ_CITY__ inside lede strings: substitute first so {city} interpolates inside lede.
    lede = lede.replace("__BIZ_CITY__", str(lead.get("city", "")))

    html = render_template(mod.TEMPLATE, lead, palette, headline, lede)
    return html, mod.PALETTE_POOL.index(palette)


def render_template_cached(archetype: str, palette_idx: int) -> str:
    """Render TEMPLATE with palette + headline+lede frozen to one slot,
    leaving __BIZ_*__ tokens un-substituted. Used by template_cache so that
    one cache file serves all leads sharing (archetype, palette_idx).

    The cache key encodes both archetype and palette_idx.
    """
    mod = ARCHETYPES.get(archetype) or ARCHETYPES["modern_salon_boutique"]
    palette = mod.PALETTE_POOL[palette_idx % len(mod.PALETTE_POOL)]
    headline = mod.HEADLINE_POOL[palette_idx % len(mod.HEADLINE_POOL)]
    lede = mod.LEDE_POOL[palette_idx % len(mod.LEDE_POOL)]

    out = mod.TEMPLATE
    out = out.replace("__BG__", palette["bg"])
    out = out.replace("__INK__", palette["ink"])
    out = out.replace("__ACCENT__", palette["accent"])
    out = out.replace("__ACCENT2__", palette["accent2"])
    out = out.replace("__ACCENT3__", palette.get("accent3", palette["accent"]))
    out = out.replace("__HEADLINE__", headline)
    out = out.replace("__LEDE__", lede)
    return out
