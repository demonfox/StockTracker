"""
CRUD operations for StockTracker.

All database interactions go through these functions. Each function
accepts an AsyncSession (injected via FastAPI's Depends) and uses
parameterized queries via SQLAlchemy — never raw string concatenation.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Stock

logger = logging.getLogger(__name__)


# ── Read Operations ───────────────────────────────────────────────────

async def get_all_stocks(db: AsyncSession) -> list[Stock]:
    """Return all tracked stocks, ordered by symbol."""
    result = await db.execute(
        select(Stock).order_by(Stock.symbol)
    )
    return list(result.scalars().all())


async def get_stock_by_symbol(
    db: AsyncSession,
    symbol: str,
    market: str = "CN",
) -> Optional[Stock]:
    """Return a single stock by its symbol and market, or None if not found."""
    result = await db.execute(
        select(Stock).where(Stock.symbol == symbol, Stock.market == market)
    )
    return result.scalar_one_or_none()


async def get_tracked_symbols(db: AsyncSession) -> list[tuple[str, str]]:
    """
    Return a list of all tracked (symbol, market) pairs.

    Returns:
        List of (symbol, market) tuples, e.g. [("600519", "CN"), ("AAPL", "US")].
    """
    result = await db.execute(
        select(Stock.symbol, Stock.market).order_by(Stock.market, Stock.symbol)
    )
    return [(row[0], row[1]) for row in result.all()]


# ── Write Operations ──────────────────────────────────────────────────

async def add_stock(
    db: AsyncSession,
    symbol: str,
    market: str = "CN",
    name: Optional[str] = None,
) -> Stock:
    """
    Add a new stock ticker to the tracking list.
    Raises ValueError if the (symbol, market) pair already exists.
    """
    existing = await get_stock_by_symbol(db, symbol, market)
    if existing is not None:
        raise ValueError(
            f"Stock with symbol '{symbol}' (market={market}) is already being tracked."
        )

    stock = Stock(symbol=symbol, market=market, name=name)
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    logger.info("Added stock: %s/%s (%s)", market, symbol, name or "no name yet")
    return stock


async def remove_stock(db: AsyncSession, symbol: str) -> bool:
    """
    Remove a stock ticker from the tracking list.
    Returns True if a record was deleted, False if symbol was not found.
    """
    result = await db.execute(
        delete(Stock).where(Stock.symbol == symbol)
    )
    await db.commit()
    deleted = result.rowcount > 0
    if deleted:
        logger.info("Removed stock: %s", symbol)
    else:
        logger.warning("Attempted to remove non-existent stock: %s", symbol)
    return deleted


# ── Batch Update (used by the scheduler) ──────────────────────────────

async def batch_update_stock_data(
    db: AsyncSession,
    stock_data_map: dict[str, dict],
) -> int:
    """
    Batch-update market data for multiple stocks in a single transaction.

    Args:
        db: Async database session.
        stock_data_map: Dict mapping symbol -> dict of field values to update.
            Example: {"600519": {"current_price": 1800.0, "name": "贵州茅台", ...}}

    Returns:
        Number of stocks successfully updated.
    """
    if not stock_data_map:
        return 0

    updated_count = 0
    now = datetime.now(timezone.utc)

    for symbol, data in stock_data_map.items():
        # Build the update dict, filtering out None keys and adding timestamp
        update_values = {k: v for k, v in data.items() if v is not None}
        update_values["updated_at"] = now

        result = await db.execute(
            update(Stock)
            .where(Stock.symbol == symbol)
            .values(**update_values)
        )
        if result.rowcount > 0:
            updated_count += 1

    await db.commit()
    logger.info(
        "Batch update complete: %d/%d stocks updated.",
        updated_count,
        len(stock_data_map),
    )
    return updated_count
