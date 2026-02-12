"""
Hacker News MCP Server — Fetch trending stories from Hacker News.

Uses the official Hacker News Firebase API (no auth required).
"""

import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hacker-news")


@mcp.tool()
async def get_top_stories(count: int = 10) -> str:
    """Fetch the current top/trending stories from Hacker News.

    Args:
        count: Number of top stories to return (1-30). Default is 10.
    """
    try:
        import httpx

        count = max(1, min(count, 30))

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get top story IDs
            resp = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            resp.raise_for_status()
            story_ids = resp.json()[:count]

            # Fetch each story's details concurrently
            import asyncio

            async def fetch_story(story_id: int) -> dict:
                r = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
                r.raise_for_status()
                return r.json()

            stories = await asyncio.gather(*[fetch_story(sid) for sid in story_ids])

        # Format output
        lines = []
        for i, story in enumerate(stories, 1):
            if story is None:
                continue
            title = story.get("title", "Untitled")
            url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}")
            score = story.get("score", 0)
            author = story.get("by", "unknown")
            comments = story.get("descendants", 0)
            hn_link = f"https://news.ycombinator.com/item?id={story.get('id', '')}"

            lines.append(
                f"{i}. {title}\n"
                f"   {score} points by {author} | {comments} comments\n"
                f"   Link: {url}\n"
                f"   Discussion: {hn_link}"
            )

        return "\n\n".join(lines) if lines else "No stories found."

    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_story_details(story_id: int) -> str:
    """Get detailed information about a specific Hacker News story by its ID.

    Args:
        story_id: The Hacker News item ID.
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            resp.raise_for_status()
            item = resp.json()

        if item is None:
            return f"No item found with ID {story_id}."

        item_type = item.get("type", "unknown")
        title = item.get("title", "N/A")
        url = item.get("url", "N/A")
        score = item.get("score", 0)
        author = item.get("by", "unknown")
        comments = item.get("descendants", 0)
        text = item.get("text", "")
        time_val = item.get("time", 0)

        from datetime import datetime, timezone
        posted = datetime.fromtimestamp(time_val, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if time_val else "unknown"

        result = (
            f"Title: {title}\n"
            f"Type: {item_type}\n"
            f"Author: {author}\n"
            f"Score: {score} points\n"
            f"Comments: {comments}\n"
            f"Posted: {posted}\n"
            f"URL: {url}\n"
            f"HN: https://news.ycombinator.com/item?id={story_id}"
        )

        if text:
            # Strip HTML tags for readability
            import re
            clean_text = re.sub(r"<[^>]+>", " ", text).strip()
            result += f"\n\nText:\n{clean_text}"

        return result

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
