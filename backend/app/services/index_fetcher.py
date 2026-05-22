# -*- coding: utf-8 -*-
"""
Market index data fetcher for StockTracker.

Fetches real-time quotes for major market indices across three markets
(CN, HK, US) using the Tencent Finance K-line API.

Also provides intraday minute-level price data (for CN & HK markets)
via the Tencent ``minute/query`` endpoint.

The indices are not persisted to the database — they are fetched live
on each API request.
"""

import json
import logging
from typing import Any

from app.services.tencent_api import _do_request, _safe_float

logger = logging.getLogger(__name__)

# ── Tencent Finance endpoints ────────────────────────────────────────
_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
_MINUTE_URL = "https://web.ifzq.gtimg.cn/appstock/app/minute/query"

# ── Index definitions ────────────────────────────────────────────────
# Each tuple: (tencent_symbol, display_name, market)

INDEX_DEFINITIONS: list[tuple[str, str, str]] = [
    # China A-share
    ("sh000001", "上证指数", "CN"),
    ("sz399001", "深证成指", "CN"),
    ("sz399006", "创业板指", "CN"),
    # Hong Kong
    ("hkHSI", "恒生指数", "HK"),
    ("hkHSTECH", "恒生科技", "HK"),
    ("hkHSCEI", "国企指数", "HK"),
    # US
    ("usDJI", "道琼斯", "US"),
    ("usIXIC", "纳斯达克", "US"),
    ("usINX", "标普500", "US"),
]


def _fetch_single_index(tencent_symbol: str) -> dict[str, Any] | None:
    """
    Fetch real-time quote for a single index from Tencent Finance.

    Returns a dict with keys: current_price, change_amount, change_percent,
    or None on failure.
    """
    url = f"{_KLINE_URL}?param={tencent_symbol},day,,,1,qfq"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent API failed for index %s: %s", tencent_symbol, exc,
        )
        return None

    try:
        stock_node = data["data"][tencent_symbol]
        qt: list[str] = stock_node["qt"][tencent_symbol]
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Unexpected response structure for index %s: %s",
            tencent_symbol, exc,
        )
        return None

    return {
        "current_price": _safe_float(qt[3]),
        "change_amount": _safe_float(qt[31]),
        "change_percent": _safe_float(qt[32]),
    }


def fetch_all_indices() -> dict[str, list[dict[str, Any]]]:
    """
    Fetch real-time quotes for all configured market indices.

    Returns:
        Dict with keys ``"cn"``, ``"hk"``, ``"us"``, each mapping to
        a list of index quote dicts.
    """
    result: dict[str, list[dict[str, Any]]] = {
        "cn": [],
        "hk": [],
        "us": [],
    }

    for tencent_symbol, display_name, market in INDEX_DEFINITIONS:
        quote_data = _fetch_single_index(tencent_symbol)

        entry: dict[str, Any] = {
            "symbol": tencent_symbol,
            "name": display_name,
            "market": market,
            "current_price": None,
            "change_amount": None,
            "change_percent": None,
        }

        if quote_data is not None:
            entry.update(quote_data)

        result[market.lower()].append(entry)

    logger.info("Fetched %d market indices.", len(INDEX_DEFINITIONS))
    return result


# ═══════════════════════════════════════════════════════════════════════
# Intraday Minute Data (CN & HK only)
# ═══════════════════════════════════════════════════════════════════════


def _fetch_single_index_minute(tencent_symbol: str) -> dict[str, Any] | None:
    """
    Fetch intraday minute-level price data for a single index.

    Uses the Tencent ``minute/query`` endpoint which returns the full
    trading day's per-minute data for the current (or last) trading day.

    Data format per point: ``"HHMM price volume turnover"``

    Returns:
        A dict with keys ``date``, ``prev_close``, ``points``
        (list of ``{time, price}`` dicts), or None on failure.
    """
    url = f"{_MINUTE_URL}?code={tencent_symbol}"

    try:
        raw = _do_request(url)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning(
            "Tencent minute API failed for %s: %s", tencent_symbol, exc,
        )
        return None

    try:
        inner = data["data"][tencent_symbol]
        minute_data = inner["data"]
        raw_points = minute_data.get("data", [])
        date_str = minute_data.get("date", "")

        # Extract prev_close from qt array (index 4)
        qt = inner.get("qt", {}).get(tencent_symbol, [])
        prev_close = _safe_float(qt[4]) if len(qt) > 4 else None
    except (KeyError, TypeError, IndexError) as exc:
        logger.warning(
            "Unexpected minute response structure for %s: %s",
            tencent_symbol, exc,
        )
        return None

    # Parse each minute point: "HHMM price volume [turnover]"
    points: list[dict[str, Any]] = []
    for raw_point in raw_points:
        parts = raw_point.split()
        if len(parts) < 2:
            continue
        time_str = parts[0]
        price = _safe_float(parts[1])
        if price is not None:
            points.append({
                "time": time_str,
                "price": price,
            })

    if not points:
        return None

    return {
        "date": date_str,
        "prev_close": prev_close,
        "points": points,
    }


def fetch_indices_minute(markets: list[str] | None = None) -> dict[str, list[dict[str, Any]]]:
    """
    Fetch intraday minute data for CN and HK market indices.

    Args:
        markets: Optional list of markets to fetch (e.g. ``["CN", "HK"]``).
                 Defaults to ``["CN", "HK"]`` since US minute data is
                 not available via this endpoint.

    Returns:
        Dict keyed by lowercase market (``"cn"``, ``"hk"``), each
        containing a list of index minute data dicts.
    """
    if markets is None:
        markets = ["CN", "HK"]

    allowed_markets = {m.upper() for m in markets}

    result: dict[str, list[dict[str, Any]]] = {
        m.lower(): [] for m in allowed_markets
    }

    for tencent_symbol, display_name, market in INDEX_DEFINITIONS:
        if market not in allowed_markets:
            continue

        minute_data = _fetch_single_index_minute(tencent_symbol)

        entry: dict[str, Any] = {
            "symbol": tencent_symbol,
            "name": display_name,
            "market": market,
            "date": None,
            "prev_close": None,
            "points": [],
        }

        if minute_data is not None:
            entry["date"] = minute_data["date"]
            entry["prev_close"] = minute_data["prev_close"]
            entry["points"] = minute_data["points"]

        result[market.lower()].append(entry)

    fetched_count = sum(len(v) for v in result.values())
    logger.info("Fetched minute data for %d indices.", fetched_count)
    return result
