"""Binance public REST.

Dialect notes:
- symbols are concatenated: BTC-USDT becomes BTCUSDT
- timestamps are milliseconds everywhere on these endpoints
- the depth endpoint returns no event timestamp; the caller stamps if needed
- isBuyerMaker means the taker sold so that the normalized side flips it
"""
from __future__ import annotations

from decimal import Decimal

from ..errors import UnsupportedRequest
from ..models import Candle, OrderBook, Ticker, Trade
from ..symbols import canonical, for_exchange
from .base import ExchangeClient

_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h",
              "12h", "1d", "1w"}


class BinanceClient(ExchangeClient):
    name = "binance"
    base_url = "https://api.binance.com"

    def ticker(self, symbol: str) -> Ticker:
        pair = for_exchange(self.name, symbol)
        data = self._get(f"/api/v3/ticker/24hr?symbol={pair}")
        return Ticker(
            exchange=self.name,
            symbol=canonical(symbol),
            last=Decimal(data["lastPrice"]),
            bid=Decimal(data["bidPrice"]),
            ask=Decimal(data["askPrice"]),
            high_24h=Decimal(data["highPrice"]),
            low_24h=Decimal(data["lowPrice"]),
            volume_24h=Decimal(data["volume"]),
            ts_ms=int(data["closeTime"]),
        )

    def orderbook(self, symbol: str, limit: int = 20) -> OrderBook:
        pair = for_exchange(self.name, symbol)
        data = self._get(f"/api/v3/depth?symbol={pair}&limit={limit}")
        return OrderBook(
            exchange=self.name,
            symbol=canonical(symbol),
            bids=tuple((Decimal(price), Decimal(qty)) for price, qty, *_ in data["bids"]),
            asks=tuple((Decimal(price), Decimal(qty)) for price, qty, *_ in data["asks"]),
            sequence=int(data["lastUpdateId"]),
            ts_ms=None,
        )

    def trades(self, symbol: str, limit: int = 20) -> tuple:
        pair = for_exchange(self.name, symbol)
        rows = self._get(f"/api/v3/trades?symbol={pair}&limit={limit}")
        return tuple(
            Trade(
                exchange=self.name,
                symbol=canonical(symbol),
                price=Decimal(row["price"]),
                size=Decimal(row["qty"]),
                side="sell" if row["isBuyerMaker"] else "buy",
                trade_id=str(row["id"]),
                ts_ms=int(row["time"]),
            )
            for row in rows
        )

    def candles(self, symbol: str, interval: str = "1h", limit: int = 100) -> tuple:
        if interval not in _INTERVALS:
            raise UnsupportedRequest(f"binance has no interval {interval!r}")
        pair = for_exchange(self.name, symbol)
        rows = self._get(f"/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}")
        return tuple(
            Candle(
                exchange=self.name,
                symbol=canonical(symbol),
                open_time_ms=int(row[0]),
                open=Decimal(row[1]),
                high=Decimal(row[2]),
                low=Decimal(row[3]),
                close=Decimal(row[4]),
                volume=Decimal(row[5]),
            )
            for row in rows
        )
