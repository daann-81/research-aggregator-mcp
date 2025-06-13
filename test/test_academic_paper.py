"""
Unit Tests for AcademicPaper Dataclass

This module contains comprehensive unit tests for the AcademicPaper dataclass,
testing its creation, validation, serialization, and utility methods.
"""

import pytest
import json
from datetime import datetime
from typing import List, Optional

# Import the paper classes we'll be testing
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.paper import AcademicPaper


class TestAcademicPaperCreation:
    """Test AcademicPaper dataclass creation and initialization"""
    
    def test_academic_paper_with_required_fields_only(self):
        """Test creating AcademicPaper with only required fields"""
        paper = AcademicPaper(
            id="test123",
            title="Test Paper Title",
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime(2023, 12, 15, 18, 30, 45),
            source="arXiv",
            url="https://example.com/paper"
        )
        
        # Test required fields
        assert paper.id == "test123"
        assert paper.title == "Test Paper Title"
        assert paper.authors == ["John Doe", "Jane Smith"]
        assert paper.publication_date == datetime(2023, 12, 15, 18, 30, 45)
        assert paper.source == "arXiv"
        assert paper.url == "https://example.com/paper"
        
        # Test optional fields default to None
        assert paper.abstract is None
        assert paper.categories is None
        assert paper.pdf_url is None
        assert paper.journal_ref is None
        assert paper.doi is None
        assert paper.download_count is None
        assert paper.affiliations is None

    def test_academic_paper_with_all_fields(self):
        """Test creating AcademicPaper with all fields populated"""
        paper = AcademicPaper(
            id="arxiv123",
            title="Complete Academic Paper",
            authors=["Alice Johnson", "Bob Wilson", "Charlie Brown"],
            publication_date=datetime(2023, 11, 20, 10, 15, 30),
            source="arXiv",
            url="https://arxiv.org/abs/arxiv123",
            abstract="This is a comprehensive test abstract for the paper.",
            categories=["q-fin.TR", "cs.LG", "stat.ML"],
            pdf_url="https://arxiv.org/pdf/arxiv123.pdf",
            journal_ref="Journal of Test Studies, 2023",
            doi="10.1234/test.2023.123",
            download_count=1500,
            affiliations=["MIT", "Stanford", "Harvard"]
        )
        
        # Test all fields are set correctly
        assert paper.id == "arxiv123"
        assert paper.title == "Complete Academic Paper"
        assert paper.authors == ["Alice Johnson", "Bob Wilson", "Charlie Brown"]
        assert paper.publication_date == datetime(2023, 11, 20, 10, 15, 30)
        assert paper.source == "arXiv"
        assert paper.url == "https://arxiv.org/abs/arxiv123"
        assert paper.abstract == "This is a comprehensive test abstract for the paper."
        assert paper.categories == ["q-fin.TR", "cs.LG", "stat.ML"]
        assert paper.pdf_url == "https://arxiv.org/pdf/arxiv123.pdf"
        assert paper.journal_ref == "Journal of Test Studies, 2023"
        assert paper.doi == "10.1234/test.2023.123"
        assert paper.download_count == 1500
        assert paper.affiliations == ["MIT", "Stanford", "Harvard"]

    def test_academic_paper_with_empty_optional_lists(self):
        """Test creating AcademicPaper with empty lists for optional fields"""
        paper = AcademicPaper(
            id="empty123",
            title="Paper with Empty Lists",
            authors=["Solo Author"],
            publication_date=datetime(2023, 10, 1),
            source="SSRN",
            url="https://ssrn.com/abstract=empty123",
            categories=[],  # Empty list
            affiliations=[]  # Empty list
        )
        
        assert paper.categories == []
        assert paper.affiliations == []
        assert paper.abstract is None  # Still None


class TestAcademicPaperSerialization:
    """Test JSON serialization and dictionary conversion"""
    
    def setup_method(self):
        """Set up test data"""
        self.test_paper = AcademicPaper(
            id="serialize123",
            title="Serialization Test Paper",
            authors=["Test Author One", "Test Author Two"],
            publication_date=datetime(2023, 12, 25, 14, 30, 0),
            source="arXiv",
            url="https://arxiv.org/abs/serialize123",
            abstract="Test abstract for serialization.",
            categories=["cs.LG", "stat.ML"],
            pdf_url="https://arxiv.org/pdf/serialize123.pdf",
            journal_ref="Test Journal 2023",
            doi="10.1234/serialize.2023",
            download_count=750,
            affiliations=["Test University", "Another Institution"]
        )

    def test_to_dict_with_all_fields(self):
        """Test to_dict method with all fields populated"""
        result = self.test_paper.to_dict()
        
        expected = {
            "id": "serialize123",
            "title": "Serialization Test Paper",
            "authors": ["Test Author One", "Test Author Two"],
            "abstract": "Test abstract for serialization.",
            "publication_date": "2023-12-25T14:30:00",
            "source": "arXiv",
            "categories": ["cs.LG", "stat.ML"],
            "url": "https://arxiv.org/abs/serialize123",
            "pdf_url": "https://arxiv.org/pdf/serialize123.pdf",
            "journal_ref": "Test Journal 2023",
            "doi": "10.1234/serialize.2023",
            "download_count": 750,
            "affiliations": ["Test University", "Another Institution"],
            # Enhanced date fields
            "date": "2023-12-25T14:30:00",  # Falls back to publication_date
            "submitted_date": None,
            "published_date": None,
            "updated_date": None,
            # New metadata fields
            "page_count": None,
            # Source-specific fields
            "comments": None,
            "abstract_type": None,
            "publication_status": None,
            "is_paid": None,
            "is_approved": None
        }
        
        assert result == expected

    def test_to_dict_with_minimal_fields(self):
        """Test to_dict method with only required fields"""
        minimal_paper = AcademicPaper(
            id="minimal123",
            title="Minimal Paper",
            authors=["Single Author"],
            publication_date=datetime(2023, 1, 1, 12, 0, 0),
            source="SSRN",
            url="https://ssrn.com/abstract=minimal123"
        )
        
        result = minimal_paper.to_dict()
        
        expected = {
            "id": "minimal123",
            "title": "Minimal Paper",
            "authors": ["Single Author"],
            "abstract": None,
            "publication_date": "2023-01-01T12:00:00",
            "source": "SSRN",
            "categories": None,
            "url": "https://ssrn.com/abstract=minimal123",
            "pdf_url": None,
            "journal_ref": None,
            "doi": None,
            "download_count": None,
            "affiliations": None,
            # Enhanced date fields
            "date": "2023-01-01T12:00:00",  # Falls back to publication_date
            "submitted_date": None,
            "published_date": None,
            "updated_date": None,
            # New metadata fields
            "page_count": None,
            # Source-specific fields
            "comments": None,
            "abstract_type": None,
            "publication_status": None,
            "is_paid": None,
            "is_approved": None
        }
        
        assert result == expected

    def test_json_serialization(self):
        """Test that to_dict output can be JSON serialized"""
        result_dict = self.test_paper.to_dict()
        
        # Should not raise an exception
        json_string = json.dumps(result_dict, indent=2)
        
        # Should be able to parse back
        parsed = json.loads(json_string)
        
        assert parsed["id"] == "serialize123"
        assert parsed["title"] == "Serialization Test Paper"
        assert parsed["publication_date"] == "2023-12-25T14:30:00"
        assert isinstance(parsed["authors"], list)
        assert len(parsed["authors"]) == 2

    def test_dict_contains_all_expected_keys(self):
        """Test that to_dict always includes all expected keys"""
        minimal_paper = AcademicPaper(
            id="keys123",
            title="Key Test",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="https://example.com"
        )
        
        result = minimal_paper.to_dict()
        
        expected_keys = {
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
        
        assert set(result.keys()) == expected_keys


class TestAcademicPaperStringRepresentation:
    """Test string representation methods"""
    
    def test_str_with_few_authors(self):
        """Test __str__ method with 3 or fewer authors"""
        paper = AcademicPaper(
            id="str123",
            title="String Representation Test",
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime(2023, 6, 15),
            source="arXiv",
            url="https://example.com"
        )
        
        result = str(paper)
        expected = "arXiv Paper: String Representation Test by John Doe, Jane Smith (2023)"
        print(result)  # For debugging purposes
        print(expected)
        assert result == expected

    def test_str_with_many_authors(self):
        """Test __str__ method with more than 3 authors"""
        paper = AcademicPaper(
            id="many123",
            title="Paper with Many Authors",
            authors=["Author One", "Author Two", "Author Three", "Author Four", "Author Five"],
            publication_date=datetime(2023, 8, 20),
            source="SSRN",
            url="https://example.com"
        )
        
        result = str(paper)
        expected = "SSRN Paper: Paper with Many Authors by Author One, Author Two, Author Three et al. (5 total) (2023)"
        
        assert result == expected

    def test_str_with_single_author(self):
        """Test __str__ method with single author"""
        paper = AcademicPaper(
            id="single123",
            title="Single Author Paper",
            authors=["Solo Author"],
            publication_date=datetime(2022, 12, 31),
            source="arXiv",
            url="https://example.com"
        )
        
        result = str(paper)
        expected = "arXiv Paper: Single Author Paper by Solo Author (2022)"
        
        assert result == expected

    def test_str_with_long_title(self):
        """Test __str__ method with very long title"""
        long_title = "A Very Long Title That Exceeds Normal Length Parameters for Academic Papers in Computer Science and Finance"
        paper = AcademicPaper(
            id="long123",
            title=long_title,
            authors=["Test Author"],
            publication_date=datetime(2023, 5, 10),
            source="arXiv",
            url="https://example.com"
        )
        
        result = str(paper)
        expected = f"arXiv Paper: {long_title} by Test Author (2023)"
        
        assert result == expected


class TestAcademicPaperEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_authors_list(self):
        """Test with empty authors list"""
        paper = AcademicPaper(
            id="empty_authors",
            title="No Authors Paper",
            authors=[],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="https://example.com"
        )
        
        assert paper.authors == []
        
        # String representation should handle empty authors gracefully
        result = str(paper)
        expected = "arXiv Paper: No Authors Paper by  (2023)"
        assert result == expected

    def test_very_large_download_count(self):
        """Test with very large download count"""
        paper = AcademicPaper(
            id="large_downloads",
            title="Popular Paper",
            authors=["Popular Author"],
            publication_date=datetime(2023, 1, 1),
            source="SSRN",
            url="https://example.com",
            download_count=999999999
        )
        
        assert paper.download_count == 999999999
        
        # Should serialize correctly
        result_dict = paper.to_dict()
        assert result_dict["download_count"] == 999999999

    def test_zero_download_count(self):
        """Test with zero download count"""
        paper = AcademicPaper(
            id="zero_downloads",
            title="New Paper",
            authors=["New Author"],
            publication_date=datetime(2023, 12, 31),
            source="SSRN",
            url="https://example.com",
            download_count=0
        )
        
        assert paper.download_count == 0
        
        result_dict = paper.to_dict()
        assert result_dict["download_count"] == 0

    def test_future_publication_date(self):
        """Test with future publication date"""
        future_date = datetime(2025, 12, 31, 23, 59, 59)
        paper = AcademicPaper(
            id="future123",
            title="Future Paper",
            authors=["Time Traveler"],
            publication_date=future_date,
            source="arXiv",
            url="https://example.com"
        )
        
        assert paper.publication_date == future_date
        
        result_dict = paper.to_dict()
        assert result_dict["publication_date"] == "2025-12-31T23:59:59"

    def test_empty_string_fields(self):
        """Test behavior with empty string values"""
        paper = AcademicPaper(
            id="empty_strings",
            title="Empty Fields Test",
            authors=["Test Author"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="https://example.com",
            abstract="",  # Empty string
            journal_ref="",  # Empty string
            doi=""  # Empty string
        )
        
        # Empty strings should be preserved (not converted to None)
        assert paper.abstract == ""
        assert paper.journal_ref == ""
        assert paper.doi == ""
        
        result_dict = paper.to_dict()
        assert result_dict["abstract"] == ""
        assert result_dict["journal_ref"] == ""
        assert result_dict["doi"] == ""


class TestAcademicPaperTypes:
    """Test type validation and consistency"""
    
    def test_required_field_types(self):
        """Test that required fields have correct types"""
        paper = AcademicPaper(
            id="types123",
            title="Type Test Paper",
            authors=["Author One", "Author Two"],
            publication_date=datetime(2023, 6, 1, 14, 30, 45),
            source="arXiv",
            url="https://arxiv.org/abs/types123"
        )
        
        assert isinstance(paper.id, str)
        assert isinstance(paper.title, str)
        assert isinstance(paper.authors, list)
        assert all(isinstance(author, str) for author in paper.authors)
        assert isinstance(paper.publication_date, datetime)
        assert isinstance(paper.source, str)
        assert isinstance(paper.url, str)

    def test_optional_field_types_when_set(self):
        """Test that optional fields have correct types when populated"""
        paper = AcademicPaper(
            id="optional_types",
            title="Optional Types Test",
            authors=["Test Author"],
            publication_date=datetime(2023, 1, 1),
            source="SSRN",
            url="https://example.com",
            abstract="Test abstract",
            categories=["cat1", "cat2"],
            pdf_url="https://example.com/pdf",
            journal_ref="Test Journal",
            doi="10.1234/test",
            download_count=100,
            affiliations=["Institution A", "Institution B"]
        )
        
        assert isinstance(paper.abstract, str)
        assert isinstance(paper.categories, list)
        assert all(isinstance(cat, str) for cat in paper.categories)
        assert isinstance(paper.pdf_url, str)
        assert isinstance(paper.journal_ref, str)
        assert isinstance(paper.doi, str)
        assert isinstance(paper.download_count, int)
        assert isinstance(paper.affiliations, list)
        assert all(isinstance(aff, str) for aff in paper.affiliations)

    def test_dataclass_equality(self):
        """Test that two identical AcademicPaper objects are equal"""
        paper1 = AcademicPaper(
            id="equal123",
            title="Equality Test",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1, 12, 0, 0),
            source="arXiv",
            url="https://example.com"
        )
        
        paper2 = AcademicPaper(
            id="equal123",
            title="Equality Test",
            authors=["Author"],
            publication_date=datetime(2023, 1, 1, 12, 0, 0),
            source="arXiv",
            url="https://example.com"
        )
        
        assert paper1 == paper2

    def test_dataclass_inequality(self):
        """Test that different AcademicPaper objects are not equal"""
        paper1 = AcademicPaper(
            id="different123",
            title="Paper One",
            authors=["Author One"],
            publication_date=datetime(2023, 1, 1),
            source="arXiv",
            url="https://example.com/1"
        )
        
        paper2 = AcademicPaper(
            id="different456",
            title="Paper Two",
            authors=["Author Two"],
            publication_date=datetime(2023, 1, 2),
            source="SSRN",
            url="https://example.com/2"
        )
        
        assert paper1 != paper2


if __name__ == "__main__":
    pytest.main([__file__])