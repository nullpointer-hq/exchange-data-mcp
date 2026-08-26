import threading
import unittest

from exchange_data_mcp.cache import TtlCache


class CacheTests(unittest.TestCase):
    def test_hit_within_ttl(self):
        now = [100.0]
        cache = TtlCache(clock=lambda: now[0])
        calls = []

        def fetch():
            calls.append(1)
            return "value"

        self.assertEqual(cache.get_or_fetch("k", 10.0, fetch), "value")
        self.assertEqual(cache.get_or_fetch("k", 10.0, fetch), "value")
        self.assertEqual(len(calls), 1)

    def test_expiry_refetches(self):
        now = [100.0]
        cache = TtlCache(clock=lambda: now[0])
        calls = []

        def fetch():
            calls.append(1)
            return len(calls)

        self.assertEqual(cache.get_or_fetch("k", 10.0, fetch), 1)
        now[0] = 111.0
        self.assertEqual(cache.get_or_fetch("k", 10.0, fetch), 2)
        self.assertEqual(len(calls), 2)

    def test_concurrent_miss_is_single_flight(self):
        cache = TtlCache()
        calls = []
        entered = threading.Event()
        release = threading.Event()
        results = []

        def fetch():
            calls.append(1)
            entered.set()
            release.wait(5)
            return "shared"

        def call():
            results.append(cache.get_or_fetch("k", 60.0, fetch))

        leader = threading.Thread(target=call)
        leader.start()
        self.assertTrue(entered.wait(2))  # the leader is inside fetch()
        follower = threading.Thread(target=call)
        follower.start()
        release.set()
        leader.join(5)
        follower.join(5)
        self.assertEqual(sorted(results), ["shared", "shared"])
        self.assertEqual(len(calls), 1)

    def test_failures_are_not_cached(self):
        cache = TtlCache()
        calls = []

        def bad():
            calls.append(1)
            raise RuntimeError("exchange on fire")

        with self.assertRaises(RuntimeError):
            cache.get_or_fetch("k", 60.0, bad)
        with self.assertRaises(RuntimeError):
            cache.get_or_fetch("k", 60.0, bad)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
