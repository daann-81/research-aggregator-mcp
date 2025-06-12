"""
Test Cases for Title-Based Paper Aggregation

This module contains unit tests for aggregating papers with identical titles
to show multiple source availability, following TDD methodology.
"""

import pytest
import json
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import patch

# Import the modules we'll be testing
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.paper import AcademicPaper
from src.server.shared import process_papers


class TestTitleAggregation:
    """Test title-based paper aggregation functionality"""

    def test_aggregate_papers_identical_titles(self):
        """Test aggregating papers with identical titles from different sources"""
        # Create papers with identical titles but different sources
        arxiv_paper = AcademicPaper(
            id="arxiv:2023.12345",
            title="Machine Learning in Finance",
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime(2023, 12, 1),
            source="arXiv",
            url="https://arxiv.org/abs/2023.12345",
            abstract="arXiv abstract...",
            doi="10.1234/example"
        )
        
        ssrn_paper = AcademicPaper(
            id="ssrn:4567890",
            title="Machine Learning in Finance",  # Identical title
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime(2023, 12, 5),
            source="SSRN", 
            url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4567890",
            abstract="SSRN abstract...",
            affiliations=["MIT", "Harvard"]
        )
        
        papers = [arxiv_paper, ssrn_paper]
        
        # This test must FAIL initially - function doesn't exist yet
        aggregated, stats = process_papers(papers, max_results=10)
        
        # Should return one aggregated paper
        assert len(aggregated) == 1
        
        # Aggregated paper should have both sources
        paper = aggregated[0]
        assert isinstance(paper.source, list)
        assert set(paper.source) == {"arXiv", "SSRN"}
        
        # Should preserve metadata from both sources
        assert paper.doi == "10.1234/example"  # From arXiv
        assert paper.affiliations == ["MIT", "Harvard"]  # From SSRN

    def test_aggregate_papers_different_titles(self):
        """Test that papers with different titles are not aggregated"""
        arxiv_paper = AcademicPaper(
            id="arxiv:2023.11111",
            title="Machine Learning in Finance",
            authors=["John Doe"],
            publication_date=datetime(2023, 12, 1),
            source="arXiv",
            url="https://arxiv.org/abs/2023.11111"
        )
        
        ssrn_paper = AcademicPaper(
            id="ssrn:2222222",
            title="Deep Learning for Trading",  # Different title
            authors=["Jane Smith"],
            publication_date=datetime(2023, 12, 5),
            source="SSRN",
            url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2222222"
        )
        
        papers = [arxiv_paper, ssrn_paper]
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        # Should return both papers unchanged
        assert len(aggregated) == 2
        
        # Both papers should have single sources
        for paper in aggregated:
            assert isinstance(paper.source, str)

    def test_title_normalization(self):
        """Test that title normalization works correctly for matching"""
        paper1 = AcademicPaper(
            id="1",
            title="Machine Learning in Finance",
            authors=["Author One"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="http://example.com/1"
        )
        
        paper2 = AcademicPaper(
            id="2", 
            title="  Machine Learning in Finance  ",  # Extra whitespace
            authors=["Author Two"],
            publication_date=datetime(2023, 1, 2),
            source="SSRN",
            url="http://example.com/2"
        )
        
        paper3 = AcademicPaper(
            id="3",
            title="machine learning in finance",  # Different case
            authors=["Author Three"],
            publication_date=datetime(2023, 1, 3),
            source="RePEc",
            url="http://example.com/3"
        )
        
        papers = [paper1, paper2, paper3]
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        # Should aggregate all three due to title normalization
        assert len(aggregated) == 1
        
        paper = aggregated[0]
        assert isinstance(paper.source, list)
        assert len(paper.source) == 3
        assert set(paper.source) == {"arXiv", "SSRN", "RePEc"}

    def test_metadata_merging_strategy(self):
        """Test that metadata is merged correctly when aggregating"""
        # Paper with DOI but no abstract
        paper1 = AcademicPaper(
            id="1",
            title="Test Paper",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="http://example.com/1",
            doi="10.1234/test",
            abstract=None
        )
        
        # Paper with abstract but no DOI
        paper2 = AcademicPaper(
            id="2",
            title="Test Paper",
            authors=["Author"],
            publication_date=datetime(2023, 1, 2),
            source="SSRN", 
            url="http://example.com/2",
            doi=None,
            abstract="This is an abstract"
        )
        
        papers = [paper1, paper2]
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        assert len(aggregated) == 1
        
        paper = aggregated[0]
        # Should have both DOI and abstract
        assert paper.doi == "10.1234/test"
        assert paper.abstract == "This is an abstract"
        assert set(paper.source) == {"arXiv", "SSRN"}

    def test_source_urls_preservation(self):
        """Test that URLs from multiple sources are preserved"""
        paper1 = AcademicPaper(
            id="1",
            title="Multi-Source Paper",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="https://arxiv.org/abs/2023.1111",
            pdf_url="https://arxiv.org/pdf/2023.1111.pdf"
        )
        
        paper2 = AcademicPaper(
            id="2",
            title="Multi-Source Paper",
            authors=["Author"],
            publication_date=datetime(2023, 1, 2),
            source="SSRN",
            url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=123456",
            pdf_url=None
        )
        
        papers = [paper1, paper2]
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        assert len(aggregated) == 1
        
        paper = aggregated[0]
        # Should have source_urls field with both URLs
        assert hasattr(paper, 'source_urls')
        assert paper.source_urls["arXiv"] == "https://arxiv.org/abs/2023.1111"
        assert paper.source_urls["SSRN"] == "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=123456"

    def test_empty_paper_list(self):
        """Test aggregation with empty paper list"""
        papers = []
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        assert aggregated == []

    def test_single_paper(self):
        """Test aggregation with single paper"""
        paper = AcademicPaper(
            id="1",
            title="Single Paper",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="http://example.com/1"
        )
        
        papers = [paper]
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        assert len(aggregated) == 1
        assert aggregated[0].source == "arXiv"  # Should remain string for single source

    def test_aggregation_preserves_most_recent_date(self):
        """Test that aggregation preserves the most recent publication date"""
        older_paper = AcademicPaper(
            id="1",
            title="Date Test Paper",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="http://example.com/1"
        )
        
        newer_paper = AcademicPaper(
            id="2",
            title="Date Test Paper",
            authors=["Author"],
            publication_date=datetime(2023, 6, 1),  # More recent
            source="SSRN",
            url="http://example.com/2"
        )
        
        papers = [older_paper, newer_paper]
        
        # This test must FAIL initially
        aggregated, stats = process_papers(papers, max_results=10)
        
        assert len(aggregated) == 1
        # Should use the more recent date
        assert aggregated[0].publication_date == datetime(2023, 6, 1)

    def test_aggregation_statistics(self):
        """Test that aggregation returns statistics about duplicates found"""
        paper1 = AcademicPaper(
            id="1", title="Paper A", authors=["Author"], 
            publication_date=datetime(2023, 1, 1), source="arXiv", url="http://1"
        )
        paper2 = AcademicPaper(
            id="2", title="Paper A", authors=["Author"],  # Duplicate title
            publication_date=datetime(2023, 1, 2), source="SSRN", url="http://2"
        )
        paper3 = AcademicPaper(
            id="3", title="Paper B", authors=["Author"],  # Unique title
            publication_date=datetime(2023, 1, 3), source="arXiv", url="http://3"
        )
        
        papers = [paper1, paper2, paper3]
        
        # This test must FAIL initially - need to return statistics
        aggregated, stats = process_papers(papers, max_results=10)
        
        assert len(aggregated) == 2  # Two unique titles
        assert stats["duplicates_removed"] == 1  # One duplicate found
        assert stats["aggregation_method"] == "title_normalization"


class TestIntegrationWithUnifiedSearch:
    """Test integration of title aggregation with unified search handlers"""

    @pytest.mark.asyncio
    async def test_unified_search_uses_title_aggregation(self):
        """Test that unified search uses title aggregation instead of no deduplication"""
        from src.server.shared import handle_search_papers
        
        # Mock the API calls to return papers with duplicate titles
        with patch('src.server.shared.AsyncArxivClient') as mock_arxiv_client, \
             patch('src.server.shared.AsyncSSRNClient') as mock_ssrn_client, \
             patch('src.server.shared.ArxivXMLParser') as mock_arxiv_parser, \
             patch('src.server.shared.SSRNJSONParser') as mock_ssrn_parser:

            # This test must FAIL initially - unified search doesn't use aggregation yet
            arguments = {
                "query": "test query",
                "max_results": 10
            }
            
            result = await handle_search_papers(arguments)
            data = json.loads(result)
            
            # Should show title_normalization method instead of "none"
            assert data["deduplication_method"] == "title_normalization"
            
            # Should have duplicates_removed count
            assert "duplicates_removed" in data
            assert isinstance(data["duplicates_removed"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])