"""Compact serializers for LLM context.

An agent reading market data pays for every token. These shapes keep the
information short: short keys, exact decimal strings, no
envelope fields. The test suite measures the byte reduction against the raw
exchange payloads so that the claim is accurate.
"""
from __future__ import annotations

from decimal import Decimal

from .models import Candle, OrderBook, Ticker, Trade


def _d(value: Decimal) -> str:
    # format(..., "f") preserves trailing zeros, so 110559.96000000 stays exact
    return format(value, "f")


def slim_ticker(t: Ticker) -> dict:
    return {"x": t.exchange, "s": t.symbol, "last": _d(t.last),
            "bid": _d(t.bid), "ask": _d(t.ask), "hi": _d(t.high_24h),
            "lo": _d(t.low_24h), "vol": _d(t.volume_24h), "ts": t.ts_ms}


def slim_book(b: OrderBook, depth: int | None = None) -> dict:
    bids = b.bids[:depth] if depth else b.bids
    asks = b.asks[:depth] if depth else b.asks
    return {"x": b.exchange, "s": b.symbol,
            "bids": [[_d(p), _d(q)] for p, q in bids],
            "asks": [[_d(p), _d(q)] for p, q in asks],
            "seq": b.sequence, "ts": b.ts_ms}


def slim_trades(trades: tuple) -> list:
    return [{"p": _d(t.price), "q": _d(t.size), "side": t.side,
             "id": t.trade_id, "ts": t.ts_ms} for t in trades]


def slim_candles(candles: tuple) -> list:
    return [[c.open_time_ms, _d(c.open), _d(c.high), _d(c.low), _d(c.close),
             _d(c.volume)] for c in candles]


def slim_compare(result: dict) -> dict:
    return {
        "s": result["symbol"],
        "quotes": [slim_ticker(q) for q in result["quotes"]],
        "best_bid": _d(result["best_bid"]),
        "best_ask": _d(result["best_ask"]),
        "spread": _d(result["spread"]),
        "spread_bps": _d(result["spread_bps"]),
    }
