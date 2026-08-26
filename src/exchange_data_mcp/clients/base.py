"""Client plumbing shared by every exchange."""
from __future__ import annotations

from ..transport import Fetcher, fetch_json


class ExchangeClient:
    name = "base"
    base_url = ""

    def __init__(self, fetcher: Fetcher):
        self._fetcher = fetcher

    def _get(self, path: str):
        return fetch_json(self._fetcher, f"{self.base_url}{path}")
