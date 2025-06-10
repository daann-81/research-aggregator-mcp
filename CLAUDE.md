# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Research Aggregator MCP (Model Context Protocol) server that provides tools for searching and retrieving academic papers from arXiv, specifically focused on quantitative finance and algorithmic trading research.

### Architecture

The project consists of three main components:

1. **MCP Server** (`src/mcp_server.py`) - The main MCP server that exposes research tools to Claude
2. **arXiv Client** (`src/arxiv/client.py`) - Async HTTP client for arXiv API with rate limiting and error handling
3. **XML Parser** (`src/arxiv/parser.py`) - Parses arXiv XML responses into structured Python objects

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
The server uses the MCP framework with async/await patterns. Tool handlers return JSON-serialized results that Claude can parse and use.

### Testing Strategy
- Unit tests in `test/` directory
- Integration tests in `integration/` directory
- Test the MCP server using `integration/test_mcp_server.py` to simulate Claude interactions

## Key Files to Understand

- `src/mcp_server.py:63-111` - Tool definitions and schemas
- `src/arxiv/client.py:155-200` - Core search functionality
- `src/arxiv/parser.py:39-77` - XML parsing logic
- `integration/test_mcp_server.py` - MCP server testing examples