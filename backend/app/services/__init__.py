"""
Business logic services for StockTracker.

- stock_fetcher: Stock data retrieval (EastMoney + Tencent Finance)
- scheduler: Background refresh job management
"""

from app.services.scheduler import (  # pyright: ignore[reportImplicitRelativeImport]
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
    update_interval,
)
from app.services.stock_fetcher import (  # pyright: ignore[reportImplicitRelativeImport]
    fetch_stocks_by_symbols,
)

__all__ = [
    "fetch_stocks_by_symbols",
    "get_scheduler_status",
    "start_scheduler",
    "stop_scheduler",
    "update_interval",
]
