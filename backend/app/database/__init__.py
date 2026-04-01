"""
Database layer for StockTracker.

Public API:
    - Stock: ORM model
    - Base: SQLAlchemy declarative base (for table creation)
    - get_db: FastAPI dependency for async sessions
    - init_db / close_db: Application lifecycle hooks
    - CRUD functions: get_all_stocks, get_stock_by_symbol, add_stock,
      remove_stock, batch_update_stock_data, get_tracked_symbols
"""

from app.database.models import Base, Stock
from app.database.session import close_db, get_db, init_db
from app.database.crud import (
    add_stock,
    batch_update_stock_data,
    get_all_stocks,
    get_stock_by_symbol,
    get_tracked_symbols,
    remove_stock,
)

__all__ = [
    "Base",
    "Stock",
    "get_db",
    "init_db",
    "close_db",
    "add_stock",
    "batch_update_stock_data",
    "get_all_stocks",
    "get_stock_by_symbol",
    "get_tracked_symbols",
    "remove_stock",
]
