"""
Pydantic schemas for StockTracker API request/response validation.

These schemas define the data contracts between frontend and backend,
ensuring all data is properly validated and typed at API boundaries.
"""

from datetime import datetime

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
    refresh_interval_seconds: int | None = Field(
        None,
        ge=10,
        le=3600,
        description="Data refresh interval in seconds (min 10, max 3600)",
    )
    market_hours_only: bool | None = Field(
        None,
        description="Only refresh during each market's trading hours (CN/US independently)",
    )


# ── Response Schemas ──────────────────────────────────────────────────

class StockResponse(BaseModel):
    """Full stock data response — maps directly from the Stock ORM model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str | None = None
    market: str = "CN"

    # Price
    current_price: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    close_price: float | None = None

    # Volume
    volume: int | None = None
    turnover: float | None = None
    turnover_rate: float | None = None

    # Change
    change_amount: float | None = None
    change_percent: float | None = None
    amplitude: float | None = None

    # Fundamentals
    market_cap: float | None = None
    circulating_market_cap: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None

    # 52-week range
    high_52w: float | None = None
    low_52w: float | None = None

    # Timestamps
    last_trade_time: datetime | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None


class StockListResponse(BaseModel):
    """Wrapper for a list of stocks with metadata."""
    count: int = Field(description="Total number of tracked stocks")
    stocks: list[StockResponse] = Field(description="List of stock records")


class SchedulerStatusResponse(BaseModel):
    """Current scheduler status information."""
    running: bool
    refresh_interval_seconds: int
    market_hours_only: bool
    next_run: str | None = None


class MessageResponse(BaseModel):
    """Generic message response for simple operations."""
    message: str
    success: bool = True
