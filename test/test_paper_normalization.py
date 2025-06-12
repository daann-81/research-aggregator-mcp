"""
Test Cases for Paper Normalization

This module contains comprehensive test cases for converting ArxivPaper and SSRNPaper
objects to the unified AcademicPaper format. These tests drive the implementation
of the normalization functions.
"""

import pytest
from datetime import datetime
from typing import List, Optional

# Import the paper classes we'll be testing conversion from
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.arxiv.parser import ArxivPaper
from src.ssrn.parser import SSRNPaper
from src.common.paper import AcademicPaper, from_arxiv_paper, from_ssrn_paper


class TestArxivToAcademicPaper:
    """Test conversion from ArxivPaper to AcademicPaper"""
    
    def setup_method(self):
        """Set up test data for ArxivPaper conversion tests"""
        # Complete ArxivPaper with all fields
        self.complete_arxiv_paper = ArxivPaper(
            id="2312.12345",
            title="Machine Learning in Quantitative Finance: A Survey",
            authors=["John Smith", "Jane Doe", "Bob Wilson"],
            abstract="This paper provides a comprehensive survey of machine learning applications in quantitative finance...",
            submitted_date=datetime(2023, 12, 15, 18, 30, 45),
            updated_date=datetime(2023, 12, 16, 10, 15, 30),
            categories=["q-fin.TR", "cs.LG", "stat.ML"],
            pdf_url="http://arxiv.org/pdf/2312.12345v1.pdf",
            arxiv_url="http://arxiv.org/abs/2312.12345",
            journal_ref="Journal of Financial Technology, 2024",
            doi="10.1234/jft.2024.12345",
            comments="25 pages, 8 figures, accepted at FinTech 2024"
        )
        
        # Minimal ArxivPaper with only required fields
        self.minimal_arxiv_paper = ArxivPaper(
            id="2312.54321",
            title="Minimal Paper",
            authors=["Single Author"],
            abstract="Short abstract.",
            submitted_date=datetime(2023, 12, 20, 12, 0, 0),
            updated_date=datetime(2023, 12, 20, 12, 0, 0),
            categories=["q-fin.MF"],
            pdf_url="http://arxiv.org/pdf/2312.54321v1.pdf",
            arxiv_url="http://arxiv.org/abs/2312.54321",
            journal_ref=None,
            doi=None,
            comments=None
        )
        
        # ArxivPaper with edge cases
        self.edge_case_arxiv_paper = ArxivPaper(
            id="2312.99999",
            title="  Title with Extra   Whitespace  ",
            authors=["", "Author With Spaces", ""],  # Empty strings in list
            abstract="Abstract\nwith\nnewlines\tand\ttabs",
            submitted_date=datetime(2023, 12, 31, 23, 59, 59),
            updated_date=datetime(2024, 1, 1, 0, 0, 1),
            categories=["q-fin.TR", "", "cs.LG"],  # Empty category
            pdf_url="",  # Empty URL
            arxiv_url="http://arxiv.org/abs/2312.99999",
            journal_ref="",  # Empty string instead of None
            doi="",
            comments=""
        )

    def test_arxiv_to_academic_paper_complete_fields(self):
        """Test conversion of ArxivPaper with all fields populated"""
        academic_paper = from_arxiv_paper(self.complete_arxiv_paper)
        
        # Test all field mappings
        assert academic_paper.id == "2312.12345"
        assert academic_paper.title == "Machine Learning in Quantitative Finance: A Survey"
        assert academic_paper.authors == ["John Smith", "Jane Doe", "Bob Wilson"]
        assert academic_paper.abstract == "This paper provides a comprehensive survey of machine learning applications in quantitative finance..."
        assert academic_paper.publication_date == datetime(2023, 12, 15, 18, 30, 45)
        assert academic_paper.source == "arXiv"
        assert academic_paper.categories == ["q-fin.TR", "cs.LG", "stat.ML"]
        assert academic_paper.url == "http://arxiv.org/abs/2312.12345"
        assert academic_paper.pdf_url == "http://arxiv.org/pdf/2312.12345v1.pdf"
        assert academic_paper.journal_ref == "Journal of Financial Technology, 2024"
        assert academic_paper.doi == "10.1234/jft.2024.12345"
        assert academic_paper.download_count is None  # arXiv doesn't provide this
        assert academic_paper.affiliations is None  # arXiv doesn't provide this

    def test_arxiv_to_academic_paper_minimal_fields(self):
        """Test conversion of ArxivPaper with only required fields"""
        academic_paper = from_arxiv_paper(self.minimal_arxiv_paper)
        
        # Test required fields
        assert academic_paper.id == "2312.54321"
        assert academic_paper.title == "Minimal Paper"
        assert academic_paper.authors == ["Single Author"]
        assert academic_paper.abstract == "Short abstract."
        assert academic_paper.publication_date == datetime(2023, 12, 20, 12, 0, 0)
        assert academic_paper.source == "arXiv"
        assert academic_paper.categories == ["q-fin.MF"]
        assert academic_paper.url == "http://arxiv.org/abs/2312.54321"
        assert academic_paper.pdf_url == "http://arxiv.org/pdf/2312.54321v1.pdf"
        
        # Test optional fields are None
        assert academic_paper.journal_ref is None
        assert academic_paper.doi is None
        assert academic_paper.download_count is None
        assert academic_paper.affiliations is None

    def test_arxiv_to_academic_paper_edge_cases(self):
        """Test conversion with edge cases and data cleaning"""
        
        academic_paper = from_arxiv_paper(self.edge_case_arxiv_paper)
        
        # Test data cleaning
        assert academic_paper.title == "Title with Extra Whitespace"  # Cleaned whitespace
        assert academic_paper.authors == ["Author With Spaces"]  # Empty strings removed
        assert "Abstract with newlines and tabs" in academic_paper.abstract  # Normalized whitespace
        assert academic_paper.categories == ["q-fin.TR", "cs.LG"]  # Empty category removed
        assert academic_paper.pdf_url is None  # Empty string converted to None
        assert academic_paper.journal_ref is None  # Empty string converted to None
        assert academic_paper.doi is None  # Empty string converted to None

    def test_arxiv_to_academic_paper_invalid_data(self):
        """Test conversion with invalid or corrupted data"""
        # Test with None values where they shouldn't be
        invalid_paper = ArxivPaper(
            id=None,  # Required field is None
            title="Valid Title",
            authors=["Valid Author"],
            abstract="Valid abstract",
            submitted_date=datetime.now(),
            updated_date=datetime.now(),
            categories=["q-fin.TR"],
            pdf_url="http://valid.url",
            arxiv_url="http://valid.url"
        )
        
        # Should raise ValueError for missing required field
        with pytest.raises(ValueError, match="id cannot be None or empty"):
            from_arxiv_paper(invalid_paper)

    def test_arxiv_to_academic_paper_type_validation(self):
        """Test that converted AcademicPaper has correct types"""
        academic_paper = from_arxiv_paper(self.complete_arxiv_paper)
        
        # Test types
        assert isinstance(academic_paper.id, str)
        assert isinstance(academic_paper.title, str)
        assert isinstance(academic_paper.authors, list)
        assert all(isinstance(author, str) for author in academic_paper.authors)
        assert isinstance(academic_paper.abstract, str)
        assert isinstance(academic_paper.publication_date, datetime)
        assert isinstance(academic_paper.source, str)
        assert isinstance(academic_paper.categories, list)
        assert all(isinstance(cat, str) for cat in academic_paper.categories)
        assert isinstance(academic_paper.url, str)
        assert academic_paper.pdf_url is None or isinstance(academic_paper.pdf_url, str)


class TestSSRNToAcademicPaper:
    """Test conversion from SSRNPaper to AcademicPaper"""
    
    def setup_method(self):
        """Set up test data for SSRNPaper conversion tests"""
        # Complete SSRNPaper with all fields
        self.complete_ssrn_paper = SSRNPaper(
            ssrn_id="4567890",
            title="Corporate Finance and Market Dynamics",
            authors=["Alice Johnson", "Charlie Brown"],
            approved_date=datetime(2023, 11, 20, 0, 0, 0),
            download_count=1250,
            ssrn_url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4567890",
            university_affiliations=["Harvard Business School", "MIT Sloan"],
            abstract_type="Working Paper",
            publication_status="Published",
            is_paid=False,
            page_count=45,
            is_approved=True,
            reference="Johnson, A., & Brown, C. (2023). Corporate Finance and Market Dynamics."
        )
        
        # Minimal SSRNPaper with only required fields
        self.minimal_ssrn_paper = SSRNPaper(
            ssrn_id="1234567",
            title="Minimal SSRN Paper",
            authors=["Solo Author"],
            approved_date=datetime(2023, 10, 15, 0, 0, 0),
            download_count=0,
            ssrn_url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1234567",
            university_affiliations=[],
            abstract_type="",
            publication_status="Draft",
            is_paid=False,
            page_count=0,
            is_approved=True,
            reference=None
        )
        
        # SSRNPaper with edge cases
        self.edge_case_ssrn_paper = SSRNPaper(
            ssrn_id="9999999",
            title="  SSRN Title with <b>HTML</b> &amp; Entities  ",
            authors=["Author One", "", "Author Two"],  # Empty string in authors
            approved_date=datetime(2023, 12, 25, 0, 0, 0),
            download_count=-1,  # Invalid download count
            ssrn_url="",  # Empty URL
            university_affiliations=["", "Valid University", ""],  # Empty affiliations
            abstract_type="",
            publication_status="",
            is_paid=True,
            page_count=0,
            is_approved=False,
            reference=""
        )

    def test_ssrn_to_academic_paper_complete_fields(self):
        """Test conversion of SSRNPaper with all fields populated"""
        
        academic_paper = from_ssrn_paper(self.complete_ssrn_paper)
        
        # Test all field mappings
        assert academic_paper.id == "4567890"
        assert academic_paper.title == "Corporate Finance and Market Dynamics"
        assert academic_paper.authors == ["Alice Johnson", "Charlie Brown"]
        assert academic_paper.abstract is None  # SSRN doesn't provide abstracts
        assert academic_paper.publication_date == datetime(2023, 11, 20, 0, 0, 0)
        assert academic_paper.source == "SSRN"
        assert academic_paper.categories is None  # SSRN doesn't provide categories
        assert academic_paper.url == "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4567890"
        assert academic_paper.pdf_url is None  # SSRN doesn't provide direct PDF URLs
        assert academic_paper.journal_ref == "Johnson, A., & Brown, C. (2023). Corporate Finance and Market Dynamics."
        assert academic_paper.doi is None  # SSRN papers typically don't have DOIs
        assert academic_paper.download_count == 1250
        assert academic_paper.affiliations == ["Harvard Business School", "MIT Sloan"]

    def test_ssrn_to_academic_paper_minimal_fields(self):
        """Test conversion of SSRNPaper with minimal fields"""
        
        academic_paper = from_ssrn_paper(self.minimal_ssrn_paper)
        
        # Test required fields
        assert academic_paper.id == "1234567"
        assert academic_paper.title == "Minimal SSRN Paper"
        assert academic_paper.authors == ["Solo Author"]
        assert academic_paper.abstract is None
        assert academic_paper.publication_date == datetime(2023, 10, 15, 0, 0, 0)
        assert academic_paper.source == "SSRN"
        assert academic_paper.url == "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1234567"
        
        # Test optional fields
        assert academic_paper.categories is None
        assert academic_paper.pdf_url is None
        assert academic_paper.journal_ref is None  # Empty reference becomes None
        assert academic_paper.doi is None
        assert academic_paper.download_count == 0
        assert academic_paper.affiliations == []  # Empty list preserved

    def test_ssrn_to_academic_paper_edge_cases(self):
        """Test conversion with edge cases and data cleaning"""
        
        academic_paper = from_ssrn_paper(self.edge_case_ssrn_paper)
        
        # Test data cleaning
        assert academic_paper.title == "SSRN Title with HTML & Entities"  # HTML cleaned
        assert academic_paper.authors == ["Author One", "Author Two"]  # Empty strings removed
        assert academic_paper.download_count == 0  # Negative count normalized to 0
        assert academic_paper.url is None or academic_paper.url.startswith("https://")  # Empty URL handled
        assert academic_paper.affiliations == ["Valid University"]  # Empty affiliations removed

    def test_ssrn_to_academic_paper_author_format_conversion(self):
        """Test conversion of SSRN author format to standard format"""
        
        # Test with author objects (SSRN API format) - note: this would be raw data before parsing
        # For now, test with already parsed author strings
        ssrn_paper_with_author_objects = SSRNPaper(
            ssrn_id="1111111",
            title="Test Paper",
            authors=["John Smith", "Jane Doe", "OnlyLastName"],  # Already parsed format
            approved_date=datetime(2023, 1, 1),
            download_count=100,
            ssrn_url="https://example.com",
            university_affiliations=[],
            abstract_type="",
            publication_status="",
            is_paid=False,
            page_count=0,
            is_approved=True,
            reference=None
        )
        
        academic_paper = from_ssrn_paper(ssrn_paper_with_author_objects)
        assert academic_paper.authors == ["John Smith", "Jane Doe", "OnlyLastName"]

    def test_ssrn_to_academic_paper_invalid_data(self):
        """Test conversion with invalid or corrupted data"""
        
        # Test with None values where they shouldn't be
        invalid_paper = SSRNPaper(
            ssrn_id=None,  # Required field is None
            title="Valid Title",
            authors=["Valid Author"],
            approved_date=datetime.now(),
            download_count=0,
            ssrn_url="https://valid.url",
            university_affiliations=[],
            abstract_type="",
            publication_status="",
            is_paid=False,
            page_count=0,
            is_approved=True,
            reference=None
        )
        
        # Should raise ValueError for missing required field
        with pytest.raises(ValueError, match="ssrn_id cannot be None or empty"):
            from_ssrn_paper(invalid_paper)

    def test_ssrn_to_academic_paper_type_validation(self):
        """Test that converted AcademicPaper has correct types"""
        
        academic_paper = from_ssrn_paper(self.complete_ssrn_paper)
        
        # Test types
        assert isinstance(academic_paper.id, str)
        assert isinstance(academic_paper.title, str)
        assert isinstance(academic_paper.authors, list)
        assert all(isinstance(author, str) for author in academic_paper.authors)
        assert academic_paper.abstract is None  # SSRN specific
        assert isinstance(academic_paper.publication_date, datetime)
        assert isinstance(academic_paper.source, str)
        assert academic_paper.categories is None  # SSRN specific
        assert isinstance(academic_paper.url, str)
        assert academic_paper.pdf_url is None  # SSRN specific


class TestNormalizationHelpers:
    """Test helper functions used in normalization"""
    
    def test_clean_title_function(self):
        """Test title cleaning helper function"""
        
        from src.common.paper import _clean_title
        
        # Test HTML cleaning
        assert _clean_title("Title with <b>bold</b> &amp; entities") == "Title with bold & entities"
        
        # Test whitespace normalization
        assert _clean_title("  Title   with   spaces  ") == "Title with spaces"
        
        # Test newline and tab handling
        assert _clean_title("Title\nwith\nnewlines\tand\ttabs") == "Title with newlines and tabs"

    def test_clean_authors_function(self):
        """Test authors list cleaning helper function"""
        
        from src.common.paper import _clean_authors
        
        # Test empty string removal
        assert _clean_authors(["Author One", "", "Author Two", ""]) == ["Author One", "Author Two"]
        
        # Test whitespace cleaning
        assert _clean_authors(["  Author  ", "\tAnother\n"]) == ["Author", "Another"]
        
        # Test empty list handling
        assert _clean_authors([]) == []
        assert _clean_authors(["", "", ""]) == []

    def test_normalize_url_function(self):
        """Test URL normalization helper function"""
        
        from src.common.paper import _normalize_url
        
        # Test empty string to None conversion
        assert _normalize_url("") is None
        assert _normalize_url("   ") is None
        
        # Test valid URL preservation
        assert _normalize_url("https://example.com") == "https://example.com"
        
        # Test whitespace trimming
        assert _normalize_url("  https://example.com  ") == "https://example.com"

    def test_safe_int_conversion(self):
        """Test safe integer conversion for download counts"""
        
        from src.common.paper import _safe_int
        
        # Test normal conversion
        assert _safe_int(100) == 100
        assert _safe_int("100") == 100
        
        # Test negative number handling
        assert _safe_int(-1) == 0
        
        # Test invalid input handling
        assert _safe_int("invalid") == 0
        assert _safe_int(None) == 0


if __name__ == "__main__":
    pytest.main([__file__])