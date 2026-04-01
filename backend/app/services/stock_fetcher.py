"""
AkShare stock data fetching service for StockTracker.

Supports both China A-share and US equity markets:
  - CN: stock_zh_a_spot_em (realtime) / stock_zh_a_hist (fallback)
  - US: stock_us_spot_em  (realtime) / stock_us_hist  (fallback)

Each market pair follows the same strategy — try the bulk realtime
endpoint first; if it fails, fall back to per-symbol historical data.
"""

import logging
from typing import Any

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)

# ── Column mapping: AkShare Chinese headers → our DB field names ──────
#
# AkShare stock_zh_a_spot_em() returns a DataFrame with Chinese columns:
#   序号, 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅,
#   最高, 最低, 今开, 昨收, 量比, 换手率, 市盈率-动态, 市净率,
#   总市值, 流通市值, 涨速, 5分钟涨跌, 60日涨跌幅, 年初至今涨跌幅
#
AKSHARE_COLUMN_MAP: dict[str, str] = {
    "代码": "symbol",
    "名称": "name",
    "最新价": "current_price",
    "今开": "open_price",
    "最高": "high_price",
    "最低": "low_price",
    "昨收": "close_price",
    "成交量": "volume",
    "成交额": "turnover",
    "换手率": "turnover_rate",
    "涨跌额": "change_amount",
    "涨跌幅": "change_percent",
    "振幅": "amplitude",
    "总市值": "market_cap",
    "流通市值": "circulating_market_cap",
    "市盈率-动态": "pe_ratio",
    "市净率": "pb_ratio",
}

# ── Column mapping: AkShare US stock Chinese headers → our DB fields ───
#
# AkShare stock_us_spot_em() returns similar Chinese-headed columns,
# but the symbol column contains exchange-prefixed codes like "105.AAPL".
#
AKSHARE_US_COLUMN_MAP: dict[str, str] = {
    "名称": "name",
    "最新价": "current_price",
    "开盘价": "open_price",
    "最高价": "high_price",
    "最低价": "low_price",
    "昨收价": "close_price",
    "总市值": "market_cap",
    "市盈率": "pe_ratio",
    "涨跌额": "change_amount",
    "涨跌幅": "change_percent",
}

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


def map_akshare_row_to_dict(row: pd.Series) -> dict[str, Any]:
    """
    Transform a single AkShare DataFrame row into a dict matching
    our Stock model field names, with proper type coercion.
    """
    data: dict[str, Any] = {}

    for cn_col, db_field in AKSHARE_COLUMN_MAP.items():
        raw_value = row.get(cn_col)

        if db_field == "symbol":
            data[db_field] = str(raw_value) if raw_value is not None else None
        elif db_field == "name":
            data[db_field] = str(raw_value) if raw_value is not None else None
        elif db_field == "volume":
            data[db_field] = _safe_int(raw_value)
        else:
            # All other fields are floats
            data[db_field] = _safe_float(raw_value)

    return data


def fetch_all_cn_stocks() -> dict[str, dict[str, Any]]:
    """
    Fetch real-time quote data for ALL China A-share stocks.

    Uses AkShare's stock_zh_a_spot_em() which returns a single
    DataFrame containing all ~5000 A-share tickers in one HTTP call.

    Returns:
        Dict mapping stock symbol -> dict of field values.
        Example: {"600519": {"name": "贵州茅台", "current_price": 1800.0, ...}}
    """
    logger.info("Fetching all China A-share quotes from AkShare...")

    try:
        df: pd.DataFrame = ak.stock_zh_a_spot_em()
    except Exception as e:
        logger.error("Failed to fetch data from AkShare: %s", e)
        return {}

    if df is None or df.empty:
        logger.warning("AkShare returned empty DataFrame.")
        return {}

    logger.info("Received %d rows from AkShare.", len(df))

    result: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        mapped = map_akshare_row_to_dict(row)
        symbol = mapped.get("symbol")
        if symbol:
            result[symbol] = mapped

    logger.info("Mapped %d stocks successfully.", len(result))
    return result


def fetch_stocks_by_hist(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fallback fetcher: retrieve the latest daily K-line data per symbol
    via AkShare's stock_zh_a_hist() endpoint.

    Used when stock_zh_a_spot_em() is unavailable (e.g. outside trading
    hours or during server maintenance). Each symbol requires a separate
    HTTP request, so this is slower than the bulk realtime API.

    Args:
        symbols: List of stock symbols to fetch.

    Returns:
        Dict mapping symbol -> data dict with the most recent trading
        day's closing data.
    """
    logger.info(
        "Fetching historical daily data for %d CN symbol(s) as fallback...",
        len(symbols),
    )

    result: dict[str, dict[str, Any]] = {}

    for symbol in symbols:
        try:
            df: pd.DataFrame = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                adjust="qfq",
            )

            if df is None or df.empty:
                logger.warning("No historical data returned for %s.", symbol)
                continue

            # Take the last row — most recent trading day
            row = df.iloc[-1]

            result[symbol] = {
                "symbol": symbol,
                "name": None,  # stock_zh_a_hist does not include name
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
            logger.debug("Got historical data for CN/%s.", symbol)

        except Exception as e:
            logger.warning("Failed to fetch hist data for %s: %s", symbol, e)

    logger.info(
        "CN historical fallback complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# US Stock Fetchers
# ═══════════════════════════════════════════════════════════════════════


def _strip_us_prefix(code: str) -> str:
    """
    Strip exchange prefix from US stock code.

    AkShare returns codes like "105.AAPL" (NASDAQ) or "106.BAC" (NYSE).
    We store the pure ticker only.
    """
    if "." in code:
        return code.split(".", maxsplit=1)[1]
    return code


def fetch_all_us_stocks() -> dict[str, dict[str, Any]]:
    """
    Fetch realtime quote data for US stocks via AkShare stock_us_spot_em().

    Returns:
        Dict mapping pure ticker (e.g. "AAPL") -> dict of field values.
    """
    logger.info("Fetching US stock quotes from AkShare (stock_us_spot_em)...")

    try:
        df: pd.DataFrame = ak.stock_us_spot_em()
    except Exception as e:
        logger.error("Failed to fetch US stock data from AkShare: %s", e)
        return {}

    if df is None or df.empty:
        logger.warning("AkShare returned empty DataFrame for US stocks.")
        return {}

    logger.info("Received %d US stock rows from AkShare.", len(df))

    result: dict[str, dict[str, Any]] = {}

    for __, row in df.iterrows():
        raw_code = str(row.get("代码", ""))
        ticker = _strip_us_prefix(raw_code)
        if not ticker:
            continue

        # Cache the prefix mapping for hist fallback
        _us_symbol_prefix_cache[ticker] = raw_code

        data: dict[str, Any] = {"symbol": ticker}
        for cn_col, db_field in AKSHARE_US_COLUMN_MAP.items():
            raw_value = row.get(cn_col)
            if db_field == "name":
                data[db_field] = str(raw_value) if raw_value is not None else None
            else:
                data[db_field] = _safe_float(raw_value)

        result[ticker] = data

    logger.info("Mapped %d US stocks successfully.", len(result))
    return result


def fetch_us_stocks_by_hist(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Fallback fetcher for US stocks: use stock_us_hist() per symbol.

    stock_us_hist() requires the exchange-prefixed code (e.g. "105.AAPL").
    We first try the cache populated by a prior spot_em call, then
    brute-force common prefixes (105=NASDAQ, 106=NYSE).

    Args:
        symbols: List of pure tickers (e.g. ["AAPL", "MSFT"]).

    Returns:
        Dict mapping ticker -> data dict.
    """
    logger.info(
        "Fetching historical daily data for %d US symbol(s) as fallback...",
        len(symbols),
    )

    # If the prefix cache is empty, try to populate it from spot_em first
    if not _us_symbol_prefix_cache:
        fetch_all_us_stocks()  # side-effect: fills the cache

    result: dict[str, dict[str, Any]] = {}

    for ticker in symbols:
        prefixed = _us_symbol_prefix_cache.get(ticker)

        # If not in cache, try common exchange prefixes
        candidate_prefixes = (
            [prefixed] if prefixed
            else [f"105.{ticker}", f"106.{ticker}"]
        )

        fetched = False
        for code in candidate_prefixes:
            try:
                df: pd.DataFrame = ak.stock_us_hist(symbol=code)
                if df is None or df.empty:
                    continue

                row = df.iloc[-1]
                result[ticker] = {
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
                # Remember the working prefix
                _us_symbol_prefix_cache[ticker] = code
                fetched = True
                logger.debug("Got historical data for US/%s via %s.", ticker, code)
                break

            except Exception as e:
                logger.debug(
                    "Prefix %s failed for %s: %s", code, ticker, e
                )

        if not fetched:
            logger.warning("Failed to fetch hist data for US/%s.", ticker)

    logger.info(
        "US historical fallback complete: got data for %d/%d symbol(s).",
        len(result),
        len(symbols),
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# Unified dispatcher
# ═══════════════════════════════════════════════════════════════════════


def fetch_stocks_by_symbols(
    symbols: list[str],
    market: str = "CN",
) -> dict[str, dict[str, Any]]:
    """
    Fetch data for specific symbols with automatic fallback.

    Strategy (per market):
        CN:
            1. Try stock_zh_a_spot_em (bulk, ~5 000 A-share tickers).
            2. Fallback: stock_zh_a_hist (per-symbol daily K-line).
        US:
            1. Try stock_us_spot_em (bulk US equities).
            2. Fallback: stock_us_hist (per-symbol daily K-line).

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
    """Internal: CN market fetch with realtime → hist fallback."""
    all_data = fetch_all_cn_stocks()

    if all_data:
        symbol_set = set(symbols)
        filtered = {s: d for s, d in all_data.items() if s in symbol_set}

        missing = symbol_set - set(filtered.keys())
        if missing:
            logger.warning(
                "CN: could not find data for %d symbol(s): %s",
                len(missing),
                ", ".join(sorted(missing)),
            )
        return filtered

    logger.info("CN realtime API unavailable, falling back to historical data.")
    return fetch_stocks_by_hist(symbols)


def _fetch_us_symbols(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """Internal: US market fetch with realtime → hist fallback."""
    all_data = fetch_all_us_stocks()

    if all_data:
        symbol_set = set(symbols)
        filtered = {s: d for s, d in all_data.items() if s in symbol_set}

        missing = symbol_set - set(filtered.keys())
        if missing:
            logger.warning(
                "US: could not find data for %d symbol(s): %s",
                len(missing),
                ", ".join(sorted(missing)),
            )
        return filtered

    logger.info("US realtime API unavailable, falling back to historical data.")
    return fetch_us_stocks_by_hist(symbols)
