"""The normalized service that agents actually call.

One instance and cache with three exchange clients sharing one fetcher. TTLs are
per endpoint type: books move fast, candles do not. Every call goes through
the cache, so repeat reads inside the TTL window cost zero HTTP requests.
"""
from __future__ import annotations

from decimal import Decimal

from .cache import TtlCache
from .clients import BinanceClient, CoinbaseClient, KucoinClient
from .errors import SymbolNotFound
from .symbols import canonical

_CLIENTS = {
    "binance": BinanceClient,
    "kucoin": KucoinClient,
    "coinbase": CoinbaseClient,
}

_TTL_S = {"ticker": 1.0, "orderbook": 1.0, "trades": 2.0, "candles": 30.0}


class MarketDataService:
    def __init__(self, fetcher):
        self._cache = TtlCache()
        self._clients = {name: cls(fetcher) for name, cls in _CLIENTS.items()}

    @property
    def exchanges(self) -> tuple:
        return tuple(self._clients)

    def _client(self, exchange: str):
        try:
            return self._clients[exchange.strip().lower()]
        except KeyError:
            raise SymbolNotFound(
                f"unknown exchange {exchange!r}; supported: {', '.join(self._clients)}"
            ) from None

    def ticker(self, exchange: str, symbol: str) -> object:
        client = self._client(exchange)
        return self._cache.get_or_fetch(
            f"ticker:{client.name}:{canonical(symbol)}",
            _TTL_S["ticker"],
            lambda: client.ticker(symbol),
        )

    def orderbook(self, exchange: str, symbol: str, depth: int = 20) -> object:
        client = self._client(exchange)
        return self._cache.get_or_fetch(
            f"orderbook:{client.name}:{canonical(symbol)}:{depth}",
            _TTL_S["orderbook"],
            lambda: client.orderbook(symbol, depth),
        )

    def trades(self, exchange: str, symbol: str, limit: int = 20) -> tuple:
        client = self._client(exchange)
        return self._cache.get_or_fetch(
            f"trades:{client.name}:{canonical(symbol)}:{limit}",
            _TTL_S["trades"],
            lambda: client.trades(symbol, limit),
        )

    def candles(self, exchange: str, symbol: str,
                interval: str = "1h", limit: int = 100) -> tuple:
        client = self._client(exchange)
        return self._cache.get_or_fetch(
            f"candles:{client.name}:{canonical(symbol)}:{interval}:{limit}",
            _TTL_S["candles"],
            lambda: client.candles(symbol, interval, limit),
        )

    def compare(self, symbol: str, exchanges=None) -> dict:
        """The same pair across venues, with the executable spread.

        The spread comes from top-of-book bid/ask:
        last-trade spreads look bigger than they are and have fooled people.
        A positive spread is what would remain after crossing both venues'
        top levels, before fees and before depth walking.
        """
        names = tuple(exchanges) if exchanges else self.exchanges
        quotes = [self.ticker(name, symbol) for name in names]
        best_bid = max(q.bid for q in quotes)
        best_ask = min(q.ask for q in quotes)
        spread = best_bid - best_ask
        return {
            "symbol": canonical(symbol),
            "quotes": quotes,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_bps": (spread / best_ask * Decimal(10_000)) if best_ask else Decimal(0),
        }
