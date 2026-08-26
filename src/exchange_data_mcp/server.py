"""MCP server entry point.

The core library has no third-party imports; only this module does, and only
when the server is actually started. Install the extra first:

    pip install "mcp[cli]"
    python -m exchange_data_mcp.server
"""
from __future__ import annotations


def build_server(service=None):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(
            "the MCP layer needs the optional dependency: pip install \"mcp[cli]\""
        ) from exc

    from .service import MarketDataService
    from .token_slim import (slim_book, slim_candles, slim_compare,
                             slim_ticker, slim_trades)
    from .transport import urllib_fetcher

    service = service or MarketDataService(urllib_fetcher())
    mcp = FastMCP("exchange-data-mcp")

    @mcp.tool()
    def get_ticker(exchange: str, symbol: str) -> dict:
        """24h ticker for a pair on one exchange (binance, kucoin, coinbase)."""
        return slim_ticker(service.ticker(exchange, symbol))

    @mcp.tool()
    def get_orderbook(exchange: str, symbol: str, depth: int = 20) -> dict:
        """Top-of-book snapshot. depth=20 works on every supported exchange."""
        return slim_book(service.orderbook(exchange, symbol, depth))

    @mcp.tool()
    def get_recent_trades(exchange: str, symbol: str, limit: int = 20) -> list:
        """Most recent public trades, taker side normalized to buy/sell."""
        return slim_trades(service.trades(exchange, symbol, limit))

    @mcp.tool()
    def get_candles(exchange: str, symbol: str,
                    interval: str = "1h", limit: int = 100) -> list:
        """OHLC candles, oldest first, timestamps in ms."""
        return slim_candles(service.candles(exchange, symbol, interval, limit))

    @mcp.tool()
    def compare_price(symbol: str) -> dict:
        """The same pair across every supported venue, with the executable
        top-of-book spread in absolute terms and basis points."""
        return slim_compare(service.compare(symbol))

    return mcp


def main():
    build_server().run()


if __name__ == "__main__":
    main()
