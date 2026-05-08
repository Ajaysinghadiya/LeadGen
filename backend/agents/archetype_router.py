"""
Map a business `lead.category` (free-form string) to an archetype slug.

Match order: most specific keywords first; fallback to modern_salon_boutique.
Keywords matched case-insensitively, on word-boundaries within the category string.
"""
from __future__ import annotations
import re

# Order matters — first match wins.
RULES: list[tuple[str, list[str]]] = [
    ("luxury_jewellery",       ["jewell", "jewel", "diamond", "gold shop", "gold smith", "bullion", "bridal jewell"]),
    ("luxury_textile",         ["silk", "saree", "sari", "patola", "handloom", "textile", "fabric", "cloth shop"]),
    ("playful_mithai",         ["sweet", "mithai", "farsan", "halwai", "bakery", "bakers", "namkeen", "snack", "confection"]),
    ("artisan_craft",          ["pattachitra", "thanka", "thangka", "painter", "painting", "artist",
                                "sculpt", "stone carv", "handicraft", "hand craft", "craft centre",
                                "craft center", "pottery", "weaver of"]),
    ("event_occasion",         ["mehndi", "mehendi", "henna", "wedding planner", "event manage",
                                "academy", "courses", "course", "training", "institute"]),
    ("modern_salon_boutique",  ["salon", "parlour", "parlor", "spa", "beauty", "hair", "nail",
                                "boutique", "fashion", "tailor", "tailoring", "dress", "garment",
                                "clothing", "designer", "couture", "stylist"]),
]


def route(category: str | None) -> str:
    """Return archetype slug for a given category. Defaults to modern_salon_boutique."""
    text = (category or "").lower().strip()
    if not text:
        return "modern_salon_boutique"

    for archetype, kws in RULES:
        for kw in kws:
            # Prefix match on word boundary — `jewell` matches `jewellery`/`jeweller`.
            # Avoids false hits inside other words (`\b` at start only).
            if re.search(r"\b" + re.escape(kw), text):
                return archetype

    return "modern_salon_boutique"


# Quick sanity table for tests / docs.
EXAMPLES = {
    "sweet shop":                        "playful_mithai",
    "mithai shop":                       "playful_mithai",
    "silk saree shop":                   "luxury_textile",
    "patan patola":                      "luxury_textile",
    "ladies tailor":                     "modern_salon_boutique",
    "boutique":                          "modern_salon_boutique",
    "unisex salon":                      "modern_salon_boutique",
    "pattachitra artist":                "artisan_craft",
    "tibetan thanka shop":               "artisan_craft",
    "mehndi club":                       "event_occasion",
    "fashion academy":                   "event_occasion",
    "jewellery shop":                    "luxury_jewellery",
    "bridal jewellery":                  "luxury_jewellery",
    "diamond store":                     "luxury_jewellery",
    "":                                  "modern_salon_boutique",
}
