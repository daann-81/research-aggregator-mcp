This is a Research Aggregator MCP (Model Context Protocol) server that provides tools for searching and retrieving academic papers from arXiv, specifically focused on quantitative finance and algorithmic trading research.

Run in the root director:

docker build -t research-aggregator-mcp:latest .

to build the image

When connecting to claude desktop, find ~/.config/Claude/claude_desktop_config.json and add the following:

{
  "mcpServers": {
    "research-aggregator": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--init",
        "research-aggregator-mcp:latest"
      ]
    }
  }
}

more details of usage in https://modelcontextprotocol.io/introduction

MCP inspector (only in dev):

run MCP in terminal using: poetry run python src/main.py --transport streamable
run MCP inspector in different terminal using: npx @modelcontextprotocol/inspector

open up MCP inspector in brower using http://127.0.0.1:XXXX (where XXXX is default of 6274)

transport type = Streamable HTTP
url = http://localhost:3001/mcp

more details of usage in https://modelcontextprotocol.io/docs/tools/inspector