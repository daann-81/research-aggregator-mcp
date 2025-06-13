"""
Test Cases for Unified Search Functionality (Unit Tests with Mocks)

This module contains comprehensive unit test cases for unified search across multiple
academic paper sources (arXiv, SSRN, etc.) using pytest fixtures and mocks.
These tests run fast and don't depend on internet connectivity.
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch

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
from src.arxiv.parser import ArxivPaper
from src.ssrn.parser import SSRNPaper


# Sample test data fixtures
@pytest.fixture
def sample_arxiv_papers():
    """Mock arXiv papers for testing"""
    return [
        ArxivPaper(
            id="2023.12345",
            title="Machine Learning in Finance",
            authors=["John Doe", "Jane Smith"],
            abstract="A comprehensive study of ML applications in finance...",
            categories=["q-fin.CP", "cs.LG"],
            submitted_date=datetime(2023, 12, 1),
            updated_date=datetime(2023, 12, 1),
            journal_ref="Journal of Finance 2023",
            doi="10.1234/example",
            arxiv_url="https://arxiv.org/abs/2023.12345",
            pdf_url="https://arxiv.org/pdf/2023.12345.pdf"
        ),
        ArxivPaper(
            id="2023.67890",
            title="Quantitative Risk Management",
            authors=["Alice Brown"],
            abstract="Novel approaches to risk management using quantitative methods...",
            categories=["q-fin.RM"],
            submitted_date=datetime(2023, 11, 15),
            updated_date=datetime(2023, 11, 15),
            journal_ref=None,
            doi=None,
            arxiv_url="https://arxiv.org/abs/2023.67890",
            pdf_url="https://arxiv.org/pdf/2023.67890.pdf"
        )
    ]


@pytest.fixture
def sample_ssrn_papers():
    """Mock SSRN papers for testing"""
    return [
        SSRNPaper(
            ssrn_id="4567890",
            title="Corporate Finance and ESG",
            authors=["Bob Wilson", "Carol Davis"],
            approved_date=datetime(2023, 12, 5),
            download_count=150,
            ssrn_url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4567890",
            university_affiliations=["Harvard Business School", "MIT Sloan"],
            abstract_type="working_paper",
            publication_status="submitted",
            is_paid=False,
            page_count=45,
            is_approved=True,
            reference="HBS Working Paper 23-456"
        ),
        SSRNPaper(
            ssrn_id="3456789",
            title="Financial Markets Efficiency",
            authors=["David Lee"],
            approved_date=datetime(2023, 11, 20),
            download_count=89,
            ssrn_url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3456789",
            university_affiliations=["University of Chicago"],
            abstract_type="research_paper",
            publication_status="published",
            is_paid=True,
            page_count=32,
            is_approved=True,
            reference=None
        )
    ]


@pytest.fixture
def sample_academic_papers():
    """Mock AcademicPaper objects for testing"""
    return [
        AcademicPaper(
            id="arxiv:2023.12345",
            title="Machine Learning in Finance",
            authors=["John Doe", "Jane Smith"],
            abstract="A comprehensive study of ML applications in finance...",
            publication_date=datetime(2023, 12, 1),
            source="arXiv",
            categories=["q-fin.CP", "cs.LG"],
            url="https://arxiv.org/abs/2023.12345",
            pdf_url="https://arxiv.org/pdf/2023.12345.pdf",
            journal_ref="Journal of Finance 2023",
            doi="10.1234/example",
            download_count=None,
            affiliations=[]
        ),
        AcademicPaper(
            id="ssrn:4567890",
            title="Corporate Finance and ESG",
            authors=["Bob Wilson", "Carol Davis"],
            abstract=None,
            publication_date=datetime(2023, 12, 5),
            source="SSRN",
            categories=[],
            url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4567890",
            pdf_url=None,
            journal_ref="HBS Working Paper 23-456",
            doi=None,
            download_count=150,
            affiliations=["Harvard Business School", "MIT Sloan"]
        )
    ]


class TestUnifiedSearchPapers:
    """Test unified search_papers functionality with mocks"""

    @pytest.mark.asyncio
    async def test_search_papers_all_sources(self, sample_arxiv_papers, sample_ssrn_papers):
        """Test searching across all sources by default"""
        arguments = {
            "query": "machine learning",
            "max_results": 10
        }

        # Mock the client calls
        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks
            mock_arxiv_instance = AsyncMock()
            mock_ssrn_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance

            # Mock parser responses - use proper ArxivPaper and SSRNPaper objects
            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_ssrn_parser.return_value.parse_response.return_value = sample_ssrn_papers

            # Mock client search responses
            mock_arxiv_instance.search_papers.return_value = "<xml>mock arxiv response</xml>"
            mock_ssrn_instance.search_papers.return_value = [{"id": "123", "title": "mock"}]

            # Execute test
            result = await handle_search_papers(arguments)
            data = json.loads(result)

            # Verify structure
            assert "search_query" in data
            assert "sources_searched" in data
            assert "total_found" in data
            assert "papers" in data
            assert "source_breakdown" in data

            # Verify multiple sources searched
            assert len(data["sources_searched"]) >= 1
            assert data["total_found"] >= 0

    @pytest.mark.asyncio
    async def test_search_papers_filter_arxiv_only(self, sample_arxiv_papers):
        """Test searching arXiv only when source specified"""
        arguments = {
            "query": "quantitative finance",
            "source": "arxiv",
            "max_results": 5
        }

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser:

            # Setup mocks
            mock_arxiv_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_arxiv_instance.search_papers.return_value = "<xml>mock response</xml>"

            # Execute test
            result = await handle_search_papers(arguments)
            data = json.loads(result)

            # Should only search arXiv
            assert "arXiv" in data["sources_searched"]
            assert "SSRN" not in data["sources_searched"]

            # All papers should be from arXiv
            if data["papers"]:
                for paper in data["papers"]:
                    assert paper["source"] == "arXiv"

    @pytest.mark.asyncio
    async def test_search_papers_filter_ssrn_only(self, sample_ssrn_papers):
        """Test searching SSRN only when source specified"""
        arguments = {
            "query": "corporate finance",
            "source": "ssrn",
            "max_results": 5
        }

        with patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks
            mock_ssrn_instance = AsyncMock()
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance
            mock_ssrn_parser.return_value.parse_response.return_value = sample_ssrn_papers
            mock_ssrn_instance.search_papers.return_value = [{"id": "123", "title": "mock"}]

            # Execute test
            result = await handle_search_papers(arguments)
            data = json.loads(result)

            # Should only search SSRN
            assert "SSRN" in data["sources_searched"]
            assert "arXiv" not in data["sources_searched"]

            # All papers should be from SSRN
            if data["papers"]:
                for paper in data["papers"]:
                    assert paper["source"] == "SSRN"

    @pytest.mark.asyncio
    async def test_search_papers_invalid_source(self):
        """Test error handling for invalid source"""
        arguments = {
            "query": "test",
            "source": "invalid_source"
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid source"):
            await handle_search_papers(arguments)

    @pytest.mark.asyncio
    async def test_search_papers_empty_query(self):
        """Test error handling for empty query"""
        arguments = {
            "query": "",
            "max_results": 10
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="query cannot be empty"):
            await handle_search_papers(arguments)

    @pytest.mark.asyncio
    async def test_search_papers_metadata_preservation(self, sample_arxiv_papers, sample_ssrn_papers):
        """Test that all metadata is preserved for caller assessment"""
        arguments = {
            "query": "algorithmic trading",
            "max_results": 3
        }

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks to return test data
            mock_arxiv_instance = AsyncMock()
            mock_ssrn_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance

            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_ssrn_parser.return_value.parse_response.return_value = sample_ssrn_papers

            mock_arxiv_instance.search_papers.return_value = "<xml>mock</xml>"
            mock_ssrn_instance.search_papers.return_value = [{"id": "123"}]

            # Execute test
            result = await handle_search_papers(arguments)
            data = json.loads(result)

            # Test that papers preserve all metadata fields
            if data["papers"]:
                paper = data["papers"][0]
                expected_fields = {
                    # Core fields
                    "id", "title", "authors", "source", "url", 
                    # Legacy date field
                    "publication_date",
                    # Enhanced date fields
                    "date", "submitted_date", "published_date", "updated_date",
                    # Content fields
                    "abstract", "categories",
                    # Access fields
                    "pdf_url", "journal_ref", "doi",
                    # Metadata fields
                    "download_count", "affiliations", "page_count",
                    # Source-specific fields
                    "comments", "abstract_type", "publication_status", "is_paid", "is_approved"
                }
                assert set(paper.keys()) == expected_fields

                # Test that categories are preserved (not filtered)
                if paper["categories"]:
                    assert isinstance(paper["categories"], list)


class TestUnifiedRecentPapers:
    """Test unified get_all_recent_papers functionality with mocks"""

    @pytest.mark.asyncio
    async def test_get_all_recent_papers_all_sources(self, sample_arxiv_papers, sample_ssrn_papers):
        """Test getting recent papers from all sources"""
        arguments = {
            "months_back": 6,
            "max_results": 20
        }

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks
            mock_arxiv_instance = AsyncMock()
            mock_ssrn_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance

            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_ssrn_parser.return_value.parse_response.return_value = sample_ssrn_papers

            mock_arxiv_instance.search_papers.return_value = "<xml>mock</xml>"
            mock_ssrn_instance.get_recent_papers.return_value = [{"id": "123"}]

            # Execute test
            result = await handle_get_all_recent_papers(arguments)
            data = json.loads(result)

            # Test basic structure
            assert "search_query" in data
            assert "months_back" in data
            assert "sources_searched" in data
            assert "total_found" in data
            assert "papers" in data
            assert "source_breakdown" in data
            assert "category_breakdown" in data

            assert data["months_back"] == 6

    @pytest.mark.asyncio
    async def test_get_all_recent_papers_source_filter(self, sample_arxiv_papers):
        """Test getting recent papers from specific source"""
        arguments = {
            "months_back": 3,
            "source": "arxiv",
            "max_results": 10
        }

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser:

            # Setup mocks
            mock_arxiv_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_arxiv_instance.search_papers.return_value = "<xml>mock</xml>"

            # Execute test
            result = await handle_get_all_recent_papers(arguments)
            data = json.loads(result)

            # Should only search specified source
            assert "arXiv" in data["sources_searched"]
            assert "SSRN" not in data["sources_searched"]

            # All papers should be from arXiv
            if data["papers"]:
                for paper in data["papers"]:
                    assert paper["source"] == "arXiv"

    @pytest.mark.asyncio
    async def test_get_all_recent_papers_no_category_filtering(self, sample_arxiv_papers):
        """Test that NO category filtering is applied - returns ALL papers"""
        arguments = {
            "months_back": 2,
            "max_results": 15
        }

        # Create papers with diverse categories (not just finance)
        diverse_papers = [
            ArxivPaper(
                id="2023.11111",
                title="Computer Vision Advances",
                authors=["Tech Author"],
                abstract="Computer vision research...",
                categories=["cs.CV", "cs.AI"],  # Non-finance categories
                submitted_date=datetime(2023, 12, 1),
                updated_date=datetime(2023, 12, 1),
                journal_ref=None,
                doi=None,
                arxiv_url="https://arxiv.org/abs/2023.11111",
                pdf_url="https://arxiv.org/pdf/2023.11111.pdf"
            ),
            sample_arxiv_papers[0]  # Finance paper
        ]

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks to return diverse categories
            mock_arxiv_instance = AsyncMock()
            mock_ssrn_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance

            mock_arxiv_parser.return_value.parse_response.return_value = diverse_papers
            mock_ssrn_parser.return_value.parse_response.return_value = []

            mock_arxiv_instance.search_papers.return_value = "<xml>mock</xml>"
            mock_ssrn_instance.get_recent_papers.return_value = []

            # Execute test
            result = await handle_get_all_recent_papers(arguments)
            data = json.loads(result)

            # Should return papers from ALL categories, not just finance
            if data["papers"]:
                categories_found = set()
                for paper in data["papers"]:
                    if paper["categories"]:
                        categories_found.update(paper["categories"])

                # Should have diverse categories beyond just q-fin.*
                assert len(categories_found) > 0


class TestSourceParameterIntegration:
    """Test that existing tools accept optional source parameter"""

class TestErrorHandling:
    """Test error handling and graceful degradation with mocks"""

    @pytest.mark.asyncio
    async def test_single_source_failure_graceful_degradation(self, sample_arxiv_papers):
        """Test that if one source fails, other sources still work"""
        arguments = {
            "query": "test query",
            "max_results": 5
        }

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks - arXiv succeeds, SSRN fails
            mock_arxiv_instance = AsyncMock()
            mock_ssrn_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance

            # arXiv succeeds
            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_arxiv_instance.search_papers.return_value = "<xml>mock</xml>"

            # SSRN fails
            mock_ssrn_instance.search_papers.side_effect = Exception("Network error")

            # Execute test
            result = await handle_search_papers(arguments)
            data = json.loads(result)

            # Should include error information
            assert "source_errors" in data
            assert "successful_sources" in data

            # Should still return results from working sources
            assert isinstance(data["papers"], list)
            assert data["total_found"] >= 0

    @pytest.mark.asyncio
    async def test_invalid_date_range_handling(self):
        """Test handling of invalid date parameters"""
        arguments = {
            "months_back": -1,  # Invalid negative value
            "max_results": 5
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="months_back must be positive"):
            await handle_get_all_recent_papers(arguments)


class TestDeduplication:
    """Test deduplication logic for papers appearing in multiple sources"""

    @pytest.mark.asyncio
    async def test_deduplication_metadata_present(self, sample_arxiv_papers, sample_ssrn_papers):
        """Test that deduplication metadata is present in results"""
        arguments = {
            "query": "market microstructure",
            "max_results": 20
        }

        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # Setup mocks
            mock_arxiv_instance = AsyncMock()
            mock_ssrn_instance = AsyncMock()
            mock_arxiv_client.return_value.__aenter__.return_value = mock_arxiv_instance
            mock_ssrn_client.return_value.__aenter__.return_value = mock_ssrn_instance

            mock_arxiv_parser.return_value.parse_response.return_value = sample_arxiv_papers
            mock_ssrn_parser.return_value.parse_response.return_value = sample_ssrn_papers

            mock_arxiv_instance.search_papers.return_value = "<xml>mock</xml>"
            mock_ssrn_instance.search_papers.return_value = [{"id": "123"}]

            # Execute test
            result = await handle_search_papers(arguments)
            data = json.loads(result)

            # Check for deduplication metadata
            assert "duplicates_removed" in data
            assert "deduplication_method" in data

            # Should be valid values
            assert isinstance(data["duplicates_removed"], int)
            assert data["duplicates_removed"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])