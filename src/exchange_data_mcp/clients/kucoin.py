"""KuCoin public REST.

Dialect notes:
- symbols keep the dash: BTC-USDT
- every payload is wrapped in {"code": "200000", "data": ...}
- trade history timestamps are NANOSECONDS and stats and books are milliseconds while
  candles are seconds. The unit changes per endpoint, so each parser converts
  in place and every model ends up in ms
- candle rows are [time_s, open, close, high, low, volume, turnover], newest
  first. Note the open/close adjacency; mapping by position
- the public book snapshot is the fixed 20-level one
"""
from __future__ import annotations

from decimal import Decimal

from ..errors import BadResponse, UnsupportedRequest
from ..models import Candle, OrderBook, Ticker, Trade
from ..symbols import canonical, for_exchange
from .base import ExchangeClient

_INTERVALS = {"1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min",
              "30m": "30min", "1h": "1hour", "2h": "2hour", "4h": "4hour",
              "6h": "6hour", "8h": "8hour", "12h": "12hour", "1d": "1day",
              "1w": "1week"}


class KucoinClient(ExchangeClient):
    name = "kucoin"
    base_url = "https://api.kucoin.com"

    def _data(self, path: str):
        payload = self._get(path)
        if not isinstance(payload, dict) or payload.get("code") != "200000":
            raise BadResponse(f"kucoin error payload for {path}: {payload!r}")
        return payload["data"]

    def ticker(self, symbol: str) -> Ticker:
        pair = for_exchange(self.name, symbol)
        data = self._data(f"/api/v1/market/stats?symbol={pair}")
        return Ticker(
            exchange=self.name,
            symbol=canonical(symbol),
            last=Decimal(data["last"]),
            bid=Decimal(data["buy"]),
            ask=Decimal(data["sell"]),
            high_24h=Decimal(data["high"]),
            low_24h=Decimal(data["low"]),
            volume_24h=Decimal(data["vol"]),
            ts_ms=int(data["time"]),
        )

    def orderbook(self, symbol: str, limit: int = 20) -> OrderBook:
        if limit != 20:
            raise UnsupportedRequest("kucoin public REST serves the fixed 20-level snapshot")
        pair = for_exchange(self.name, symbol)
        data = self._data(f"/api/v1/market/orderbook/level2_20?symbol={pair}")
        return OrderBook(
            exchange=self.name,
            symbol=canonical(symbol),
            bids=tuple((Decimal(price), Decimal(size)) for price, size, *_ in data["bids"]),
            asks=tuple((Decimal(price), Decimal(size)) for price, size, *_ in data["asks"]),
            sequence=int(data["sequence"]),
            ts_ms=int(data["time"]),
        )

    def trades(self, symbol: str, limit: int = 20) -> tuple:
        pair = for_exchange(self.name, symbol)
        rows = self._data(f"/api/v1/market/histories?symbol={pair}")
        return tuple(
            Trade(
                exchange=self.name,
                symbol=canonical(symbol),
                price=Decimal(row["price"]),
                size=Decimal(row["size"]),
                side=row["side"],
                trade_id=str(row["sequence"]),
                ts_ms=int(row["time"]) // 1_000_000,  # nanoseconds on this endpoint
            )
            for row in rows[:limit]
        )

    def candles(self, symbol: str, interval: str = "1h", limit: int = 100) -> tuple:
        if interval not in _INTERVALS:
            raise UnsupportedRequest(f"kucoin has no interval {interval!r}")
        pair = for_exchange(self.name, symbol)
        rows = self._data(
            f"/api/v1/market/candles?type={_INTERVALS[interval]}&symbol={pair}")
        out = []
        for row in rows[:limit]:
            out.append(Candle(
                exchange=self.name,
                symbol=canonical(symbol),
                open_time_ms=int(row[0]) * 1000,
                open=Decimal(row[1]),
                close=Decimal(row[2]),
                high=Decimal(row[3]),
                low=Decimal(row[4]),
                volume=Decimal(row[5]),
            ))
        out.reverse()  # kucoin serves candles newest first
        return tuple(out)
