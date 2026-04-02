# -*- coding: utf-8 -*-
"""
Direct HTTP client for EastMoney's push API.

Uses Python's stdlib ``urllib.request`` which sends ``Connection: close``
by default, avoiding the stale-connection-pool problem that plagues
``requests``/``urllib3`` when talking to EastMoney's servers.

This module is intentionally decoupled from AkShare so that we have
full control over connection lifecycle, error handling and retries.
"""

import json
import logging
import time
import urllib.request
from typing import Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# EastMoney push2 endpoint for single-stock realtime quotes.
_PUSH2_STOCK_URL = "https://push2.eastmoney.com/api/qt/stock/get"

# Exactly the same field list used by AkShare's stock_bid_ask_em.
_FIELDS = (
    "f120,f121,f122,f174,f175,f59,f163,f43,f57,f58,f169,f170,f46,f44,f51,"
    "f168,f47,f164,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,"
    "f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,"
    "f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,"
    "f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,"
    "f268,f255,f256,f257,f258,f127,f199,f128,f198,f259,f260,f261,f171,f277,f278,"
    "f279,f288,f152,f250,f251,f252,f253,f254,f269,f270,f271,f272,f273,f274,f275,"
    "f276,f265,f266,f289,f290,f286,f285,f292,f293,f294,f295"
)

# Mapping from EastMoney JSON field codes to human-readable Chinese keys
# (same keys that AkShare's stock_bid_ask_em uses in its DataFrame).
_FIELD_MAP: dict[str, str] = {
    "f58": "名称",
    "f43": "最新",
    "f44": "最高",
    "f45": "最低",
    "f46": "今开",
    "f47": "总手",
    "f48": "金额",
    "f49": "外盘",
    "f50": "量比",
    "f51": "涨停",
    "f52": "跌停",
    "f60": "昨收",
    "f71": "均价",
    "f161": "内盘",
    "f168": "换手",
    "f169": "涨跌",
    "f170": "涨幅",
    "f116": "总市值",
    "f117": "流通市值",
    "f162": "市盈率",
    "f167": "市净率",
}

# Default timeout for HTTP requests (seconds).
_TIMEOUT = 10

# Retry configuration for transient failures (e.g. server empty replies).
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 0.5  # seconds; actual delay = base * 2^attempt


def _build_url(symbol: str) -> str:
    """
    Build the full request URL for a single A-share symbol.

    EastMoney uses market codes: 1 for Shanghai (6xxxxx), 0 for Shenzhen.
    """
    market_code = 1 if symbol.startswith("6") else 0
    params = urlencode({
        "fltt": "2",
        "invt": "2",
        "fields": _FIELDS,
        "secid": f"{market_code}.{symbol}",
    })
    return f"{_PUSH2_STOCK_URL}?{params}"


def _do_request(url: str) -> bytes:
    """
    Send a single HTTP GET request and return the raw response body.

    Raises on any network / HTTP error so callers can decide to retry.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Connection": "close",
        },
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return resp.read()


def fetch_stock_quote(symbol: str) -> dict[str, Any] | None:
    """
    Fetch a realtime quote for a single A-share stock from EastMoney.

    Makes a fresh TCP connection per call (``Connection: close``) and
    automatically retries up to ``_MAX_RETRIES`` times with exponential
    back-off on transient failures (e.g. ``RemoteDisconnected``).

    Args:
        symbol: 6-digit A-share code, e.g. ``"600519"``.

    Returns:
        A dict mapping Chinese item names (e.g. ``"最新"``, ``"今开"``)
        to their numeric values, or ``None`` on any failure.
    """
    url = _build_url(symbol)
    raw: bytes | None = None
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            raw = _do_request(url)
            break
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BACKOFF_BASE * (2 ** attempt)
                logger.info(
                    "EastMoney request for %s failed (attempt %d/%d), "
                    "retrying in %.1fs: %s",
                    symbol,
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                    exc,
                )
                time.sleep(delay)

    if raw is None:
        exc_chain = type(last_exc).__name__ if last_exc else "Unknown"
        cause = getattr(last_exc, "__cause__", None) or getattr(
            last_exc, "__context__", None,
        )
        while cause:
            exc_chain += f" -> {type(cause).__name__}"
            cause = getattr(cause, "__cause__", None) or getattr(
                cause, "__context__", None,
            )
        logger.warning(
            "EastMoney push API request failed for %s "
            "after %d attempts:\n"
            "  exception chain : %s\n"
            "  message         : %s\n"
            "  url             : %s",
            symbol,
            _MAX_RETRIES,
            exc_chain,
            last_exc,
            url,
        )
        return None

    try:
        data_json = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(
            "EastMoney push API returned invalid JSON for %s: %s",
            symbol,
            exc,
        )
        return None

    inner = data_json.get("data")
    if not inner:
        logger.warning(
            "EastMoney push API returned empty data for %s.", symbol,
        )
        return None

    result: dict[str, Any] = {}
    for field_code, cn_name in _FIELD_MAP.items():
        value = inner.get(field_code)
        if value is not None and value != "-":
            result[cn_name] = value

    return result
