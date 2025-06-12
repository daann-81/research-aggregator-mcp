# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Research Aggregator MCP (Model Context Protocol) server that provides tools for searching and retrieving academic papers from arXiv, specifically focused on quantitative finance and algorithmic trading research.

### Architecture

The project consists of several main components:

1. **Main Entry Point** (`src/main.py`) - Command-line interface with transport selection (stdio/HTTP/SSE)
2. **Server Implementations**:
   - `src/server/stdio_server.py` - stdio transport using low-level MCP server API
   - `src/server/http_server.py` - HTTP/SSE transport using FastMCP framework
   - `src/server/shared.py` - Shared tool handlers and schemas
3. **arXiv Components**:
   - `src/arxiv/client.py` - Async HTTP client for arXiv API with rate limiting and error handling
   - `src/arxiv/parser.py` - Parses arXiv XML responses into structured Python objects

### Key Features

- **search_trading_papers** - Search for algorithmic trading and market microstructure papers
- **search_quant_finance_papers** - Search across all quantitative finance categories
- **get_recent_papers** - Get papers from the last X months with category filtering

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Testing
```bash
# Run unit tests
pytest

# Run integration tests
python integration/test_mcp_server.py
python integration/test_arxiv_connection.py

# Run tests with verbose output
pytest -v
```

### Development Tools
```bash
# Check code formatting (if available)
black src/ test/

# Type checking (if mypy is installed)
mypy src/

# Lint code (if flake8 is installed)
flake8 src/
```

### Running the Server
```bash
# Run with stdio transport (default, for Claude Desktop)
python src/main.py --transport stdio

# Run with HTTP/SSE transport (for web integration)
python src/main.py --transport sse --port 3001

# Run with HTTP streamable transport
python src/main.py --transport streamable --port 3001

# Custom host and port
python src/main.py --transport sse --host 127.0.0.1 --port 8080
```

## Development Methodology

### Test-Driven Development (TDD) Approach
**ALWAYS follow TDD methodology for all new features and significant changes:**

1. **Write Failing Tests First**: Write comprehensive test cases that define expected behavior and MUST FAIL initially
2. **Create Minimal Implementation**: Create skeleton implementations that make tests runnable but failing
3. **Make Tests Pass**: Implement real functionality iteratively to make tests pass one by one
4. **Refactor**: Clean up code while keeping tests passing

### Critical TDD Rules
- **Tests MUST fail initially** - this proves they're testing the right behavior
- **NO pytest.skip()** - tests should run and fail, not be skipped
- **NO commented out assertions** - all test assertions should be active from day one
- **Skeleton implementations return dummy data** - enough to make tests runnable but wrong enough to fail

### TDD Implementation Planning Template
When asked to implement new features, ALWAYS structure your plan as follows:

```markdown
# Feature Implementation Plan (TDD Approach)

## Overview
[Brief description of what needs to be implemented]

## Phase 1: Write Failing Tests First
### Test Files to Create:
- `test/test_[feature].py` - Core functionality tests

### Test Requirements:
- ✅ All tests must RUN (no syntax errors)
- ✅ All tests must FAIL initially (proving they test expected behavior)
- ✅ NO pytest.skip() statements
- ✅ NO commented out assertions
- ✅ Full assertion coverage for expected behavior

### Test Categories:
- **Happy Path Tests**: Normal usage scenarios with expected outputs
- **Edge Case Tests**: Boundary conditions, empty inputs, malformed data
- **Error Handling Tests**: Invalid inputs with expected exceptions
- **Type Validation Tests**: Ensure correct types returned

## Phase 2: Create Skeleton Implementation
### Files to Create:
- `src/[module]/[feature].py` - Main implementation with dummy returns

### Skeleton Requirements:
- ✅ All functions/classes defined with proper signatures
- ✅ Return dummy/wrong values that make tests FAIL
- ✅ Include proper type hints and docstrings
- ✅ Tests can run but should fail on assertions

## Phase 3: Make Tests Pass Incrementally
### Implementation Order:
1. [First test group to implement - e.g., basic functionality]
2. [Second test group - e.g., edge cases]
3. [Third test group - e.g., error handling]
4. [Continue until all tests pass]

## Phase 4: Integration and Regression Testing
- Update existing code to use new functionality
- Run full test suite to ensure no regressions
```

### Verification Checklist
Before considering TDD phase complete:
- [ ] All tests run without syntax errors
- [ ] All tests initially FAIL (before real implementation)
- [ ] No pytest.skip() statements in codebase
- [ ] No commented out test assertions
- [ ] Skeleton returns dummy data that causes test failures
- [ ] Test failures clearly show what needs to be implemented

### Automatic Testing Rules
**ALWAYS run tests automatically during development:**
- **After implementing any function** - immediately run relevant tests
- **After fixing code** - re-run failed tests to verify fixes
- **Before declaring completion** - run full test suite
- **NO prompting required** - just run tests as part of normal workflow
- **Show test results** - always include pass/fail status in responses

### Test Running Guidelines
- Use `python -m pytest path/to/test.py::TestClass::test_method -v` for specific tests
- Use `python -m pytest path/to/test.py -v` for test file
- Use `python -m pytest` for full suite
- Always include `-v` flag for verbose output
- Run tests immediately after code changes to verify functionality

## Important Implementation Details

### Rate Limiting
The arXiv client (`AsyncArxivClient`) implements rate limiting with a default 3-second delay between requests to respect arXiv's usage policies.

### Error Handling
All components use Rich logging with structured error handling:
- `ArxivAPIError` for API-specific errors
- Exponential backoff for retries
- Comprehensive logging with emoji indicators

### Date Handling
Date parameters use YYYY-MM-DD format but are converted to arXiv's YYYYMMDDHHMM format internally using `_convert_to_arxiv_date()`.

### MCP Integration
The server supports multiple transports:
- **stdio transport** - For Claude Desktop integration using low-level MCP server API
- **HTTP/SSE transport** - For web-based integration using FastMCP framework
- Tool handlers are shared between transports and return JSON-serialized results

### Testing Strategy
- Unit tests in `test/` directory
- Integration tests in `integration/` directory
- Test the MCP server using `integration/test_mcp_server.py` to simulate Claude interactions

## Key Files to Understand

- `src/main.py:16-65` - Command-line interface and transport selection
- `src/server/shared.py:31-224` - Shared tool handlers, schemas, and utilities
- `src/server/stdio_server.py:35-83` - stdio transport tool definitions
- `src/server/http_server.py:36-61` - HTTP transport tool definitions
- `src/arxiv/client.py:155-200` - Core search functionality
- `src/arxiv/parser.py:39-77` - XML parsing logic
- `integration/test_mcp_server.py` - MCP server testing examples

## Development Memories
- For python, always use pytest for testing, including writing fixtures, mocks, etc. do not use unittest