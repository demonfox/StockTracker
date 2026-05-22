# -*- coding: utf-8 -*-
"""
Market index data fetcher for StockTracker.

Fetches real-time quotes for major market indices across three markets
(CN, HK, US) using the Tencent Finance K-line API.

The indices are not persisted to the database — they are fetched live
on each API request.
"""

import json
import logging
from typing import Any

from app.services.tencent_api import _do_request, _safe_float

logger = logging.getLogger(__name__)

# ── Tencent Finance K-line endpoint ──────────────────────────────────
_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

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
