"""
Research Aggregation MCP Server - Entry Point

Command-line interface for the Research Aggregation MCP Server.
Supports both stdio and HTTP/SSE transports for connecting to Claude Desktop.
"""

import asyncio
import argparse
import logging

from util.logging import setup_logging

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
        from server.stdio_server import run_stdio

        setup_logging(logToStdout=False)
        asyncio.run(run_stdio())
    elif args.transport.lower() == "sse" or args.transport.lower() == "streamable":
        from server.http_server import run_http

        setup_logging(logToStdout=True)
        asyncio.run(run_http(args.host, args.port, args.transport.lower() == "sse"))


if __name__ == "__main__":
    main()
