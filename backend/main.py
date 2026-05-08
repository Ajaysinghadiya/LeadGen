"""
main.py — FastAPI application entry point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import settings
from database import init_db
from routers import jobs, leads, whatsapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting LeadGen API...")
    settings.ensure_dirs()
    await init_db()
    logger.info("Database initialized ✓")
    yield
    logger.info("Shutting down LeadGen API...")


app = FastAPI(
    title="LeadGen API",
    description="Lead Generation & Automated Outreach System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(jobs.router)
app.include_router(leads.router)
app.include_router(whatsapp.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Serve generated sites statically
sites_path = Path(settings.generated_sites_dir)
if sites_path.exists():
    app.mount("/sites", StaticFiles(directory=str(sites_path)), name="sites")

videos_path = Path(settings.videos_dir)
if videos_path.exists():
    app.mount("/videos", StaticFiles(directory=str(videos_path)), name="videos")
