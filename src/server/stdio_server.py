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

from typing import Any, Dict, List, Optional

from rich.logging import RichHandler

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent

from .shared import DATE_RANGE_SCHEMA, initialize_arxiv_components, handle_search_trading_papers, handle_search_quant_finance_papers, handle_get_recent_papers

logger = logging.getLogger(__name__)
def create_mcp_server() -> Server:
    """Create and configure the MCP server with tool handlers"""
    # Initialize components for the server
    arxiv_client, parser = initialize_arxiv_components()
    
    # Create MCP server instance
    server = Server("research-aggregation-mcp")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """Register available tools with the MCP server"""
        return [
            Tool(
                name="search_trading_papers",
                description="Search for algorithmic trading and quantitative finance papers including high-frequency trading, market making, and trading systems",
                inputSchema={
                    "type": "object",
                    "properties": DATE_RANGE_SCHEMA,
                    "required": []
                }
            ),
            Tool(
                name="search_quant_finance_papers",
                description="Search for quantitative finance papers including derivatives pricing, risk management, portfolio optimization, mathematical finance, and statistical finance",
                inputSchema={
                    "type": "object",
                    "properties": DATE_RANGE_SCHEMA,
                    "required": []
                }
            ),
            Tool(
                name="get_recent_papers",
                description="Get papers from the last X months with optional category filtering. Useful for finding recent research in specific areas",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "months_back": {
                            "type": "integer",
                            "description": "Number of months to look back (required)",
                            "minimum": 1,
                            "maximum": 60
                        },
                        "category": {
                            "type": "string",
                            "description": "ArXiv category (optional, defaults to all quantitative finance 'q-fin.*'). Examples: 'q-fin.TR' for trading, 'q-fin.MF' for mathematical finance",
                            "default": "q-fin.*"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of papers to return (default: 200, max: 2000)",
                            "default": 200
                        }
                    },
                    "required": ["months_back"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls from Claude"""
        try:
            logger.debug(f"🔧 [cyan]Tool called: {name}[/cyan] with arguments: {arguments}")
            
            if name == "search_trading_papers":
                result = await handle_search_trading_papers(arguments, parser)
            elif name == "search_quant_finance_papers":
                result = await handle_search_quant_finance_papers(arguments, parser)
            elif name == "get_recent_papers":
                result = await handle_get_recent_papers(arguments, parser)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            error_msg = f"❌ Error in tool '{name}': {str(e)}"
            logger.error(f"[red]{error_msg}[/red]")
            return [TextContent(type="text", text=error_msg)]
    
    logger.info("🚀 [bold green]Research Aggregation MCP Server fully initialized[/bold green]")
    return server

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
