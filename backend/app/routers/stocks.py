"""
Stock API router for StockTracker.

Endpoints:
    GET    /api/stocks            — List all tracked stocks
    POST   /api/stocks            — Add a new stock ticker
    GET    /api/stocks/{symbol}   — Get a single stock by symbol
    DELETE /api/stocks/{symbol}   — Remove a stock from tracking
    GET    /api/indices           — Fetch real-time market indices (CN/HK/US)
    GET    /api/indices/minute    — Intraday minute data for CN/HK/US indices
    GET    /api/scheduler/status  — Get scheduler status info
    PATCH  /api/config            — Update scheduler config at runtime
    POST   /api/scheduler/refresh — Trigger an immediate data refresh
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.crud import (
    add_stock,
    get_all_stocks,
    get_stock_by_symbol,
    remove_stock,
)
from app.schemas.stock import (
    ConfigUpdate,
    IndexMinuteData,
    IndexQuote,
    IndicesMinuteResponse,
    IndicesResponse,
    KlinePoint,
    MessageResponse,
    SchedulerStatusResponse,
    StockCreate,
    StockKlineResponse,
    StockListResponse,
    StockResponse,
)
from app.services.scheduler import (
    get_scheduler_status,
    refresh_stock_data,
    update_interval,
)
from app.services.stock_fetcher import fetch_stocks_by_symbols
from app.services.index_fetcher import fetch_all_indices, fetch_indices_minute
from app.services.tencent_api import fetch_cn_stock_weekly_kline
from app.database.crud import batch_update_stock_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["stocks"])


# ── Stock CRUD endpoints ──────────────────────────────────────────────

@router.get("/stocks", response_model=StockListResponse)
async def list_stocks(db: AsyncSession = Depends(get_db)) -> StockListResponse:
    """
    List all tracked stocks with their latest data.

    Returns a sorted list of all stock records currently in the database.
    """
    stocks = await get_all_stocks(db)
    return StockListResponse(
        count=len(stocks),
        stocks=[StockResponse.model_validate(s) for s in stocks],
    )


@router.post(
    "/stocks",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_stock_endpoint(
    payload: StockCreate,
    db: AsyncSession = Depends(get_db),
) -> StockResponse:
    """
    Add a new stock ticker to the tracking list.

    After adding, immediately attempts to fetch the stock's current data
    from Tencent Finance so the user gets immediate feedback.
    """
    symbol = payload.symbol.strip()
    market = payload.market.strip().upper()

    try:
        stock = await add_stock(db, symbol, market=market)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Attempt immediate data fetch for the new stock
    # Run in thread pool since Tencent Finance fetcher is synchronous
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            fetch_stocks_by_symbols,
            [symbol],
            market,
        )
        if data and symbol in data:
            await batch_update_stock_data(db, {symbol: data[symbol]})
            # Refresh the stock object to include updated data
            stock = await get_stock_by_symbol(db, symbol, market)
            logger.info("Fetched initial data for new stock: %s/%s", market, symbol)
    except Exception as e:
        # Non-fatal: the stock is added but data will come with next refresh
        logger.warning(
            "Could not fetch initial data for %s/%s: %s (will retry on next refresh)",
            market,
            symbol,
            e,
        )

    return StockResponse.model_validate(stock)


@router.get("/stocks/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> StockResponse:
    """Get a single stock's data by its symbol."""
    stock = await get_stock_by_symbol(db, symbol)
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found.",
        )
    return StockResponse.model_validate(stock)


@router.delete("/stocks/{symbol}", response_model=MessageResponse)
async def delete_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Remove a stock ticker from the tracking list."""
    deleted = await remove_stock(db, symbol)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found.",
        )
    return MessageResponse(
        message=f"Stock '{symbol}' removed successfully.",
        success=True,
    )


# ── Stock K-line endpoint ──────────────────────────────────────────────

@router.get("/stocks/{symbol}/kline", response_model=StockKlineResponse)
async def get_stock_kline(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> StockKlineResponse:
    """
    Get 52-week weekly K-line data for a CN stock.

    Returns weekly closing prices (前复权) for the past ~52 weeks,
    suitable for rendering a price trend chart.
    """
    stock = await get_stock_by_symbol(db, symbol)
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found.",
        )

    if stock.market != "CN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weekly K-line is currently only supported for CN stocks.",
        )

    loop = asyncio.get_event_loop()
    bars = await loop.run_in_executor(
        None,
        fetch_cn_stock_weekly_kline,
        symbol,
        52,
    )

    return StockKlineResponse(
        symbol=symbol,
        name=stock.name,
        market="CN",
        points=[KlinePoint(date=b["date"], close=b["close"]) for b in bars],
    )


# ── Market Indices endpoint ────────────────────────────────────────────

@router.get("/indices", response_model=IndicesResponse)
async def get_indices() -> IndicesResponse:
    """
    Fetch real-time quotes for major market indices (CN, HK, US).

    Returns grouped index data — 3 indices per market.
    Data is fetched live from Tencent Finance (not persisted).
    """
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_all_indices)
    return IndicesResponse(
        cn=[IndexQuote(**item) for item in data["cn"]],
        hk=[IndexQuote(**item) for item in data["hk"]],
        us=[IndexQuote(**item) for item in data["us"]],
    )


@router.get("/indices/minute", response_model=IndicesMinuteResponse)
async def get_indices_minute() -> IndicesMinuteResponse:
    """
    Fetch intraday minute-level price data for CN, HK, and US market indices.

    Returns per-minute price points for the current (or last) trading day.
    CN/HK use Tencent minute/query (per-minute), US uses Sina 5-min K-line.
    """
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_indices_minute)
    return IndicesMinuteResponse(
        cn=[IndexMinuteData(**item) for item in data.get("cn", [])],
        hk=[IndexMinuteData(**item) for item in data.get("hk", [])],
        us=[IndexMinuteData(**item) for item in data.get("us", [])],
    )


# ── Scheduler & Config endpoints ─────────────────────────────────────

@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def scheduler_status() -> SchedulerStatusResponse:
    """Get the current scheduler status (running, interval, next run)."""
    status_data = get_scheduler_status()
    return SchedulerStatusResponse(**status_data)


@router.patch("/config", response_model=MessageResponse)
async def update_config(payload: ConfigUpdate) -> MessageResponse:
    """
    Update scheduler configuration at runtime.

    Supports changing refresh interval and market_hours_only setting
    without restarting the application.
    """
    changes: list[str] = []

    if payload.refresh_interval_seconds is not None:
        try:
            update_interval(payload.refresh_interval_seconds)
            changes.append(
                f"refresh_interval_seconds={payload.refresh_interval_seconds}"
            )
        except (ValueError, RuntimeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    if payload.market_hours_only is not None:
        # Import here to update the live setting
        from app.config import settings
        settings.scheduler.market_hours_only = payload.market_hours_only
        changes.append(f"market_hours_only={payload.market_hours_only}")

    if not changes:
        return MessageResponse(
            message="No configuration changes provided.",
            success=True,
        )

    change_summary = ", ".join(changes)
    logger.info("Configuration updated: %s", change_summary)
    return MessageResponse(
        message=f"Configuration updated: {change_summary}",
        success=True,
    )


@router.post("/scheduler/refresh", response_model=MessageResponse)
async def trigger_refresh() -> MessageResponse:
    """
    Trigger an immediate stock data refresh.

    Bypasses the scheduler interval and market hours check,
    running a full data refresh cycle right now.
    """
    logger.info("Manual refresh triggered via API.")

    try:
        await refresh_stock_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refresh failed: {e}",
        )

    return MessageResponse(
        message="Stock data refresh completed successfully.",
        success=True,
    )
