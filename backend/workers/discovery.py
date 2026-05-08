"""
workers/discovery.py — Module 1: Business Discovery

Priority order for real-data sources:
  1. Google Places API       (GOOGLE_PLACES_API_KEY in .env)
  2. SerpAPI Google Maps     (SERPAPI_KEY in .env — free 100 searches/month)
  3. Mock data               (fallback when no keys configured)
"""
import asyncio
import logging
import httpx
from sqlalchemy import select

from config import settings
from models import Job, Lead
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ─── Mock Businesses (fallback) ───────────────────────────────────────────────
MOCK_BUSINESSES = [
    {"business_name": "Spice Garden Restaurant", "phone": "+919876543210", "address": "12, MG Road", "existing_website": None},
    {"business_name": "Royal Sweets & Snacks",   "phone": "+919876543211", "address": "45, Nehru Bazaar", "existing_website": None},
    {"business_name": "Hotel Sunrise Inn",        "phone": "+919876543212", "address": "78, Station Road", "existing_website": "http://sunriseinn.in"},
    {"business_name": "Sharma Dhaba",             "phone": "+919876543213", "address": "Plot 5, Industrial Area", "existing_website": None},
    {"business_name": "Taj Family Restaurant",    "phone": "+919876543214", "address": "22, Civil Lines", "existing_website": "http://tajrestaurant.business.site"},
    {"business_name": "Green Leaf Cafe",          "phone": "+919876543215", "address": "7, Pink Square Mall", "existing_website": None},
    {"business_name": "Bikaner Mishthan Bhandar", "phone": "+919876543216", "address": "3, Johari Bazaar", "existing_website": None},
    {"business_name": "Chotu Dhaba",              "phone": "+919876543217", "address": "Near Bus Stand", "existing_website": None},
]


# ─── Source 1: Google Places API ──────────────────────────────────────────────
async def fetch_google_places(city: str, category: str) -> list[dict]:
    """Fetch businesses from Google Places Text Search API."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    businesses = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "query": f"{category} in {city}",
            "key": settings.google_places_api_key,
        }
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            raise ValueError(f"Google Places error: {data.get('status')} — {data.get('error_message', '')}")

        def parse_place(place):
            return {
                "business_name": place.get("name", "Unknown"),
                "phone": None,          # requires Place Details call
                "email": None,
                "address": place.get("formatted_address", ""),
                "existing_website": place.get("website"),
            }

        for place in data.get("results", []):
            businesses.append(parse_place(place))

        # Paginate (up to 2 extra pages = 60 results max)
        for _ in range(2):
            next_token = data.get("next_page_token")
            if not next_token:
                break
            await asyncio.sleep(2)   # Google requires a short delay
            params2 = {"pagetoken": next_token, "key": settings.google_places_api_key}
            resp2 = await client.get(url, params=params2)
            data = resp2.json()
            for place in data.get("results", []):
                businesses.append(parse_place(place))

    logger.info(f"Google Places returned {len(businesses)} results")
    return businesses


# ─── Source 2: SerpAPI (Google Maps Results) ──────────────────────────────────
async def fetch_serpapi(city: str, category: str) -> list[dict]:
    """Fetch businesses using SerpAPI's Google Maps engine.
    Free plan: 100 searches/month. Sign up at https://serpapi.com/
    """
    url = "https://serpapi.com/search"
    businesses = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "engine": "google_maps",
            "q": f"{category} in {city}",
            "api_key": settings.serpapi_key,
            "type": "search",
            "hl": "en",
        }
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for place in data.get("local_results", []):
            businesses.append({
                "business_name": place.get("title", "Unknown"),
                "phone": place.get("phone"),
                "email": None,
                "address": place.get("address", ""),
                "existing_website": place.get("website"),
            })

    logger.info(f"SerpAPI returned {len(businesses)} results")
    return businesses


# ─── Orchestration ────────────────────────────────────────────────────────────
async def run_discovery(job_id: int) -> int:
    """
    Step 1: Discover businesses for a job.
    Returns the number of businesses found.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        city, category = job.city, job.category

    logger.info(f"[Job {job_id}] Starting discovery for '{category}' in '{city}'")

    businesses = None
    source_used = "mock"

    # Try Source 1: Google Places
    if settings.is_real("google_places_api_key"):
        try:
            businesses = await fetch_google_places(city, category)
            source_used = "google_places"
            logger.info(f"[Job {job_id}] Using Google Places API ✓")
        except Exception as e:
            logger.warning(f"[Job {job_id}] Google Places failed: {e}")

    # Try Source 2: SerpAPI (fallback from Google Places)
    if businesses is None and settings.is_real("serpapi_key"):
        try:
            businesses = await fetch_serpapi(city, category)
            source_used = "serpapi"
            logger.info(f"[Job {job_id}] Using SerpAPI ✓")
        except Exception as e:
            logger.warning(f"[Job {job_id}] SerpAPI failed: {e}")

    # Fallback: Mock data
    if businesses is None:
        logger.info(
            f"[Job {job_id}] ⚠ No real API keys configured — using mock data. "
            "Add GOOGLE_PLACES_API_KEY or SERPAPI_KEY to .env to get live results."
        )
        businesses = [{**b, "city": city, "category": category} for b in MOCK_BUSINESSES]
        source_used = "mock"

    # Enrich with city/category
    for b in businesses:
        b.setdefault("city", city)
        b.setdefault("category", category)
        b.setdefault("email", None)

    # Persist to DB
    async with AsyncSessionLocal() as db:
        for biz in businesses:
            lead = Lead(
                job_id=job_id,
                business_name=biz["business_name"],
                phone=biz.get("phone"),
                email=biz.get("email"),
                address=biz.get("address"),
                city=biz.get("city", city),
                category=biz.get("category", category),
                existing_website=biz.get("existing_website"),
                status="discovered",
            )
            db.add(lead)

        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one()
        job.total_found = len(businesses)
        await db.commit()

    logger.info(
        f"[Job {job_id}] Discovery complete — {len(businesses)} businesses found "
        f"via {source_used}"
    )
    return len(businesses)
