"""
Pydantic schemas for StockTracker API request/response validation.

These schemas define the data contracts between frontend and backend,
ensuring all data is properly validated and typed at API boundaries.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request Schemas ───────────────────────────────────────────────────

class StockCreate(BaseModel):
    """Schema for adding a new stock ticker."""
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock symbol code, e.g. '600519' for A-share or 'AAPL' for US",
        examples=["600519", "000001", "AAPL", "MSFT"],
    )
    market: str = Field(
        default="CN",
        pattern=r"^(CN|US)$",
        description="Market identifier: 'CN' for China A-share, 'US' for US stocks",
    )


class ConfigUpdate(BaseModel):
    """Schema for updating scheduler configuration at runtime."""
    refresh_interval_seconds: Optional[int] = Field(
        None,
        ge=10,
        le=3600,
        description="Data refresh interval in seconds (min 10, max 3600)",
    )
    market_hours_only: Optional[bool] = Field(
        None,
        description="Only refresh during China market trading hours",
    )


# ── Response Schemas ──────────────────────────────────────────────────

class StockResponse(BaseModel):
    """Full stock data response — maps directly from the Stock ORM model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: Optional[str] = None
    market: str = "CN"

    # Price
    current_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None

    # Volume
    volume: Optional[int] = None
    turnover: Optional[float] = None
    turnover_rate: Optional[float] = None

    # Change
    change_amount: Optional[float] = None
    change_percent: Optional[float] = None
    amplitude: Optional[float] = None

    # Fundamentals
    market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None

    # 52-week range
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None

    # Timestamps
    last_trade_time: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class StockListResponse(BaseModel):
    """Wrapper for a list of stocks with metadata."""
    count: int = Field(description="Total number of tracked stocks")
    stocks: list[StockResponse] = Field(description="List of stock records")


class SchedulerStatusResponse(BaseModel):
    """Current scheduler status information."""
    running: bool
    refresh_interval_seconds: int
    market_hours_only: bool
    next_run: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response for simple operations."""
    message: str
    success: bool = True
