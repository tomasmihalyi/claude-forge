# Technical Research — Forge Prerequisites

## 1. MCP Server Creation (Python FastMCP)

### Minimal Server Example
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description."""
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Key Points
- FastMCP is the recommended Python SDK for rapid MCP server development
- Servers run via stdio transport (stdin/stdout communication)
- `@mcp.tool()` decorator registers functions as tools
- Tool docstrings become the tool's description for the LLM
- Type hints on parameters become the input schema
- **Never print to stdout** in stdio servers (use stderr for logging)
- Dependencies: `pip install "mcp[cli]"`

### Server with Dependencies
```python
from mcp.server.fastmcp import FastMCP
import httpx  # for HTTP requests

mcp = FastMCP("hackernews")

@mcp.tool()
async def get_top_stories(count: int = 5) -> str:
    """Get top stories from Hacker News."""
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        story_ids = resp.json()[:count]
        stories = []
        for sid in story_ids:
            r = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            stories.append(r.json())
    return "\n".join(f"- {s['title']} ({s.get('score', 0)} pts)" for s in stories)
```

---

## 2. Registering MCP Servers with Claude Code

### Via CLI
```bash
# Add a server (project scope = shared in .mcp.json)
claude mcp add --transport stdio --scope project server-name -- python /abs/path/to/server.py

# List registered servers
claude mcp list

# Remove a server
claude mcp remove server-name

# Get server details
claude mcp get server-name
```

### Via .mcp.json (project root)
```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "python",
      "args": ["/abs/path/to/server.py"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### Via claude_desktop_config.json (user scope)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": ["--directory", "/path/to/project", "run", "server.py"]
    }
  }
}
```

### CRITICAL: Same-Session Availability
- **Must test on Day 1**: Can a server registered via `claude mcp add` be used immediately in the same session?
- If not, `claude --continue` or session restart may be needed
- Fallback: direct Python execution of generated server functions

---

## 3. Claude Code Custom Agents

### Agent File Location
`.claude/agents/agent-name.md` (project) or `~/.claude/agents/agent-name.md` (user)

### Agent File Format
```markdown
---
name: forge
description: Self-extending agent that builds MCP tools
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep
---

System prompt instructions go here...
```

### Running an Agent
```bash
claude --agent forge
```

### Key Agent Features
- `model`: Which Claude model to use (opus, sonnet)
- `tools`: Whitelist of allowed tools
- `memory: project` or `memory: user` for persistence
- Agents can use all Claude Code tools (Read, Write, Edit, Bash, etc.)

---

## 4. Claude Code Skills

### Skill File Location
`.claude/skills/skill-name/SKILL.md`

### Skill File Format
```yaml
---
name: forge-status
description: Show all forged tools and their usage stats
user-invocable: true
allowed-tools: Read, Bash
---

Read registry.json and display all forged tools with their
descriptions, creation dates, and usage counts.
```

### Invocation
```
/forge-status
```

---

## 5. Claude Code Hooks

### Settings File (`.claude/settings.json`)
```json
{
  "permissions": {
    "allow": [
      "Bash(python *)",
      "Bash(uv *)",
      "Bash(claude mcp *)",
      "Read",
      "Write",
      "Edit"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'File written' >&2"
          }
        ]
      }
    ]
  }
}
```

### Available Hook Events
- `PreToolUse` / `PostToolUse`: Before/after any tool call
- `SessionStart` / `SessionEnd`: Session lifecycle
- `SubagentStart` / `SubagentStop`: Team agent lifecycle

---

## 6. Opus 4.6 Extended Thinking

### API Usage
```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},  # Recommended for Opus 4.6
    messages=[{"role": "user", "content": "Design an MCP server for..."}]
)

# Parse response
for block in response.content:
    if block.type == "thinking":
        print("Reasoning:", block.thinking)
    elif block.type == "text":
        print("Answer:", block.text)
```

### Key Details
- **Adaptive thinking** (recommended): `{"type": "adaptive"}` — model decides depth
- **Manual thinking**: `{"type": "enabled", "budget_tokens": 10000}` — you set budget (min 1024)
- Opus 4.6 supports up to 128k output tokens
- Thinking blocks are summarized in output but you pay for full thinking tokens
- Always preserve thinking blocks when passing tool results back
- In Claude Code: extended thinking happens automatically when using Opus model

---

## 7. MCP Server Capabilities

### Three Primitives
1. **Tools**: Functions the LLM can call (our primary focus)
2. **Resources**: Data the LLM can read (files, DB records)
3. **Prompts**: Template prompts available as slash commands

### Output Limits
- Warning: 10,000 tokens per tool output
- Default max: 25,000 tokens
- Override: `MAX_MCP_OUTPUT_TOKENS=50000`

### Server Capabilities Declaration
```json
{
  "capabilities": {
    "tools": { "listChanged": true }
  }
}
```

---

## 8. Python Environment Setup

### Using uv (recommended)
```bash
# Create project
mkdir forge && cd forge
uv init
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install "mcp[cli]" httpx

# Run server with project venv
.venv/bin/python servers/my-server/server.py
```

### Register server with venv Python
```bash
claude mcp add --transport stdio --scope project my-server \
  -- /abs/path/forge/.venv/bin/python /abs/path/forge/servers/my-server/server.py
```

This ensures the server uses the project's venv (with `mcp` and other deps installed) rather than the system Python.
