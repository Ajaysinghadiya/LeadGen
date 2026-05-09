"""
agents/lead_finder.py — v2 discovery: auto-sweep "boring" Indian SMB categories.

Replaces the city+category single-query path. For each new job we:
  1. Fan out 8 SerpAPI / Google Places queries in parallel (one per "boring" category)
  2. Filter results by reviews ∈ [5,100], rating ≥ 3.8, phone present
  3. Dedup by phone within the sweep
  4. If < 5 qualified leads in the city, sweep the NEAREST city as well
     (we never loosen the filters — we only widen the geography)

Why "boring" categories?
  Sweet shops, dhabas, sarees, jewellers, bakeries, tailors, printing presses, and
  handicraft shops are real local SMBs with ₹5K spend potential that NO digital
  agency is currently pitching. Pitched-to-death verticals (gyms, salons, cafes)
  are deliberately excluded.

This module sits in agents/ (not workers/) so the locked workers/discovery.py
stays untouched. orchestrator.run_job → run_discovery here instead of the worker.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import httpx
from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal
from models import Job, Lead

logger = logging.getLogger(__name__)


# ─── Boring categories (curated, locked 2026-05-09) ─────────────────────────

BORING_CATEGORIES: list[str] = [
    "sweet shop",
    "dhaba",
    "saree shop",
    "local jeweller",
    "bakery",
    "tailor boutique",
    "printing press",
    "handicraft shop",
]

# Sentinel value stored on Job.category so reuse / dedup logic still works.
SWEEP_TAG = "auto_boring_sweep"


# ─── Qualification filters ──────────────────────────────────────────────────

MIN_REVIEWS = 5      # below = too thin / fly-by-night
MAX_REVIEWS = 100    # above = already pitched by competitor agencies
MIN_RATING = 3.8     # below = customer-experience problem, not website problem


def _passes_filter(biz: dict) -> bool:
    """Inclusion gate — applied during discovery, not during audit."""
    rating = biz.get("rating")
    reviews = biz.get("reviews")
    phone = biz.get("phone")
    if not phone:
        return False
    if rating is None or reviews is None:
        return False
    if rating < MIN_RATING:
        return False
    if not (MIN_REVIEWS <= reviews <= MAX_REVIEWS):
        return False
    return True


# ─── Nearest-city expansion (no external geocoding needed) ──────────────────
# When a city returns < 5 qualified leads, we widen the search to one of these
# neighbours WITHOUT loosening any filter. Keys are normalized lowercase.
# Picks lean conservative — only well-known metros + their satellite cities.

NEAREST_CITY: dict[str, list[str]] = {
    "jaipur":     ["ajmer", "jodhpur", "kishangarh"],
    "udaipur":    ["chittorgarh", "rajsamand", "ajmer"],
    "jodhpur":    ["jaisalmer", "barmer", "pali"],
    "ajmer":      ["jaipur", "kishangarh", "pushkar"],
    "delhi":      ["gurgaon", "noida", "ghaziabad", "faridabad"],
    "gurgaon":    ["delhi", "noida", "faridabad"],
    "noida":      ["delhi", "ghaziabad", "gurgaon"],
    "mumbai":     ["thane", "navi mumbai", "kalyan"],
    "thane":      ["mumbai", "navi mumbai", "kalyan"],
    "pune":       ["pimpri-chinchwad", "satara", "nashik"],
    "nashik":     ["pune", "ahmednagar"],
    "bangalore":  ["mysore", "tumkur", "hosur"],
    "mysore":     ["bangalore", "mandya"],
    "ahmedabad":  ["gandhinagar", "vadodara", "anand"],
    "vadodara":   ["ahmedabad", "anand", "bharuch"],
    "surat":      ["vadodara", "navsari", "valsad"],
    "chennai":    ["kanchipuram", "tiruvallur", "vellore"],
    "kolkata":    ["howrah", "barrackpore", "durgapur"],
    "hyderabad":  ["secunderabad", "warangal", "nizamabad"],
    "lucknow":    ["kanpur", "barabanki", "unnao"],
    "kanpur":     ["lucknow", "unnao"],
    "indore":     ["ujjain", "dewas", "bhopal"],
    "bhopal":     ["indore", "vidisha"],
    "patna":      ["gaya", "muzaffarpur"],
    "kochi":      ["thrissur", "alappuzha", "ernakulam"],
}


def _nearest_city(city: str) -> str | None:
    neighbours = NEAREST_CITY.get((city or "").strip().lower())
    if not neighbours:
        return None
    return neighbours[0]   # first entry = best match


# ─── Provider parsers (extract rating + reviews count) ──────────────────────

def _parse_serpapi_place(place: dict, city: str, category: str) -> dict:
    return {
        "business_name": place.get("title") or "Unknown",
        "phone": place.get("phone"),
        "email": None,
        "address": place.get("address") or "",
        "city": city,
        "category": category,
        "existing_website": place.get("website"),
        "rating": place.get("rating"),
        "reviews": place.get("reviews"),   # SerpAPI returns count under this key
    }


def _parse_google_place(place: dict, city: str, category: str) -> dict:
    return {
        "business_name": place.get("name") or "Unknown",
        "phone": None,                      # would need a Place Details follow-up
        "email": None,
        "address": place.get("formatted_address") or "",
        "city": city,
        "category": category,
        "existing_website": place.get("website"),
        "rating": place.get("rating"),
        "reviews": place.get("user_ratings_total"),
    }


# ─── HTTP fetchers ──────────────────────────────────────────────────────────

async def _fetch_serpapi(city: str, category: str) -> list[dict]:
    """Single SerpAPI Google Maps query → parsed list."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_maps",
        "q": f"{category} in {city}",
        "api_key": settings.serpapi_key,
        "type": "search",
        "hl": "en",
    }
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    return [_parse_serpapi_place(p, city, category) for p in data.get("local_results", [])]


async def _fetch_google_places(city: str, category: str) -> list[dict]:
    """Single Google Places Text Search query → parsed list (no phone — Place Details
    would be a separate paid call per result)."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{category} in {city}",
        "key": settings.google_places_api_key,
    }
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise ValueError(f"Google Places error: {data.get('status')}")
    return [_parse_google_place(p, city, category) for p in data.get("results", [])]


# ─── Mock fallback (when neither key is configured) ─────────────────────────

_MOCK_LEADS = [
    # (name, phone, address, category, existing_website, rating, reviews)
    ("Royal Mithai Bhandar",   "+919876500011", "45, Nehru Bazaar",       "sweet shop",       None,                                    4.3, 47),
    ("Sharma Halwai",          "+919876500012", "12, MI Road",             "sweet shop",       "http://sharmahalwai.business.site",     4.0, 22),
    ("Lakshmi Family Dhaba",   "+919876500013", "Highway 8, Outskirts",    "dhaba",            None,                                    4.4, 81),
    ("Padma Silk Sarees",      "+919876500014", "Big Bazaar Street",       "saree shop",       None,                                    4.2, 35),
    ("Andavar Jewellers",      "+919876500015", "East Masi Street",        "local jeweller",   "http://andavar.wix.com",                4.1, 18),
    ("Sweet Bakers",           "+919876500016", "5, Pink Square Mall",     "bakery",           None,                                    4.5, 64),
    ("Style Tailor Boutique",  "+919876500017", "22, Civil Lines",         "tailor boutique",  None,                                    3.9, 12),
    ("Reliable Print Press",   "+919876500018", "Plot 7, Industrial Area", "printing press",   None,                                    4.0, 27),
    ("Pattachitra Crafts",     "+919876500019", "Heritage Crafts Village", "handicraft shop",  None,                                    4.6, 53),
]


def _mock_sweep(city: str) -> list[dict]:
    """One mock lead per boring category, all with usable rating/reviews/phone."""
    return [
        {
            "business_name": name,
            "phone": phone,
            "email": None,
            "address": addr,
            "city": city,
            "category": cat,
            "existing_website": site,
            "rating": rating,
            "reviews": reviews,
        }
        for (name, phone, addr, cat, site, rating, reviews) in _MOCK_LEADS
    ]


# ─── Sweep one city across ALL boring categories in parallel ────────────────

async def _sweep_city(city: str) -> tuple[list[dict], str]:
    """Fan out one query per BORING_CATEGORIES, filter, dedup-by-phone.
    Returns (qualified_leads, source_used). Skips the API entirely if no key."""

    if settings.is_real("google_places_api_key"):
        fetcher = _fetch_google_places
        source = "google_places"
    elif settings.is_real("serpapi_key"):
        fetcher = _fetch_serpapi
        source = "serpapi"
    else:
        return _mock_sweep(city), "mock"

    # Parallel fan-out — 8 concurrent calls instead of 8 sequential.
    results = await asyncio.gather(
        *[fetcher(city, cat) for cat in BORING_CATEGORIES],
        return_exceptions=True,
    )

    raw: list[dict] = []
    for cat, res in zip(BORING_CATEGORIES, results):
        if isinstance(res, Exception):
            logger.warning(f"{source} sweep failed for ({city}, {cat}): {res}")
            continue
        raw.extend(res)

    # Filter — rating, reviews, phone present.
    qualified = [b for b in raw if _passes_filter(b)]

    # Dedup by phone (a sweet shop might also list under bakery, etc).
    seen_phones: set[str] = set()
    deduped: list[dict] = []
    for b in qualified:
        phone = b.get("phone")
        if not phone or phone in seen_phones:
            continue
        seen_phones.add(phone)
        deduped.append(b)

    return deduped, source


# ─── Persistence ────────────────────────────────────────────────────────────

async def _persist_leads(job_id: int, leads: Iterable[dict]) -> int:
    """Insert leads as Lead rows with status='discovered'. Returns insert count.
    Lead.category is set to the matching boring category — drives archetype routing
    and later seo_pitch / build_site branching unaffected."""
    count = 0
    async with AsyncSessionLocal() as db:
        for biz in leads:
            db.add(Lead(
                job_id=job_id,
                business_name=biz["business_name"],
                phone=biz.get("phone"),
                email=biz.get("email"),
                address=biz.get("address"),
                city=biz["city"],
                category=biz["category"],
                existing_website=biz.get("existing_website"),
                status="discovered",
            ))
            count += 1

        cur = await db.execute(select(Job).where(Job.id == job_id))
        job = cur.scalar_one()
        job.total_found = count
        await db.commit()
    return count


# ─── Public entry point — replaces workers/discovery.run_discovery for v2 ───

MIN_LEADS_BEFORE_EXPANSION = 5


async def run_discovery(job_id: int) -> int:
    """Sweep the job's city across all boring categories. If under
    MIN_LEADS_BEFORE_EXPANSION qualified, also sweep the nearest city.
    Filters never loosen — only geography widens. Returns total persisted count."""

    async with AsyncSessionLocal() as db:
        cur = await db.execute(select(Job).where(Job.id == job_id))
        job = cur.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        primary_city = job.city

    primary, source = await _sweep_city(primary_city)
    logger.info(
        f"[Job {job_id}] sweep('{primary_city}') via {source} → "
        f"{len(primary)} qualified across {len(BORING_CATEGORIES)} categories"
    )

    leads = list(primary)
    expanded_from = None

    if len(leads) < MIN_LEADS_BEFORE_EXPANSION:
        neighbour = _nearest_city(primary_city)
        if neighbour and source != "mock":
            extra, _src = await _sweep_city(neighbour)
            # Dedup phones across both cities
            seen = {b.get("phone") for b in leads if b.get("phone")}
            extra = [b for b in extra if b.get("phone") and b["phone"] not in seen]
            if extra:
                # Tag expanded leads' city with the original target city — outreach
                # talks about the customer's city, not where Google Maps sourced them.
                # But keep an internal note in address for the audit log.
                for b in extra:
                    b["address"] = f"{b['address']} (sourced from {neighbour})".strip()
                    b["city"] = primary_city
                leads.extend(extra)
                expanded_from = neighbour
                logger.info(
                    f"[Job {job_id}] expanded to '{neighbour}' (+{len(extra)} leads) "
                    f"because primary city had only {len(primary)}"
                )

    inserted = await _persist_leads(job_id, leads)
    logger.info(
        f"[Job {job_id}] discovery complete — {inserted} qualified leads persisted "
        f"(source={source}, expanded_from={expanded_from})"
    )
    return inserted
