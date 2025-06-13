"""
HTTP/SSE transport implementation for the Research Aggregation MCP Server

This module provides the HTTP/SSE transport server implementation using
the FastMCP framework.
"""

import logging

from enum import Enum

from typing import Annotated, Literal
from pydantic import BaseModel, Field

from src.common.paper import AcademicPaper

from .shared import handle_search_papers, handle_get_all_recent_papers

logger = logging.getLogger(__name__)


class TransportType(Enum):
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE = "streamable"


async def run_mcp(
    host: str = "0.0.0.0",
    port: int = 3001,
    transport: TransportType = TransportType.SSE,
):
    """Run server with HTTP/SSE transport using FastMCP approach"""
    try:
        from mcp.server.fastmcp import FastMCP

        logger.info(
            f"🚀 Starting Research Aggregation MCP Server with {transport} transport"
        )
        logger.info(f"🌐 Starting HTTP server on {host}:{port}")

        # Create FastMCP server instance
        mcp = FastMCP("research-aggregation-mcp")

        # Configure host and port
        mcp.settings.host = host
        mcp.settings.port = port

        # Register our unified tools with FastMCP
        @mcp.tool(
            description="Search for academic papers across multiple sources (arXiv, SSRN). Supports general search queries with source-specific filtering.\n" + AcademicPaper.get_field_descriptions_as_markdown(),
        )
        async def search_papers(
            query: Annotated[str, Field(description="Search terms or keywords")],
            source: Annotated[str, Field(description="sources, can be set to arXiv or SSRN")]  = "all",
            max_results: Annotated[int , Field(description="max returned results")] = 20,
            timeout: Annotated[float, Field(description="how many seconds to wait")] = 30.0,
        ) -> str:
            return await handle_search_papers(
                {
                    "query": query,
                    "source": source,
                    "max_results": max_results,
                    "timeout": timeout,
                }
            )

        @mcp.tool(
            description="Get recent academic papers from multiple sources (arXiv, SSRN) within a specific time range. Supports filtering by source and limiting results.\n" + AcademicPaper.get_field_descriptions_as_markdown(),
        )
        async def get_all_recent_papers(
            months_back: int, 
            source: Annotated[str, Field(description="source of academic papers, can be set to arXiv or SSRN")]  = "all", 
            max_results: Annotated[int , Field(description="max returned results")] = 50
        ) -> str:
            return await handle_get_all_recent_papers(
                {
                    "months_back": months_back,
                    "source": source,
                    "max_results": max_results,
                }
            )

        # Run FastMCP with SSE transport
        if transport == TransportType.SSE:
            await mcp.run_sse_async()
        elif transport == TransportType.STREAMABLE:
            await mcp.run_streamable_http_async()
        elif transport == TransportType.STDIO:
            await mcp.run_stdio_async()
        else:
            raise ValueError(f"Unsupported transport type: {transport}")

    except ImportError as e:
        logger.error(f"❌ HTTP transport dependencies not installed: {e}")
        logger.error("Please install with: poetry install")
        raise
