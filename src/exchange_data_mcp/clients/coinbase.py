"""Coinbase Exchange public REST.

Dialect notes:
- symbols keep the dash: BTC-USD and BTC-USDT both exist; USD books are the
  liquid ones by convention
- the ticker has no 24h high/low; those live on a separate stats call, so one
  normalized Ticker costs two requests here
- event times are ISO strings
- candle rows are [time_s, low, high, open, close, volume], NEWEST FIRST.
 That is the documented column order
- book level 2 rows carry a third column (order count) that we drop
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from ..errors import UnsupportedRequest
from ..models import Candle, OrderBook, Ticker, Trade
from ..symbols import canonical, for_exchange
from .base import ExchangeClient

_GRANULARITY = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "6h": 21600, "1d": 86400}


def _iso_to_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return int(parsed.timestamp() * 1000)


class CoinbaseClient(ExchangeClient):
    name = "coinbase"
    base_url = "https://api.exchange.coinbase.com"

    def ticker(self, symbol: str) -> Ticker:
        pair = for_exchange(self.name, symbol)
        tick = self._get(f"/products/{pair}/ticker")
        stats = self._get(f"/products/{pair}/stats")
        return Ticker(
            exchange=self.name,
            symbol=canonical(symbol),
            last=Decimal(tick["price"]),
            bid=Decimal(tick["bid"]),
            ask=Decimal(tick["ask"]),
            high_24h=Decimal(stats["high"]),
            low_24h=Decimal(stats["low"]),
            volume_24h=Decimal(stats["volume"]),
            ts_ms=_iso_to_ms(tick["time"]),
        )

    def orderbook(self, symbol: str, limit: int = 20) -> OrderBook:
        pair = for_exchange(self.name, symbol)
        data = self._get(f"/products/{pair}/book?level=2")
        return OrderBook(
            exchange=self.name,
            symbol=canonical(symbol),
            bids=tuple((Decimal(price), Decimal(size))
                       for price, size, *_ in data["bids"][:limit]),
            asks=tuple((Decimal(price), Decimal(size))
                       for price, size, *_ in data["asks"][:limit]),
            sequence=int(data["sequence"]),
            ts_ms=_iso_to_ms(data["time"]),
        )

    def trades(self, symbol: str, limit: int = 20) -> tuple:
        pair = for_exchange(self.name, symbol)
        rows = self._get(f"/products/{pair}/trades")
        return tuple(
            Trade(
                exchange=self.name,
                symbol=canonical(symbol),
                price=Decimal(row["price"]),
                size=Decimal(row["size"]),
                side=row["side"],
                trade_id=str(row["trade_id"]),
                ts_ms=_iso_to_ms(row["time"]),
            )
            for row in rows[:limit]
        )

    def candles(self, symbol: str, interval: str = "1h", limit: int = 100) -> tuple:
        if interval not in _GRANULARITY:
            raise UnsupportedRequest(f"coinbase has no interval {interval!r}")
        pair = for_exchange(self.name, symbol)
        rows = self._get(
            f"/products/{pair}/candles?granularity={_GRANULARITY[interval]}")
        out = []
        for row in rows[:limit]:
            out.append(Candle(
                exchange=self.name,
                symbol=canonical(symbol),
                open_time_ms=int(row[0]) * 1000,
                low=Decimal(str(row[1])),
                high=Decimal(str(row[2])),
                open=Decimal(str(row[3])),
                close=Decimal(str(row[4])),
                volume=Decimal(str(row[5])),
            ))
        out.reverse()  # coinbase serves candles newest first
        return tuple(out)
