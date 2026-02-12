"""
Forge Server Template — Reference for MCP server generation.

The Forge agent uses this as the canonical pattern when generating new servers.
Every generated server MUST follow this structure exactly.

RULES:
- One FastMCP instance per server
- 1-3 tools per server (keep focused)
- All tools must be async
- All tools must have docstrings (these become tool descriptions)
- All tools must have type hints (these become input schemas)
- All tools must return strings
- Wrap tool bodies in try/except, return f"Error: {e}" on failure
- NEVER print to stdout (stdio transport uses stdout for communication)
- Use stderr for any debug logging: import sys; print("debug", file=sys.stderr)
- Prefer stdlib modules. Only use packages already in the project venv.
"""

import sys
from mcp.server.fastmcp import FastMCP

# Server name should be kebab-case, descriptive
mcp = FastMCP("server-name")


@mcp.tool()
async def tool_name(param: str, count: int = 5) -> str:
    """One-line description of what this tool does.

    Args:
        param: Description of param.
        count: Description of count.
    """
    try:
        # Implementation here
        result = f"Processed: {param}"
        return result
    except Exception as e:
        return f"Error: {e}"


# CLI wrapper for direct invocation (used by Forge for first-use before MCP registration takes effect)
if __name__ == "__main__":
    import asyncio
    import json

    if len(sys.argv) > 1 and sys.argv[1] == "--call":
        # Direct invocation: python server.py --call tool_name '{"param": "value"}'
        _tools = {name: func.fn for name, func in mcp._tool_manager._tools.items()}
        func_name = sys.argv[2] if len(sys.argv) > 2 else None
        if func_name not in _tools:
            print(f"Error: Unknown tool '{func_name}'. Available: {', '.join(_tools.keys())}")
            sys.exit(1)
        try:
            args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON arguments: {e}")
            sys.exit(1)
        result = asyncio.run(_tools[func_name](**args))
        print(result)
    else:
        # Standard MCP stdio transport
        mcp.run(transport="stdio")
