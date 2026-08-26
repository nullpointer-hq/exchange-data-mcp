import unittest
from decimal import Decimal

from exchange_data_mcp import MarketDataService
from exchange_data_mcp.errors import SymbolNotFound

from ._fixtures import BTC_FIXTURES, fixture_fetcher


class CountingFetcher:
    """Fixture fetcher that counts request so that cache behavior is observable."""

    def __init__(self):
        self._fetch = fixture_fetcher(BTC_FIXTURES)
        self.count = 0

    def __call__(self, url):
        self.count += 1
        return self._fetch(url)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = CountingFetcher()
        self.service = MarketDataService(self.fetcher)

    def test_normalizes_exchange_and_symbol_case(self):
        ticker = self.service.ticker("Binance", "btc/usdt")
        self.assertEqual(ticker.symbol, "BTC-USDT")
        self.assertEqual(ticker.exchange, "binance")

    def test_repeat_reads_hit_the_cache(self):
        self.service.ticker("binance", "BTC-USDT")
        self.service.ticker("binance", "BTC-USDT")
        self.assertEqual(self.fetcher.count, 1)

    def test_compare_builds_executable_spread(self):
        result = self.service.compare("BTC-USDT")
        self.assertEqual(len(result["quotes"]), 3)
        self.assertEqual(result["best_bid"], Decimal("110560.90"))  # coinbase
        self.assertEqual(result["best_ask"], Decimal("110559.96"))  # binance
        self.assertEqual(result["spread"], Decimal("0.94"))
        expected_bps = Decimal("0.94") / Decimal("110559.96") * Decimal(10_000)
        self.assertEqual(result["spread_bps"], expected_bps)

    def test_unknown_exchange(self):
        with self.assertRaises(SymbolNotFound):
            self.service.ticker("mtgox", "BTC-USDT")


if __name__ == "__main__":
    unittest.main()
