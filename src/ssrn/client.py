"""
SSRN Async Client

Async HTTP client for accessing SSRN API with rate limiting, error handling,
and client-side filtering capabilities.
"""

import aiohttp
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import json

# Setup Rich logging
logger = logging.getLogger(__name__)


class SSRNAPIError(Exception):
    """Custom exception for SSRN API errors"""
    pass


class AsyncSSRNClient:
    """Async SSRN API client with robust error handling and rate limiting"""

    def __init__(self, delay_seconds: float = 3.0):
        self.base_url = "https://api.ssrn.com/content/v1/bindings/204/papers"
        self.delay_seconds = delay_seconds
        self.last_request_time = 0
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session: Optional[aiohttp.ClientSession] = None
        self._papers_cache: List[Dict[str, Any]] = []
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
        # Headers - use browser-like User-Agent to avoid bot detection
        browser_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        import random
        self.headers = {
            "User-Agent": random.choice(browser_agents),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        logger.info(f"🚀 Initialized AsyncSSRNClient with [bold cyan]{delay_seconds}s[/bold cyan] delay")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()

    async def start_session(self):
        """Start aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers
            )
            logger.debug("🔌 Started aiohttp session")

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("❌ Closed aiohttp session")

    async def _handle_rate_limit(self):
        """Handle rate limiting with delay"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay_seconds:
            sleep_time = self.delay_seconds - time_since_last
            logger.debug(f"⏳ Rate limiting: sleeping [yellow]{sleep_time:.2f}s[/yellow]")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired"""
        if not self._papers_cache or not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_duration

    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to SSRN API with error handling"""
        if not self.session:
            await self.start_session()

        await self._handle_rate_limit()

        try:
            logger.debug(f"📡 Making SSRN API request with params: {params}")
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"✅ Received {len(data.get('papers', []))} papers from SSRN")
                    return data
                elif response.status == 429:
                    logger.warning("⚠️ Rate limited by SSRN API")
                    await asyncio.sleep(self.delay_seconds * 2)  # Double delay on rate limit
                    raise SSRNAPIError(f"Rate limited by SSRN API (429)")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ SSRN API error {response.status}: {error_text}")
                    raise SSRNAPIError(f"SSRN API error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"🚫 Network error accessing SSRN: {e}")
            raise SSRNAPIError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"🚫 JSON decode error: {e}")
            raise SSRNAPIError(f"Invalid JSON response: {e}")

    async def get_all_papers(self, max_results: int = 2000) -> List[Dict[str, Any]]:
        """
        Retrieve all papers from SSRN with pagination.
        Uses caching to avoid repeated full downloads.
        """
        # Check cache first
        if self._is_cache_valid():
            logger.info(f"📚 Using cached SSRN papers ({len(self._papers_cache)} papers)")
            return self._papers_cache[:max_results]

        logger.info(f"🔄 Fetching all SSRN papers (up to {max_results})")
        all_papers = []
        index = 0
        page_size = 200  # SSRN API maximum

        while len(all_papers) < max_results:
            params = {
                "index": index,
                "count": min(page_size, max_results - len(all_papers)),
                "sort": 0
            }

            try:
                response_data = await self._make_request(params)
                papers = response_data.get("papers", [])
                
                if not papers:
                    logger.info(f"📄 No more papers returned at index {index}")
                    break
                
                all_papers.extend(papers)
                logger.info(f"📊 Retrieved {len(papers)} papers (total: {len(all_papers)})")
                
                # If we got fewer papers than requested, we've reached the end
                if len(papers) < page_size:
                    logger.info("📄 Reached end of SSRN dataset")
                    break
                    
                index += page_size
                
            except SSRNAPIError as e:
                logger.error(f"❌ Error fetching papers at index {index}: {e}")
                break

        # Update cache
        self._papers_cache = all_papers
        self._cache_timestamp = datetime.now()
        
        logger.info(f"✅ Successfully retrieved [bold green]{len(all_papers)}[/bold green] SSRN papers")
        return all_papers


    def _filter_by_author(self, papers: List[Dict[str, Any]], author_name: str) -> List[Dict[str, Any]]:
        """Filter papers by author name (case-insensitive partial match)"""
        if not author_name:
            return papers
            
        author_lower = author_name.lower()
        filtered = []
        
        for paper in papers:
            authors = paper.get("authors", [])
            
            # Handle SSRN author format: list of objects with first_name, last_name
            found_author = False
            for author in authors:
                if isinstance(author, dict):
                    first_name = str(author.get("first_name", ""))
                    last_name = str(author.get("last_name", ""))
                    full_name = f"{first_name} {last_name}".strip()
                    
                    if (author_lower in first_name.lower() or 
                        author_lower in last_name.lower() or 
                        author_lower in full_name.lower()):
                        found_author = True
                        break
                elif isinstance(author, str):
                    if author_lower in author.lower():
                        found_author = True
                        break
            
            if found_author:
                filtered.append(paper)
                
        logger.debug(f"👤 Author filter: {len(papers)} → {len(filtered)} papers")
        return filtered

    def _filter_by_text(self, papers: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter papers by text search in title only (no abstracts in SSRN API)"""
        if not query:
            return papers
            
        query_lower = query.lower()
        filtered = []
        
        for paper in papers:
            title = str(paper.get("title", "")).lower()
            
            # Clean HTML tags from title for searching
            import re
            title_clean = re.sub(r'<[^>]+>', '', title)
            
            # Search in title only
            if query_lower in title_clean:
                filtered.append(paper)
                
        logger.debug(f"🔍 Text filter: {len(papers)} → {len(filtered)} papers")
        return filtered

    def _filter_by_date(self, papers: List[Dict[str, Any]], start_date: Optional[str], end_date: Optional[str]) -> List[Dict[str, Any]]:
        """Filter papers by approved date range"""
        if not start_date and not end_date:
            return papers
            
        filtered = []
        
        for paper in papers:
            paper_date_str = paper.get("approved_date")
            if not paper_date_str:
                continue
                
            try:
                # Parse paper date (SSRN format: "DD MMM YYYY")
                if isinstance(paper_date_str, str):
                    paper_date = datetime.strptime(paper_date_str, "%d %b %Y")
                else:
                    continue
                    
                # Check date range
                if start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    if paper_date < start_dt:
                        continue
                        
                if end_date:
                    end_dt = datetime.fromisoformat(end_date)
                    if paper_date > end_dt:
                        continue
                        
                filtered.append(paper)
                
            except (ValueError, TypeError) as e:
                logger.debug(f"⚠️ Could not parse date {paper_date_str}: {e}")
                continue
                
        logger.debug(f"📅 Date filter: {len(papers)} → {len(filtered)} papers")
        return filtered

    async def search_papers(self, query: str, max_results: int = 200) -> List[Dict[str, Any]]:
        """Search papers by text query in titles"""
        logger.info(f"🔍 Searching SSRN papers by text: '{query}'")
        
        all_papers = await self.get_all_papers(max_results * 5)  # Get more to account for filtering
        filtered_papers = self._filter_by_text(all_papers, query)
        
        return filtered_papers[:max_results]

    async def search_by_author(self, author_name: str, max_results: int = 200) -> List[Dict[str, Any]]:
        """Search papers by author name"""
        logger.info(f"👤 Searching SSRN papers by author: {author_name}")
        
        all_papers = await self.get_all_papers(max_results * 5)  # Get more to account for filtering
        filtered_papers = self._filter_by_author(all_papers, author_name)
        
        return filtered_papers[:max_results]


    async def get_recent_papers(self, months_back: int = 6, max_results: int = 200) -> List[Dict[str, Any]]:
        """Get recent papers from the last X months"""
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=months_back * 30)).isoformat()
        
        logger.info(f"📅 Searching SSRN papers from last {months_back} months")
        
        all_papers = await self.get_all_papers(max_results * 5)  # Get more to account for filtering
        filtered_papers = self._filter_by_date(all_papers, start_date, end_date)
        
        return filtered_papers[:max_results]

    async def search_finance_papers(self, start_date: Optional[str] = None, end_date: Optional[str] = None, max_results: int = 200) -> List[Dict[str, Any]]:
        """Search for finance-related papers using common finance keywords"""
        finance_keywords = [
            "finance", "financial", "investment", "trading", "market", "portfolio",
            "risk", "derivative", "option", "bond", "equity", "asset", "valuation",
            "capital", "banking", "economics", "monetary", "corporate finance"
        ]
        
        logger.info(f"💰 Searching SSRN finance papers with keywords: {finance_keywords[:5]}...")
        
        all_papers = await self.get_all_papers(max_results * 5)  # Get more to account for filtering
        
        # Filter by finance keywords in title
        filtered_papers = []
        for paper in all_papers:
            title = str(paper.get("title", "")).lower()
            # Clean HTML tags from title
            import re
            title_clean = re.sub(r'<[^>]+>', '', title)
            
            # Check if any finance keyword appears in title
            if any(keyword in title_clean for keyword in finance_keywords):
                filtered_papers.append(paper)
        
        logger.debug(f"💰 Finance filter: {len(all_papers)} → {len(filtered_papers)} papers")
        
        if start_date or end_date:
            filtered_papers = self._filter_by_date(filtered_papers, start_date, end_date)
        
        return filtered_papers[:max_results]