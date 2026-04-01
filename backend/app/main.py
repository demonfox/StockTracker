"""
FastAPI application entry point for StockTracker.

Configures CORS, registers API routers, mounts static files
(production), and manages application lifespan (DB init/close,
scheduler start/stop).
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.session import init_db, close_db
from app.routers.stocks import router as stocks_router
from app.services.scheduler import start_scheduler, stop_scheduler

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup:
        1. Initialize database (create tables if needed)
        2. Start background scheduler

    Shutdown:
        1. Stop background scheduler
        2. Close database connections
    """
    # ── Startup ───
    logger.info("StockTracker is starting up...")
    await init_db()
    start_scheduler()
    logger.info("StockTracker startup complete.")

    yield

    # ── Shutdown ──
    logger.info("StockTracker is shutting down...")
    stop_scheduler()
    await close_db()
    logger.info("StockTracker shutdown complete.")


# ── Application factory ──────────────────────────────────────────────

app = FastAPI(
    title="StockTracker API",
    description=(
        "A real-time stock tracking API for China A-share market. "
        "Add tickers, view live quotes, and manage scheduler settings."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ───────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API Routers ───────────────────────────────────────────────────────

app.include_router(stocks_router)


# ── Static file serving (production) ─────────────────────────────────

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.exists() and STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    logger.info("Serving static files from: %s", STATIC_DIR)
else:
    logger.info(
        "No static directory found at %s — frontend will be served by Vite dev server.",
        STATIC_DIR,
    )


# ── Health check ──────────────────────────────────────────────────────

@app.get("/api/health", tags=["system"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "StockTracker"}
