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

# ── Timezone constants ────────────────────────────────────────────────

# China Standard Time (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))

# US Eastern Time — fixed UTC-4 (EDT).
# For exact DST handling, consider ``zoneinfo.ZoneInfo("America/New_York")``.
US_EASTERN_TZ = timezone(timedelta(hours=-4))


# ── Market hours check ────────────────────────────────────────────────

def is_cn_market_hours() -> bool:
    """
    Check if the current time falls within China A-share trading hours.

    Trading hours: 9:30 - 11:30 and 13:00 - 15:00 CST, Mon-Fri.
    """
    now = datetime.now(CHINA_TZ)

    # Weekend check (Mon=0, Sun=6)
    if now.weekday() >= 5:
        return False

    t = now.hour * 60 + now.minute

    morning_open = 9 * 60 + 30    # 09:30 = 570
    morning_close = 11 * 60 + 30  # 11:30 = 690
    afternoon_open = 13 * 60      # 13:00 = 780
    afternoon_close = 15 * 60     # 15:00 = 900

    return (morning_open <= t <= morning_close
            or afternoon_open <= t <= afternoon_close)


def is_us_market_hours() -> bool:
    """
    Check if the current time falls within US stock regular trading hours.

    Trading hours: 9:30 - 16:00 ET, Mon-Fri.
    """
    now = datetime.now(US_EASTERN_TZ)

    if now.weekday() >= 5:
        return False

    t = now.hour * 60 + now.minute

    market_open = 9 * 60 + 30   # 09:30 = 570
    market_close = 16 * 60      # 16:00 = 960

    return market_open <= t <= market_close


def is_market_open(market: str) -> bool:
    """
    Check if the given market is currently in trading hours.

    Args:
        market: ``"CN"`` or ``"US"``.
    """
    if market == "CN":
        return is_cn_market_hours()
    if market == "US":
        return is_us_market_hours()
    # Unknown market — default to open so we don't silently skip it
    return True


# ── Core refresh job ──────────────────────────────────────────────────

async def refresh_stock_data() -> None:
    """
    The main scheduled job: fetch latest data and update the database.

    This function is called by APScheduler at the configured interval.
    It runs AkShare fetch in a thread pool to avoid blocking the event loop
    (AkShare uses synchronous HTTP requests internally).

    Symbols are grouped by market so each group hits the correct API.
    When ``market_hours_only`` is enabled, only markets whose exchanges
    are currently open will be refreshed.
    """
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

        # Filter out closed markets when market_hours_only is enabled
        if settings.scheduler.market_hours_only:
            open_markets = {
                mkt: syms for mkt, syms in market_groups.items()
                if is_market_open(mkt)
            }
            skipped = set(market_groups) - set(open_markets)
            if skipped:
                logger.debug(
                    "market_hours_only: skipping closed market(s) %s.",
                    ", ".join(sorted(skipped)),
                )
            if not open_markets:
                logger.debug(
                    "Skipping refresh — all markets closed and "
                    "market_hours_only is enabled.",
                )
                return
            market_groups = open_markets

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
