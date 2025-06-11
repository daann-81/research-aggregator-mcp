# SSRN Integration Implementation Plan

## Overview

This document outlines the implementation plan for integrating SSRN (Social Science Research Network) into the Research Aggregator MCP server, providing similar capabilities to the existing ArXiv integration.

## Research Summary

### SSRN API Structure
Based on research, SSRN provides an undocumented API that can be accessed for retrieving academic papers:

- **Base URL:** `https://api.ssrn.com/content/v1/bindings/204/papers`
- **Response Format:** JSON (unlike ArXiv's XML)
- **Total Papers:** Approximately 43,602 papers available
- **Pagination:** Maximum 200 results per request

### API Parameters
**Direct API Support:**
- `index` - Starting position for pagination (0, 200, 400...)
- `count` - Number of results per page (maximum 200)
- `sort` - Sort order (0 = default sorting)

**⚠️ Important Discovery: No Direct Category Filtering**
The API does NOT support direct filtering parameters like `jel`, `category`, or `query`. All filtering must be done client-side.

### Search Capabilities
**Available through client-side filtering:**
- JEL (Journal of Economic Literature) classification codes - **filtered after retrieval**
- Author name searches - **filtered after retrieval**
- Date range filtering - **filtered after retrieval**
- University affiliation searches - **filtered after retrieval**
- Full-text search across title, abstract - **filtered after retrieval**

## Implementation Architecture

### File Structure
```
src/
├── ssrn/
│   ├── __init__.py         # Package initialization
│   ├── client.py           # AsyncSSRNClient
│   └── parser.py           # SSRNJSONParser & SSRNPaper
integration/
└── test_ssrn_connection.py # SSRN API testing
docs/
└── SSRN.md               # This documentation
```

## Phase 1: Core SSRN Components

### 1. `src/ssrn/__init__.py`
- Package initialization file
- Export main classes: `AsyncSSRNClient`, `SSRNPaper`, `SSRNJSONParser`, `SSRNAPIError`

### 2. `src/ssrn/client.py`
**AsyncSSRNClient Class Features:**
- Async HTTP client using aiohttp
- Rate limiting (3-second delays like ArXiv)
- Async context manager support
- Pagination handling for large result sets
- Custom error handling with `SSRNAPIError`

**Key Methods:**
- `get_all_papers(max_results=2000)` - Retrieve all papers with pagination
- `search_by_jel(jel_code, max_results=200)` - Client-side JEL filtering
- `search_by_author(author_name, max_results=200)` - Client-side author filtering  
- `search_by_text(query, max_results=200)` - Client-side text search
- `get_recent_papers(months_back=6, max_results=200)` - Client-side date filtering
- `_paginate_results()` - Handle API pagination internally
- `_filter_papers()` - Client-side filtering logic
- `_handle_rate_limit()` - Rate limiting implementation

### 3. `src/ssrn/parser.py`
**SSRNPaper Dataclass:**
```python
@dataclass
class SSRNPaper:
    ssrn_id: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: datetime
    jel_codes: List[str]
    download_count: int
    pdf_url: str
    ssrn_url: str
    university_affiliations: List[str]
    approval_status: str
    doi: Optional[str] = None
    journal_ref: Optional[str] = None
    comments: Optional[str] = None
```

**SSRNJSONParser Class:**
- `parse_response(json_data)` - Parse SSRN JSON response
- `_parse_paper(paper_data)` - Parse individual paper data
- `_extract_authors()` - Extract and clean author information
- `_extract_jel_codes()` - Parse JEL classification codes
- `_parse_date()` - Handle date parsing
- `filter_by_jel(papers, jel_codes)` - Filter papers by JEL codes
- `filter_by_author(papers, author_name)` - Filter papers by author
- `filter_by_text(papers, query)` - Filter papers by text search
- `filter_by_date(papers, start_date, end_date)` - Filter papers by date range
- Error handling for malformed data

## Phase 2: Integration Testing

### `integration/test_ssrn_connection.py`
**Test Coverage:**
- API connectivity verification
- Response format validation
- Search function testing:
  - Basic text search
  - JEL code search (e.g., "G12" for asset pricing)
  - Author search
  - Date range filtering
- Pagination testing
- Rate limiting verification
- Error handling validation
- Parser accuracy testing

**Test Examples:**
```python
async def test_basic_search():
    # Test general finance search
    
async def test_jel_search():
    # Test JEL code "G12" (Asset Pricing)
    
async def test_author_search():
    # Test specific author search
    
async def test_pagination():
    # Test handling of large result sets
```

## API Documentation

### Endpoint Structure
```
GET https://api.ssrn.com/content/v1/bindings/204/papers
```

### Parameters
| Parameter | Type | Description | Default | Notes |
|-----------|------|-------------|---------|-------|
| index | integer | Starting position for results | 0 | Only pagination parameter |
| count | integer | Number of results (max 200) | 200 | Maximum per request |
| sort | integer | Sort order | 0 | Limited sorting options |

**❌ NOT Supported:**
- `jel` - JEL code filtering
- `query` - Text search
- `author` - Author filtering
- `category` - Subject category filtering
- `date` - Date range filtering

### Response Format
```json
{
  "papers": [
    {
      "id": "paper_id",
      "title": "Paper Title",
      "authors": [...],
      "abstract": "Abstract text",
      "jel_codes": ["G12", "G13"],
      "publication_date": "2024-01-01",
      "download_count": 150,
      "pdf_url": "https://...",
      "university_affiliations": [...]
    }
  ],
  "total_count": 43602
}
```

## Error Handling Strategy

### Custom Exceptions
- `SSRNAPIError` - Base exception for SSRN API errors
- `SSRNRateLimitError` - Rate limiting exceeded
- `SSRNParseError` - JSON parsing errors
- `SSRNConnectionError` - Network connectivity issues

### Error Scenarios
- API rate limiting (implement exponential backoff)
- Invalid JEL codes
- Malformed JSON responses
- Network timeouts
- Authentication errors (if any)

## Rate Limiting Policy

### Implementation Strategy
- 3-second delay between requests (similar to ArXiv)
- Exponential backoff for rate limit errors
- Configurable delay timing
- Request queuing for high-volume operations

## Testing Strategy

### Unit Tests
- Parser functionality
- Date handling
- Error handling
- Data validation

### Integration Tests
- Live API connectivity
- Response format validation
- Search functionality
- Pagination handling

### Performance Tests
- Rate limiting effectiveness
- Large result set handling
- Memory usage with pagination

## Future Enhancements

### Phase 3: MCP Server Integration
- Add SSRN tools to MCP server
- Combined ArXiv + SSRN search capabilities
- Cross-platform paper deduplication

### Phase 4: Advanced Features
- Advanced search with boolean operators
- Citation network analysis
- Paper recommendation system
- Export functionality (BibTeX, EndNote)

### Phase 5: Data Enrichment
- Paper categorization
- Sentiment analysis of abstracts
- Trending topics identification
- Author collaboration networks

## Client-Side Filtering Strategy

### JEL Code Filtering Implementation
**Key Finance JEL Codes:**
- **G00-G59**: Financial Economics (general)
- **G10-G19**: Financial Markets
- **G12**: Asset Pricing, Trading Volume
- **G13**: Contingent Pricing, Futures Pricing  
- **G14**: Information and Market Efficiency
- **G20-G29**: Financial Institutions and Services

### Filtering Approach
1. **Bulk Retrieval**: Get all papers via API pagination
2. **Local Filtering**: Apply JEL, author, date, text filters client-side
3. **Caching Strategy**: Cache filtered results by category
4. **Performance**: Minimize API calls, maximize local processing

## Implementation Timeline

### Week 1: Core Components
- [x] Research SSRN API structure
- [x] Discover API filtering limitations
- [ ] Implement `AsyncSSRNClient` with bulk retrieval
- [ ] Implement `SSRNJSONParser` with filtering methods
- [ ] Create integration tests

### Week 2: Testing & Refinement
- [ ] Test bulk paper retrieval and pagination
- [ ] Test client-side filtering accuracy
- [ ] Performance optimization for large datasets
- [ ] Error handling refinement
- [ ] Documentation updates

### Week 3: MCP Integration
- [ ] Add SSRN tools to MCP server
- [ ] Implement filtered search tools
- [ ] Update shared handlers
- [ ] Integration testing
- [ ] User documentation

## Notes and Considerations

### API Limitations
- **No server-side filtering** - All filtering must be done client-side
- Undocumented API may change without notice
- Rate limiting policies not officially documented
- Maximum 200 results per request (requires pagination for full dataset)
- Maximum result set of ~43,602 papers total
- Potential authentication requirements in future

### Performance Implications
- **Full dataset retrieval required** for comprehensive searches
- **Higher memory usage** due to client-side filtering
- **Slower initial response** due to bulk data retrieval
- **Caching essential** to avoid repeated full dataset downloads

### Data Quality
- Inconsistent data formats possible
- Missing fields in some papers
- Duplicate paper handling needed
- Date format variations

### Compliance
- Respect SSRN's terms of service
- Implement appropriate rate limiting
- Consider caching strategies
- Monitor for API changes

## References

- SSRN Main Site: https://www.ssrn.com/
- SSRN Papers: https://papers.ssrn.com/
- JEL Classification: https://www.aeaweb.org/jel/guide/jel.php
- API Endpoint: https://api.ssrn.com/content/v1/bindings/204/papers