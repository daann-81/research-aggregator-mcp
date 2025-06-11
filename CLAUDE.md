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