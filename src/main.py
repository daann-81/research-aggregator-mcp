"""
Research Aggregation MCP Server - Entry Point

Command-line interface for the Research Aggregation MCP Server.
Supports both stdio and HTTP/SSE transports for connecting to Claude Desktop.
"""

import asyncio
import argparse
import logging

from util.logging import setup_logging

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.server.mcp_server import TransportType, run_mcp

logger = logging.getLogger(__name__)


def main():
    """Main entry point with transport selection"""
    parser = argparse.ArgumentParser(
        description="Research Aggregation MCP Server",
        epilog="""
Examples:
  # Run with stdio transport (default)
  python mcp_server.py --transport stdio
  
  # Run with HTTP/SSE transport
  python mcp_server.py --transport sse --port 3001
  
  # Run with custom host and port
  python mcp_server.py --transport sse --host 127.0.0.1 --port 8080
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable"],
        default="stdio",
        help="Transport method (default: stdio)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=3001, help="Port for HTTP transport (default: 3001)"
    )

    args = parser.parse_args()

    # Import and run the appropriate server
    
    if args.transport.lower() == "stdio":
        setup_logging(logToStdout=False)
        asyncio.run(run_mcp(args.host, args.port, transport=TransportType.STDIO))
    elif args.transport.lower() == "sse":
        setup_logging(logToStdout=True)
        asyncio.run(run_mcp(args.host, args.port, transport=TransportType.SSE))
    elif args.transport.lower() == "streamable":
        setup_logging(logToStdout=True)
        asyncio.run(run_mcp(args.host, args.port, transport=TransportType.STREAMABLE))
    else:
        logger.error(f"Unsupported transport type: {args.transport}")
        parser.print_help()
        exit(1)

if __name__ == "__main__":
    main()
