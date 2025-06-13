"""
Common Paper Schema for Academic Papers

This module defines the unified AcademicPaper dataclass and conversion functions
for normalizing papers from different sources (arXiv, SSRN) into a common format.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

# Import paper classes from different sources
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.arxiv.parser import ArxivPaper
from src.ssrn.parser import SSRNPaper


@dataclass
class AcademicPaper:
    """
    Unified data class representing an academic paper from any source.
    
    This class normalizes papers from different academic databases (arXiv, SSRN)
    into a common format for consistent processing and display.
    """
    
    # Required fields
    id: str
    title: str
    authors: List[str]
    publication_date: datetime  # Legacy field - kept for backward compatibility
    source: Union[str, List[str]]  # Single source or list for aggregated papers
    url: str
    
    # Enhanced date fields
    submitted_date: Optional[datetime] = None
    published_date: Optional[datetime] = None 
    updated_date: Optional[datetime] = None
    
    # Optional fields (may be None based on source)
    abstract: Optional[str] = None
    categories: Optional[List[str]] = None
    pdf_url: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    download_count: Optional[int] = None
    affiliations: Optional[List[str]] = None
    source_urls: Optional[Dict[str, str]] = None  # Maps source name to URL for aggregated papers
    
    # New metadata fields
    page_count: Optional[int] = None
    
    # ArxivPaper-specific fields
    comments: Optional[str] = None
    
    # SSRNPaper-specific fields  
    abstract_type: Optional[str] = None
    publication_status: Optional[str] = None
    is_paid: Optional[bool] = None
    is_approved: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert AcademicPaper to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        result = {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "publication_date": self.publication_date.isoformat(),
            "source": self.source,
            "categories": self.categories,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "journal_ref": self.journal_ref,
            "doi": self.doi,
            "download_count": self.download_count,
            "affiliations": self.affiliations,
            
            # Enhanced date fields
            "date": self.date.isoformat(), 
            "submitted_date": self.submitted_date.isoformat() if self.submitted_date else None,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "page_count": self.page_count,
            "comments": self.comments,
            "abstract_type": self.abstract_type,
            "publication_status": self.publication_status,
            "is_paid": self.is_paid,
            "is_approved": self.is_approved
        }
        
        # Add source_urls if present (for aggregated papers)
        if self.source_urls:
            result["source_urls"] = self.source_urls
            
        return result
    
    @property
    def date(self) -> datetime:
        """
        Computed date property - returns the most recent date from available date fields.
        
        Returns the maximum of submitted_date, published_date, and updated_date
        where those fields are not None. Falls back to publication_date for
        backward compatibility when new date fields are not available.
        
        Returns:
            Most recent date available
            
        Raises:
            ValueError: If no date fields are provided (all are None)
        """
        available_dates = [
            d for d in [self.submitted_date, self.published_date, self.updated_date] 
            if d is not None
        ]
        
        if not available_dates:
            # Fall back to legacy publication_date for backward compatibility
            if self.publication_date is not None:
                return self.publication_date
            raise ValueError("At least one date field must be provided")
            
        return max(available_dates)
    
    @classmethod
    def get_field_descriptions(cls) -> Dict[str, str]:
        """
        Return comprehensive descriptions for all AcademicPaper fields.
        
        Descriptions are sourced from official arXiv and SSRN documentation
        to provide authoritative field definitions.
        
        Returns:
            Dictionary mapping field names to their official descriptions
        """
        return {
            # Core identification fields
            'id': 'Unique identifier from the source database (arXiv ID format like "2312.12345" or SSRN ID number)',
            'title': 'Official paper title as provided by the source, searchable and indexed for discovery',
            'authors': 'List of author names in source order, containing the full names as provided by the publication database',
            'source': 'Source database name(s) - single source string (e.g., "arXiv", "SSRN") or list for aggregated papers from multiple sources',
            'url': 'Primary URL for accessing the paper abstract and details page on the source platform',
            
            # Enhanced date fields  
            'date': 'Most recent date available - computed as the maximum of submitted_date, published_date, and updated_date',
            'submitted_date': 'Date when paper was first submitted to the platform (arXiv: <published> field, when version 1 was submitted)',
            'published_date': 'Date when paper was officially published or approved (SSRN: approved_date when paper passed editorial review)',
            'updated_date': 'Date when paper was last updated or revised (arXiv: <updated> field for the specific version)',
            
            # Content fields
            'abstract': 'Paper abstract or summary (arXiv: <summary> element; SSRN: may be unavailable via API)',
            'categories': 'Subject classification categories (arXiv: primary category and additional categories using arXiv taxonomy like "q-fin.TR")',
            
            # Access fields
            'pdf_url': 'Direct URL for PDF download when available (arXiv: link with title="pdf"; SSRN: typically not provided)',
            'doi': 'Digital Object Identifier for published papers (arXiv: <arxiv:doi> element when paper is published in journal)',
            'journal_ref': 'Journal reference when paper is published in a journal (arXiv: <arxiv:journal_ref>; SSRN: reference field)',
            
            # Metadata fields
            'download_count': 'Number of times paper has been downloaded (SSRN: download tracking; arXiv: not provided)',
            'affiliations': 'Author institutional affiliations (SSRN: university_affiliations; arXiv: optional <arxiv:affiliation>)',
            'page_count': 'Number of pages in the document (SSRN: page_count field; arXiv: may be mentioned in comments)',
            
            # ArxivPaper-specific fields
            'comments': 'Author-provided comments and metadata (arXiv: <arxiv:comment> element, often includes page count, figures, conference info)',
            
            # SSRNPaper-specific fields  
            'abstract_type': 'Type or category of abstract in SSRN system (e.g., "Working Paper", "Executive Summary")',
            'publication_status': 'Current publication status in SSRN workflow (e.g., "Published", "Under Review")',
            'is_paid': 'Whether paper requires payment for full access (SSRN premium content access model)',
            'is_approved': 'Whether paper has been approved by SSRN editorial review process',
            
            # Aggregation fields
            'source_urls': 'Maps source name to URL for papers aggregated from multiple sources (e.g., {"arXiv": "...", "SSRN": "..."})'
        }
    
    @classmethod  
    def get_field_description(cls, field_name: str) -> str:
        """
        Return description for a specific field.
        
        Args:
            field_name: Name of the field to get description for
            
        Returns:
            Field description string, or empty string if field not found
        """
        descriptions = cls.get_field_descriptions()
        return descriptions.get(field_name, "")
    
    def to_dict_with_descriptions(self) -> Dict[str, Any]:
        """
        Convert to dictionary including field descriptions for API responses.
        
        Returns:
            Dictionary containing all paper data plus field descriptions
        """
        data = self.to_dict()
        data["_field_descriptions"] = self.get_field_descriptions()
        return data
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += f" et al. ({len(self.authors)} total)"
        
        return f"{self.source} Paper: {self.title} by {authors_str} ({self.publication_date.year})"


# Conversion functions (skeleton implementation - no actual conversion logic)
def from_arxiv_paper(arxiv_paper: ArxivPaper) -> AcademicPaper:
    """
    Convert ArxivPaper to AcademicPaper.
    
    Args:
        arxiv_paper: ArxivPaper object to convert
        
    Returns:
        AcademicPaper object with normalized fields
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    if not arxiv_paper.id:
        raise ValueError("id cannot be None or empty")
    
    if not arxiv_paper.title:
        raise ValueError("title cannot be None or empty")
    
    if not arxiv_paper.authors:
        raise ValueError("authors cannot be None or empty")
    
    # Clean and normalize fields
    clean_title = _clean_title(arxiv_paper.title)
    clean_authors = _clean_authors(arxiv_paper.authors)
    clean_abstract = _clean_title(arxiv_paper.abstract) if arxiv_paper.abstract else None
    clean_categories = [cat for cat in arxiv_paper.categories if cat and cat.strip()] if arxiv_paper.categories else None
    
    if not clean_title:
        raise ValueError("title cannot be empty after cleaning")
    
    if not clean_authors:
        raise ValueError("authors cannot be empty after cleaning")
    
    # Create AcademicPaper with mapped fields
    return AcademicPaper(
        id=str(arxiv_paper.id).strip(),
        title=clean_title,
        authors=clean_authors,
        abstract=clean_abstract,
        publication_date=arxiv_paper.submitted_date,
        source="arXiv",
        categories=clean_categories,
        url=arxiv_paper.arxiv_url,
        pdf_url=_normalize_url(arxiv_paper.pdf_url),
        journal_ref=_normalize_url(arxiv_paper.journal_ref),
        doi=_normalize_url(arxiv_paper.doi),
        download_count=None,  # arXiv doesn't provide download counts
        affiliations=None,  # arXiv doesn't provide affiliations
        
        # Enhanced date fields
        submitted_date=arxiv_paper.submitted_date,
        published_date=None,  # arXiv doesn't have published_date concept
        updated_date=arxiv_paper.updated_date,
        
        # New metadata fields
        page_count=None,      # arXiv doesn't provide page_count directly
        
        # ArxivPaper-specific fields
        comments=arxiv_paper.comments,
        
        # SSRNPaper-specific fields (all None for arXiv)
        abstract_type=None,
        publication_status=None,
        is_paid=None,
        is_approved=None
    )


def from_ssrn_paper(ssrn_paper: SSRNPaper) -> AcademicPaper:
    """
    Convert SSRNPaper to AcademicPaper.
    
    Args:
        ssrn_paper: SSRNPaper object to convert
        
    Returns:
        AcademicPaper object with normalized fields
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Validate required fields
    if not ssrn_paper.ssrn_id:
        raise ValueError("ssrn_id cannot be None or empty")
    
    if not ssrn_paper.title:
        raise ValueError("title cannot be None or empty")
    
    # Handle missing authors gracefully - some SSRN papers have incomplete data
    if not ssrn_paper.authors:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ SSRN paper {ssrn_paper.ssrn_id} has missing authors - using default")
        clean_authors = ["Unknown Author"]
    else:
        clean_authors = _clean_authors(ssrn_paper.authors)
    
    # Clean and normalize fields
    clean_title = _clean_title(ssrn_paper.title)
    
    # Handle affiliations - preserve empty list if explicitly provided
    if ssrn_paper.university_affiliations is not None:
        clean_affiliations = _clean_authors(ssrn_paper.university_affiliations)
    else:
        clean_affiliations = None
    
    if not clean_title:
        raise ValueError("title cannot be empty after cleaning")
    
    # Ensure we always have at least one author after cleaning
    if not clean_authors:
        clean_authors = ["Unknown Author"]
    
    # Clean download count (handle negative values)
    clean_download_count = _safe_int(ssrn_paper.download_count, 0)
    
    # Create AcademicPaper with mapped fields
    return AcademicPaper(
        id=str(ssrn_paper.ssrn_id).strip(),
        title=clean_title,
        authors=clean_authors,
        abstract=None,  # SSRN doesn't provide abstracts via API
        publication_date=ssrn_paper.approved_date,
        source="SSRN",
        categories=None,  # SSRN doesn't provide categories
        url=_normalize_url(ssrn_paper.ssrn_url) or f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_paper.ssrn_id}",
        pdf_url=None,  # SSRN doesn't provide direct PDF URLs
        journal_ref=_normalize_url(ssrn_paper.reference),
        doi=None,  # SSRN papers typically don't have DOIs in the API
        download_count=clean_download_count,
        affiliations=clean_affiliations,
        
        # Enhanced date fields
        submitted_date=None,     # SSRN doesn't have submitted_date concept
        published_date=ssrn_paper.approved_date,
        updated_date=None,       # SSRN doesn't track updates
        
        # New metadata fields
        page_count=ssrn_paper.page_count,
        
        # ArxivPaper-specific fields (all None for SSRN)
        comments=None,
        
        # SSRNPaper-specific fields
        abstract_type=ssrn_paper.abstract_type,
        publication_status=ssrn_paper.publication_status,
        is_paid=ssrn_paper.is_paid,
        is_approved=ssrn_paper.is_approved
    )


# Helper functions
def _clean_title(title: str) -> str:
    """
    Clean and normalize paper title.
    
    Args:
        title: Raw title string
        
    Returns:
        Cleaned title string
    """
    if not title:
        return ""
    
    # Convert to string and strip whitespace
    text = str(title).strip()
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
        '&mdash;': '—',
        '&ndash;': '–',
        '&ldquo;': '"',
        '&rdquo;': '"',
        '&lsquo;': ''',
        '&rsquo;': '''
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    # Replace multiple whitespace/newlines/tabs with single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def _clean_authors(authors: List[str]) -> List[str]:
    """
    Clean and normalize authors list.
    
    Args:
        authors: List of author names (may contain empty strings)
        
    Returns:
        Cleaned list of author names
    """
    if not authors:
        return []
    
    cleaned = []
    for author in authors:
        if author and isinstance(author, str):
            # Clean whitespace and normalize
            clean_author = re.sub(r'\s+', ' ', str(author).strip())
            if clean_author:  # Only add non-empty authors
                cleaned.append(clean_author)
    
    return cleaned


def _normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Normalize URL, converting empty strings to None.
    
    Args:
        url: Raw URL string
        
    Returns:
        Normalized URL or None if empty/invalid
    """
    if not url or not isinstance(url, str):
        return None
    
    # Strip whitespace
    url = url.strip()
    
    # Return None for empty or whitespace-only strings
    if not url:
        return None
    
    return url


def _safe_int(value: Union[int, str, None], default: int = 0) -> int:
    """
    Safely convert value to integer with default.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    if value is None:
        return default
    
    try:
        result = int(value)
        # Return default for negative values (normalize negative download counts)
        return max(result, 0) if result >= 0 else default
    except (ValueError, TypeError):
        return default