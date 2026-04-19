"""
SQLAlchemy ORM models for StockTracker.

Defines the Stock model with all tracked fields for China A-share and
US stock markets. The ``market`` column distinguishes between "CN" and
"US" tickers; it defaults to "CN" for backward compatibility.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Stock(Base):
    """
    Represents a tracked stock ticker and its latest market data.

    Fields are populated by the background scheduler via AkShare.
    Only `symbol` is required when adding a new ticker; all other
    data fields are nullable and filled in on the next refresh cycle.
    """

    __tablename__ = "stocks"

    # ── Primary key & identifier ──────────────────────────────────────
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    symbol: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Stock code, e.g. 600519 or AAPL"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Stock name, e.g. 贵州茅台 / Apple Inc."
    )
    market: Mapped[str] = mapped_column(
        String(5), nullable=False, default="CN",
        comment="Market identifier: CN (China A-share) or US",
    )

    # ── Price data ────────────────────────────────────────────────────
    current_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Latest / real-time price"
    )
    open_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Today's opening price"
    )
    high_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Today's highest price"
    )
    low_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Today's lowest price"
    )
    close_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Previous close (yesterday)"
    )

    # ── Volume & turnover ─────────────────────────────────────────────
    volume: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="Trading volume (shares)"
    )
    turnover: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Trading turnover (CNY)"
    )
    turnover_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Turnover rate (%)"
    )

    # ── Change metrics ────────────────────────────────────────────────
    change_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Price change amount"
    )
    change_percent: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Price change percentage (%)"
    )
    amplitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Price amplitude (%)"
    )

    # ── Fundamentals ──────────────────────────────────────────────────
    market_cap: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Total market capitalization (CNY)"
    )
    circulating_market_cap: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Circulating market cap (CNY)"
    )
    pe_ratio: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Price-to-Earnings ratio (dynamic)"
    )
    pb_ratio: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Price-to-Book ratio"
    )

    # ── 52-week range ─────────────────────────────────────────────────
    high_52w: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="52-week high price"
    )
    low_52w: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="52-week low price"
    )

    # ── Timestamps ────────────────────────────────────────────────────
    last_trade_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Timestamp of the last market trade for this ticker"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=func.now(),
        comment="Last data update time"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(),
        comment="Record creation time"
    )

    # ── Indexes ───────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_stocks_symbol", "symbol"),
        Index("ix_stocks_market", "market"),
        Index("ix_stocks_symbol_market", "symbol", "market", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<Stock(symbol={self.symbol!r}, market={self.market!r}, "
            f"name={self.name!r}, price={self.current_price})>"
        )
