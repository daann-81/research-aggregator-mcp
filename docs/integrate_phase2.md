# Phase 2: Unified Source-Agnostic Search (TDD Approach)

## Overview
Create unified search tools that aggregate results from multiple sources (arXiv, SSRN, future sources) with source filtering capabilities. Tools will return ALL available papers with metadata, letting callers assess relevance using their own logic.

## Phase 1: Write Failing Tests First
### Test Files to Create:
- `test/test_unified_search.py` - Unified search functionality tests

### Test Requirements:
- ✅ All tests must RUN (no syntax errors)
- ✅ All tests must FAIL initially (proving they test expected behavior)
- ✅ NO pytest.skip() statements
- ✅ NO commented out assertions
- ✅ Full assertion coverage for expected behavior

### Test Categories:
- **Multi-Source Search Tests**: Search across arXiv + SSRN with combined results
- **Source Filtering Tests**: Filter results by source (`arxiv`, `ssrn`, `all`)
- **Raw Paper Retrieval Tests**: Return ALL papers regardless of category/topic
- **Metadata Preservation Tests**: Ensure all categories/metadata preserved for caller assessment
- **Deduplication Tests**: Handle duplicate papers across sources
- **Source-Agnostic Tool Tests**: Verify existing tools work with optional `source` parameter
- **Edge Case Tests**: Empty results, single source failures, invalid source names
- **Error Handling Tests**: Network failures, invalid parameters

## Phase 2: Create Skeleton Implementation
### Files to Modify:
- `src/server/shared.py` - Add unified search handlers with dummy returns
- Update existing handlers to accept optional `source` parameter

### New Tool Design:
- **`search_papers()`**: Generic search by text/author across all sources
- **`get_recent_papers()`**: Get papers from last N months, all categories/sources
- **Existing tools**: Add optional `source` parameter for filtering

### Skeleton Requirements:
- ✅ All functions defined with proper signatures including optional `source` parameter
- ✅ Return dummy/wrong values that make tests FAIL
- ✅ Include proper type hints and docstrings
- ✅ Tests can run but should fail on assertions

## Phase 3: Make Tests Pass Incrementally
### Implementation Order:
1. **Source Parameter Integration**: Add optional `source` filtering to existing tools
2. **Multi-Source Aggregation**: Implement parallel searching across sources
3. **Raw Paper Retrieval**: Remove topic/category filtering - return ALL papers
4. **Deduplication Logic**: Remove duplicate papers based on title/author similarity
5. **Metadata Preservation**: Ensure all categories/affiliations/metadata preserved
6. **Error Handling**: Graceful degradation when one source fails

## Phase 4: Tool Description Updates
- **Remove Topic Bias**: Tools describe paper retrieval, not finance-specific search
- **Caller Assessment**: Descriptions emphasize that relevance assessment is caller's responsibility
- **Metadata Focus**: Highlight available metadata fields for caller's filtering logic

## Key Design Principles:
1. **No Pre-filtering**: Return ALL papers matching date/text criteria
2. **Full Metadata**: Preserve all categories, abstracts, affiliations for caller analysis
3. **Source Transparency**: Always indicate paper source in results
4. **Backward Compatibility**: Existing tools maintain current behavior unless `source` specified