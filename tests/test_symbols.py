import unittest

from exchange_data_mcp.errors import SymbolNotFound
from exchange_data_mcp.symbols import canonical, for_exchange, split


class SymbolTests(unittest.TestCase):
    def test_split_dashed(self):
        self.assertEqual(split("BTC-USDT"), ("BTC", "USDT"))

    def test_split_slash_lowercase(self):
        self.assertEqual(split("btc/usdt"), ("BTC", "USDT"))

    def test_split_concatenated(self):
        self.assertEqual(split("BTCUSDT"), ("BTC", "USDT"))

    def test_usd_quote_not_confused_with_usdt(self):
        self.assertEqual(split("BTCUSD"), ("BTC", "USD"))

    def test_canonical(self):
        self.assertEqual(canonical("eth/btc"), "ETH-BTC")

    def test_dialects(self):
        self.assertEqual(for_exchange("binance", "BTC-USDT"), "BTCUSDT")
        self.assertEqual(for_exchange("kucoin", "BTC-USDT"), "BTC-USDT")
        self.assertEqual(for_exchange("coinbase", "BTC-USDT"), "BTC-USDT")

    def test_rejects_garbage(self):
        for bad in ("???", "BTC-", "-USDT", "", "BTC-USDT-X"):
            with self.assertRaises(SymbolNotFound, msg=bad):
                split(bad)

    def test_unknown_exchange(self):
        with self.assertRaises(SymbolNotFound):
            for_exchange("mtgox", "BTC-USDT")


if __name__ == "__main__":
    unittest.main()
