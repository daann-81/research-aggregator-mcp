"""
Research Aggregation Server Module

This module provides MCP (Model Context Protocol) server implementations
for searching and retrieving academic papers from arXiv.
"""

from .mcp_server import run_mcp

__all__ = ["run_mcp"]