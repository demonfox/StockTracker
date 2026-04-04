"""
AkShare stock data fetching service for StockTracker.

Supports both China A-share and US equity markets using **per-symbol**
queries to avoid downloading the entire market each refresh:
  - CN: EastMoney push API (realtime per-symbol) / stock_zh_a_hist (fallback)
  - US: stock_us_hist      (per-symbol daily K-line)
"""

import logging
from typing import Any

import akshare as ak
import pandas as pd

from backend.app.services.eastmoney_api import fetch_stock_quote

logger = logging.getLogger(__name__)

# Cache: pure ticker → exchange-prefixed code (e.g. "AAPL" → "105.AAPL")
_us_symbol_prefix_cache: dict[str, str] = {}


def _safe_float(value: Any) -> float | None:
    """Convert a value to float, returning None for invalid/missing data."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    """Convert a value to int, returning None for invalid/missing data."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════════════
# CN Stock Fetchers — per-symbol strategy
# ═══════════════════════════════════════════════════════════════════════

# Mapping from EastMoney push API Chinese item names → our DB field names.
_BID_ASK_ITEM_MAP: dict[str, str] = {
    "最新": "current_price",
    "今开": "open_price",
    "最高": "high_price",
    "最低": "low_price",
    "昨收": "close_price",
    "总手": "volume",
    "金额": "turnover",
    "换手": "turnover_rate",
    "涨跌": "change_amount",
    "涨幅": "change_percent",
}


def fetch_cn_stock_realtime(symbol: str) -> dict[str, Any] | None:
    """
    Fetch realtime quote for a single A-share stock from EastMoney.

    Uses ``eastmoney_api.fetch_stock_quote`` which makes a fresh TCP
    connection per call (``Connection: close``), completely avoiding
    the stale-connection-pool ``RemoteDisconnected`` errors that occur
    with ``requests``/urllib3's default keep-alive behaviour.

    Args:
        symbol: 6-digit A-share code, e.g. "600519".

    Returns:
        Data dict or None on failure.
    """
    lookup = fetch_stock_quote(symbol)
    if not lookup:
        return None

    data: dict[str, Any] = {"symbol": symbol, "name": lookup.get("名称")}
    for cn_key, db_field in _BID_ASK_ITEM_MAP.items():
        raw = lookup.get(cn_key)
        if db_field == "volume":
            data[db_field] = _safe_int(raw)
        else:
            data[db_field] = _safe_float(raw)

    # Fields not directly in _BID_ASK_ITEM_MAP but available from the API
    data["amplitude"] = None
    data["market_cap"] = _safe_float(lookup.get("总市值"))
    data["circulating_market_cap"] = _safe_float(lookup.get("流通市值"))
    data["pe_ratio"] = _safe_float(lookup.get("市盈率"))
    data["pb_ratio"] = _safe_float(lookup.get("市净率"))

    return data


def fetch_cn_stock_by_hist(symbol: str) -> dict[str, Any] | None:
    """
    Fallback fetcher for a single CN stock: latest daily K-line.

    Used when stock_bid_ask_em fails (e.g. outside trading hours).

    Args:
        symbol: 6-digit A-share code, e.g. "600519".

    Returns:
        Data dict or None on failure.
    """
    try:
        df: pd.DataFrame = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            adjust="qfq",
        )
    except Exception as e:
        logger.warning("stock_zh_a_hist failed for %s: %s", symbol, e)
        return None

    if df is None or df.empty:
        logger.warning("No historical data returned for CN/%s.", symbol)
        return None

    row = df.iloc[-1]
    return {
        "symbol": symbol,
        "name": None,
        "current_price": _safe_float(row.get("收盘")),
        "open_price": _safe_float(row.get("开盘")),
        "high_price": _safe_float(row.get("最高")),
        "low_price": _safe_float(row.get("最低")),
        "close_price": _safe_float(row.get("收盘")),
        "volume": _safe_int(row.get("成交量")),
        "turnover": _safe_float(row.get("成交额")),
        "change_amount": _safe_float(row.get("涨跌额")),
        "change_percent": _safe_float(row.get("涨跌幅")),
        "amplitude": _safe_float(row.get("振幅")),
        "turnover_rate": _safe_float(row.get("换手率")),
        "market_cap": None,
        "circulating_market_cap": None,
        "pe_ratio": None,
        "pb_ratio": None,
    }


# ═══════════════════════════════════════════════════════════════════════
# US Stock Fetchers — per-symbol strategy
# ═══════════════════════════════════════════════════════════════════════


def fetch_us_stock_by_hist(ticker: str) -> dict[str, Any] | None:
    """
    Fetch the latest daily K-line for a single US stock.

    stock_us_hist() requires exchange-prefixed codes like "105.AAPL".
    We first check the cache, then brute-force common prefixes
    (105 = NASDAQ, 106 = NYSE).

    Args:
        ticker: Pure ticker, e.g. "AAPL".

    Returns:
        Data dict or None on failure.
    """
    prefixed = _us_symbol_prefix_cache.get(ticker)
    candidate_prefixes = (
        [prefixed] if prefixed
        else [f"105.{ticker}", f"106.{ticker}"]
    )

    for code in candidate_prefixes:
        try:
            df: pd.DataFrame = ak.stock_us_hist(symbol=code)
            if df is None or df.empty:
                continue

            row = df.iloc[-1]
            # Remember the working prefix for next time
            _us_symbol_prefix_cache[ticker] = code
            logger.debug("Got data for US/%s via %s.", ticker, code)

            return {
                "symbol": ticker,
                "name": None,
                "current_price": _safe_float(row.get("收盘")),
                "open_price": _safe_float(row.get("开盘")),
                "high_price": _safe_float(row.get("最高")),
                "low_price": _safe_float(row.get("最低")),
                "close_price": _safe_float(row.get("收盘")),
                "volume": _safe_int(row.get("成交量")),
                "turnover": _safe_float(row.get("成交额")),
                "change_amount": _safe_float(row.get("涨跌额")),
                "change_percent": _safe_float(row.get("涨跌幅")),
                "amplitude": _safe_float(row.get("振幅")),
                "turnover_rate": _safe_float(row.get("换手率")),
                "market_cap": None,
                "circulating_market_cap": None,
                "pe_ratio": None,
                "pb_ratio": None,
            }

        except Exception as e:
            logger.debug("Prefix %s failed for %s: %s", code, ticker, e)

    logger.warning("Failed to fetch data for US/%s.", ticker)
    return None


# ═══════════════════════════════════════════════════════════════════════
# Unified dispatcher
# ═══════════════════════════════════════════════════════════════════════


def fetch_stocks_by_symbols(
    symbols: list[str],
    market: str = "CN",
) -> dict[str, dict[str, Any]]:
    """
    Fetch data for specific symbols using per-symbol APIs.

    Strategy (per market):
        CN:
            1. Try EastMoney push API per symbol (realtime, ~100 ms each).
            2. Fallback per symbol: stock_zh_a_hist (daily K-line).
        US:
            1. stock_us_hist per symbol (daily K-line with prefix probing).

    Args:
        symbols: List of stock symbols (e.g. ["600519"] or ["AAPL"]).
        market:  "CN" or "US".

    Returns:
        Dict mapping symbol -> data dict.
    """
    if not symbols:
        return {}

    if market == "US":
        return _fetch_us_symbols(symbols)

    return _fetch_cn_symbols(symbols)


def _fetch_cn_symbols(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch CN stocks one-by-one: realtime bid_ask → hist fallback.
    """
    logger.info("Fetching realtime data for %d CN symbol(s)...", len(symbols))
    result: dict[str, dict[str, Any]] = {}

    for symbol in symbols:
        data = fetch_cn_stock_realtime(symbol)
        if data is not None:
            result[symbol] = data
            continue

        # Realtime failed — fall back to daily hist
        logger.info(
            "CN realtime failed for %s, falling back to hist.", symbol
        )
        data = fetch_cn_stock_by_hist(symbol)
        if data is not None:
            result[symbol] = data

    logger.info(
        "CN fetch complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result


def _fetch_us_symbols(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fetch US stocks one-by-one via daily hist endpoint.
    """
    logger.info("Fetching data for %d US symbol(s)...", len(symbols))
    result: dict[str, dict[str, Any]] = {}

    for ticker in symbols:
        data = fetch_us_stock_by_hist(ticker)
        if data is not None:
            result[ticker] = data

    logger.info(
        "US fetch complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result
