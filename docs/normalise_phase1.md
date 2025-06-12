# Phase 1: Common Paper Schema with Test-Driven Development

## Overview
Create a unified paper schema called `AcademicPaper` using test-driven development approach, ensuring no regressions to existing arXiv functionality.

## Goals
- Establish a common data model for academic papers from multiple sources
- Use test-driven development to ensure robust implementation
- Maintain backward compatibility with existing arXiv functionality
- Prepare foundation for Phase 2 SSRN integration

## Phase 1 Implementation Steps (Test-Driven Approach)

### 1. ✅ Write Normalization Test Cases First (`test/test_paper_normalization.py`)
**COMPLETED** - Comprehensive test suite created with:

- **`test_arxiv_to_academic_paper()`**: Test ArxivPaper → AcademicPaper conversion
  - ✅ Test all field mappings
  - ✅ Test required field validation  
  - ✅ Test optional field handling
  - ✅ Test date format conversion
  - ✅ Test edge cases (empty fields, malformed data)
  - ✅ Test URL validation
  - ✅ Test invalid data handling with expected exceptions
  - ✅ Test type validation

- **`test_ssrn_to_academic_paper()`**: Test SSRNPaper → AcademicPaper conversion
  - ✅ Test all field mappings
  - ✅ Test missing abstract handling (SSRN doesn't provide abstracts)
  - ✅ Test author list conversion
  - ✅ Test affiliation mapping
  - ✅ Test date format differences
  - ✅ Test edge cases and validation
  - ✅ Test invalid data handling with expected exceptions
  - ✅ Test type validation

- **`test_normalization_helpers()`**: Test helper functions
  - ✅ Test title cleaning (HTML removal, whitespace normalization)
  - ✅ Test author list cleaning (empty string removal)
  - ✅ Test URL normalization (empty string to None conversion)
  - ✅ Test safe integer conversion with fallbacks

**Status**: All tests are written and currently FAILING as expected (TDD approach)

### 2. ✅ Create AcademicPaper Schema Skeleton (`src/common/paper.py`)
**COMPLETED** - Basic structure implemented with:
- Define `AcademicPaper` dataclass with normalized fields:
  - `id`: Unique identifier (arXiv ID or SSRN ID)
  - `title`: Paper title (cleaned of HTML/formatting)
  - `authors`: List of author names
  - `abstract`: Paper abstract/summary
  - `publication_date`: Date when paper was published/submitted
  - `source`: Source database ("arXiv" or "SSRN")
  - `categories`: List of subject categories
  - `url`: Main paper URL
  - `pdf_url`: Direct PDF download URL (if available)
  - `journal_ref`: Journal reference (optional)
  - `doi`: Digital Object Identifier (optional)
  - `download_count`: Number of downloads (optional)
  - `affiliations`: Author affiliations (optional)

- Add conversion functions:
  - `from_arxiv_paper(arxiv_paper: ArxivPaper) -> AcademicPaper`
  - `from_ssrn_paper(ssrn_paper: SSRNPaper) -> AcademicPaper`

- Add utility methods:
  - `to_dict()`: Convert to dictionary for JSON serialization
  - `__str__()`: Human-readable representation

### 6. Update Existing Code to Use AcademicPaper
- Modify `src/server/shared.py`:
  - Update `paper_to_dict()` function to work with AcademicPaper
  - Modify existing handlers to convert ArxivPaper → AcademicPaper
  - Ensure all existing functionality is preserved
  - Maintain identical JSON output format for backward compatibility

- Keep existing tool schemas and descriptions unchanged (no regressions)

- ✅ AcademicPaper dataclass with all required and optional fields
- ✅ Stub conversion functions (`from_arxiv_paper`, `from_ssrn_paper`) that return dummy data
- ✅ Stub helper functions (`_clean_title`, `_clean_authors`, etc.) with no logic
- ✅ JSON serialization method (`to_dict()`)
- ✅ String representation method (`__str__()`)

**Status**: Skeleton complete, tests can run and fail as expected

### 3. 🔄 NEXT: Implement Real Conversion Logic
- Implement actual field mapping in `from_arxiv_paper()`
- Implement actual field mapping in `from_ssrn_paper()`
- Implement helper functions with real cleaning logic
- Make tests pass one by one

### 4. 📋 PENDING: Additional Unit Testing (`test/test_academic_paper.py`)
- Test AcademicPaper dataclass creation and validation
- Test JSON serialization/deserialization
- Test edge cases and error handling
- Test string representations and equality

### 5. 📋 PENDING: Update Existing Code and Regression Testing
- Update `test/test_arxiv.py` to use AcademicPaper where appropriate
- Ensure backward compatibility and regression testing

## Test Coverage Requirements
- `test_academic_paper.py`: 
  - Core dataclass functionality
  - Field validation and type checking
  - JSON serialization edge cases
  - String representation methods

- `test_paper_normalization.py`: 
  - Conversion function accuracy
  - Field mapping correctness
  - Handling of None/missing values
  - Date format standardization
  - URL format validation

## Regression Testing Strategy
- Run existing integration tests to ensure no functionality breaks
- Verify MCP server tools return identical JSON structure as before
- Test with real arXiv data to ensure output consistency
- Compare before/after JSON outputs for identical papers

## Implementation Guidelines

### Data Mapping Strategy
- **ArxivPaper → AcademicPaper**:
  - `id` ← `id`
  - `title` ← `title`
  - `authors` ← `authors`
  - `abstract` ← `abstract`
  - `publication_date` ← `submitted_date`
  - `source` ← "arXiv"
  - `categories` ← `categories`
  - `url` ← `arxiv_url`
  - `pdf_url` ← `pdf_url`
  - `journal_ref` ← `journal_ref`
  - `doi` ← `doi`

- **SSRNPaper → AcademicPaper**:
  - `id` ← `ssrn_id`
  - `title` ← `title`
  - `authors` ← `authors`
  - `abstract` ← None (SSRN doesn't provide abstracts via API)
  - `publication_date` ← `approved_date`
  - `source` ← "SSRN"
  - `categories` ← None (SSRN doesn't provide this)
  - `url` ← `ssrn_url`
  - `pdf_url` ← None (SSRN doesn't provide direct PDF URLs)
  - `download_count` ← `download_count`
  - `affiliations` ← `university_affiliations`

### Error Handling
- Graceful handling of missing required fields
- Default values for optional fields
- Validation of date formats
- URL format validation
- Type checking for all fields

## Success Criteria
- [ ] All existing tests pass (no regressions)
- [ ] New unit tests achieve >95% coverage on AcademicPaper schema
- [ ] MCP server tools return identical JSON structure as before
- [ ] Integration tests pass with new schema
- [ ] Code is ready for Phase 2 (SSRN integration)

## Risk Mitigation
- Extensive regression testing to catch breaking changes
- Backward compatibility maintained through identical JSON output
- Gradual rollout with fallback to original implementation if needed
- Comprehensive unit tests to catch edge cases early

## Next Steps (Phase 2)
After Phase 1 completion:
1. Integrate SSRN search functionality into MCP server
2. Create aggregated search handlers combining arXiv and SSRN
3. Update tool descriptions to be source-agnostic
4. Implement deduplication logic for papers appearing in both sources