"""
Common components for the Research Aggregation MCP Server

This module contains shared data models and utilities used across
different academic paper sources (arXiv, SSRN, etc.).
"""

from .paper import AcademicPaper, from_arxiv_paper, from_ssrn_paper

__all__ = ["AcademicPaper", "from_arxiv_paper", "from_ssrn_paper"]