# async_client.py
import aiohttp
import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List
import random

from rich.logging import RichHandler

# Setup Rich logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=True)],
)

logger = logging.getLogger(__name__)


class ArxivAPIError(Exception):
    """Custom exception for arXiv API errors"""
    pass


class AsyncArxivClient:
    """Async arXiv API client with robust error handling and rate limiting"""

    def __init__(self, delay_seconds: float = 3.0):
        self.base_url = "http://export.arxiv.org/api/query"
        self.delay_seconds = delay_seconds
        self.last_request_time = 0
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Headers
        self.headers = {
            "User-Agent": "ArxivMCPClient/1.0 (Research; Python)"
        }

        logger.info(f"🚀 Initialized AsyncArxivClient with [bold cyan]{delay_seconds}s[/bold cyan] delay")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()

    async def start_session(self):
        """Start the aiohttp session"""
        try:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=self.timeout
                )
                logger.debug("🔗 [green]HTTP session started[/green]")
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise ArxivAPIError(f"Could not initialize HTTP session: {e}")

    async def close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("🔌 [yellow]HTTP session closed[/yellow]")

    async def _throttle(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            logger.debug(f"⏱️  Throttling: sleeping for [yellow]{sleep_time:.2f}[/yellow] seconds")
            await asyncio.sleep(sleep_time)
        self.last_request_time = time.time()

    async def _make_request(self, params: Dict, max_retries: int = 3) -> str:
        """Make async request with retries and exponential backoff"""
        if not self.session or self.session.closed:
            await self.start_session()

        if self.session is None:
            raise ArxivAPIError("Failed to initialize HTTP session")
        
        await self._throttle()
        
        # Build URL manually to avoid encoding issues with arXiv
        query_string = self._build_query_string(params)
        full_url = f"{self.base_url}?{query_string}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Making arXiv API request (attempt [bold]{attempt + 1}[/bold]/[bold]{max_retries}[/bold])")
                logger.debug(f"Full URL: [dim]{full_url}[/dim]")
                
                async with self.session.get(full_url) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        logger.info(f"✅ Successfully received [green]{len(xml_data):,}[/green] characters")
                        return xml_data
                    elif response.status == 429:
                        backoff_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"🚫 Rate limited (429). Backing off for [red]{backoff_time:.2f}[/red] seconds")
                        await asyncio.sleep(backoff_time)
                        continue
                    elif response.status >= 500:
                        backoff_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"🔥 Server error ([red]{response.status}[/red]). Retrying in [yellow]{backoff_time:.2f}[/yellow] seconds")
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        response.raise_for_status()
                        
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Request timeout (attempt [yellow]{attempt + 1}[/yellow]/[yellow]{max_retries}[/yellow])")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise ArxivAPIError("Request timed out after all retries")
                    
            except aiohttp.ClientError as e:
                logger.warning(f"🔌 Connection error (attempt [yellow]{attempt + 1}[/yellow]/[yellow]{max_retries}[/yellow]): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise ArxivAPIError(f"Connection failed after all retries: {e}")
                    
            except Exception as e:
                logger.error(f"💥 Unexpected request error: [red]{e}[/red]")
                raise ArxivAPIError(f"Request failed: {e}")
        
        raise ArxivAPIError("Max retries exceeded")

    def _build_query_string(self, params: Dict) -> str:
        """Build query string manually to avoid URL encoding issues with arXiv"""
        query_parts = []
        
        for key, value in params.items():
            if key == 'search_query':
                # Don't encode the search query - arXiv expects raw format
                query_parts.append(f"{key}={value}")
            else:
                # Encode other parameters normally
                from urllib.parse import quote
                query_parts.append(f"{key}={quote(str(value))}")
        
        return "&".join(query_parts)

    async def search_papers(self, query: str, start_date: Optional[str] = None, end_date: Optional[str] = None,
                           max_results: int = 100, start_index: int = 0) -> str:
        """
        Universal paper search method
        
        Args:
            query: Search query (e.g., 'cat:q-fin.TR', 'au:smith', 'ti:machine learning')
            start_date: Optional start date in 'YYYY-MM-DD' format
            end_date: Optional end date in 'YYYY-MM-DD' format
            max_results: Maximum papers to retrieve (up to 2000 per request)
            start_index: Starting index for pagination
            
        Returns:
            Raw XML response
        """
        # Validate inputs
        if max_results and not 1 <= max_results <= 2000:
            raise ValueError("max_results must be between 1 and 2000")
        
        # Build date filter if provided
        if start_date and end_date:
            self._validate_date_format(start_date)
            self._validate_date_format(end_date)
            
            arxiv_start = self._convert_to_arxiv_date(start_date, is_start=True)
            arxiv_end = self._convert_to_arxiv_date(end_date, is_start=False)
            
            # Add date filter to query
            query = f"{query} AND submittedDate:[{arxiv_start}+TO+{arxiv_end}]"
        
        logger.info(f"🔍 Searching arXiv: [cyan]{query}[/cyan]")
        
        params = {
            'search_query': query,
            'start': start_index,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            return await self._make_request(params)
        except Exception as e:
            logger.error(f"❌ Failed to search arXiv: [red]{e}[/red]")
            raise

    async def search_papers_paginated(self, query: str, start_date: Optional[str] = None, end_date: Optional[str] = None,
                                     max_total_results: Optional[int] = None, batch_size: int = 1000) -> List[str]:
        """
        Search papers with automatic pagination to get all results
        
        Args:
            query: Search query
            start_date: Optional start date in 'YYYY-MM-DD' format
            end_date: Optional end date in 'YYYY-MM-DD' format
            max_total_results: Maximum total results to fetch (None = unlimited)
            batch_size: Results per API call (max 2000)
            
        Returns:
            List of XML responses from each batch
        """
        if batch_size > 2000:
            batch_size = 2000
            logger.warning("🔧 Batch size capped at 2000 (arXiv limit)")
        
        all_responses = []
        start_index = 0
        total_fetched = 0
        
        logger.info(f"📦 Starting paginated search with batch_size={batch_size}")
        
        while True:
            # Calculate how many to fetch in this batch
            if max_total_results:
                remaining = max_total_results - total_fetched
                current_batch_size = min(batch_size, remaining)
                if current_batch_size <= 0:
                    logger.info("🏁 Reached max_total_results limit")
                    break
            else:
                current_batch_size = batch_size
            
            logger.info(f"📄 Fetching batch {len(all_responses) + 1} (start_index={start_index}, batch_size={current_batch_size})")
            
            # Fetch this batch
            xml_data = await self.search_papers(
                query, start_date, end_date, 
                max_results=current_batch_size,
                start_index=start_index
            )
            
            # Count actual results in this batch
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(xml_data)
                entries = root.findall('atom:entry', {'atom': 'http://www.w3.org/2005/Atom'})
                batch_count = len(entries)
            except ET.ParseError:
                logger.error("❌ Failed to parse XML response")
                break
            
            if batch_count == 0:
                logger.info("🏁 No more results available")
                break
            
            all_responses.append(xml_data)
            total_fetched += batch_count
            
            logger.info(f"✅ Retrieved {batch_count} papers (total: {total_fetched})")
            
            # Check if we got fewer results than requested (end of results)
            if batch_count < current_batch_size:
                logger.info("🏁 Reached end of available results")
                break
            
            start_index += batch_count
            
            # Safety check to avoid infinite loops
            if start_index >= 50000:
                logger.warning("⚠️ Reached arXiv's ~50k result limit, stopping")
                break
        
        logger.info(f"🎉 Pagination complete: {len(all_responses)} batches, {total_fetched} total papers")
        return all_responses

    async def get_total_count(self, query: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """
        Get the total count of results for a query without fetching paper data
        
        Returns:
            Total number of papers matching the query
        """
        # Fetch with max_results=0 to get just metadata (if supported) or minimal data
        try:
            # Try with 0 results first (just metadata)
            xml_data = await self.search_papers(query, start_date, end_date, max_results=0)
        except:
            # Fallback to 1 result if 0 is not supported
            xml_data = await self.search_papers(query, start_date, end_date, max_results=1)
        
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_data)
            # Look for opensearch:totalResults
            total_elem = root.find('opensearch:totalResults', 
                                 {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'})
            
            if total_elem is not None and total_elem.text:
                total_count = int(total_elem.text)
                logger.info(f"📊 Total results available: [bold blue]{total_count:,}[/bold blue]")
                return total_count
            else:
                logger.warning("⚠️ Could not determine total count")
                return 0
                
        except (ET.ParseError, ValueError) as e:
            logger.error(f"❌ Failed to parse total count: {e}")
            return 0

    @staticmethod
    def _convert_to_arxiv_date(date_str: str, is_start: bool = True) -> str:
        """Convert YYYY-MM-DD to arXiv date format YYYYMMDDHHMM"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        if is_start:
            return date_obj.strftime('%Y%m%d0000')  # Start of day: 00:00
        else:
            return date_obj.strftime('%Y%m%d2359')  # End of day: 23:59

    @staticmethod
    def _validate_date_format(date_str: str):
        """Validate date format"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")

    # Convenience methods for common searches
    async def search_trading_papers(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                                   max_results: int = 100) -> str:
        """Search for trading and market microstructure papers"""
        return await self.search_papers("cat:q-fin.TR", start_date, end_date, max_results)

    async def search_all_quant_finance(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                                      max_results: int = 100) -> str:
        """Search all quantitative finance categories"""
        return await self.search_papers("cat:q-fin.*", start_date, end_date, max_results)
    
    async def get_all_trading_papers(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                                    max_total_results: Optional[int] = None) -> List[str]:
        """Get all trading papers using pagination"""
        return await self.search_papers_paginated("cat:q-fin.TR", start_date, end_date, max_total_results)
    
    async def get_all_quant_finance_papers(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                                          max_total_results: Optional[int] = None) -> List[str]:
        """Get all quantitative finance papers using pagination"""
        return await self.search_papers_paginated("cat:q-fin.*", start_date, end_date, max_total_results)