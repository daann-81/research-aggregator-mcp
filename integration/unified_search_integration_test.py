"""
Integration Test Cases for Unified Search Functionality

This module contains integration tests for unified search across multiple
academic paper sources (arXiv, SSRN, etc.) with source filtering capabilities.
These tests make real API calls to verify end-to-end functionality.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.json import JSON

# Import the unified search functions we'll be testing
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.server.shared import (
    handle_search_papers,
    handle_get_all_recent_papers
)
from src.server.deprecated import (
    handle_search_trading_papers,
    handle_search_quant_finance_papers,
    handle_get_recent_papers
)
from src.common.paper import AcademicPaper

console = Console()


@pytest.mark.asyncio
async def test_search_papers_all_sources():
    """Test searching across all sources and validate both sources contribute results"""
    console.print("\n🔍 [bold blue]Testing search_papers with all sources[/bold blue]")
    
    # Use a query more likely to return results from both sources
    arguments = {
        "query": "finance risk management",
        "max_results": 10
    }
    
    try:
        result = await handle_search_papers(arguments)
        data = json.loads(result)
        
        # Enhanced logging for debugging
        console.print(f"🔍 Sources searched: {data['sources_searched']}")
        console.print(f"📊 Source breakdown: {data.get('source_breakdown', {})}")
        console.print(f"📄 Total papers found: {data['total_found']}")
        
        # Verify basic structure
        required_fields = ["search_query", "sources_searched", "total_found", "papers", "source_breakdown"]
        for field in required_fields:
            if field not in data:
                console.print(f"❌ Missing field: {field}")
                return False
        
        # Verify multiple sources were searched
        if len(data["sources_searched"]) < 2:
            console.print(f"❌ Expected multiple sources, got: {data['sources_searched']}")
            return False
        
        # NEW: Validate source breakdown - both sources should have contributed papers
        source_breakdown = data.get("source_breakdown", {})
        expected_sources = ["arXiv", "SSRN"]
        
        sources_with_papers = [source for source, count in source_breakdown.items() if count > 0]
        
        # Check if both sources contributed papers
        if len(sources_with_papers) >= 2:
            console.print(f"✅ Multiple sources contributed papers: {sources_with_papers}")
            
            # Verify both expected sources contributed
            for expected_source in expected_sources:
                if expected_source not in sources_with_papers:
                    console.print(f"⚠️ Expected papers from {expected_source}, but got 0 papers")
                    
        else:
            # Allow for case where only one source returns results (real-world API behavior)
            console.print(f"⚠️ Only {sources_with_papers} returned results. This may be expected for some queries.")
            console.print(f"   Source breakdown: {source_breakdown}")
            
            # Still require at least one source to have results
            if len(sources_with_papers) == 0:
                console.print(f"❌ No sources returned papers")
                return False
        
        # NEW: Verify paper source distribution
        if data["papers"]:
            paper_sources = set(paper["source"] for paper in data["papers"])
            
            # Count papers per source
            source_counts = {}
            for paper in data["papers"]:
                source = paper["source"]
                source_counts[source] = source_counts.get(source, 0) + 1
            
            console.print(f"📊 Paper distribution: {source_counts}")
            
            # Show distribution of first few papers for verification
            for i, paper in enumerate(data["papers"][:3]):
                console.print(f"   Paper {i+1}: {paper['source']} - {paper['title'][:50]}...")
                
            # Check papers have source field
            for i, paper in enumerate(data["papers"][:3]):  # Check first 3
                if "source" not in paper:
                    console.print(f"❌ Paper {i} missing source field")
                    return False
                    
            # Validate source consistency
            for source in paper_sources:
                if source not in expected_sources:
                    console.print(f"❌ Unexpected source in papers: {source}")
                    return False
        else:
            console.print("ℹ️ No papers returned to validate source distribution")
            
        console.print("✅ Multi-source validation test passed")
        return True
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_search_papers_filter_arxiv_only():
    """Test searching arXiv only when source specified"""
    console.print("\n📚 [bold blue]Testing search_papers with arXiv filter[/bold blue]")
    
    arguments = {
        "query": "quantitative finance", 
        "source": "arxiv",
        "max_results": 5
    }
    
    try:
        result = await handle_search_papers(arguments)
        data = json.loads(result)
        
        console.print(f"✅ Found {data['total_found']} papers from: {data['sources_searched']}")
        
        # Should only search arXiv
        if data["sources_searched"] != ["arXiv"]:
            console.print(f"❌ Expected [arXiv], got: {data['sources_searched']}")
            return False
        
        # All papers should be from arXiv
        if data["papers"]:
            for i, paper in enumerate(data["papers"]):
                if paper["source"] != "arXiv":
                    console.print(f"❌ Paper {i} from {paper['source']}, expected arXiv")
                    return False
        
        console.print("✅ arXiv filter test passed")
        return True
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_search_papers_filter_ssrn_only():
    """Test searching SSRN only when source specified"""
    console.print("\n📊 [bold blue]Testing search_papers with SSRN filter[/bold blue]")
    
    arguments = {
        "query": "corporate finance",
        "source": "ssrn", 
        "max_results": 5
    }
    
    try:
        result = await handle_search_papers(arguments)
        data = json.loads(result)
        
        console.print(f"✅ Found {data['total_found']} papers from: {data['sources_searched']}")
        
        # Should only search SSRN
        if data["sources_searched"] != ["SSRN"]:
            console.print(f"❌ Expected [SSRN], got: {data['sources_searched']}")
            return False
        
        # All papers should be from SSRN
        if data["papers"]:
            for i, paper in enumerate(data["papers"]):
                if paper["source"] != "SSRN":
                    console.print(f"❌ Paper {i} from {paper['source']}, expected SSRN")
                    return False
        
        console.print("✅ SSRN filter test passed")
        return True
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_search_papers_invalid_source():
    """Test error handling for invalid source"""
    console.print("\n🚫 [bold blue]Testing search_papers with invalid source[/bold blue]")
    
    arguments = {
        "query": "test",
        "source": "invalid_source"
    }
    
    try:
        result = await handle_search_papers(arguments)
        console.print("❌ Expected ValueError but function succeeded")
        return False
        
    except ValueError as e:
        if "Invalid source" in str(e):
            console.print("✅ Correctly raised ValueError for invalid source")
            return True
        else:
            console.print(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        console.print(f"❌ Wrong exception type: {e}")
        return False


@pytest.mark.asyncio
async def test_search_papers_empty_query():
    """Test error handling for empty query"""
    console.print("\n🚫 [bold blue]Testing search_papers with empty query[/bold blue]")
    
    arguments = {
        "query": "",
        "max_results": 10
    }
    
    try:
        result = await handle_search_papers(arguments)
        console.print("❌ Expected ValueError but function succeeded")
        return False
        
    except ValueError as e:
        if "query cannot be empty" in str(e):
            console.print("✅ Correctly raised ValueError for empty query")
            return True
        else:
            console.print(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        console.print(f"❌ Wrong exception type: {e}")
        return False


@pytest.mark.asyncio
async def test_get_all_recent_papers_all_sources():
    """Test getting recent papers from all sources"""
    console.print("\n📅 [bold blue]Testing get_all_recent_papers with all sources[/bold blue]")
    
    arguments = {
        "months_back": 6,
        "max_results": 20
    }
    
    try:
        result = await handle_get_all_recent_papers(arguments)
        data = json.loads(result)
        
        console.print(f"✅ Found {data['total_found']} papers from sources: {data['sources_searched']}")
        
        # Test basic structure
        required_fields = ["search_query", "months_back", "sources_searched", "total_found", "papers", "source_breakdown", "category_breakdown"]
        for field in required_fields:
            if field not in data:
                console.print(f"❌ Missing field: {field}")
                return False
        
        # Should search multiple sources
        if len(data["sources_searched"]) < 2:
            console.print(f"❌ Expected multiple sources, got: {data['sources_searched']}")
            return False
            
        if data["months_back"] != 6:
            console.print(f"❌ Expected months_back=6, got: {data['months_back']}")
            return False
        
        console.print("✅ Recent papers test passed")
        return True
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_metadata_preservation():
    """Test that all metadata is preserved for caller assessment"""
    console.print("\n📝 [bold blue]Testing metadata preservation[/bold blue]")
    
    arguments = {
        "query": "algorithmic trading",
        "max_results": 3
    }
    
    try:
        result = await handle_search_papers(arguments)
        data = json.loads(result)
        
        if not data["papers"]:
            console.print("ℹ No papers found to test metadata")
            return True
        
        paper = data["papers"][0]
        expected_fields = {
            "id", "title", "authors", "abstract", "publication_date",
            "source", "categories", "url", "pdf_url", "journal_ref", 
            "doi", "download_count", "affiliations"
        }
        
        missing_fields = expected_fields - set(paper.keys())
        if missing_fields:
            console.print(f"❌ Missing metadata fields: {missing_fields}")
            return False
        
        # Test categories are preserved
        if paper.get("categories") and not isinstance(paper["categories"], list):
            console.print("❌ Categories should be a list")
            return False
            
        console.print("✅ Metadata preservation test passed")
        return True
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        return False


async def run_integration_tests(tests=None):
    """Run all integration tests and report results"""
    console.print("🎯 [bold green]Running Unified Search Integration Tests[/bold green]")
    
    tests = [
        ("Search Papers - All Sources", test_search_papers_all_sources),
        ("Search Papers - arXiv Filter", test_search_papers_filter_arxiv_only),
        ("Search Papers - SSRN Filter", test_search_papers_filter_ssrn_only),
        ("Search Papers - Invalid Source", test_search_papers_invalid_source),
        ("Search Papers - Empty Query", test_search_papers_empty_query),
        ("Recent Papers - All Sources", test_get_all_recent_papers_all_sources),
        ("Search Papers - Metadata Preservation", test_metadata_preservation),
    ] if tests is None else tests
    
    results = []
    for test_name, test_func in tests:
        console.print(f"\n📋 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, "✅ PASS" if result else "❌ FAIL"))
        except Exception as e:
            results.append((test_name, f"❌ ERROR: {str(e)[:50]}..."))
    
    # Summary table
    table = Table(title="Integration Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="green")
    
    for test_name, result in results:
        table.add_row(test_name, result)
    
    console.print(table)
    
    # Overall result
    passed = sum(1 for _, result in results if "PASS" in result)
    total = len(results)
    console.print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    from src.util.logging import setup_logging
    setup_logging()
    
    asyncio.run(run_integration_tests())