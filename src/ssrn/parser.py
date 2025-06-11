"""
SSRN JSON Parser

Parser for SSRN API JSON responses and data structures.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


@dataclass
class SSRNPaper:
    """Data class representing a parsed SSRN paper"""
    ssrn_id: str
    title: str
    authors: List[str]
    approved_date: datetime
    download_count: int
    ssrn_url: str
    university_affiliations: List[str]
    abstract_type: str
    publication_status: str
    is_paid: bool
    page_count: int
    is_approved: bool
    reference: Optional[str] = None


class SSRNJSONParser:
    """Parse SSRN API JSON responses into structured data"""
    
    def __init__(self):
        logger.info("🔧 Initialized SSRNJSONParser")
    
    def parse_response(self, json_data: Dict[str, Any]) -> List[SSRNPaper]:
        """
        Parse SSRN API JSON response into list of SSRNPaper objects
        
        Args:
            json_data: Parsed JSON response from SSRN API
            
        Returns:
            List of parsed SSRNPaper objects
        """
        try:
            papers_data = json_data.get("papers", [])
            if not papers_data:
                logger.warning("⚠️ No papers found in SSRN response")
                return []
            
            parsed_papers = []
            for paper_data in papers_data:
                try:
                    paper = self._parse_paper(paper_data)
                    if paper:
                        parsed_papers.append(paper)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse paper: {e}")
                    continue
            
            logger.info(f"✅ Successfully parsed [bold green]{len(parsed_papers)}[/bold green] SSRN papers")
            return parsed_papers
            
        except Exception as e:
            logger.error(f"❌ Failed to parse SSRN response: {e}")
            raise
    
    def _parse_paper(self, paper_data: Dict[str, Any]) -> Optional[SSRNPaper]:
        """
        Parse individual paper data into SSRNPaper object
        
        Args:
            paper_data: Dictionary containing paper information
            
        Returns:
            SSRNPaper object or None if parsing fails
        """
        try:
            # Extract required fields
            ssrn_id = str(paper_data.get("id", ""))
            title = self._clean_html(paper_data.get("title", ""))
            
            # Parse authors from structured format
            authors = self._extract_authors(paper_data.get("authors", []))
            
            # Parse approved date
            approved_date = self._parse_date(paper_data.get("approved_date")) or datetime.now()
            
            # Extract other fields
            download_count = int(paper_data.get("downloads", 0))
            ssrn_url = paper_data.get("url", "") or f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={ssrn_id}"
            
            # Extract affiliations
            university_affiliations = self._extract_affiliations(paper_data.get("affiliations", ""))
            
            # Extract status and type fields
            abstract_type = paper_data.get("abstract_type", "")
            publication_status = paper_data.get("publication_status", "")
            is_paid = bool(paper_data.get("is_paid", False))
            page_count = int(paper_data.get("page_count", 0))
            is_approved = bool(paper_data.get("is_approved", True))
            reference = paper_data.get("reference", "")
            
            return SSRNPaper(
                ssrn_id=ssrn_id,
                title=title,
                authors=authors,
                approved_date=approved_date,
                download_count=download_count,
                ssrn_url=ssrn_url,
                university_affiliations=university_affiliations,
                abstract_type=abstract_type,
                publication_status=publication_status,
                is_paid=is_paid,
                page_count=page_count,
                is_approved=is_approved,
                reference=reference if reference else None
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing paper {paper_data.get('id', 'unknown')}: {e}")
            return None
    
    def _extract_authors(self, authors_data: Any) -> List[str]:
        """Extract and clean author names from SSRN format"""
        if not authors_data:
            return []
        
        authors = []
        
        # Handle SSRN author object format
        if isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, dict):
                    # SSRN format: {"id": 123, "first_name": "John", "last_name": "Doe", "url": "..."}
                    first_name = author.get("first_name", "")
                    last_name = author.get("last_name", "")
                    
                    if first_name and last_name:
                        full_name = f"{first_name} {last_name}"
                    elif last_name:
                        full_name = last_name
                    elif first_name:
                        full_name = first_name
                    else:
                        full_name = str(author.get("id", "Unknown"))
                    
                    authors.append(self._clean_text(full_name))
                elif isinstance(author, str):
                    authors.append(self._clean_text(author))
                else:
                    authors.append(self._clean_text(str(author)))
        elif isinstance(authors_data, str):
            authors.append(self._clean_text(authors_data))
        
        return authors
    
    
    def _extract_affiliations(self, affiliations_data: Any) -> List[str]:
        """Extract university/institution affiliations from SSRN format"""
        if not affiliations_data:
            return []
        
        # SSRN format is typically a single string
        if isinstance(affiliations_data, str):
            cleaned = self._clean_text(affiliations_data)
            return [cleaned] if cleaned else []
        elif isinstance(affiliations_data, list):
            affiliations = []
            for affiliation in affiliations_data:
                if isinstance(affiliation, str):
                    cleaned = self._clean_text(affiliation)
                    if cleaned:
                        affiliations.append(cleaned)
                elif isinstance(affiliation, dict):
                    # Handle object format
                    name = (affiliation.get("institution") or 
                           affiliation.get("university") or 
                           affiliation.get("name") or 
                           str(affiliation))
                    cleaned = self._clean_text(name)
                    if cleaned:
                        affiliations.append(cleaned)
            return affiliations
        else:
            cleaned = self._clean_text(str(affiliations_data))
            return [cleaned] if cleaned else []
    
    def _parse_date(self, date_data: Any) -> Optional[datetime]:
        """Parse SSRN date format: 'DD MMM YYYY' (e.g., '11 Jun 2025')"""
        if not date_data:
            return None
        
        date_str = None
        
        try:
            if isinstance(date_data, datetime):
                return date_data
            
            date_str = str(date_data).strip()
            if not date_str:
                return None
            
            # SSRN uses format: "11 Jun 2025"
            return datetime.strptime(date_str, "%d %b %Y")
            
        except ValueError:
            logger.warning(f"⚠️ Could not parse SSRN date format '{date_str}' (expected: DD MMM YYYY)")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Date parsing error: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text fields"""
        if not text:
            return ""
        
        # Convert to string and strip whitespace
        text = str(text).strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _clean_html(self, text: str) -> str:
        """Clean HTML tags and entities from text"""
        if not text:
            return ""
        
        # Convert to string and strip whitespace
        text = str(text).strip()
        
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
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def filter_by_text(self, papers: List[SSRNPaper], query: str) -> List[SSRNPaper]:
        """Filter papers by text search in title only (no abstracts in SSRN API)"""
        if not query:
            return papers
        
        query_lower = query.lower()
        filtered = []
        
        for paper in papers:
            if query_lower in paper.title.lower():
                filtered.append(paper)
        
        logger.debug(f"🔍 Text filter: {len(papers)} → {len(filtered)} papers")
        return filtered
    
    def filter_by_author(self, papers: List[SSRNPaper], author_name: str) -> List[SSRNPaper]:
        """Filter papers by author name (case-insensitive partial match)"""
        if not author_name:
            return papers
        
        author_lower = author_name.lower()
        filtered = []
        
        for paper in papers:
            if any(author_lower in author.lower() for author in paper.authors):
                filtered.append(paper)
        
        logger.debug(f"👤 Author filter: {len(papers)} → {len(filtered)} papers")
        return filtered
    
    def filter_by_date(self, papers: List[SSRNPaper], start_date: Optional[str], end_date: Optional[str]) -> List[SSRNPaper]:
        """Filter papers by approved date range"""
        if not start_date and not end_date:
            return papers
        
        filtered = []
        
        for paper in papers:
            paper_date = paper.approved_date
            
            # Check date range
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    if paper_date < start_dt:
                        continue
                except ValueError:
                    logger.warning(f"⚠️ Invalid start_date format: {start_date}")
                    continue
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    if paper_date > end_dt:
                        continue
                except ValueError:
                    logger.warning(f"⚠️ Invalid end_date format: {end_date}")
                    continue
            
            filtered.append(paper)
        
        logger.debug(f"📅 Date filter: {len(papers)} → {len(filtered)} papers")
        return filtered