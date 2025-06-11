"""
SSRN Integration Package

This package provides tools for accessing and parsing academic papers from 
the Social Science Research Network (SSRN) via their undocumented API.

Key Features:
- Async HTTP client for SSRN API access
- Client-side filtering by JEL codes, authors, dates, and text
- JSON response parsing with structured data models
- Rate limiting and error handling

Main Components:
- AsyncSSRNClient: HTTP client for SSRN API requests
- SSRNPaper: Data model for SSRN paper information
- SSRNJSONParser: Parser for SSRN API JSON responses
- SSRNAPIError: Custom exception for SSRN-specific errors
"""

from .client import AsyncSSRNClient, SSRNAPIError
from .parser import SSRNPaper, SSRNJSONParser

__all__ = [
    "AsyncSSRNClient",
    "SSRNPaper", 
    "SSRNJSONParser",
    "SSRNAPIError"
]

__version__ = "0.1.0"