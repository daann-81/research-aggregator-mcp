"""
Tests for enhanced AcademicPaper with complete field set and date logic.

This test suite follows strict TDD methodology - all tests must initially FAIL
to prove they're testing the expected behavior before implementation.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# Import the current classes
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.paper import AcademicPaper, from_arxiv_paper, from_ssrn_paper
from src.arxiv.parser import ArxivPaper
from src.ssrn.parser import SSRNPaper


class TestAcademicPaperFieldMapping:
    """Test that AcademicPaper has all fields from both source types."""
    
    def test_has_all_arxiv_specific_fields(self):
        """Test that AcademicPaper has all ArxivPaper-specific fields."""
        # These fields should exist in AcademicPaper but currently don't
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"],
            publication_date=datetime.now(),
            source="test",
            url="test"
        )
        
        # Test ArxivPaper-specific fields exist
        assert hasattr(paper, 'submitted_date'), "submitted_date field missing"
        assert hasattr(paper, 'updated_date'), "updated_date field missing"
        assert hasattr(paper, 'comments'), "comments field missing"
        
    def test_has_all_ssrn_specific_fields(self):
        """Test that AcademicPaper has all SSRNPaper-specific fields."""
        paper = AcademicPaper(
            id="test",
            title="test", 
            authors=["test"],
            publication_date=datetime.now(),
            source="test",
            url="test"
        )
        
        # Test SSRNPaper-specific fields exist
        assert hasattr(paper, 'abstract_type'), "abstract_type field missing"
        assert hasattr(paper, 'publication_status'), "publication_status field missing"
        assert hasattr(paper, 'is_paid'), "is_paid field missing"
        assert hasattr(paper, 'page_count'), "page_count field missing"
        assert hasattr(paper, 'is_approved'), "is_approved field missing"
        
    def test_has_enhanced_date_fields(self):
        """Test that AcademicPaper has separate date fields plus computed date."""
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"], 
            publication_date=datetime.now(),
            source="test",
            url="test"
        )
        
        # Test enhanced date fields exist
        assert hasattr(paper, 'submitted_date'), "submitted_date field missing"
        assert hasattr(paper, 'published_date'), "published_date field missing"
        assert hasattr(paper, 'updated_date'), "updated_date field missing"
        assert hasattr(paper, 'date'), "computed date property missing"
        
    def test_field_types_correct(self):
        """Test all field types are correctly defined."""
        from typing import get_type_hints
        from datetime import datetime
        from typing import Optional, List, Union, Dict
        
        hints = get_type_hints(AcademicPaper)
        
        # Test required fields
        assert hints['id'] == str
        assert hints['title'] == str  
        assert hints['authors'] == List[str]
        assert hints['source'] == Union[str, List[str]]
        assert hints['url'] == str
        
        # Test optional date fields
        assert hints['submitted_date'] == Optional[datetime]
        assert hints['published_date'] == Optional[datetime]
        assert hints['updated_date'] == Optional[datetime]
        
        # Test optional metadata fields
        assert hints['page_count'] == Optional[int]
        assert hints['comments'] == Optional[str]
        assert hints['abstract_type'] == Optional[str]
        assert hints['publication_status'] == Optional[str]
        assert hints['is_paid'] == Optional[bool]
        assert hints['is_approved'] == Optional[bool]


class TestAcademicPaperDateLogic:
    """Test the enhanced date computation logic."""
    
    def test_date_computed_from_max_of_dates(self):
        """Test date field is max of submitted/published/updated dates."""
        submitted = datetime(2023, 1, 1)
        published = datetime(2023, 2, 1)  # This should be the max
        updated = datetime(2023, 1, 15)
        
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"],
            publication_date=datetime.now(),  # Legacy field
            source="test",
            url="test",
            submitted_date=submitted,
            published_date=published,
            updated_date=updated
        )
        
        # The computed date property should return the maximum date
        assert paper.date == published, f"Expected {published}, got {paper.date}"
        
    def test_date_with_single_date_field(self):
        """Test date computation with only one date available."""
        submitted = datetime(2023, 1, 1)
        
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"],
            publication_date=datetime.now(),  # Legacy field
            source="test", 
            url="test",
            submitted_date=submitted,
            published_date=None,
            updated_date=None
        )
        
        # Should return the only available date
        assert paper.date == submitted, f"Expected {submitted}, got {paper.date}"
        
    def test_date_with_mixed_none_values(self):
        """Test date computation with some None values."""
        updated = datetime(2023, 3, 1)
        
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"],
            publication_date=datetime.now(),  # Legacy field
            source="test",
            url="test", 
            submitted_date=None,
            published_date=None,
            updated_date=updated
        )
        
        # Should return the only non-None date
        assert paper.date == updated, f"Expected {updated}, got {paper.date}"
        
    def test_date_raises_error_when_no_dates(self):
        """Test error raised when no date fields provided."""
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"],
            publication_date=None,  # No legacy field either
            source="test",
            url="test",
            submitted_date=None,
            published_date=None,
            updated_date=None
        )
        
        # Should raise ValueError when no dates available
        with pytest.raises(ValueError, match="At least one date field must be provided"):
            _ = paper.date


class TestAcademicPaperDescriptions:
    """Test programmatic field description access."""
    
    def test_get_field_descriptions_method_exists(self):
        """Test get_field_descriptions() class method exists."""
        assert hasattr(AcademicPaper, 'get_field_descriptions'), "get_field_descriptions method missing"
        assert callable(getattr(AcademicPaper, 'get_field_descriptions')), "get_field_descriptions not callable"
        
    def test_get_field_descriptions_returns_dict(self):
        """Test get_field_descriptions() returns dictionary."""
        descriptions = AcademicPaper.get_field_descriptions()
        assert isinstance(descriptions, dict), f"Expected dict, got {type(descriptions)}"
        
    def test_get_field_descriptions_returns_all_fields(self):
        """Test get_field_descriptions() returns description for every field."""
        descriptions = AcademicPaper.get_field_descriptions()
        if isinstance(descriptions, str):
            pytest.fail("get_field_descriptions returned a string instead of a dict")
        # Should have descriptions for all fields
        expected_fields = {
            'id', 'title', 'authors', 'source', 'url', 'date',
            'submitted_date', 'published_date', 'updated_date',
            'abstract', 'categories', 'pdf_url', 'journal_ref', 'doi',
            'download_count', 'affiliations', 'page_count', 
            'comments', 'abstract_type', 'publication_status', 
            'is_paid', 'is_approved', 'source_urls'
        }
        
        for field in expected_fields:
            assert field in descriptions, f"Missing description for field: {field}"
            assert descriptions[field], f"Empty description for field: {field}"
            
    def test_get_field_description_single_field(self):
        """Test get_field_description() for individual field."""
        assert hasattr(AcademicPaper, 'get_field_description'), "get_field_description method missing"
        
        # Test individual field description
        id_desc = AcademicPaper.get_field_description('id')
        assert isinstance(id_desc, str), f"Expected str, got {type(id_desc)}"
        assert id_desc, "Empty description for 'id' field"
        
        title_desc = AcademicPaper.get_field_description('title')
        assert title_desc, "Empty description for 'title' field"
        
    def test_field_descriptions_not_empty(self):
        """Test all field descriptions contain meaningful content."""
        descriptions = AcademicPaper.get_field_descriptions()
        if isinstance(descriptions, str):
            pytest.fail("get_field_descriptions returned a string instead of a dict")
        for field, desc in descriptions.items():
            assert len(desc) > 10, f"Description too short for {field}: {desc}"
            assert not desc.startswith("TODO"), f"Placeholder description for {field}: {desc}"
            
    def test_field_descriptions_contain_source_info(self):
        """Test field descriptions reference their source systems when applicable."""
        descriptions = AcademicPaper.get_field_descriptions()
        if isinstance(descriptions, str):
            pytest.fail("get_field_descriptions returned a string instead of a dict")
        # ArxivPaper-specific fields should mention arXiv
        assert 'arXiv' in descriptions['comments'], "comments description should mention arXiv"
        
        # SSRNPaper-specific fields should mention SSRN  
        assert 'SSRN' in descriptions['abstract_type'], "abstract_type description should mention SSRN"
        assert 'SSRN' in descriptions['is_paid'], "is_paid description should mention SSRN"


class TestArxivPaperConversion:
    """Test conversion from ArxivPaper to enhanced AcademicPaper."""
    
    def create_sample_arxiv_paper(self) -> ArxivPaper:
        """Create a sample ArxivPaper for testing."""
        return ArxivPaper(
            id="2312.12345",
            title="Test Paper Title",
            authors=["John Doe", "Jane Smith"],
            abstract="This is a test abstract.",
            submitted_date=datetime(2023, 12, 1),
            updated_date=datetime(2023, 12, 15),
            categories=["q-fin.TR", "cs.AI"],
            pdf_url="https://arxiv.org/pdf/2312.12345.pdf",
            arxiv_url="https://arxiv.org/abs/2312.12345",
            journal_ref="Journal of Test 2024",
            doi="10.1000/test",
            comments="12 pages, 5 figures"
        )
        
    def test_arxiv_all_fields_mapped(self):
        """Test all ArxivPaper fields are mapped to AcademicPaper."""
        arxiv_paper = self.create_sample_arxiv_paper()
        academic_paper = from_arxiv_paper(arxiv_paper)
        
        # Test all ArxivPaper fields are preserved
        assert academic_paper.id == arxiv_paper.id
        assert academic_paper.title == arxiv_paper.title
        assert academic_paper.authors == arxiv_paper.authors
        assert academic_paper.abstract == arxiv_paper.abstract
        assert academic_paper.categories == arxiv_paper.categories
        assert academic_paper.pdf_url == arxiv_paper.pdf_url
        assert academic_paper.url == arxiv_paper.arxiv_url
        assert academic_paper.journal_ref == arxiv_paper.journal_ref
        assert academic_paper.doi == arxiv_paper.doi
        assert academic_paper.comments == arxiv_paper.comments
        
    def test_arxiv_date_mapping(self):
        """Test ArxivPaper date fields mapped correctly."""
        arxiv_paper = self.create_sample_arxiv_paper()
        academic_paper = from_arxiv_paper(arxiv_paper)
        
        # Test date field mappings
        assert academic_paper.submitted_date == arxiv_paper.submitted_date
        assert academic_paper.updated_date == arxiv_paper.updated_date
        assert academic_paper.published_date is None  # arXiv doesn't have published_date
        
        # Test computed date is the max (updated_date in this case)
        assert academic_paper.date == arxiv_paper.updated_date
        
    def test_arxiv_source_specific_fields(self):
        """Test ArxivPaper-specific fields are set correctly."""
        arxiv_paper = self.create_sample_arxiv_paper()
        academic_paper = from_arxiv_paper(arxiv_paper)
        
        # Test source is correct
        assert academic_paper.source == "arXiv"
        
        # Test SSRN-specific fields are None for arXiv papers
        assert academic_paper.abstract_type is None
        assert academic_paper.publication_status is None
        assert academic_paper.is_paid is None
        assert academic_paper.is_approved is None
        assert academic_paper.download_count is None  # arXiv doesn't provide this


class TestSSRNPaperConversion:
    """Test conversion from SSRNPaper to enhanced AcademicPaper."""
    
    def create_sample_ssrn_paper(self) -> SSRNPaper:
        """Create a sample SSRNPaper for testing."""
        return SSRNPaper(
            ssrn_id="4123456",
            title="SSRN Test Paper",
            authors=["Alice Johnson", "Bob Wilson"],
            approved_date=datetime(2023, 11, 1),
            download_count=150,
            ssrn_url="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4123456",
            university_affiliations=["Harvard University", "MIT"],
            abstract_type="Executive Summary",
            publication_status="Published",
            is_paid=False,
            page_count=25,
            is_approved=True,
            reference="Financial Review 2023"
        )
        
    def test_ssrn_all_fields_mapped(self):
        """Test all SSRNPaper fields are mapped to AcademicPaper."""
        ssrn_paper = self.create_sample_ssrn_paper()
        academic_paper = from_ssrn_paper(ssrn_paper)
        
        # Test all SSRNPaper fields are preserved
        assert academic_paper.id == ssrn_paper.ssrn_id
        assert academic_paper.title == ssrn_paper.title
        assert academic_paper.authors == ssrn_paper.authors
        assert academic_paper.url == ssrn_paper.ssrn_url
        assert academic_paper.affiliations == ssrn_paper.university_affiliations
        assert academic_paper.download_count == ssrn_paper.download_count
        assert academic_paper.page_count == ssrn_paper.page_count
        assert academic_paper.abstract_type == ssrn_paper.abstract_type
        assert academic_paper.publication_status == ssrn_paper.publication_status
        assert academic_paper.is_paid == ssrn_paper.is_paid
        assert academic_paper.is_approved == ssrn_paper.is_approved
        assert academic_paper.journal_ref == ssrn_paper.reference
        
    def test_ssrn_date_mapping(self):
        """Test SSRNPaper approved_date maps to published_date."""
        ssrn_paper = self.create_sample_ssrn_paper()
        academic_paper = from_ssrn_paper(ssrn_paper)
        
        # Test date field mappings
        assert academic_paper.published_date == ssrn_paper.approved_date
        assert academic_paper.submitted_date is None  # SSRN doesn't have submitted_date
        assert academic_paper.updated_date is None    # SSRN doesn't have updated_date
        
        # Test computed date is the approved_date
        assert academic_paper.date == ssrn_paper.approved_date
        
    def test_ssrn_source_specific_fields(self):
        """Test SSRNPaper-specific fields are set correctly."""
        ssrn_paper = self.create_sample_ssrn_paper()
        academic_paper = from_ssrn_paper(ssrn_paper)
        
        # Test source is correct
        assert academic_paper.source == "SSRN"
        
        # Test arXiv-specific fields are None for SSRN papers
        assert academic_paper.comments is None
        
        # Test SSRN limitations
        assert academic_paper.abstract is None    # SSRN doesn't provide abstracts
        assert academic_paper.categories is None  # SSRN doesn't use categories
        assert academic_paper.pdf_url is None     # SSRN doesn't provide direct PDF URLs


class TestAcademicPaperSerialization:
    """Test serialization methods include all fields."""
    
    def create_sample_academic_paper(self) -> AcademicPaper:
        """Create a sample AcademicPaper with all fields populated."""
        return AcademicPaper(
            id="test123",
            title="Test Paper",
            authors=["Test Author"],
            publication_date=datetime(2023, 1, 1),  # Legacy field
            source="Test",
            url="https://test.com",
            submitted_date=datetime(2023, 1, 1),
            published_date=datetime(2023, 2, 1),
            updated_date=datetime(2023, 1, 15),
            abstract="Test abstract",
            categories=["test-category"],
            pdf_url="https://test.com/pdf",
            journal_ref="Test Journal",
            doi="10.1000/test",
            download_count=100,
            affiliations=["Test University"],
            page_count=10,
            comments="Test comments",
            abstract_type="Test Type",
            publication_status="Published",
            is_paid=False,
            is_approved=True
        )
        
    def test_to_dict_includes_all_fields(self):
        """Test to_dict() includes all new fields."""
        paper = self.create_sample_academic_paper()
        paper_dict = paper.to_dict()
        
        # Test all fields are included
        expected_fields = {
            'id', 'title', 'authors', 'source', 'url', 'date',
            'submitted_date', 'published_date', 'updated_date',
            'abstract', 'categories', 'pdf_url', 'journal_ref', 'doi',
            'download_count', 'affiliations', 'page_count',
            'comments', 'abstract_type', 'publication_status',
            'is_paid', 'is_approved'
        }
        
        for field in expected_fields:
            assert field in paper_dict, f"Missing field in to_dict(): {field}"
            
    def test_to_dict_with_descriptions_method_exists(self):
        """Test to_dict_with_descriptions() method exists."""
        paper = self.create_sample_academic_paper()
        assert hasattr(paper, 'to_dict_with_descriptions'), "to_dict_with_descriptions method missing"
        
    def test_to_dict_with_descriptions_includes_descriptions(self):
        """Test to_dict_with_descriptions() includes field descriptions."""
        paper = self.create_sample_academic_paper()
        paper_dict = paper.to_dict_with_descriptions()
        
        # Should include regular fields plus descriptions
        assert '_field_descriptions' in paper_dict, "Missing _field_descriptions in output"
        assert isinstance(paper_dict['_field_descriptions'], dict), "_field_descriptions should be dict"
        
        # Should have descriptions for all fields
        descriptions = paper_dict['_field_descriptions']
        assert len(descriptions) > 0, "No field descriptions included"
        
    def test_date_serialization_format(self):
        """Test date fields are serialized in ISO format."""
        paper = self.create_sample_academic_paper()
        paper_dict = paper.to_dict()
        
        # Test date fields are in ISO format
        assert isinstance(paper_dict['date'], str), "date should be serialized as string"
        assert paper_dict['submitted_date'].endswith('T00:00:00'), "submitted_date should be ISO format"
        assert paper_dict['published_date'].endswith('T00:00:00'), "published_date should be ISO format"
        assert paper_dict['updated_date'].endswith('T00:00:00'), "updated_date should be ISO format"


class TestBackwardCompatibility:
    """Test that existing functionality still works."""
    
    def test_legacy_publication_date_still_works(self):
        """Test that legacy publication_date field still works for existing code."""
        paper = AcademicPaper(
            id="test",
            title="test",
            authors=["test"],
            publication_date=datetime(2023, 1, 1),
            source="test",
            url="test"
        )
        
        # Legacy field should still exist and work
        assert hasattr(paper, 'publication_date'), "publication_date field missing"
        assert paper.publication_date == datetime(2023, 1, 1)
        
    def test_existing_to_dict_structure_preserved(self):
        """Test that existing to_dict() structure is preserved for backward compatibility."""
        paper = AcademicPaper(
            id="test",
            title="test", 
            authors=["test"],
            publication_date=datetime(2023, 1, 1),
            source="test",
            url="test"
        )
        
        paper_dict = paper.to_dict()
        
        # Test existing fields are still there
        legacy_fields = {'id', 'title', 'authors', 'source', 'url', 'abstract', 
                        'categories', 'pdf_url', 'journal_ref', 'doi', 
                        'download_count', 'affiliations'}
                        
        for field in legacy_fields:
            assert field in paper_dict, f"Legacy field missing from to_dict(): {field}"