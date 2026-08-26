"""Fixture plumbing. The tests run fully offline because the fetcher maps URL substrings
to recorded payloads in the same (status, headers, body) shape
transport returns."""
import json
import os

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

BTC_FIXTURES = {
    "api.binance.com/api/v3/ticker/24hr": "binance_ticker.json",
    "api.binance.com/api/v3/depth": "binance_depth.json",
    "api.binance.com/api/v3/trades": "binance_trades.json",
    "api.binance.com/api/v3/klines": "binance_klines.json",
    "api.kucoin.com/api/v1/market/stats": "kucoin_stats.json",
    "api.kucoin.com/api/v1/market/orderbook/level2_20": "kucoin_level2.json",
    "api.kucoin.com/api/v1/market/histories": "kucoin_histories.json",
    "api.kucoin.com/api/v1/market/candles": "kucoin_candles.json",
    "api.exchange.coinbase.com/products/BTC-USDT/ticker": "coinbase_ticker.json",
    "api.exchange.coinbase.com/products/BTC-USDT/stats": "coinbase_stats.json",
    "api.exchange.coinbase.com/products/BTC-USDT/book": "coinbase_book.json",
    "api.exchange.coinbase.com/products/BTC-USDT/trades": "coinbase_trades.json",
    "api.exchange.coinbase.com/products/BTC-USDT/candles": "coinbase_candles.json",
}


def read_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURE_DIR, name), "rb") as handle:
        return handle.read()


def fixture_fetcher(mapping):
    """Build a Fetcher from {url substring: fixture filename}."""

    def fetch(url: str):
        for needle, fixture in mapping.items():
            if needle in url:
                return 200, {}, read_fixture(fixture)
        raise AssertionError(f"no fixture registered for {url}")

    return fetch


def fixture_json(name: str):
    return json.loads(read_fixture(name))
