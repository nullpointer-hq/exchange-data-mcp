"""Read-only crypto market data for AI agents: normalized across exchanges,
cached against public rate limits, and serialized small for LLM context."""
from .errors import (BadResponse, ExchangeError, ExchangeUnavailable,
                     RateLimited, SymbolNotFound, UnsupportedRequest)
from .models import Candle, OrderBook, Ticker, Trade
from .service import MarketDataService

__all__ = [
    "MarketDataService",
    "Ticker",
    "OrderBook",
    "Trade",
    "Candle",
    "ExchangeError",
    "SymbolNotFound",
    "UnsupportedRequest",
    "RateLimited",
    "ExchangeUnavailable",
    "BadResponse",
]

__version__ = "0.1.0"
