#!/bin/bash
# Launch script for MCP server with HTTP/SSE transport

cd /workspaces/research-aggregator-mcp
python src/mcp_server.py --transport sse --host 0.0.0.0 --port 3001