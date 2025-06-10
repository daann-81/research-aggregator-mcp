"""
Research Aggregation Server Module

This module provides MCP (Model Context Protocol) server implementations
for searching and retrieving academic papers from arXiv.
"""

from .stdio_server import run_stdio
from .http_server import run_http

__all__ = ["run_stdio", "run_http"]