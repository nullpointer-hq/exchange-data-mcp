"""TTL cache with a single-flight guard.

Public endpoints rate-limit by IP, and agent tools are used in bursts so same second tool calls get aggregated into one.
Concurrent misses collapse onto the leader's request.
Also, a caller whose leader raised retries immediately.
"""
from __future__ import annotations

import threading
import time


class TtlCache:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._entries: dict = {}
        self._inflight: dict = {}
        self._lock = threading.Lock()

    def get_or_fetch(self, key: str, ttl_s: float, fetch):
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and self._clock() - entry[0] < ttl_s:
                return entry[1]
            event = self._inflight.get(key)
            if event is None:
                event = threading.Event()
                self._inflight[key] = event
                leader = True
            else:
                leader = False
        if not leader:
            event.wait()
            with self._lock:
                entry = self._entries.get(key)
                if entry is not None and self._clock() - entry[0] < ttl_s:
                    return entry[1]
            # the leader raised and stored nothing; try to become the leader
            return self.get_or_fetch(key, ttl_s, fetch)
        try:
            value = fetch()
        finally:
            with self._lock:
                self._inflight.pop(key, None)
                event.set()
        with self._lock:
            self._entries[key] = (self._clock(), value)
        return value
