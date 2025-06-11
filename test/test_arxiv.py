import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from aioresponses import aioresponses

# Clean imports now that package is properly installed
from src.arxiv.client import AsyncArxivClient, ArxivAPIError
from src.arxiv.parser import ArxivXMLParser, ArxivPaper


# Sample XML response for testing
SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <link href="http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&amp;id_list=&amp;start=0&amp;max_results=2" rel="self" type="application/atom+xml"/>
  <title type="html">ArXiv Query: search_query=cat:q-fin.TR&amp;id_list=&amp;start=0&amp;max_results=2</title>
  <id>http://arxiv.org/api/test</id>
  <updated>2024-06-10T00:00:00-04:00</updated>
  <opensearch:totalResults>150</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>2</opensearch:itemsPerPage>
  
  <entry>
    <id>http://arxiv.org/abs/2406.12345v1</id>
    <updated>2024-06-10T09:00:00Z</updated>
    <published>2024-06-10T09:00:00Z</published>
    <title>Algorithmic Trading with Deep Reinforcement Learning</title>
    <summary>This paper presents a novel approach to algorithmic trading using deep reinforcement learning techniques. We demonstrate improved performance on high-frequency trading scenarios.</summary>
    <author>
      <name>John Smith</name>
    </author>
    <author>
      <name>Jane Doe</name>
    </author>
    <arxiv:comment>15 pages, 8 figures</arxiv:comment>
    <link href="http://arxiv.org/abs/2406.12345v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2406.12345v1.pdf" rel="related" type="application/pdf"/>
    <category term="q-fin.TR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  
  <entry>
    <id>http://arxiv.org/abs/2406.54321v1</id>
    <updated>2024-06-09T15:30:00Z</updated>
    <published>2024-06-09T15:30:00Z</published>
    <title>Market Microstructure Analysis Using Machine Learning</title>
    <summary>We analyze market microstructure patterns using advanced machine learning techniques to predict short-term price movements and liquidity dynamics.</summary>
    <author>
      <name>Alice Johnson</name>
    </author>
    <arxiv:comment>22 pages, 12 figures, accepted to Journal of Finance</arxiv:comment>
    <arxiv:journal_ref>Journal of Finance, 2024</arxiv:journal_ref>
    <link href="http://arxiv.org/abs/2406.54321v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2406.54321v1.pdf" rel="related" type="application/pdf"/>
    <category term="q-fin.TR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="q-fin.ST" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>"""

EMPTY_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>0</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>0</opensearch:itemsPerPage>
</feed>"""


class TestArxivClient:
    """Test suite for AsyncArxivClient"""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initializes correctly"""
        client = AsyncArxivClient(delay_seconds=2.0)
        assert client.delay_seconds == 2.0
        assert client.base_url == "http://export.arxiv.org/api/query"
        assert client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:  # Very fast for testing
            assert client.session is not None
            assert not client.session.closed
        # Session should be closed after context exit
        assert client.session.closed

    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test manual session start/stop"""
        client = AsyncArxivClient(delay_seconds=0.01)
        
        # Initially no session
        assert client.session is None
        
        # Start session
        await client.start_session()
        assert client.session is not None
        assert not client.session.closed
        
        # Close session
        await client.close_session()
        assert client.session.closed

    @pytest.mark.asyncio
    async def test_search_papers_with_mock(self):
        """Test basic search with mocked HTTP response"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                # Mock the arXiv API response
                expected_url = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending"
                m.get(expected_url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                result = await client.search_papers("cat:q-fin.TR", max_results=100)
                
                assert isinstance(result, str)
                assert "2406.12345" in result
                assert "Algorithmic Trading" in result

    @pytest.mark.asyncio
    async def test_search_papers_with_dates(self):
        """Test search with date filtering"""
        start_date = "2024-01-01"
        end_date = "2024-06-01"
        
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                # The URL should include the converted dates
                expected_query = "cat:q-fin.TR AND submittedDate:[202401010000+TO+202406012359]"
                m.get(f"http://export.arxiv.org/api/query?search_query={expected_query}&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending", 
                      body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                result = await client.search_papers("cat:q-fin.TR", start_date, end_date, max_results=50)
                
                assert isinstance(result, str)
                assert "totalResults" in result

    @pytest.mark.asyncio
    async def test_search_trading_papers(self):
        """Test convenience method for trading papers"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                expected_url = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=200&sortBy=submittedDate&sortOrder=descending"
                m.get(expected_url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                result = await client.search_trading_papers(max_results=200)
                
                assert isinstance(result, str)
                assert "q-fin.TR" in result

    @pytest.mark.asyncio
    async def test_search_all_quant_finance(self):
        """Test convenience method for all quant finance"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                expected_url = "http://export.arxiv.org/api/query?search_query=cat:q-fin.*&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending"
                m.get(expected_url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                result = await client.search_all_quant_finance()
                
                assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_total_count(self):
        """Test getting total count of results"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                expected_url = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=0&sortBy=submittedDate&sortOrder=descending"
                m.get(expected_url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                count = await client.get_total_count("cat:q-fin.TR")
                
                assert count == 150  # From SAMPLE_ARXIV_XML

    @pytest.mark.asyncio
    async def test_get_total_count_fallback(self):
        """Test total count fallback to max_results=1"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                # First request (max_results=0) fails
                url_0 = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=0&sortBy=submittedDate&sortOrder=descending"
                m.get(url_0, status=400)
                
                # Second request (max_results=1) succeeds
                url_1 = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending"
                m.get(url_1, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                count = await client.get_total_count("cat:q-fin.TR")
                
                assert count == 150

    @pytest.mark.asyncio
    async def test_search_papers_paginated(self):
        """Test paginated search functionality"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                # First batch
                url_1 = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=2&sortBy=submittedDate&sortOrder=descending"
                m.get(url_1, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                # Second batch (empty - end of results)
                url_2 = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=2&max_results=2&sortBy=submittedDate&sortOrder=descending"
                m.get(url_2, body=EMPTY_ARXIV_XML, content_type='application/xml')
                
                results = await client.search_papers_paginated("cat:q-fin.TR", batch_size=2, max_total_results=5)
                
                assert len(results) == 1  # Only first batch had results
                assert isinstance(results[0], str)

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        import time
        
        async with AsyncArxivClient(delay_seconds=0.05) as client:  # 50ms delay for testing
            with aioresponses() as m:
                # Mock both requests with the same URL
                url = "http://export.arxiv.org/api/query?search_query=test&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending"
                m.get(url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                m.get(url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                # Make two requests and measure time
                start_time = time.time()
                await client.search_papers("test", max_results=1)
                await client.search_papers("test", max_results=1)
                elapsed = time.time() - start_time
                
                # Should have delayed by delay_seconds (0.05s for test)
                assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_error_handling_429(self):
        """Test handling of rate limit errors"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                url = "http://export.arxiv.org/api/query?search_query=test&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending"
                # First request: rate limited
                m.get(url, status=429)
                # Second request: success
                m.get(url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                result = await client.search_papers("test", max_results=1)
                assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_error_handling_500(self):
        """Test handling of server errors"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                url = "http://export.arxiv.org/api/query?search_query=test&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending"
                # First request: server error
                m.get(url, status=500)
                # Second request: success
                m.get(url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                result = await client.search_papers("test", max_results=1)
                assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_error_handling_max_retries(self):
        """Test max retries exceeded"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with aioresponses() as m:
                url = "http://export.arxiv.org/api/query?search_query=test&start=0&max_results=1&sortBy=submittedDate&sortOrder=descending"
                # All requests fail
                m.get(url, status=500)
                m.get(url, status=500)
                m.get(url, status=500)
                
                with pytest.raises(ArxivAPIError, match="Max retries exceeded"):
                    await client.search_papers("test", max_results=1)

    @pytest.mark.asyncio
    async def test_invalid_date_format(self):
        """Test validation of date formats"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with pytest.raises(ValueError, match="Invalid date format"):
                await client.search_papers("test", start_date="invalid-date", end_date="2024-01-01")

    @pytest.mark.asyncio
    async def test_invalid_max_results(self):
        """Test validation of max_results parameter"""
        async with AsyncArxivClient(delay_seconds=0.01) as client:
            with pytest.raises(ValueError, match="max_results must be between 1 and 2000"):
                await client.search_papers("test", max_results=3000)

    def test_date_conversion(self):
        """Test date format conversion"""
        start_date = AsyncArxivClient._convert_to_arxiv_date("2024-06-10", is_start=True)
        end_date = AsyncArxivClient._convert_to_arxiv_date("2024-06-10", is_start=False)
        
        assert start_date == "202406100000"
        assert end_date == "202406102359"

    def test_query_string_building(self):
        """Test query string building"""
        client = AsyncArxivClient()
        params = {
            'search_query': 'cat:q-fin.TR',
            'start': 0,
            'max_results': 100
        }
        
        query_string = client._build_query_string(params)
        
        assert 'search_query=cat:q-fin.TR' in query_string
        assert 'start=0' in query_string
        assert 'max_results=100' in query_string


class TestArxivXMLParser:
    """Test suite for ArxivXMLParser"""

    @pytest.fixture
    def parser(self):
        return ArxivXMLParser()

    def test_parse_sample_response(self, parser):
        """Test parsing of sample XML response"""
        papers = parser.parse_response(SAMPLE_ARXIV_XML)
        
        assert len(papers) == 2
        
        # Test first paper
        paper1 = papers[0]
        assert paper1.id == "2406.12345"
        assert "Algorithmic Trading" in paper1.title
        assert len(paper1.authors) == 2
        assert "John Smith" in paper1.authors
        assert "Jane Doe" in paper1.authors
        assert "q-fin.TR" in paper1.categories
        assert "cs.AI" in paper1.categories
        assert paper1.pdf_url == "http://arxiv.org/pdf/2406.12345v1.pdf"
        
        # Test second paper
        paper2 = papers[1]
        assert paper2.id == "2406.54321"
        assert "Market Microstructure" in paper2.title
        assert paper2.journal_ref == "Journal of Finance, 2024"

    def test_parse_empty_response(self, parser):
        """Test parsing of empty XML response"""
        papers = parser.parse_response(EMPTY_ARXIV_XML)
        assert len(papers) == 0

    def test_parse_invalid_xml(self, parser):
        """Test handling of invalid XML"""
        invalid_xml = "This is not valid XML"
        
        with pytest.raises(ValueError, match="Invalid XML response"):
            parser.parse_response(invalid_xml)

    def test_arxiv_paper_dataclass(self):
        """Test ArxivPaper dataclass functionality"""
        from datetime import datetime
        
        paper = ArxivPaper(
            id="test123",
            title="Test Paper",
            authors=["Test Author"],
            abstract="Test abstract",
            submitted_date=datetime.now(),
            updated_date=datetime.now(),
            categories=["q-fin.TR"],
            pdf_url="http://test.com/pdf",
            arxiv_url="http://test.com/abs"
        )
        
        assert paper.id == "test123"
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 1
        assert "q-fin.TR" in paper.categories


class TestIntegration:
    """Integration tests combining client and parser"""

    @pytest.mark.asyncio
    async def test_full_search_and_parse_flow(self):
        """Test complete flow from search to parsed results"""
        async with AsyncArxivClient(delay_seconds=0.1) as client:
            parser = ArxivXMLParser()
            
            with aioresponses() as m:
                url = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
                m.get(url, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                # Search and parse
                xml_data = await client.search_trading_papers(max_results=10)
                papers = parser.parse_response(xml_data)
                
                assert len(papers) == 2
                assert all(isinstance(paper, ArxivPaper) for paper in papers)
                assert any("Algorithmic Trading" in paper.title for paper in papers)

    @pytest.mark.asyncio
    async def test_pagination_with_parsing(self):
        """Test paginated search with parsing"""
        async with AsyncArxivClient(delay_seconds=0.1) as client:
            parser = ArxivXMLParser()
            
            with aioresponses() as m:
                # First batch
                url_1 = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=0&max_results=2&sortBy=submittedDate&sortOrder=descending"
                m.get(url_1, body=SAMPLE_ARXIV_XML, content_type='application/xml')
                
                # Second batch (empty)
                url_2 = "http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&start=2&max_results=2&sortBy=submittedDate&sortOrder=descending"
                m.get(url_2, body=EMPTY_ARXIV_XML, content_type='application/xml')
                
                # Get paginated results and parse
                xml_responses = await client.search_papers_paginated("cat:q-fin.TR", batch_size=2)
                
                all_papers = []
                for xml_data in xml_responses:
                    papers = parser.parse_response(xml_data)
                    all_papers.extend(papers)
                
                assert len(all_papers) == 2  # From first batch only
                assert all(isinstance(paper, ArxivPaper) for paper in all_papers)


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Add requirements for testing
"""
To run these tests, install test dependencies:

pip install pytest pytest-asyncio aioresponses

Or add to pyproject.toml:
[tool.poetry.group.test.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
aioresponses = "^0.7.0"

Run tests with:
pytest test/test_arxiv.py -v
"""