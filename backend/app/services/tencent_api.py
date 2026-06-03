# -*- coding: utf-8 -*-
"""
Direct HTTP client for Tencent Finance's K-line / quote API.

Uses Python's stdlib ``urllib.request`` with ``Connection: close`` to
avoid the stale-connection-pool problem (same strategy as
``eastmoney_api.py``).

The primary endpoint returns both daily K-line data **and** a rich
``qt`` real-time quote array for each requested stock.

Supported markets: CN (A-share), US, HK (Hong Kong).

This module is intentionally decoupled from ``stock_fetcher.py`` so
it can be reused for future features (e.g. multi-day history charts).
"""

import json
import logging
import urllib.request
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ── Tencent Finance K-line endpoint ──────────────────────────────────
_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

# Default HTTP timeout (seconds).
_TIMEOUT = 10

# ── qt array index mapping (Tencent Finance quote array) ────────────
# Positions were reverse-engineered from live responses and
# cross-validated against EastMoney push2 data.
#
# A-share (88+ fields):
#   [1]  名称            [3]  最新价          [4]  昨收
#   [5]  今开            [6]  成交量(手)      [30] 时间戳 YYYYMMDDHHmmss
#   [31] 涨跌额          [32] 涨跌幅%         [33] 最高
#   [34] 最低            [37] 成交额(万元)     [38] 换手率%
#   [39] 市盈率(动)      [43] 振幅%           [44] 总市值(亿元)
#   [45] 流通市值(亿元)   [46] 市净率
#
# US equity (71 fields — key differences from A-share):
#   [30] 时间戳 "YYYY-MM-DD HH:MM:SS"  (not YYYYMMDDHHmmss)
#   [35] 货币 (e.g. "USD")
#   [37] 成交额(原始货币，不是万)
#   [44] 总市值(亿美元)   [45] 流通市值(亿美元)
#   [46] 公司英文名(NOT 市净率)
#   [51] 市净率
#
# HK equity (key differences from A-share):
#   [30] 时间戳 "YYYY/MM/DD HH:MM:SS"
#   [37] 成交额(港元，原始值)
#   [39] 市盈率            [43] 振幅(需手动计算)
#   [44] 总市值(亿港元)   [45] 流通市值(亿港元，often same as total)
#   [46] 公司英文名(NOT 市净率)
#   [47] 换手率%           [48] 52周最高   [49] 52周最低
#   [56] 市净率

# Timestamp formats by market.
_CN_TS_FMT = "%Y%m%d%H%M%S"
_US_TS_FMT = "%Y-%m-%d %H:%M:%S"
_HK_TS_FMT = "%Y/%m/%d %H:%M:%S"


def _do_request(url: str) -> bytes:
    """
    Send a single HTTP GET and return the raw response body.

    Raises on any network / HTTP error so callers can decide how to
    handle failures.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Connection": "close",
        },
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read()


def _safe_float(value: Any) -> float | None:
    """Convert to float; return *None* for missing / unparseable values."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    """Convert to int; return *None* for missing / unparseable values."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_qt(
    symbol: str,
    qt: list[str],
    market: str = "CN",
) -> dict[str, Any]:
    """
    Parse a Tencent ``qt`` quote array into a standardised data dict.

    The returned dict uses standardised field names that map directly
    to the ``Stock`` ORM model columns in ``database/models.py``.

    Args:
        symbol: Stock symbol (e.g. ``"600519"``, ``"AAPL"``, ``"00700"``).
        qt:     Raw qt string list from the Tencent API.
        market: ``"CN"``, ``"US"``, or ``"HK"`` — controls unit
                conversions and field-index differences.

    Unit conversions applied (CN):
    - 成交额:  万元 → 元  (× 10 000)
    - 总市值 / 流通市值:  亿元 → 元  (× 1e8)

    Unit conversions applied (US):
    - 成交额:  already in raw currency (no conversion)
    - 总市值 / 流通市值:  亿美元 → 美元  (× 1e8)

    Unit conversions applied (HK):
    - 成交额:  港元原始值 (no conversion)
    - 总市值 / 流通市值:  亿港元 → 港元  (× 1e8)
    """
    is_us = market == "US"
    is_hk = market == "HK"

    # ── Timestamp ───────────────────────────────────────────────────
    if is_us:
        ts_fmt = _US_TS_FMT
    elif is_hk:
        ts_fmt = _HK_TS_FMT
    else:
        ts_fmt = _CN_TS_FMT

    trade_time: datetime | None = None
    try:
        trade_time = datetime.strptime(qt[30], ts_fmt)
    except (ValueError, IndexError):
        pass

    # ── Turnover (成交额) ──────────────────────────────────────────
    # CN: 万元 → 元;  US/HK: already in raw currency.
    turnover_raw = _safe_float(qt[37])
    if is_us or is_hk:
        turnover = turnover_raw
    else:
        turnover = turnover_raw * 10_000 if turnover_raw is not None else None

    # ── Market cap / circ cap (亿 → 原始货币) ─────────────────────
    # qt[44] = 流通市值, qt[45] = 总市值 (单位：亿)
    circ_cap_raw = _safe_float(qt[44])
    circ_cap = circ_cap_raw * 1e8 if circ_cap_raw is not None else None

    market_cap_raw = _safe_float(qt[45])
    market_cap = market_cap_raw * 1e8 if market_cap_raw is not None else None

    # ── PB ratio — different index per market ─────────────────────
    # CN: qt[46];  US: qt[51];  HK: qt[56] (qt[46] is English name).
    if is_us:
        pb_index = 51
    elif is_hk:
        pb_index = 56
    else:
        pb_index = 46
    pb_ratio = _safe_float(qt[pb_index]) if len(qt) > pb_index else None

    # ── Turnover rate — different index for HK ────────────────────
    # CN/US: qt[38];  HK: qt[47].
    turnover_rate_index = 47 if is_hk else 38
    turnover_rate = (
        _safe_float(qt[turnover_rate_index])
        if len(qt) > turnover_rate_index
        else None
    )

    # ── 52-week high/low — HK provides them in qt[48]/qt[49] ─────
    high_52w: float | None = None
    low_52w: float | None = None
    if is_hk:
        high_52w = _safe_float(qt[48]) if len(qt) > 48 else None
        low_52w = _safe_float(qt[49]) if len(qt) > 49 else None

    result: dict[str, Any] = {
        "symbol": symbol,
        "name": qt[1] if len(qt) > 1 else None,
        "current_price": _safe_float(qt[3]),
        "open_price": _safe_float(qt[5]),
        "high_price": _safe_float(qt[33]),
        "low_price": _safe_float(qt[34]),
        "close_price": _safe_float(qt[4]),
        "volume": _safe_int(qt[6]),
        "turnover": turnover,
        "change_amount": _safe_float(qt[31]),
        "change_percent": _safe_float(qt[32]),
        "amplitude": _safe_float(qt[43]),
        "turnover_rate": turnover_rate,
        "market_cap": market_cap,
        "circulating_market_cap": circ_cap,
        "pe_ratio": _safe_float(qt[39]),
        "pb_ratio": pb_ratio,
        "last_trade_time": trade_time,
    }

    # Attach 52-week range if available (HK provides inline)
    if high_52w is not None:
        result["high_52w"] = high_52w
    if low_52w is not None:
        result["low_52w"] = low_52w

    return result


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════


def fetch_cn_stock_kline(
    symbol: str,
    count: int = 1,
) -> dict[str, Any] | None:
    """
    Fetch daily K-line + real-time quote for a single A-share stock.

    Args:
        symbol: 6-digit A-share code, e.g. ``"600519"``.
        count:  Number of most-recent K-line bars to request
                (default ``1`` — latest day only).

    Returns:
        A data dict whose keys map to ``Stock`` model columns
        (sourced from the ``qt`` quote array), or *None* on any failure.
    """
    prefix = "sh" if symbol.startswith("6") else "sz"
    tencent_symbol = f"{prefix}{symbol}"

    url = f"{_KLINE_URL}?param={tencent_symbol},day,,,{count},qfq"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent kline API failed for CN/%s: %s", symbol, exc,
        )
        return None

    # Navigate: data -> {tencent_symbol} -> qt -> {tencent_symbol}
    try:
        stock_node = data["data"][tencent_symbol]
        qt: list[str] = stock_node["qt"][tencent_symbol]
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Tencent kline response structure unexpected for CN/%s: %s",
            symbol, exc,
        )
        return None

    return _parse_qt(symbol, qt, market="CN")


def fetch_us_stock_kline(
    ticker: str,
    count: int = 1,
) -> dict[str, Any] | None:
    """
    Fetch daily K-line + real-time quote for a single US equity.

    The Tencent symbol for US stocks is ``"us"`` + uppercase ticker
    (e.g. ``"usAAPL"``).

    Args:
        ticker: US ticker symbol, e.g. ``"AAPL"``.
        count:  Number of most-recent K-line bars to request
                (default ``1`` — latest day only).

    Returns:
        A data dict whose keys map to ``Stock`` model columns
        (sourced from the ``qt`` quote array), or *None* on any failure.
    """
    tencent_symbol = f"us{ticker.upper()}"

    url = f"{_KLINE_URL}?param={tencent_symbol},day,,,{count},qfq"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent kline API failed for US/%s: %s", ticker, exc,
        )
        return None

    # Navigate: data -> {tencent_symbol} -> qt -> {tencent_symbol}
    try:
        stock_node = data["data"][tencent_symbol]
        qt: list[str] = stock_node["qt"][tencent_symbol]
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Tencent kline response structure unexpected for US/%s: %s",
            ticker, exc,
        )
        return None

    return _parse_qt(ticker, qt, market="US")


def fetch_cn_stock_weekly_kline(
    symbol: str,
    count: int = 52,
) -> list[dict[str, Any]]:
    """
    Fetch weekly K-line data (前复权) for a CN A-share stock.

    Args:
        symbol: 6-digit A-share code, e.g. ``"600519"``.
        count:  Number of most-recent weekly bars to request (default 52).

    Returns:
        A list of dicts with ``{"date": "YYYY-MM-DD", "close": float}``
        ordered from oldest to newest. Returns empty list on failure.
    """
    prefix = "sh" if symbol.startswith("6") else "sz"
    tencent_symbol = f"{prefix}{symbol}"

    url = f"{_KLINE_URL}?param={tencent_symbol},week,,,{count},qfq"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent weekly kline API failed for CN/%s: %s", symbol, exc,
        )
        return []

    try:
        stock_node = data["data"][tencent_symbol]
        # Key is 'qfqweek' for 前复权 weekly data
        kline_key = "qfqweek" if "qfqweek" in stock_node else "week"
        bars = stock_node[kline_key]
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Tencent weekly kline response structure unexpected for CN/%s: %s",
            symbol, exc,
        )
        return []

    # Each bar: [date, open, close, high, low, volume]
    result = []
    for bar in bars:
        if len(bar) < 3:
            continue
        close = _safe_float(bar[2])
        if close is not None:
            result.append({"date": bar[0], "close": close})

    return result


def fetch_hk_stock_weekly_kline(
    code: str,
    count: int = 52,
) -> list[dict[str, Any]]:
    """
    Fetch weekly K-line data (前复权) for a HK stock.

    Args:
        code:  HK stock code, e.g. ``"00700"``.
        count: Number of most-recent weekly bars to request (default 52).

    Returns:
        A list of dicts with ``{"date": "YYYY-MM-DD", "close": float}``
        ordered from oldest to newest. Returns empty list on failure.
    """
    tencent_symbol = f"hk{code}"

    url = f"{_KLINE_URL}?param={tencent_symbol},week,,,{count},qfq"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent weekly kline API failed for HK/%s: %s", code, exc,
        )
        return []

    try:
        stock_node = data["data"][tencent_symbol]
        # HK uses 'week' key (not 'qfqweek')
        kline_key = "qfqweek" if "qfqweek" in stock_node else "week"
        bars = stock_node[kline_key]
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Tencent weekly kline response structure unexpected for HK/%s: %s",
            code, exc,
        )
        return []

    # Each bar: [date, open, close, high, low, volume, ...]
    result = []
    for bar in bars:
        if len(bar) < 3:
            continue
        close = _safe_float(bar[2])
        if close is not None:
            result.append({"date": bar[0], "close": close})

    return result


def fetch_hk_stock_kline(
    code: str,
    count: int = 1,
) -> dict[str, Any] | None:
    """
    Fetch daily K-line + real-time quote for a single HK stock.

    The Tencent symbol for HK stocks is ``"hk"`` + 5-digit code
    (e.g. ``"hk00700"`` for Tencent Holdings).

    Args:
        code:  HK stock code, e.g. ``"00700"``.
        count: Number of most-recent K-line bars to request
               (default ``1`` — latest day only).

    Returns:
        A data dict whose keys map to ``Stock`` model columns
        (sourced from the ``qt`` quote array), or *None* on any failure.
    """
    tencent_symbol = f"hk{code}"

    url = f"{_KLINE_URL}?param={tencent_symbol},day,,,{count},qfq"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent kline API failed for HK/%s: %s", code, exc,
        )
        return None

    # Navigate: data -> {tencent_symbol} -> qt -> {tencent_symbol}
    try:
        stock_node = data["data"][tencent_symbol]
        qt: list[str] = stock_node["qt"][tencent_symbol]
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Tencent kline response structure unexpected for HK/%s: %s",
            code, exc,
        )
        return None

    return _parse_qt(code, qt, market="HK")
