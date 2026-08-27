# exchange-data-mcp

Read-only market data MCP server for crypto exchanges with public endpoints only and no API keys and no accounts. Binance, KuCoin and Coinbase normalized into one shape and serialized for LLM context.

Works as an MCP server for agent clients or as a plain Python library with zero dependencies.

## Why this exists

Agents that work with markets need order books, trades and candles, and the existing options hand the model raw exchange JSON. Raw payloads often carry additional useless stuff the model doesn't read, while this option doesn't, and on top of that it unifies info across the exchanges. This package normalizes the dialects once then serializes them more easily.

## Notable stuff about it:

* Symbol dialects. BTC-USDT on KuCoin and Coinbase, BTCUSDT on Binance, are aggregated in one canonical form (BASE-QUOTE).
* Timestamp units change per exchange and per endpoint. Binance is milliseconds, KuCoin stats and books are milliseconds, KuCoin trade history is nanoseconds, candles on KuCoin and Coinbase are seconds, Coinbase tickers are ISO strings. Every model comes out in ms since epoch.
* Coinbase candle rows are [time, low, high, open, close, volume], newest first. That is the documented column order. KuCoin candles use [time, open, close, high, low, ...] instead. Positional mapping with tests, or the parser inverts candles.
* Rate limits are per IP and agent tools wake up in bursts. The cache holds per-endpoint TTLs and collapses concurrent misses into one request (single-flight) so that five tools reading the same book in the same second cost one HTTP call. Failures aren't cached and a caller whose leader raised retries immediately after.
* Spread math runs on Decimal end to end.
* Slim serializers keep exact decimal strings under short keys. Measured on the recorded fixtures: the 24h ticker drops from 605 bytes of raw envelope to 207 bytes (34%). On the already-compact book snapshot the size is roughly neutral; the win is one schema in three exchanges.

## Usage

As a library (zero dependencies):

```python
from exchange_data_mcp import MarketDataService
from exchange_data_mcp.transport import urllib_fetcher

svc = MarketDataService(urllib_fetcher())
svc.ticker("kucoin", "BTC-USDT")
svc.compare("BTC-USDT")   # same pair on every venue, executable spread from top of book
```

As an MCP server:

```
pip install -e ".[mcp]"
python -m exchange_data_mcp.server
```

Tools exposed: get_ticker, get_orderbook, get_recent_trades, get_candles, compare_price.

Errors are profiled: retryable (RateLimited carrying retry_after, ExchangeUnavailable), fix-the-input (SymbolNotFound, UnsupportedRequest), or the-exchange-changed-something (BadResponse).

## Tests

37 tests, fully offline against recorded fixtures:

```
python3 -m unittest discover -s tests -t .
```

## Status

For portfolio purposes. REST with a TTL cache. For the live 10 ms streaming side of the same engineering, see [kucoin-fast-stream](https://github.com/nullpointer-hq/kucoin-fast-stream).
