"""
Shared utilities for archetype templates.

Each archetype module exposes:
  PALETTE_POOL   : list[dict]  — keys: bg, ink, accent, accent2, [optional more]
  HEADLINE_POOL  : list[str]
  LEDE_POOL      : list[str]
  TEMPLATE       : str         — HTML with __BIZ_*__ and palette/headline tokens

Tokens substituted at render time:
  __BIZ_NAME__     business_name
  __BIZ_CATEGORY__ category
  __BIZ_CITY__     city
  __BIZ_ADDRESS__  address
  __BIZ_PHONE__    phone
  __BG__           palette["bg"]
  __INK__          palette["ink"]
  __ACCENT__       palette["accent"]
  __ACCENT2__      palette["accent2"]
  __ACCENT3__      palette["accent3"]  (some archetypes)
  __HEADLINE__     headline
  __LEDE__         lede
"""
from __future__ import annotations


def variation_seed(business_name: str) -> int:
    """Stable per-business hash used to pick palette/headline/lede slots."""
    return sum(ord(c) for c in (business_name or ""))


def pick(seed: int, pool: list):
    return pool[seed % len(pool)]


def render_template(
    template: str,
    lead: dict,
    palette: dict,
    headline: str,
    lede: str,
) -> str:
    out = template
    repl = {
        "__BIZ_NAME__": str(lead.get("business_name", "")),
        "__BIZ_CATEGORY__": str(lead.get("category", "")),
        "__BIZ_CITY__": str(lead.get("city", "")),
        "__BIZ_ADDRESS__": str(lead.get("address") or "Local Area"),
        "__BIZ_PHONE__": str(lead.get("phone") or "+91-XXXXXXXXXX"),
        "__BG__": palette.get("bg", "#0e0e0c"),
        "__INK__": palette.get("ink", "#f0e8d4"),
        "__ACCENT__": palette.get("accent", "#cf9b3e"),
        "__ACCENT2__": palette.get("accent2", "#b8392f"),
        "__ACCENT3__": palette.get("accent3", palette.get("accent", "#cf9b3e")),
        "__HEADLINE__": headline,
        "__LEDE__": lede,
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


# Shared SVG grain overlay — reused inside every archetype's <style> block.
GRAIN_DATA_URI = (
    "url(\"data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter>"
    "<rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.55'/></svg>\")"
)
