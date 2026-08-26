"""HTTP transport.

A Fetcher is any callable taking a URL and returning (status, headers, body).
The default implementation is stdlib urllib, which means that the core library has zero
third-party dependencies. Tests inject fixture fetchers so that the MCP layer never
touches a socket directly.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

from .errors import BadResponse, ExchangeUnavailable, RateLimited

Fetcher = Callable[[str], "tuple[int, dict, bytes]"]


def urllib_fetcher(timeout_s: float = 10.0) -> Fetcher:
    """Build the default fetcher. One concern: return the response, map the
    transport failures, never parse."""

    def fetch(url: str) -> tuple[int, dict, bytes]:
        request = urllib.request.Request(url, headers={"User-Agent": "exchange-data-mcp"})
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers or {}), exc.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ExchangeUnavailable(f"transport failure for {url}: {exc}") from exc

    return fetch


def fetch_json(fetch: Fetcher, url: str):
    """Fetch and decode JSON, mapping HTTP failures onto the error taxonomy."""
    status, headers, body = fetch(url)
    if status == 429:
        retry_after = None
        for key, value in headers.items():
            if key.lower() == "retry-after":
                retry_after = float(value)
        raise RateLimited(f"rate limited fetching {url}", retry_after=retry_after)
    if status >= 500:
        raise ExchangeUnavailable(f"{status} from {url}")
    if status >= 400:
        raise BadResponse(f"{status} from {url}: {body[:200]!r}")
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise BadResponse(f"non-JSON body from {url}: {exc}") from exc
