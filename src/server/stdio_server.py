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

from .shared import handle_search_papers, handle_get_all_recent_papers

logger = logging.getLogger(__name__)
def create_mcp_server() -> Server:
    """Create and configure the MCP server with tool handlers"""
    # Create MCP server instance
    server = Server("research-aggregation-mcp")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """Register available tools with the MCP server"""
        return [
            Tool(
                name="search_papers",
                description="Search for academic papers across multiple sources (arXiv, SSRN) with optional source filtering. Supports general search queries with source-specific filtering.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (required). Examples: 'machine learning', 'algorithmic trading', 'risk management'"
                        },
                        "source": {
                            "type": "string",
                            "description": "Source to search (optional, defaults to 'all'). Options: 'all', 'arxiv', 'ssrn'",
                            "enum": ["all", "arxiv", "ssrn"],
                            "default": "all"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of papers to return (default: 20, max: 100)",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Search timeout in seconds (default: 30.0)",
                            "default": 30.0
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_all_recent_papers",
                description="Get recent papers from multiple sources (arXiv, SSRN) without category filtering. Returns papers from ALL academic categories, not just finance.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "months_back": {
                            "type": "integer",
                            "description": "Number of months to look back (required)",
                            "minimum": 1,
                            "maximum": 60
                        },
                        "source": {
                            "type": "string",
                            "description": "Source to search (optional, defaults to 'all'). Options: 'all', 'arxiv', 'ssrn'",
                            "enum": ["all", "arxiv", "ssrn"],
                            "default": "all"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of papers to return (default: 50, max: 200)",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 200
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
            
            if name == "search_papers":
                result = await handle_search_papers(arguments)
            elif name == "get_all_recent_papers":
                result = await handle_get_all_recent_papers(arguments)
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
