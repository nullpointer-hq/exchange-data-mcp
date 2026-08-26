import unittest
from decimal import Decimal

from exchange_data_mcp.clients import BinanceClient, CoinbaseClient, KucoinClient
from exchange_data_mcp.errors import BadResponse, UnsupportedRequest

from ._fixtures import BTC_FIXTURES, fixture_fetcher


def make_client(cls):
    return cls(fixture_fetcher(BTC_FIXTURES))


class BinanceClientTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client(BinanceClient)

    def test_ticker(self):
        ticker = self.client.ticker("BTC-USDT")
        self.assertEqual(ticker.exchange, "binance")
        self.assertEqual(ticker.symbol, "BTC-USDT")
        self.assertEqual(ticker.last, Decimal("110559.96000000"))
        self.assertEqual(ticker.bid, Decimal("110559.95000000"))
        self.assertEqual(ticker.volume_24h, Decimal("8421.55210000"))
        self.assertEqual(ticker.ts_ms, 1766620799999)

    def test_orderbook(self):
        book = self.client.orderbook("BTC-USDT")
        self.assertEqual(book.bids[0], (Decimal("110559.95"), Decimal("0.51")))
        self.assertEqual(book.sequence, 74105025832)
        self.assertIsNone(book.ts_ms)  # binance depth carries no event time

    def test_trades_side_flip(self):
        trades = self.client.trades("BTC-USDT")
        # isBuyerMaker=true means the taker sold
        self.assertEqual(trades[0].side, "sell")
        self.assertEqual(trades[1].side, "buy")
        self.assertEqual(trades[0].ts_ms, 1766620799900)

    def test_candles(self):
        candles = self.client.candles("BTC-USDT", "1h")
        self.assertEqual(candles[0].open_time_ms, 1766534400000)
        self.assertEqual(candles[0].close, Decimal("111900.00000000"))

    def test_bad_interval(self):
        with self.assertRaises(UnsupportedRequest):
            self.client.candles("BTC-USDT", "7h")


class KucoinClientTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client(KucoinClient)

    def test_ticker(self):
        ticker = self.client.ticker("BTC-USDT")
        self.assertEqual(ticker.last, Decimal("110560"))
        self.assertEqual(ticker.bid, Decimal("110558.1"))
        self.assertEqual(ticker.ts_ms, 1766620799900)

    def test_orderbook(self):
        book = self.client.orderbook("BTC-USDT")
        self.assertEqual(book.sequence, 1842394021)
        self.assertEqual(book.ts_ms, 1766620799950)
        self.assertEqual(book.asks[0], (Decimal("110560.4"), Decimal("0.23")))

    def test_trades_nanoseconds_become_ms(self):
        trades = self.client.trades("BTC-USDT")
        self.assertEqual(trades[0].ts_ms, 1766620799900)
        self.assertEqual(trades[0].side, "buy")
        self.assertEqual(trades[0].trade_id, "1842394055")

    def test_candles_reversed_and_position_mapped(self):
        # fixture is newest-first, as kucoin serves it; output must be ascending
        candles = self.client.candles("BTC-USDT", "1h")
        self.assertEqual([c.open_time_ms for c in candles],
                         [1766534400000, 1766538000000])
        first = candles[0]
        self.assertEqual((first.open, first.close, first.high, first.low),
                         (Decimal("111746.2"), Decimal("111900"),
                          Decimal("112300"), Decimal("111100")))

    def test_fixed_book_depth(self):
        with self.assertRaises(UnsupportedRequest):
            self.client.orderbook("BTC-USDT", 50)

    def test_error_payload_raises_bad_response(self):
        client = KucoinClient(lambda url: (200, {}, b'{"code":"700100","msg":"no data"}'))
        with self.assertRaises(BadResponse):
            client.ticker("BTC-USDT")


class CoinbaseClientTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client(CoinbaseClient)

    def test_ticker_merges_stats_and_parses_iso_time(self):
        ticker = self.client.ticker("BTC-USDT")
        self.assertEqual(ticker.last, Decimal("110561.00"))
        self.assertEqual(ticker.high_24h, Decimal("112400"))
        self.assertEqual(ticker.ts_ms, 1766624399900)

    def test_orderbook_drops_order_count_column(self):
        book = self.client.orderbook("BTC-USDT", 2)
        self.assertEqual(book.bids[0], (Decimal("110560.90"), Decimal("0.51")))
        self.assertEqual(book.sequence, 8821002345)
        self.assertEqual(book.ts_ms, 1766624399950)

    def test_trades(self):
        trades = self.client.trades("BTC-USDT")
        self.assertEqual(trades[0].side, "buy")
        self.assertEqual(trades[1].ts_ms, 1766624399800)

    def test_candles_column_order_and_reversal(self):
        # coinbase rows are [time, low, high, open, close, volume], newest first
        candles = self.client.candles("BTC-USDT", "1h")
        self.assertEqual([c.open_time_ms for c in candles],
                         [1766534400000, 1766620800000])
        newest = candles[-1]
        self.assertEqual((newest.low, newest.high, newest.open, newest.close),
                         (Decimal("109900"), Decimal("112400"),
                          Decimal("111750"), Decimal("110561")))


if __name__ == "__main__":
    unittest.main()
