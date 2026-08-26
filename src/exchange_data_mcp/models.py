"""Normalized market data shapes.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Ticker:
    exchange: str
    symbol: str          # canonical "BTC-USDT"
    last: Decimal
    bid: Decimal
    ask: Decimal
    high_24h: Decimal
    low_24h: Decimal
    volume_24h: Decimal  # base currency
    ts_ms: int           # event time, milliseconds since epoch


@dataclass(frozen=True)
class OrderBook:
    exchange: str
    symbol: str
    bids: tuple  # tuple[tuple[Decimal, Decimal], ...], best first
    asks: tuple
    sequence: int | None
    ts_ms: int | None


@dataclass(frozen=True)
class Trade:
    exchange: str
    symbol: str
    price: Decimal
    size: Decimal
    side: str            # "buy" or "sell", taker side
    trade_id: str
    ts_ms: int


@dataclass(frozen=True)
class Candle:
    exchange: str
    symbol: str
    open_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
