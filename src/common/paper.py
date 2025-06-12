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
    publication_date: datetime
    source: str  # "arXiv" or "SSRN"
    url: str
    
    # Optional fields (may be None based on source)
    abstract: Optional[str] = None
    categories: Optional[List[str]] = None
    pdf_url: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    download_count: Optional[int] = None
    affiliations: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert AcademicPaper to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
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
            "affiliations": self.affiliations
        }
    
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
        affiliations=None  # arXiv doesn't provide affiliations
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
    
    if not ssrn_paper.authors:
        raise ValueError("authors cannot be None or empty")
    
    # Clean and normalize fields
    clean_title = _clean_title(ssrn_paper.title)
    clean_authors = _clean_authors(ssrn_paper.authors)
    
    # Handle affiliations - preserve empty list if explicitly provided
    if ssrn_paper.university_affiliations is not None:
        clean_affiliations = _clean_authors(ssrn_paper.university_affiliations)
    else:
        clean_affiliations = None
    
    if not clean_title:
        raise ValueError("title cannot be empty after cleaning")
    
    if not clean_authors:
        raise ValueError("authors cannot be empty after cleaning")
    
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
        affiliations=clean_affiliations
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