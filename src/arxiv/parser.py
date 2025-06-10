# parser.py
import xml.etree.ElementTree as ET
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
import re

logger = logging.getLogger(__name__)

@dataclass
class ArxivPaper:
    """Data class representing a parsed arXiv paper"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    submitted_date: datetime
    updated_date: datetime
    categories: List[str]
    pdf_url: str
    arxiv_url: str
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    comments: Optional[str] = None

class ArxivXMLParser:
    """Parse arXiv API XML responses into structured data"""
    
    # arXiv XML namespaces
    NAMESPACES = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    def __init__(self):
        logger.info("🔧 Initialized ArxivXMLParser")
    
    def parse_response(self, xml_data: str) -> List[ArxivPaper]:
        """
        Parse arXiv API XML response into list of ArxivPaper objects
        
        Args:
            xml_data: Raw XML response from arXiv API
            
        Returns:
            List of parsed ArxivPaper objects
        """
        try:
            root = ET.fromstring(xml_data)
            logger.debug(f"🔍 Parsed XML root element: {root.tag}")
            
            # Find all entry elements (papers)
            entries = root.findall('atom:entry', self.NAMESPACES)
            logger.info(f"📄 Found [bold blue]{len(entries)}[/bold blue] papers in response")
            
            papers = []
            for i, entry in enumerate(entries):
                try:
                    paper = self._parse_entry(entry)
                    papers.append(paper)
                    logger.debug(f"✅ Parsed paper {i+1}/{len(entries)}: [green]{paper.title}...[/green]")
                    logger.debug(f"   ID: {paper.id}, Authors: {', '.join(paper.authors)}") 
                    logger.debug(f"   Categories: {', '.join(paper.categories)}") 
                except Exception as e:
                    logger.warning(f"⚠️  Failed to parse entry {i+1}: [yellow]{e}[/yellow]")
                    continue
            
            logger.info(f"🎉 Successfully parsed [bold green]{len(papers)}[/bold green] papers")
            return papers
            
        except ET.ParseError as e:
            logger.error(f"❌ XML parsing error: [red]{e}[/red]")
            raise ValueError(f"Invalid XML response: {e}")
        except Exception as e:
            logger.error(f"💥 Unexpected parsing error: [red]{e}[/red]")
            raise
    
    def _parse_entry(self, entry: ET.Element) -> ArxivPaper:
        """Parse a single entry element into an ArxivPaper"""
        
        # Extract ID (clean arXiv ID from URL)
        id_elem = entry.find('atom:id', self.NAMESPACES)
        arxiv_id = self._extract_arxiv_id(id_elem.text if id_elem is not None and id_elem.text else "")
        
        # Extract title (clean up whitespace)
        title_elem = entry.find('atom:title', self.NAMESPACES)
        title = self._clean_text(title_elem.text if title_elem is not None and title_elem.text else "Untitled")
        
        # Extract authors
        authors = self._extract_authors(entry)
        
        # Extract abstract
        summary_elem = entry.find('atom:summary', self.NAMESPACES)
        abstract = self._clean_text(summary_elem.text if summary_elem is not None and summary_elem.text else "")
        
        # Extract dates
        submitted_date = self._parse_date(entry.find('atom:published', self.NAMESPACES))
        updated_date = self._parse_date(entry.find('atom:updated', self.NAMESPACES))
        
        # Extract categories
        categories = self._extract_categories(entry)
        
        # Extract URLs
        pdf_url, arxiv_url = self._extract_urls(entry)
        
        # Extract optional fields
        journal_ref = self._extract_journal_ref(entry)
        doi = self._extract_doi(entry)
        comments = self._extract_comments(entry)
        
        return ArxivPaper(
            id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            submitted_date=submitted_date,
            updated_date=updated_date,
            categories=categories,
            pdf_url=pdf_url,
            arxiv_url=arxiv_url,
            journal_ref=journal_ref,
            doi=doi,
            comments=comments
        )
    
    def _extract_arxiv_id(self, id_url: str) -> str:
        """Extract clean arXiv ID from URL"""
        # arXiv URLs look like: http://arxiv.org/abs/2312.12345v1
        match = re.search(r'arxiv\.org/abs/([^v]+)', id_url)
        return match.group(1) if match else id_url.split('/')[-1]
    
    def _clean_text(self, text: str) -> str:
        """Clean up text by removing extra whitespace and newlines"""
        if not text:
            return ""
        # Replace multiple whitespace/newlines with single space
        return re.sub(r'\s+', ' ', text.strip())
    
    def _extract_authors(self, entry: ET.Element) -> List[str]:
        """Extract author names from entry"""
        authors = []
        author_elems = entry.findall('atom:author', self.NAMESPACES)
        
        for author_elem in author_elems:
            name_elem = author_elem.find('atom:name', self.NAMESPACES)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        
        return authors
    
    def _parse_date(self, date_elem: Optional[ET.Element]) -> datetime:
        """Parse date element into datetime object"""
        if date_elem is None or not date_elem.text:
            return datetime.now()
        
        try:
            # arXiv dates are in ISO format: 2023-12-15T18:30:45Z
            date_str = date_elem.text.replace('Z', '+00:00')
            return datetime.fromisoformat(date_str)
        except ValueError:
            logger.warning(f"⚠️  Could not parse date: {date_elem.text}")
            return datetime.now()
    
    def _extract_categories(self, entry: ET.Element) -> List[str]:
        """Extract category information"""
        categories = []
        category_elems = entry.findall('atom:category', self.NAMESPACES)
        
        for cat_elem in category_elems:
            term = cat_elem.get('term')
            if term:
                categories.append(term)
        
        return categories
    
    def _extract_urls(self, entry: ET.Element) -> tuple[str, str]:
        """Extract PDF and arXiv URLs"""
        pdf_url = ""
        arxiv_url = ""
        
        link_elems = entry.findall('atom:link', self.NAMESPACES)
        for link_elem in link_elems:
            href = link_elem.get('href', '')
            title = link_elem.get('title', '')
            
            if title == 'pdf':
                pdf_url = href
            elif 'arxiv.org/abs/' in href:
                arxiv_url = href
        
        return pdf_url, arxiv_url
    
    def _extract_journal_ref(self, entry: ET.Element) -> Optional[str]:
        """Extract journal reference if available"""
        journal_elem = entry.find('arxiv:journal_ref', self.NAMESPACES)
        return journal_elem.text.strip() if journal_elem is not None and journal_elem.text else None
    
    def _extract_doi(self, entry: ET.Element) -> Optional[str]:
        """Extract DOI if available"""
        doi_elem = entry.find('arxiv:doi', self.NAMESPACES)
        return doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None
    
    def _extract_comments(self, entry: ET.Element) -> Optional[str]:
        """Extract comments if available"""
        comment_elem = entry.find('arxiv:comment', self.NAMESPACES)
        return self._clean_text(comment_elem.text) if comment_elem is not None and comment_elem.text else None