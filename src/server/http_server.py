# http_server.py
"""
HTTP/SSE transport implementation for the Research Aggregation MCP Server

This module provides the HTTP/SSE transport server implementation using
the FastMCP framework.
"""

import logging

from src.arxiv.parser import ArxivXMLParser

from .shared import handle_search_trading_papers, handle_search_quant_finance_papers, handle_get_recent_papers

logger = logging.getLogger(__name__)

async def run_http(host: str = "0.0.0.0", port: int = 3001, useSSE: bool = True):
    """Run server with HTTP/SSE transport using FastMCP approach"""
    try:
        from mcp.server.fastmcp import FastMCP
        
        logger.info(f"🚀 Starting Research Aggregation MCP Server with {"SSE" if useSSE else "streamable"} transport")
        logger.info(f"🌐 Starting HTTP server on {host}:{port}")
        
        # Initialize parser for HTTP server
        parser = ArxivXMLParser()
        
        # Create FastMCP server instance
        mcp = FastMCP("research-aggregation-mcp")
        
        # Configure host and port
        mcp.settings.host = host
        mcp.settings.port = port
        
        # Register our tools with FastMCP
        @mcp.tool()
        async def search_trading_papers(start_date: str = "", end_date: str = "", max_results: int = 200) -> str:
            """Search for algorithmic trading and quantitative finance papers including high-frequency trading, market making, and trading systems"""
            return await handle_search_trading_papers({
                "start_date": start_date if start_date else None,
                "end_date": end_date if end_date else None,
                "max_results": max_results
            }, parser)
        
        @mcp.tool()
        async def search_quant_finance_papers(start_date: str = "", end_date: str = "", max_results: int = 200) -> str:
            """Search for quantitative finance papers including derivatives pricing, risk management, portfolio optimization, mathematical finance, and statistical finance"""
            return await handle_search_quant_finance_papers({
                "start_date": start_date if start_date else None,
                "end_date": end_date if end_date else None,
                "max_results": max_results
            }, parser)
        
        @mcp.tool()
        async def get_recent_papers(months_back: int, category: str = "q-fin.*", max_results: int = 200) -> str:
            """Get papers from the last X months with optional category filtering. Useful for finding recent research in specific areas"""
            return await handle_get_recent_papers({
                "months_back": months_back,
                "category": category,
                "max_results": max_results
            }, parser)
        
        # Run FastMCP with SSE transport
        if useSSE: 
            await mcp.run_sse_async()
        else:
            await mcp.run_streamable_http_async()
        
    except ImportError as e:
        logger.error(f"❌ HTTP transport dependencies not installed: {e}")
        logger.error("Please install with: poetry install")
        raise