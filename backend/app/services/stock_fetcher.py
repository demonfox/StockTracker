"""
Stock data fetching service for StockTracker.

Supports both China A-share and US equity markets using **per-symbol**
queries to avoid downloading the entire market each refresh:
  - CN: EastMoney push API (realtime) / Tencent Finance K-line (fallback)
  - US: EastMoney push API (realtime) / stock_us_hist (fallback)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import akshare as ak
import pandas as pd

from app.services.eastmoney_api import (  # pyright: ignore[reportImplicitRelativeImport]
    fetch_cn_stock_quote,
    fetch_us_stock_quote,
)
from app.services.tencent_api import (  # pyright: ignore[reportImplicitRelativeImport]
    fetch_cn_stock_kline,
)

logger = logging.getLogger(__name__)


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

    Uses ``eastmoney_api.fetch_cn_stock_quote`` which makes a fresh TCP
    connection per call (``Connection: close``), completely avoiding
    the stale-connection-pool ``RemoteDisconnected`` errors that occur
    with ``requests``/urllib3's default keep-alive behaviour.

    Args:
        symbol: 6-digit A-share code, e.g. "600519".

    Returns:
        Data dict or None on failure.
    """
    lookup = fetch_cn_stock_quote(symbol)
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

    # Last trade timestamp (f86): Unix epoch → market-local naive datetime.
    # CN stocks use CST (UTC+8). We store the naive local time because
    # SQLite drops timezone info; the frontend knows to display CN times
    # in Asia/Shanghai.
    _CST = timezone(timedelta(hours=8))
    raw_ts = lookup.get("最新成交时间")
    if raw_ts is not None:
        try:
            aware_dt = datetime.fromtimestamp(int(raw_ts), tz=_CST)
            data["last_trade_time"] = aware_dt.replace(tzinfo=None)
        except (ValueError, TypeError, OSError):
            data["last_trade_time"] = None
    else:
        data["last_trade_time"] = None

    return data


def fetch_cn_stock_by_hist(symbol: str) -> dict[str, Any] | None:
    """
    Fallback fetcher for a single CN stock via Tencent Finance K-line API.

    Used when the primary EastMoney push2 API fails (e.g. outside trading
    hours).  Delegates to :func:`tencent_api.fetch_cn_stock_kline` which
    returns a data dict whose keys match ``fetch_cn_stock_realtime``.

    Args:
        symbol: 6-digit A-share code, e.g. "600519".

    Returns:
        Data dict compatible with ``fetch_cn_stock_realtime``, or *None*
        on failure.
    """
    return fetch_cn_stock_kline(symbol)


# ═══════════════════════════════════════════════════════════════════════
# US Stock Fetchers — per-symbol strategy
# ═══════════════════════════════════════════════════════════════════════

# US Eastern Time (ET) is UTC-5 (EST) / UTC-4 (EDT).
# We use UTC-4 as a fixed offset; the frontend labels it "ET" generically.
# For exact DST-aware conversion, consider ``zoneinfo`` (Python 3.9+).
_ET = timezone(timedelta(hours=-4))


def fetch_us_stock_realtime(ticker: str) -> dict[str, Any] | None:
    """
    Fetch realtime quote for a single US stock from EastMoney push2.

    Uses ``eastmoney_api.fetch_us_stock_quote`` which probes NASDAQ /
    NYSE / AMEX exchange prefixes automatically.

    Args:
        ticker: US ticker, e.g. "AAPL".

    Returns:
        Data dict or None on failure.
    """
    lookup = fetch_us_stock_quote(ticker)
    if not lookup:
        return None

    data: dict[str, Any] = {"symbol": ticker, "name": lookup.get("名称")}
    for cn_key, db_field in _BID_ASK_ITEM_MAP.items():
        raw = lookup.get(cn_key)
        if db_field == "volume":
            data[db_field] = _safe_int(raw)
        else:
            data[db_field] = _safe_float(raw)

    data["amplitude"] = None
    data["market_cap"] = _safe_float(lookup.get("总市值"))
    data["circulating_market_cap"] = _safe_float(lookup.get("流通市值"))
    data["pe_ratio"] = _safe_float(lookup.get("市盈率"))
    data["pb_ratio"] = _safe_float(lookup.get("市净率"))

    # Last trade timestamp → naive ET datetime (see CN counterpart for rationale).
    raw_ts = lookup.get("最新成交时间")
    if raw_ts is not None:
        try:
            aware_dt = datetime.fromtimestamp(int(raw_ts), tz=_ET)
            data["last_trade_time"] = aware_dt.replace(tzinfo=None)
        except (ValueError, TypeError, OSError):
            data["last_trade_time"] = None
    else:
        data["last_trade_time"] = None

    return data


def fetch_us_stock_by_hist(ticker: str) -> dict[str, Any] | None:
    """
    Fallback fetcher for a single US stock: latest daily K-line.

    Uses AkShare's ``stock_us_hist`` which hits EastMoney's historical
    K-line endpoint.  This endpoint may be unreliable (connection
    resets), so ``fetch_us_stock_realtime`` should be preferred.

    Args:
        ticker: US ticker, e.g. "AAPL".

    Returns:
        Data dict or None on failure.
    """
    # Probe NASDAQ (105), NYSE (106), AMEX (107)
    for prefix in ("105", "106", "107"):
        code = f"{prefix}.{ticker}"
        try:
            df: pd.DataFrame = ak.stock_us_hist(symbol=code)
            if df is None or df.empty:
                continue

            row = df.iloc[-1]
            logger.debug("Got hist data for US/%s via %s.", ticker, code)

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
                "last_trade_time": None,
            }

        except Exception as e:
            logger.debug("Hist prefix %s failed for %s: %s", code, ticker, e)

    logger.warning("fetch_us_stock_by_hist failed for US/%s.", ticker)
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
            1. Try EastMoney push API per symbol (realtime).
            2. Fallback per symbol: stock_us_hist (daily K-line, may be unreliable).

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
        data = fetch_cn_stock_by_hist(symbol)
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
    Fetch US stocks one-by-one: realtime push2 → daily hist fallback.
    """
    logger.info("Fetching realtime data for %d US symbol(s)...", len(symbols))
    result: dict[str, dict[str, Any]] = {}

    for ticker in symbols:
        data = fetch_us_stock_realtime(ticker)
        if data is not None:
            result[ticker] = data
            continue

        # Realtime failed — fall back to daily hist (may also fail)
        logger.info(
            "US realtime failed for %s, falling back to hist.", ticker,
        )
        data = fetch_us_stock_by_hist(ticker)
        if data is not None:
            result[ticker] = data

    logger.info(
        "US fetch complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result
