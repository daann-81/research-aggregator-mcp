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
from typing import Any, Dict, List, Optional, Tuple

# Our existing modules
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.arxiv.client import AsyncArxivClient
from src.arxiv.parser import ArxivXMLParser
from src.ssrn.client import AsyncSSRNClient, SSRNAPIError
from src.ssrn.parser import SSRNJSONParser
from src.common.paper import AcademicPaper, from_arxiv_paper, from_ssrn_paper

# Setup Rich logging
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


def get_category_breakdown(papers) -> Dict[str, int]:
    """Get count of papers by category"""
    category_counts = {}
    for paper in papers:
        if paper.categories:  # Handle None case for AcademicPaper
            for category in paper.categories:
                category_counts[category] = category_counts.get(category, 0) + 1
    return dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))


# Unified search handlers
async def handle_search_papers(arguments: Dict[str, Any]) -> str:
    """
    Handle unified search_papers tool across multiple sources.
    
    Searches across arXiv and SSRN based on source parameter.
    """
    try:
        # Extract parameters
        query = arguments.get("query", "")
        source = arguments.get("source", "all")
        max_results = arguments.get("max_results", 20)
        timeout = arguments.get("timeout", 30.0)  # Reserved for future use - clients use default timeouts
        
        if not query:
            raise ValueError("query cannot be empty")
        
        if source not in ["all", "arxiv", "ssrn"]:
            raise ValueError("Invalid source")
        
        logger.info(f"🔍 Unified search for '{query}' across {source} source(s)")
        
        # Determine which sources to search
        sources_to_search = []
        if source == "all":
            sources_to_search = ["arxiv", "ssrn"]
        else:
            sources_to_search = [source]
        
        # Collect papers from each source
        all_papers = []
        sources_searched = []
        source_errors = {}
        source_breakdown = {}
        
        # Search arXiv if requested
        if "arxiv" in sources_to_search:
            try:
                logger.info(f"📚 Searching arXiv for: {query}")
                async with AsyncArxivClient(delay_seconds=3.0) as arxiv_client:
                    # Search arXiv using general search
                    xml_data = await arxiv_client.search_papers(query, max_results=max_results)
                    
                    # Parse to ArxivPaper objects
                    arxiv_parser = ArxivXMLParser()
                    arxiv_papers = arxiv_parser.parse_response(xml_data)
                    
                    # Convert to AcademicPaper objects
                    for paper in arxiv_papers:
                        academic_paper = from_arxiv_paper(paper)
                        all_papers.append(academic_paper)
                    
                    sources_searched.append("arXiv")
                    source_breakdown["arXiv"] = len(arxiv_papers)
                    logger.info(f"✅ Found {len(arxiv_papers)} papers from arXiv")
                    
            except Exception as e:
                logger.warning(f"⚠️ arXiv search failed: {e}")
                source_errors["arXiv"] = str(e)
        
        # Search SSRN if requested  
        if "ssrn" in sources_to_search:
            try:
                logger.info(f"📊 Searching SSRN for: {query}")
                async with AsyncSSRNClient(delay_seconds=3.0) as ssrn_client:
                    # Search SSRN using text search
                    ssrn_raw_papers = await ssrn_client.search_papers(query, max_results=max_results)
                    
                    # Parse to SSRNPaper objects
                    ssrn_parser = SSRNJSONParser()
                    # Wrap raw papers list in expected format for parser
                    ssrn_response = {"papers": ssrn_raw_papers}
                    ssrn_papers = ssrn_parser.parse_response(ssrn_response)
                    
                    # Convert to AcademicPaper objects
                    for paper in ssrn_papers:
                        academic_paper = from_ssrn_paper(paper)
                        all_papers.append(academic_paper)
                    
                    sources_searched.append("SSRN")
                    source_breakdown["SSRN"] = len(ssrn_papers)
                    logger.info(f"✅ Found {len(ssrn_papers)} papers from SSRN")
                    
            except Exception as e:
                logger.warning(f"⚠️ SSRN search failed: {e}")
                source_errors["SSRN"] = str(e)
        
        # Process papers: aggregate, sort by date, and limit results
        aggregated_papers, aggregation_stats = process_papers(all_papers, max_results)
        duplicates_removed = aggregation_stats["duplicates_removed"]
        
        # Build result
        result = {
            "search_query": f"Search for: {query}",
            "sources_searched": sources_searched,
            "total_found": len(aggregated_papers),
            "papers": [paper.to_dict() for paper in aggregated_papers],
            "source_breakdown": source_breakdown,
            "duplicates_removed": duplicates_removed,
            "deduplication_method": aggregation_stats["aggregation_method"],
            "source_errors": source_errors,
            "successful_sources": sources_searched
        }
        
        logger.info(f"🎯 Total unified search results: {len(aggregated_papers)} papers")
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"💥 Unified search error: [red]{e}[/red]")
        raise


async def handle_get_all_recent_papers(arguments: Dict[str, Any]) -> str:
    """
    Handle unified get_all_recent_papers tool across multiple sources.
    
    Gets recent papers from all sources without category filtering.
    """
    try:
        # Extract parameters
        months_back = arguments.get("months_back")
        source = arguments.get("source", "all")
        max_results = arguments.get("max_results", 50)
        
        if not months_back:
            raise ValueError("months_back is required")
        
        if months_back <= 0:
            raise ValueError("months_back must be positive")
        
        if source not in ["all", "arxiv", "ssrn"]:
            raise ValueError("Invalid source")
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d')
        
        logger.info(f"📅 Getting recent papers from {source} source(s) over last {months_back} months")
        
        # Determine which sources to search
        sources_to_search = []
        if source == "all":
            sources_to_search = ["arxiv", "ssrn"]
        else:
            sources_to_search = [source]
        
        # Collect papers from each source
        all_papers = []
        sources_searched = []
        source_errors = {}
        source_breakdown = {}
        
        # Search arXiv if requested - get ALL categories, not just finance
        if "arxiv" in sources_to_search:
            try:
                logger.info(f"📚 Getting recent arXiv papers from {start_date} to {end_date}")
                async with AsyncArxivClient(delay_seconds=3.0) as arxiv_client:
                    # Search ALL categories - use a broad query instead of wildcard
                    xml_data = await arxiv_client.search_papers("all:electron", start_date, end_date, max_results=max_results)
                    
                    # Parse to ArxivPaper objects
                    arxiv_parser = ArxivXMLParser()
                    arxiv_papers = arxiv_parser.parse_response(xml_data)
                    
                    # Convert to AcademicPaper objects
                    for paper in arxiv_papers:
                        academic_paper = from_arxiv_paper(paper)
                        all_papers.append(academic_paper)
                    
                    sources_searched.append("arXiv")
                    source_breakdown["arXiv"] = len(arxiv_papers)
                    logger.info(f"✅ Found {len(arxiv_papers)} recent papers from arXiv")
                    
            except Exception as e:
                logger.warning(f"⚠️ arXiv recent papers search failed: {e}")
                source_errors["arXiv"] = str(e)
        
        # Search SSRN if requested
        if "ssrn" in sources_to_search:
            try:
                logger.info(f"📊 Getting recent SSRN papers from last {months_back} months")
                async with AsyncSSRNClient(delay_seconds=3.0) as ssrn_client:
                    # Get recent papers from SSRN
                    ssrn_raw_papers = await ssrn_client.get_recent_papers(months_back=months_back, max_results=max_results)
                    
                    # Parse to SSRNPaper objects
                    ssrn_parser = SSRNJSONParser()
                    # Wrap raw papers list in expected format for parser
                    ssrn_response = {"papers": ssrn_raw_papers}
                    ssrn_papers = ssrn_parser.parse_response(ssrn_response)
                    
                    # Convert to AcademicPaper objects
                    for paper in ssrn_papers:
                        academic_paper = from_ssrn_paper(paper)
                        all_papers.append(academic_paper)
                    
                    sources_searched.append("SSRN")
                    source_breakdown["SSRN"] = len(ssrn_papers)
                    logger.info(f"✅ Found {len(ssrn_papers)} recent papers from SSRN")
                    
            except Exception as e:
                logger.warning(f"⚠️ SSRN recent papers search failed: {e}")
                source_errors["SSRN"] = str(e)
        
        # Process papers: aggregate, sort by date, and limit results
        aggregated_papers, aggregation_stats = process_papers(all_papers, max_results)
        duplicates_removed = aggregation_stats["duplicates_removed"]
        
        # Build result
        result = {
            "search_query": f"Recent papers from last {months_back} months",
            "months_back": months_back,
            "date_range": {"start": start_date, "end": end_date},
            "sources_searched": sources_searched,
            "total_found": len(aggregated_papers),
            "papers": [paper.to_dict() for paper in aggregated_papers],
            "source_breakdown": source_breakdown,
            "category_breakdown": get_category_breakdown(aggregated_papers),
            "duplicates_removed": duplicates_removed,
            "deduplication_method": aggregation_stats["aggregation_method"],
            "source_errors": source_errors,
            "successful_sources": sources_searched
        }
        
        logger.info(f"🎯 Total recent papers found: {len(aggregated_papers)} papers")
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"💥 Recent papers search error: [red]{e}[/red]")
        raise


def normalize_title(title: str) -> str:
    """
    Normalize title for comparison by removing punctuation, extra whitespace, and converting to lowercase.
    
    Args:
        title: Original title string
        
    Returns:
        Normalized title string for comparison
    """
    import re
    if not title:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = title.lower().strip()
    
    # Remove common punctuation and extra whitespace
    normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
    normalized = re.sub(r'\s+', ' ', normalized)      # Collapse whitespace
    normalized = normalized.strip()
    
    return normalized


def process_papers(papers: List[AcademicPaper], max_results: int) -> Tuple[List[AcademicPaper], Dict[str, Any]]:
    """
    Process papers by aggregating duplicates, sorting by date, and limiting results.
    
    Papers with the same normalized title are merged into a single entry that shows
    all sources where the paper is available, preserving metadata from all sources.
    Then papers are sorted by publication date (most recent first) and limited to max_results.
    
    Args:
        papers: List of AcademicPaper objects to process
        max_results: Maximum number of papers to return after processing
        
    Returns:
        Tuple of (processed papers list, processing stats)
    """
    if not papers:
        return [], {"duplicates_removed": 0, "aggregation_method": "title_normalization", "total_before_limit": 0}
    
    # Group papers by normalized title
    title_groups = {}
    for paper in papers:
        normalized_title = normalize_title(paper.title)
        if normalized_title not in title_groups:
            title_groups[normalized_title] = []
        title_groups[normalized_title].append(paper)
    
    # Aggregate papers with duplicate titles
    aggregated_papers = []
    duplicates_removed = 0
    
    for normalized_title, paper_group in title_groups.items():
        if len(paper_group) == 1:
            # Single paper, no aggregation needed
            aggregated_papers.append(paper_group[0])
        else:
            # Multiple papers with same title - aggregate them
            duplicates_removed += len(paper_group) - 1
            
            # Create aggregated paper
            aggregated_paper = _merge_papers(paper_group)
            aggregated_papers.append(aggregated_paper)
            
            logger.info(f"📋 Aggregated {len(paper_group)} papers with title: '{paper_group[0].title[:50]}...'")
    
    # Sort by publication date (most recent first)
    aggregated_papers.sort(key=lambda p: p.publication_date, reverse=True)
    total_before_limit = len(aggregated_papers)
    
    # Limit results to max_results
    if len(aggregated_papers) > max_results:
        aggregated_papers = aggregated_papers[:max_results]
    
    stats = {
        "duplicates_removed": duplicates_removed,
        "aggregation_method": "title_normalization",
        "total_before_limit": total_before_limit
    }
    return aggregated_papers, stats



def _merge_papers(papers: List[AcademicPaper]) -> AcademicPaper:
    """
    Merge multiple papers with the same title into a single aggregated paper.
    
    Strategy:
    - Use most recent publication date
    - Combine sources into a list
    - Keep most complete metadata (prefer non-None values)
    - Create source_urls mapping
    
    Args:
        papers: List of papers with identical titles to merge
        
    Returns:
        Single aggregated AcademicPaper
    """
    if not papers:
        raise ValueError("Cannot merge empty paper list")
    
    if len(papers) == 1:
        return papers[0]
    
    # Sort by publication date (most recent first) for primary paper selection
    sorted_papers = sorted(papers, key=lambda p: p.publication_date, reverse=True)
    primary_paper = sorted_papers[0]
    
    # Collect all sources and URLs
    sources = []
    source_urls = {}
    for paper in papers:
        if isinstance(paper.source, list):
            sources.extend(paper.source)
            if paper.source_urls:
                source_urls.update(paper.source_urls)
        else:
            sources.append(paper.source)
            source_urls[paper.source] = paper.url
    
    # Remove duplicates while preserving order
    unique_sources = []
    seen = set()
    for source in sources:
        if source not in seen:
            unique_sources.append(source)
            seen.add(source)
    
    # Merge metadata - prefer non-None values
    merged_abstract = _get_best_value([p.abstract for p in papers])
    merged_categories = _merge_lists([p.categories for p in papers])
    merged_pdf_url = _get_best_value([p.pdf_url for p in papers])
    merged_journal_ref = _get_best_value([p.journal_ref for p in papers])
    merged_doi = _get_best_value([p.doi for p in papers])
    merged_download_count = _get_best_value([p.download_count for p in papers])
    merged_affiliations = _merge_lists([p.affiliations for p in papers])
    
    # Create aggregated paper
    return AcademicPaper(
        id=primary_paper.id,  # Use primary paper's ID
        title=primary_paper.title,  # Use primary paper's title (original case)
        authors=primary_paper.authors,  # Use primary paper's authors
        publication_date=primary_paper.publication_date,  # Most recent date
        source=unique_sources if len(unique_sources) > 1 else unique_sources[0],
        url=primary_paper.url,  # Use primary paper's URL
        abstract=merged_abstract,
        categories=merged_categories,
        pdf_url=merged_pdf_url,
        journal_ref=merged_journal_ref,
        doi=merged_doi,
        download_count=merged_download_count,
        affiliations=merged_affiliations,
        source_urls=source_urls if len(unique_sources) > 1 else None
    )


def _get_best_value(values: List[Any]) -> Any:
    """Get the first non-None value from a list"""
    for value in values:
        if value is not None:
            return value
    return None


def _merge_lists(lists: List[Optional[List[str]]]) -> Optional[List[str]]:
    """Merge multiple lists, removing duplicates while preserving order"""
    if not any(lists):
        return None
    
    merged = []
    seen = set()
    
    for lst in lists:
        if lst:
            for item in lst:
                if item not in seen:
                    merged.append(item)
                    seen.add(item)
    
    return merged if merged else None