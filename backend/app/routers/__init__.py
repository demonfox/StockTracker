"""
API routers for StockTracker.

All route modules are registered here and imported by main.py.
"""

from app.routers.stocks import router as stocks_router

__all__ = [
    "stocks_router",
]
