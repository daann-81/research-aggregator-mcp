# shared.py
"""
Shared components for the Research Aggregation MCP Server

This module contains common functionality used by both stdio and HTTP transports,
including tool handlers, schemas, and utility functions.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent

# Rich logging
from rich.logging import RichHandler

# Our existing modules
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.arxiv.client import AsyncArxivClient, ArxivAPIError
from src.arxiv.parser import ArxivXMLParser

# Setup Rich logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
    handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=True)]
)
logger = logging.getLogger(__name__)

# Define shared input schemas
DATE_RANGE_SCHEMA = {
    "start_date": {
        "type": "string",
        "description": "Start date in YYYY-MM-DD format (optional, defaults to 6 months ago)"
    },
    "end_date": {
        "type": "string", 
        "description": "End date in YYYY-MM-DD format (optional, defaults to today)"
    },
    "max_results": {
        "type": "integer",
        "description": "Maximum number of papers to return (default: 200, max: 2000)",
        "default": 200
    }
}

# Initialize our arXiv components
def initialize_arxiv_components():
    """Initialize arXiv client and parser with error handling"""
    try:
        arxiv_client = AsyncArxivClient(delay_seconds=3.0)
        parser = ArxivXMLParser()
        logger.info("✅ [bold green]ArXiv client and parser initialized successfully[/bold green]")
        return arxiv_client, parser
    except Exception as e:
        logger.error(f"❌ [bold red]Failed to initialize arXiv components: {e}[/bold red]")
        raise

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

async def handle_search_trading_papers(arguments: Dict[str, Any], parser: Optional[ArxivXMLParser] = None) -> str:
    """Handle search_trading_papers tool"""
    # Initialize parser if not provided
    if parser is None:
        parser = ArxivXMLParser()
    
    try:
        # Extract parameters with defaults
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date") 
        max_results = arguments.get("max_results", 200)
        
        # Set default dates if not provided (last 6 months)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Searching trading papers from [bold]{start_date}[/bold] to [bold]{end_date}[/bold]")
        
        # Use context manager for proper session handling
        async with AsyncArxivClient(delay_seconds=3.0) as client:
            # Get XML data
            xml_data = await client.search_trading_papers(start_date, end_date, max_results)
            
            # Parse to structured objects
            papers = parser.parse_response(xml_data)
            
            # Convert to JSON format for Claude
            result = {
                "search_query": "Trading and Market Microstructure Papers",
                "date_range": {"start": start_date, "end": end_date},
                "total_found": len(papers),
                "papers": [paper_to_dict(paper) for paper in papers]
            }
            
            logger.info(f"✅ Found [bold green]{len(papers)}[/bold green] trading papers")
            return json.dumps(result, indent=2, default=str)
            
    except ArxivAPIError as e:
        logger.error(f"🚫 ArXiv API error: [red]{e}[/red]")
        return f"ArXiv API Error: {e}"
    except Exception as e:
        logger.error(f"💥 Unexpected error: [red]{e}[/red]")
        raise

async def handle_search_quant_finance_papers(arguments: Dict[str, Any], parser: Optional[ArxivXMLParser] = None) -> str:
    """Handle search_quant_finance_papers tool"""
    # Initialize parser if not provided
    if parser is None:
        parser = ArxivXMLParser()
    
    try:
        # Extract parameters with defaults
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date") 
        max_results = arguments.get("max_results", 200)
        
        # Set default dates if not provided (last 6 months)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Searching quant finance papers from [bold]{start_date}[/bold] to [bold]{end_date}[/bold]")
        
        async with AsyncArxivClient(delay_seconds=3.0) as client:
            # Get XML data for all quantitative finance categories
            xml_data = await client.search_all_quant_finance(start_date, end_date, max_results)
            
            # Parse to structured objects
            papers = parser.parse_response(xml_data)
            
            # Convert to JSON format for Claude
            result = {
                "search_query": "All Quantitative Finance Papers",
                "date_range": {"start": start_date, "end": end_date},
                "total_found": len(papers),
                "category_breakdown": get_category_breakdown(papers),
                "papers": [paper_to_dict(paper) for paper in papers]
            }
            
            logger.info(f"✅ Found [bold green]{len(papers)}[/bold green] quant finance papers")
            return json.dumps(result, indent=2, default=str)
            
    except ArxivAPIError as e:
        logger.error(f"🚫 ArXiv API error: [red]{e}[/red]")
        return f"ArXiv API Error: {e}"
    except Exception as e:
        logger.error(f"💥 Unexpected error: [red]{e}[/red]")
        raise

async def handle_get_recent_papers(arguments: Dict[str, Any], parser: Optional[ArxivXMLParser] = None) -> str:
    """Handle get_recent_papers tool"""
    # Initialize parser if not provided
    if parser is None:
        parser = ArxivXMLParser()
    
    try:
        # Extract required and optional parameters
        months_back = arguments.get("months_back")
        category = arguments.get("category", "q-fin.*")
        max_results = arguments.get("max_results", 200)
        
        if not months_back:
            raise ValueError("months_back is required")
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Searching [cyan]{category}[/cyan] papers from last [bold]{months_back}[/bold] months")
        
        async with AsyncArxivClient(delay_seconds=3.0) as client:
            # Use the general search method with the specified category
            xml_data = await client.search_papers(f"cat:{category}", start_date, end_date, max_results)
            
            # Parse to structured objects
            papers = parser.parse_response(xml_data)
            
            # Convert to JSON format for Claude
            result = {
                "search_query": f"Recent papers in {category}",
                "months_back": months_back,
                "date_range": {"start": start_date, "end": end_date},
                "category": category,
                "total_found": len(papers),
                "papers": [paper_to_dict(paper) for paper in papers]
            }
            
            logger.info(f"✅ Found [bold green]{len(papers)}[/bold green] papers in {category}")
            return json.dumps(result, indent=2, default=str)
            
    except ArxivAPIError as e:
        logger.error(f"🚫 ArXiv API error: [red]{e}[/red]")
        return f"ArXiv API Error: {e}"
    except Exception as e:
        logger.error(f"💥 Unexpected error: [red]{e}[/red]")
        raise

def paper_to_dict(paper) -> Dict[str, Any]:
    """Convert ArxivPaper object to dictionary for JSON serialization"""
    return {
        "id": paper.id,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "submitted_date": paper.submitted_date.isoformat(),
        "updated_date": paper.updated_date.isoformat(),
        "categories": paper.categories,
        "pdf_url": paper.pdf_url,
        "arxiv_url": paper.arxiv_url,
        "journal_ref": paper.journal_ref,
        "doi": paper.doi,
        "comments": paper.comments
    }

def get_category_breakdown(papers) -> Dict[str, int]:
    """Get count of papers by category"""
    category_counts = {}
    for paper in papers:
        for category in paper.categories:
            category_counts[category] = category_counts.get(category, 0) + 1
    return dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))