"""
World Clock — Get the current time in any timezone worldwide.
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("world-clock")


@mcp.tool()
async def get_time(timezone: str = "UTC") -> str:
    """Get the current date and time in a specified timezone.

    Args:
        timezone: IANA timezone name (e.g., 'Asia/Tokyo', 'America/New_York', 'Europe/London', 'UTC').
    """
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        return (
            f"🕐 Current time in {timezone}:\n"
            f"   {now.strftime('%A, %B %d, %Y')}\n"
            f"   {now.strftime('%I:%M:%S %p %Z')}"
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def list_timezones(region: str = "") -> str:
    """List available IANA timezones, optionally filtered by region.

    Args:
        region: Optional region filter (e.g., 'Asia', 'America', 'Europe'). Leave empty for all regions.
    """
    try:
        all_tz = sorted(available_timezones())
        if region:
            filtered = [tz for tz in all_tz if tz.lower().startswith(region.lower())]
        else:
            # Just show region prefixes to avoid overwhelming output
            regions = sorted(set(tz.split("/")[0] for tz in all_tz if "/" in tz))
            return "Available timezone regions:\n" + "\n".join(f"  • {r}" for r in regions)

        if not filtered:
            return f"No timezones found for region '{region}'. Use list_timezones() to see available regions."

        return f"Timezones in {region} ({len(filtered)}):\n" + "\n".join(f"  • {tz}" for tz in filtered)
    except Exception as e:
        return f"Error: {e}"


# CLI wrapper for direct invocation
if __name__ == "__main__":
    import asyncio
    import json

    if len(sys.argv) > 1 and sys.argv[1] == "--call":
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
        mcp.run(transport="stdio")
