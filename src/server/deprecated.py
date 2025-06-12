# deprecated.py
"""
Deprecated components for the Research Aggregation MCP Server

This module contains functions that have been superseded by unified search functionality
but are preserved for backward compatibility and testing purposes.

These functions are no longer used by the active MCP server but are kept for:
1. Backward compatibility if external code depends on them
2. Testing the transition from individual to unified search tools
3. Documentation of the previous implementation approach

DEPRECATED: Use handle_search_papers() and handle_get_all_recent_papers() instead.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple

# Our existing modules
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.arxiv.client import AsyncArxivClient, ArxivAPIError
from src.arxiv.parser import ArxivXMLParser
from src.common.paper import AcademicPaper, from_arxiv_paper

# Setup Rich logging
logger = logging.getLogger(__name__)

def _deprecation_warning(old_function: str, new_function: str):
    """Log a deprecation warning for old functions"""
    logger.warning(f"⚠️ [yellow]DEPRECATED[/yellow]: {old_function}() is deprecated. Use {new_function}() instead.")

async def handle_search_trading_papers(arguments: Dict[str, Any], parser: Optional[ArxivXMLParser] = None) -> str:
    """
    DEPRECATED: Handle search_trading_papers tool
    
    This function has been superseded by handle_search_papers() with appropriate query terms.
    Use handle_search_papers({"query": "algorithmic trading OR market microstructure"}) instead.
    """
    _deprecation_warning("handle_search_trading_papers", "handle_search_papers")
    
    # Initialize parser if not provided
    if parser is None:
        parser = ArxivXMLParser()
    
    try:
        # Extract parameters with defaults
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date") 
        max_results = arguments.get("max_results", 200)
        source = arguments.get("source", "all")  # New optional source parameter
        
        # Set default dates if not provided (last 6 months)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Searching trading papers from [bold]{start_date}[/bold] to [bold]{end_date}[/bold]")
        
        # For now, source parameter is ignored - existing handlers only support arXiv
        # TODO: Implement multi-source support for existing handlers when source="all"
        
        # Use context manager for proper session handling
        async with AsyncArxivClient(delay_seconds=3.0) as client:
            # Get XML data
            xml_data = await client.search_trading_papers(start_date, end_date, max_results)
            
            # Parse to ArxivPaper objects
            arxiv_papers = parser.parse_response(xml_data)
            
            # Convert to AcademicPaper objects
            academic_papers = [from_arxiv_paper(paper) for paper in arxiv_papers]
            
            # Convert to JSON format for Claude
            result = {
                "search_query": "Trading and Market Microstructure Papers",
                "date_range": {"start": start_date, "end": end_date},
                "total_found": len(academic_papers),
                "papers": [paper.to_dict() for paper in academic_papers],
                "sources_searched": ["arXiv"]  # Add source info for backward compatibility
            }
            
            logger.info(f"✅ Found [bold green]{len(academic_papers)}[/bold green] trading papers")
            return json.dumps(result, indent=2, default=str)
            
    except ArxivAPIError as e:
        logger.error(f"🚫 ArXiv API error: [red]{e}[/red]")
        return f"ArXiv API Error: {e}"
    except Exception as e:
        logger.error(f"💥 Unexpected error: [red]{e}[/red]")
        raise

async def handle_search_quant_finance_papers(arguments: Dict[str, Any], parser: Optional[ArxivXMLParser] = None) -> str:
    """
    DEPRECATED: Handle search_quant_finance_papers tool
    
    This function has been superseded by handle_search_papers() with appropriate query terms.
    Use handle_search_papers({"query": "quantitative finance"}) instead.
    """
    _deprecation_warning("handle_search_quant_finance_papers", "handle_search_papers")
    
    # Initialize parser if not provided
    if parser is None:
        parser = ArxivXMLParser()
    
    try:
        # Extract parameters with defaults
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date") 
        max_results = arguments.get("max_results", 200)
        source = arguments.get("source", "all")  # New optional source parameter
        
        # Set default dates if not provided (last 6 months)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Searching quant finance papers from [bold]{start_date}[/bold] to [bold]{end_date}[/bold]")
        
        async with AsyncArxivClient(delay_seconds=3.0) as client:
            # Get XML data for all quantitative finance categories
            xml_data = await client.search_all_quant_finance(start_date, end_date, max_results)
            
            # Parse to ArxivPaper objects
            arxiv_papers = parser.parse_response(xml_data)
            
            # Convert to AcademicPaper objects
            academic_papers = [from_arxiv_paper(paper) for paper in arxiv_papers]
            
            # Convert to JSON format for Claude
            result = {
                "search_query": "All Quantitative Finance Papers",
                "date_range": {"start": start_date, "end": end_date},
                "total_found": len(academic_papers),
                "category_breakdown": get_category_breakdown(academic_papers),
                "papers": [paper.to_dict() for paper in academic_papers],
                "sources_searched": ["arXiv"]  # Add source info for backward compatibility
            }
            
            logger.info(f"✅ Found [bold green]{len(academic_papers)}[/bold green] quant finance papers")
            return json.dumps(result, indent=2, default=str)
            
    except ArxivAPIError as e:
        logger.error(f"🚫 ArXiv API error: [red]{e}[/red]")
        return f"ArXiv API Error: {e}"
    except Exception as e:
        logger.error(f"💥 Unexpected error: [red]{e}[/red]")
        raise

async def handle_get_recent_papers(arguments: Dict[str, Any], parser: Optional[ArxivXMLParser] = None) -> str:
    """
    DEPRECATED: Handle get_recent_papers tool
    
    This function has been superseded by handle_get_all_recent_papers().
    Use handle_get_all_recent_papers() instead for broader coverage across all sources.
    """
    _deprecation_warning("handle_get_recent_papers", "handle_get_all_recent_papers")
    
    # Initialize parser if not provided
    if parser is None:
        parser = ArxivXMLParser()
    
    try:
        # Extract required and optional parameters
        months_back = arguments.get("months_back")
        category = arguments.get("category", "q-fin.*")
        max_results = arguments.get("max_results", 200)
        source = arguments.get("source", "all")  # New optional source parameter
        
        if not months_back:
            raise ValueError("months_back is required")
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Searching [cyan]{category}[/cyan] papers from last [bold]{months_back}[/bold] months")
        
        async with AsyncArxivClient(delay_seconds=3.0) as client:
            # Use the general search method with the specified category
            xml_data = await client.search_papers(f"cat:{category}", start_date, end_date, max_results)
            
            # Parse to ArxivPaper objects
            arxiv_papers = parser.parse_response(xml_data)
            
            # Convert to AcademicPaper objects
            academic_papers = [from_arxiv_paper(paper) for paper in arxiv_papers]
            
            # Convert to JSON format for Claude
            result = {
                "search_query": f"Recent papers in {category}",
                "months_back": months_back,
                "date_range": {"start": start_date, "end": end_date},
                "category": category,
                "total_found": len(academic_papers),
                "papers": [paper.to_dict() for paper in academic_papers],
                "sources_searched": ["arXiv"]  # Add source info for backward compatibility
            }
            
            logger.info(f"✅ Found [bold green]{len(academic_papers)}[/bold green] papers in {category}")
            return json.dumps(result, indent=2, default=str)
            
    except ArxivAPIError as e:
        logger.error(f"🚫 ArXiv API error: [red]{e}[/red]")
        return f"ArXiv API Error: {e}"
    except Exception as e:
        logger.error(f"💥 Unexpected error: [red]{e}[/red]")
        raise

def get_category_breakdown(papers) -> Dict[str, int]:
    """Get count of papers by category"""
    category_counts = {}
    for paper in papers:
        if paper.categories:  # Handle None case for AcademicPaper
            for category in paper.categories:
                category_counts[category] = category_counts.get(category, 0) + 1
    return dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))