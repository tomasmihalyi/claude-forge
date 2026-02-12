# Forge

**A Claude Code agent that builds its own tools.**

Forge detects when it lacks the capability to fulfill a request, then autonomously designs, builds, validates, and registers a new MCP tool server — and uses it immediately. Every tool it creates persists forever. The agent gets permanently smarter with every request.

```
User: "What time is it in Tokyo?"

Forge: I don't have a tool for this. Forging one now...
       [Designs world-clock server]
       [Generates servers/world-clock/server.py]
       [Validates: 11/11 checks passed]
       [Registers with Claude Code]
       [Uses it]

       The current time in Tokyo is 2:30 AM JST.
       Tool used: world-clock (forged just now)

User: "What time is it in London?"

Forge: I already have a tool for this: world-clock
       The current time in London is 5:30 PM GMT.
```

## Quick Start

```bash
# Clone and set up
git clone https://github.com/tomasmihalyi/claude-forge.git && cd claude-forge
uv sync

# Start the Forge agent
claude --agent forge
```

Then ask it anything:
- `"What time is it in Tokyo?"` — forges a timezone tool (stdlib)
- `"Analyze demo/sales.csv"` — forges a CSV analysis tool (stdlib)
- `"What's trending on Hacker News?"` — forges an HN API tool (httpx)
- `"What time is it in London?"` — reuses the timezone tool instantly

Check what's been forged: type `/forge-status` in the agent session.

## How It Works

### The Forge Protocol (9 steps)

```
User Request
    │
    ▼
1. CHECK REGISTRY ─── Match found? ──Yes──► 8. USE EXISTING TOOL
    │                                              │
    No                                             ▼
    ▼                                        9. CONFIRM
2. ASSESS GAP ──── Reusable capability?
    │
    Yes
    ▼
3. ANNOUNCE ──── "Forging a new tool..."
    ▼
4. DESIGN ───── Reason about architecture (visible to user)
    ▼
5. GENERATE ─── Write FastMCP server to servers/{name}/server.py
    ▼
6. VALIDATE ─── 11-check validation (syntax, async, types, imports...)
    │            Retry up to 3x on failure
    ▼
7. REGISTER ─── claude mcp add + update registry.json
    ▼
8. USE TOOL ─── Invoke via CLI wrapper
    ▼
9. CONFIRM ──── Return answer + "Tool is now permanent"
```

### Architecture

```
forge/
├── .claude/
│   ├── agents/forge.md              ← The agent brain (Forge Protocol)
│   ├── settings.json                ← Permissions + hooks
│   └── skills/forge-status/         ← /forge-status slash command
├── forge/
│   ├── templates/server_template.py ← Pattern for code generation
│   ├── validate_server.py          ← 11-check server validator
│   └── registry.py                 ← Atomic registry operations
├── servers/                         ← Auto-generated MCP servers
│   ├── world-clock/server.py
│   ├── csv-analyzer/server.py
│   └── hacker-news/server.py
├── registry.json                    ← Persistent tool memory
├── .mcp.json                        ← Claude Code MCP server config
└── demo/sales.csv                   ← Sample data for demos
```

### Key Design Decisions

**CLI wrapper pattern**: Every generated server includes a `--call` CLI wrapper so Forge can use tools immediately in the same session, without waiting for MCP registration to take effect.

**11-check validator**: Before any server is registered, it passes through AST-based validation: syntax, async functions, docstrings, type hints, return types, no stdout contamination, successful imports, FastMCP instance, tool registration, and main block.

**Atomic registry**: The registry helper (`forge/registry.py`) uses temp-file-and-rename for safe writes, prevents duplicate entries, and provides increment operations.

**Security policy**: The agent refuses to forge tools that delete files, execute shell commands, access credentials, or call non-public APIs.

## Claude Code Platform Integration

| Feature | How Forge Uses It |
|---------|------------------|
| **Custom Agents** | `.claude/agents/forge.md` — the entire Forge Protocol |
| **MCP Servers** | Forge creates and registers new MCP servers dynamically |
| **Skills** | `/forge-status` — reports forged tools and usage stats |
| **Hooks** | `PostToolUse` hook logs validation events |
| **Opus 4.6** | Extended thinking drives server architecture design (Step 4) |

## Built With

- **Claude Opus 4.6** — extended thinking for tool architecture design
- **Claude Code** — agents, skills, hooks, MCP integration
- **FastMCP** (Python) — MCP server SDK
- **Python 3.13** — stdlib + httpx for generated servers

Built for the "Built with Opus 4.6: a Claude Code hackathon" (Feb 10-16, 2026).
