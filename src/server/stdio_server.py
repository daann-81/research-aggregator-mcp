# stdio_server.py
"""
stdio transport implementation for the Research Aggregation MCP Server

This module provides the stdio transport server implementation using
the low-level MCP server API.
"""

import asyncio
import logging
import sys
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
from rich.logging import RichHandler

from .shared import create_mcp_server


logger = logging.getLogger(__name__)

async def run_stdio():
    """Run server with stdio transport"""
    logger.info("🚀 Starting Research Aggregation MCP Server with stdio transport")
    
    # Create the MCP server with tool handlers
    server = create_mcp_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="research-aggregation-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )