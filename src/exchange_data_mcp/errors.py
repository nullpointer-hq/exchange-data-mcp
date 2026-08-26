"""Error taxonomy for the service layer.

Agents consume these errors, so the split is by what the caller should do:
retry, fix the input, or give up.
"""
from __future__ import annotations


class ExchangeError(Exception):
    """Base for everything the service raises."""

    retryable = False


class SymbolNotFound(ExchangeError):
    """The exchange does not list this pair, or the symbol cannot be parsed.
    Fix the input; retrying the same call is pointless."""


class UnsupportedRequest(ExchangeError):
    """The exchange's public API cannot serve this request as asked
    (for example a candle interval the endpoint does not publish)."""


class RateLimited(ExchangeError):
    """The exchange asked us to slow down. Safe to retry after retry_after."""

    retryable = True

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ExchangeUnavailable(ExchangeError):
    """Network failure or a 5xx from the exchange. Safe to retry with backoff."""

    retryable = True


class BadResponse(ExchangeError):
    """The exchange answered but the payload was not what was documented.

    Not retryable without a code change.
    """
