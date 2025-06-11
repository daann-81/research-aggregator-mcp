# http_server.py
"""
HTTP/SSE transport implementation for the Research Aggregation MCP Server

This module provides the HTTP/SSE transport server implementation using
the FastMCP framework.
"""

import logging
from .shared import handle_search_trading_papers, handle_search_quant_finance_papers, handle_get_recent_papers
from src.arxiv.parser import ArxivXMLParser

# Rich logging
from rich.logging import RichHandler

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
    handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=True)]
)

async def run_http(host: str = "0.0.0.0", port: int = 3001):
    """Run server with HTTP/SSE transport using FastMCP approach"""
    try:
        from mcp.server.fastmcp import FastMCP
        
        logger.info(f"🚀 Starting Research Aggregation MCP Server with sse transport")
        logger.info(f"🌐 Starting HTTP server on {host}:{port}")
        
        # Initialize parser for HTTP server
        parser = ArxivXMLParser()
        
        # Create FastMCP server instance
        fastmcp = FastMCP("research-aggregation-mcp")
        
        # Configure host and port
        fastmcp.settings.host = host
        fastmcp.settings.port = port
        
        # Register our tools with FastMCP
        @fastmcp.tool()
        async def search_trading_papers(start_date: str = "", end_date: str = "", max_results: int = 200) -> str:
            """Search for algorithmic trading and quantitative finance papers including high-frequency trading, market making, and trading systems"""
            return await handle_search_trading_papers({
                "start_date": start_date if start_date else None,
                "end_date": end_date if end_date else None,
                "max_results": max_results
            }, parser)
        
        @fastmcp.tool()
        async def search_quant_finance_papers(start_date: str = "", end_date: str = "", max_results: int = 200) -> str:
            """Search for quantitative finance papers including derivatives pricing, risk management, portfolio optimization, mathematical finance, and statistical finance"""
            return await handle_search_quant_finance_papers({
                "start_date": start_date if start_date else None,
                "end_date": end_date if end_date else None,
                "max_results": max_results
            }, parser)
        
        @fastmcp.tool()
        async def get_recent_papers(months_back: int, category: str = "q-fin.*", max_results: int = 200) -> str:
            """Get papers from the last X months with optional category filtering. Useful for finding recent research in specific areas"""
            return await handle_get_recent_papers({
                "months_back": months_back,
                "category": category,
                "max_results": max_results
            }, parser)
        
        # Run FastMCP with SSE transport
        await fastmcp.run_sse_async()
        
    except ImportError as e:
        logger.error(f"❌ HTTP transport dependencies not installed: {e}")
        logger.error("Please install with: poetry install")
        raise