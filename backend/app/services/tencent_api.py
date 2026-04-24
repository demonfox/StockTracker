# -*- coding: utf-8 -*-
"""
Direct HTTP client for Tencent Finance's K-line / quote API.

Uses Python's stdlib ``urllib.request`` with ``Connection: close`` to
avoid the stale-connection-pool problem (same strategy as
``eastmoney_api.py``).

The primary endpoint returns both daily K-line data **and** a rich
``qt`` real-time quote array (88 fields) for each requested stock.

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

# Timestamp formats by market.
_CN_TS_FMT = "%Y%m%d%H%M%S"
_US_TS_FMT = "%Y-%m-%d %H:%M:%S"


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

    The returned dict uses the same field names as
    ``stock_fetcher.fetch_cn_stock_realtime`` /
    ``stock_fetcher.fetch_us_stock_realtime`` so it can serve as a
    drop-in fallback.

    Args:
        symbol: Stock symbol (e.g. ``"600519"`` or ``"AAPL"``).
        qt:     Raw qt string list from the Tencent API.
        market: ``"CN"`` or ``"US"`` — controls unit conversions and
                field-index differences.

    Unit conversions applied (CN):
    - 成交额:  万元 → 元  (× 10 000)
    - 总市值 / 流通市值:  亿元 → 元  (× 1e8)

    Unit conversions applied (US):
    - 成交额:  already in raw currency (no conversion)
    - 总市值 / 流通市值:  亿美元 → 美元  (× 1e8)
    """
    is_us = market == "US"

    # ── Timestamp ───────────────────────────────────────────────────
    ts_fmt = _US_TS_FMT if is_us else _CN_TS_FMT
    trade_time: datetime | None = None
    try:
        trade_time = datetime.strptime(qt[30], ts_fmt)
    except (ValueError, IndexError):
        pass

    # ── Turnover (成交额) ──────────────────────────────────────────
    # CN: 万元 → 元;  US: already in raw currency.
    turnover_raw = _safe_float(qt[37])
    if is_us:
        turnover = turnover_raw
    else:
        turnover = turnover_raw * 10_000 if turnover_raw is not None else None

    # ── Market cap / circ cap (亿 → 原始货币) ─────────────────────
    market_cap_raw = _safe_float(qt[44])
    market_cap = market_cap_raw * 1e8 if market_cap_raw is not None else None

    circ_cap_raw = _safe_float(qt[45])
    circ_cap = circ_cap_raw * 1e8 if circ_cap_raw is not None else None

    # ── PB ratio — different index per market ─────────────────────
    # CN: qt[46];  US: qt[51] (qt[46] is the English company name).
    pb_index = 51 if is_us else 46
    pb_ratio = _safe_float(qt[pb_index]) if len(qt) > pb_index else None

    return {
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
        "turnover_rate": _safe_float(qt[38]),
        "market_cap": market_cap,
        "circulating_market_cap": circ_cap,
        "pe_ratio": _safe_float(qt[39]),
        "pb_ratio": pb_ratio,
        "last_trade_time": trade_time,
    }


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
        A data dict whose keys match ``fetch_cn_stock_realtime`` in
        ``stock_fetcher.py`` (sourced from the ``qt`` quote array),
        or *None* on any failure.
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
        A data dict whose keys match ``fetch_us_stock_realtime`` in
        ``stock_fetcher.py`` (sourced from the ``qt`` quote array),
        or *None* on any failure.
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
