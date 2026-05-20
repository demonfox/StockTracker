"""
Stock data fetching service for StockTracker.

Supports China A-share, US equity, and Hong Kong stock markets using
**per-symbol** queries via the Tencent Finance K-line / quote API.

The Tencent endpoint returns both daily K-line history **and** a rich
real-time ``qt`` quote array in a single request, so there is no need
for separate "realtime" vs "history" fetch modes.

Data source:
  - CN: Tencent Finance K-line API (``tencent_api.fetch_cn_stock_kline``)
  - US: Tencent Finance K-line API (``tencent_api.fetch_us_stock_kline``)
  - HK: Tencent Finance K-line API (``tencent_api.fetch_hk_stock_kline``)
"""

import logging
from typing import Any

from app.services.tencent_api import (  # pyright: ignore[reportImplicitRelativeImport]
    fetch_cn_stock_kline,
    fetch_hk_stock_kline,
    fetch_us_stock_kline,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Unified dispatcher
# ═══════════════════════════════════════════════════════════════════════


def fetch_stocks_by_symbols(
    symbols: list[str],
    market: str = "CN",
) -> dict[str, dict[str, Any]]:
    """
    Fetch latest quote data for the given symbols via Tencent Finance.

    Args:
        symbols: List of stock symbols (e.g. ``["600519"]``, ``["AAPL"]``,
                 or ``["00700"]``).
        market:  ``"CN"``, ``"US"``, or ``"HK"``.

    Returns:
        Dict mapping symbol → data dict.  Missing symbols (API failure)
        are simply omitted from the result.
    """
    if not symbols:
        return {}

    if market == "US":
        return _fetch_us_symbols(symbols)
    if market == "HK":
        return _fetch_hk_symbols(symbols)

    return _fetch_cn_symbols(symbols)


# ── Per-market helpers ────────────────────────────────────────────────


def _fetch_cn_symbols(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch CN stocks one-by-one via Tencent Finance K-line API."""
    logger.info("Fetching data for %d CN symbol(s) via Tencent...", len(symbols))
    result: dict[str, dict[str, Any]] = {}

    for symbol in symbols:
        data = fetch_cn_stock_kline(symbol)
        if data is not None:
            result[symbol] = data

    logger.info(
        "CN fetch complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result


def _fetch_us_symbols(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch US stocks one-by-one via Tencent Finance K-line API."""
    logger.info("Fetching data for %d US symbol(s) via Tencent...", len(symbols))
    result: dict[str, dict[str, Any]] = {}

    for ticker in symbols:
        data = fetch_us_stock_kline(ticker)
        if data is not None:
            result[ticker] = data

    logger.info(
        "US fetch complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result


def _fetch_hk_symbols(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch HK stocks one-by-one via Tencent Finance K-line API."""
    logger.info("Fetching data for %d HK symbol(s) via Tencent...", len(symbols))
    result: dict[str, dict[str, Any]] = {}

    for code in symbols:
        data = fetch_hk_stock_kline(code)
        if data is not None:
            result[code] = data

    logger.info(
        "HK fetch complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result
