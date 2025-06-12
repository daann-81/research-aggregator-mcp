"""
Test to verify that process_papers correctly sorts papers by publication date (most recent first)
"""

import pytest
from datetime import datetime
from src.common.paper import AcademicPaper
from src.server.shared import process_papers


def test_papers_sorted_by_most_recent_first():
    """Test that papers are sorted by publication date with most recent first"""
    # Create papers with different publication dates
    old_paper = AcademicPaper(
        id="1",
        title="Old Paper",
        authors=["Author One"],
        publication_date=datetime(2020, 1, 1),
        source="arXiv",
        url="http://example.com/1"
    )
    
    recent_paper = AcademicPaper(
        id="2",
        title="Recent Paper",
        authors=["Author Two"],
        publication_date=datetime(2023, 12, 1),
        source="arXiv",
        url="http://example.com/2"
    )
    
    middle_paper = AcademicPaper(
        id="3",
        title="Middle Paper",
        authors=["Author Three"],
        publication_date=datetime(2022, 6, 1),
        source="arXiv",
        url="http://example.com/3"
    )
    
    # Input papers in random order
    papers = [old_paper, recent_paper, middle_paper]
    
    # Process papers
    processed_papers, stats = process_papers(papers, max_results=10)
    
    # Verify papers are sorted by date (most recent first)
    assert len(processed_papers) == 3
    assert processed_papers[0].publication_date == datetime(2023, 12, 1)  # Most recent
    assert processed_papers[1].publication_date == datetime(2022, 6, 1)   # Middle
    assert processed_papers[2].publication_date == datetime(2020, 1, 1)   # Oldest


def test_max_results_applied_after_sorting():
    """Test that max_results is applied after sorting, keeping the most recent papers"""
    papers = []
    expected_dates = []
    
    # Create 5 papers with different dates
    for i in range(5):
        date = datetime(2020 + i, 1, 1)
        expected_dates.append(date)
        paper = AcademicPaper(
            id=str(i),
            title=f"Paper {i}",
            authors=[f"Author {i}"],
            publication_date=date,
            source="arXiv",
            url=f"http://example.com/{i}"
        )
        papers.append(paper)
    
    # Process with max_results=3 (should keep 3 most recent)
    processed_papers, stats = process_papers(papers, max_results=3)
    
    # Should return only 3 papers, and they should be the 3 most recent
    assert len(processed_papers) == 3
    assert stats["total_before_limit"] == 5  # All 5 papers before limiting
    
    # Should be sorted most recent first: 2024, 2023, 2022
    assert processed_papers[0].publication_date == datetime(2024, 1, 1)
    assert processed_papers[1].publication_date == datetime(2023, 1, 1)
    assert processed_papers[2].publication_date == datetime(2022, 1, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])