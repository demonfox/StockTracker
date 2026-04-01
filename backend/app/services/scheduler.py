"""
Background scheduler service for StockTracker.

Manages an APScheduler AsyncIOScheduler that periodically:
1. Reads tracked tickers from the database
2. Fetches latest market data via AkShare
3. Batch-updates the database with fresh data

The scheduler respects the configurable refresh interval and
optional market-hours-only restriction.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database.session import async_session_factory
from app.database.crud import batch_update_stock_data, get_tracked_symbols
from app.services.stock_fetcher import fetch_stocks_by_symbols

logger = logging.getLogger(__name__)

# ── Module state ──────────────────────────────────────────────────────

_scheduler: AsyncIOScheduler | None = None

JOB_ID = "refresh_stock_data"

# China market trading hours (CST = UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 0


# ── Market hours check ────────────────────────────────────────────────

def is_market_hours() -> bool:
    """
    Check if the current time falls within China A-share trading hours.
    Trading hours: 9:30 - 11:30 and 13:00 - 15:00 CST, Mon-Fri.
    """
    now = datetime.now(CHINA_TZ)

    # Weekend check (Mon=0, Sun=6)
    if now.weekday() >= 5:
        return False

    current_time = now.hour * 60 + now.minute

    morning_open = MARKET_OPEN_HOUR * 60 + MARKET_OPEN_MINUTE   # 9:30 = 570
    morning_close = 11 * 60 + 30                                 # 11:30 = 690
    afternoon_open = 13 * 60                                     # 13:00 = 780
    afternoon_close = MARKET_CLOSE_HOUR * 60 + MARKET_CLOSE_MINUTE  # 15:00 = 900

    return (morning_open <= current_time <= morning_close or
            afternoon_open <= current_time <= afternoon_close)


# ── Core refresh job ──────────────────────────────────────────────────

async def refresh_stock_data() -> None:
    """
    The main scheduled job: fetch latest data and update the database.

    This function is called by APScheduler at the configured interval.
    It runs AkShare fetch in a thread pool to avoid blocking the event loop
    (AkShare uses synchronous HTTP requests internally).

    Symbols are grouped by market so each group hits the correct API.
    """
    # Skip if market_hours_only is enabled and market is closed
    if settings.scheduler.market_hours_only and not is_market_hours():
        logger.debug("Skipping refresh — market is closed and market_hours_only is enabled.")
        return

    logger.info("Starting stock data refresh cycle...")

    try:
        # Step 1: Get tracked (symbol, market) pairs from DB
        async with async_session_factory() as db:
            symbol_market_pairs = await get_tracked_symbols(db)

        if not symbol_market_pairs:
            logger.info("No stocks being tracked — skipping refresh.")
            return

        # Group symbols by market
        market_groups: dict[str, list[str]] = {}
        for sym, mkt in symbol_market_pairs:
            market_groups.setdefault(mkt, []).append(sym)

        logger.info(
            "Refreshing data for %d tracked symbol(s) across %d market(s).",
            len(symbol_market_pairs),
            len(market_groups),
        )

        # Step 2: Fetch from AkShare per market (run in thread pool)
        loop = asyncio.get_event_loop()
        all_stock_data: dict[str, dict] = {}

        for market, symbols in market_groups.items():
            data = await loop.run_in_executor(
                None,
                fetch_stocks_by_symbols,
                symbols,
                market,
            )
            if data:
                all_stock_data.update(data)

        if not all_stock_data:
            logger.warning("No data returned from AkShare — skipping DB update.")
            return

        # Step 3: Batch update the database
        async with async_session_factory() as db:
            updated = await batch_update_stock_data(db, all_stock_data)

        logger.info(
            "Refresh cycle complete: %d/%d stocks updated.",
            updated,
            len(symbol_market_pairs),
        )

    except Exception as e:
        logger.error("Error during stock data refresh: %s", e, exc_info=True)


# ── Scheduler lifecycle ───────────────────────────────────────────────

def start_scheduler() -> None:
    """
    Initialize and start the APScheduler background scheduler.
    Called during FastAPI application startup.
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler is already running.")
        return

    _scheduler = AsyncIOScheduler()

    interval_seconds = settings.scheduler.refresh_interval_seconds

    _scheduler.add_job(
        refresh_stock_data,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id=JOB_ID,
        name="Refresh stock market data",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    _scheduler.start()
    logger.info(
        "Scheduler started — refreshing every %d seconds (market_hours_only=%s).",
        interval_seconds,
        settings.scheduler.market_hours_only,
    )


def stop_scheduler() -> None:
    """
    Gracefully shut down the scheduler.
    Called during FastAPI application shutdown.
    """
    global _scheduler

    if _scheduler is None:
        return

    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Scheduler stopped.")


def update_interval(new_interval_seconds: int) -> None:
    """
    Update the refresh interval at runtime without restarting the scheduler.

    Args:
        new_interval_seconds: New interval in seconds (minimum 10).

    Raises:
        ValueError: If the interval is below the minimum.
    """
    if new_interval_seconds < 10:
        raise ValueError("Refresh interval must be at least 10 seconds.")

    if _scheduler is None:
        raise RuntimeError("Scheduler is not running.")

    _scheduler.reschedule_job(
        JOB_ID,
        trigger=IntervalTrigger(seconds=new_interval_seconds),
    )

    # Also update the in-memory config
    settings.scheduler.refresh_interval_seconds = new_interval_seconds

    logger.info("Scheduler interval updated to %d seconds.", new_interval_seconds)


def get_scheduler_status() -> dict:
    """
    Return the current scheduler status for the API.
    """
    if _scheduler is None:
        return {
            "running": False,
            "refresh_interval_seconds": settings.scheduler.refresh_interval_seconds,
            "market_hours_only": settings.scheduler.market_hours_only,
            "next_run": None,
        }

    job = _scheduler.get_job(JOB_ID)
    next_run = None
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()

    return {
        "running": True,
        "refresh_interval_seconds": settings.scheduler.refresh_interval_seconds,
        "market_hours_only": settings.scheduler.market_hours_only,
        "next_run": next_run,
    }
