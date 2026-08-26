import json
import unittest

from exchange_data_mcp import MarketDataService
from exchange_data_mcp.clients import BinanceClient
from exchange_data_mcp.token_slim import (slim_book, slim_candles,
                                          slim_compare, slim_ticker,
                                          slim_trades)

from ._fixtures import BTC_FIXTURES, fixture_fetcher, fixture_json


class SlimTests(unittest.TestCase):
    def setUp(self):
        self.client = BinanceClient(fixture_fetcher(BTC_FIXTURES))

    def test_ticker_shape_and_exact_decimals(self):
        slim = slim_ticker(self.client.ticker("BTC-USDT"))
        self.assertEqual(slim, {
            "x": "binance", "s": "BTC-USDT",
            "last": "110559.96000000", "bid": "110559.95000000",
            "ask": "110559.96000000", "hi": "112300.00000000",
            "lo": "109980.00000000", "vol": "8421.55210000",
            "ts": 1766620799999,
        })

    def test_slim_is_measurably_smaller_than_raw(self):
        raw = json.dumps(fixture_json("binance_ticker.json")).encode()
        slim = json.dumps(slim_ticker(self.client.ticker("BTC-USDT"))).encode()
        self.assertLess(len(slim), len(raw) // 2)

    def test_book_depth_truncation(self):
        book = self.client.orderbook("BTC-USDT")
        self.assertEqual(len(slim_book(book, depth=2)["bids"]), 2)
        self.assertEqual(slim_book(book)["bids"][0],
                         ["110559.95000000", "0.51000000"])

    def test_trades_shape(self):
        slim = slim_trades(self.client.trades("BTC-USDT"))
        self.assertEqual(slim[0]["side"], "sell")
        self.assertEqual(slim[0]["p"], "110559.96000000")

    def test_candles_shape(self):
        slim = slim_candles(self.client.candles("BTC-USDT", "1h"))
        self.assertEqual(slim[0][0], 1766534400000)
        self.assertEqual(slim[0][4], "111900.00000000")

    def test_compare_shape(self):
        service = MarketDataService(fixture_fetcher(BTC_FIXTURES))
        slim = slim_compare(service.compare("BTC-USDT"))
        self.assertEqual(slim["s"], "BTC-USDT")
        self.assertEqual(slim["spread"], "0.94000000")  # Decimal keeps operand precision
        self.assertEqual(len(slim["quotes"]), 3)


if __name__ == "__main__":
    unittest.main()
