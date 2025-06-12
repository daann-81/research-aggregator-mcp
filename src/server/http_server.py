# http_server.py
"""
HTTP/SSE transport implementation for the Research Aggregation MCP Server

This module provides the HTTP/SSE transport server implementation using
the FastMCP framework.
"""

import logging

from .shared import handle_search_papers, handle_get_all_recent_papers

logger = logging.getLogger(__name__)

async def run_http(host: str = "0.0.0.0", port: int = 3001, useSSE: bool = True):
    """Run server with HTTP/SSE transport using FastMCP approach"""
    try:
        from mcp.server.fastmcp import FastMCP
        
        logger.info(f"🚀 Starting Research Aggregation MCP Server with {"SSE" if useSSE else "streamable"} transport")
        logger.info(f"🌐 Starting HTTP server on {host}:{port}")
        
        # Create FastMCP server instance
        mcp = FastMCP("research-aggregation-mcp")
        
        # Configure host and port
        mcp.settings.host = host
        mcp.settings.port = port
        
        # Register our unified tools with FastMCP
        @mcp.tool()
        async def search_papers(query: str, source: str = "all", max_results: int = 20, timeout: float = 30.0) -> str:
            """Search for academic papers across multiple sources (arXiv, SSRN) with optional source filtering. Supports general search queries with source-specific filtering."""
            return await handle_search_papers({
                "query": query,
                "source": source,
                "max_results": max_results,
                "timeout": timeout
            })
        
        @mcp.tool()
        async def get_all_recent_papers(months_back: int, source: str = "all", max_results: int = 50) -> str:
            """Get recent papers from multiple sources (arXiv, SSRN) without category filtering. Returns papers from ALL academic categories, not just finance."""
            return await handle_get_all_recent_papers({
                "months_back": months_back,
                "source": source,
                "max_results": max_results
            })
        
        # Run FastMCP with SSE transport
        if useSSE: 
            await mcp.run_sse_async()
        else:
            await mcp.run_streamable_http_async()
        
    except ImportError as e:
        logger.error(f"❌ HTTP transport dependencies not installed: {e}")
        logger.error("Please install with: poetry install")
        raise