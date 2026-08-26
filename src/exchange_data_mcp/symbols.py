"""Canonical symbol handling.

Canonical form is BASE-QUOTE (BTC-USDT). Each exchange speaks its own dialect
(Binance concatenates, the other 2 keep the dash). Quote detection for concatenated input is limited to
known quote currencies; ambiguous input is rejected.
"""
from __future__ import annotations

from .errors import SymbolNotFound

_SEP = "-"

_DIALECTS = {
    "binance": lambda base, quote: f"{base}{quote}",
    "kucoin": lambda base, quote: f"{base}{_SEP}{quote}",
    "coinbase": lambda base, quote: f"{base}{_SEP}{quote}",
}

# longest first so USDT wins over USD on a trailing match
_KNOWN_QUOTES = ("USDT", "USDC", "USD", "BTC", "ETH", "EUR")


def split(symbol: str) -> tuple[str, str]:
    """Split a symbol into (base, quote). Accepts BTC-USDT, btc/usdt, BTCUSDT."""
    cleaned = symbol.strip().upper().replace("/", _SEP)
    base, quote = "", ""
    if _SEP in cleaned:
        base, _, quote = cleaned.partition(_SEP)
    else:
        for candidate in _KNOWN_QUOTES:
            if cleaned.endswith(candidate) and len(cleaned) > len(candidate):
                base, quote = cleaned[: -len(candidate)], candidate
                break
    if not base or not quote or not base.isalnum() or not quote.isalnum():
        raise SymbolNotFound(f"cannot parse symbol {symbol!r}; use BASE-QUOTE form")
    return base, quote


def canonical(symbol: str) -> str:
    base, quote = split(symbol)
    return f"{base}{_SEP}{quote}"


def for_exchange(exchange: str, symbol: str) -> str:
    """Render a canonical symbol in one exchange's dialect."""
    base, quote = split(symbol)
    try:
        mapper = _DIALECTS[exchange]
    except KeyError:
        raise SymbolNotFound(f"unknown exchange {exchange!r}") from None
    return mapper(base, quote)
