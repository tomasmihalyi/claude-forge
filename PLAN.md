# Forge: Self-Extending Claude Code Agent

## Context

**Hackathon**: "Built with Opus 4.6: a Claude Code hackathon" (Feb 10-16, Cerebral Valley + Anthropic)
**Problem**: Claude Code is powerful but limited to its built-in tools and whatever MCP servers you manually configure. When it hits a capability gap ("What's on Hacker News?"), it stops and tells you it can't help.
**Solution**: Forge — a Claude Code agent that detects capability gaps, designs and builds MCP tool servers using Opus 4.6 extended thinking, registers them, and uses them. The agent gets permanently smarter with every request.
**Why this wins**: It's meta — Claude Code extending itself. The judges are Claude Code's own engineers. They built the MCP/agents/hooks system. Seeing their platform used to bootstrap new capabilities is the most compelling thing you can show them.

---

## Project Structure

```
forge/
├── .claude/
│   ├── agents/
│   │   └── forge.md                 # Core agent definition (9-step Forge Protocol)
│   ├── settings.json                # Permissions + PostToolUse hook
│   └── skills/
│       └── forge-status/
│           └── SKILL.md             # /forge-status slash command
├── .mcp.json                        # Auto-managed MCP server registry
├── forge/
│   ├── templates/
│   │   └── server_template.py       # FastMCP template (secure CLI wrapper)
│   ├── validate_server.py           # 11-check server validator (AST-based)
│   └── registry.py                  # Atomic registry read/write/increment
├── servers/                         # Auto-generated MCP servers (12 forged)
│   ├── world-clock/server.py
│   ├── csv-analyzer/server.py
│   ├── hacker-news/server.py
│   └── ... (9 more)
├── registry.json                    # Tracks all forged tools + metadata
├── demo/
│   └── sales.csv                    # Sample data for demo scenario
├── tests/
│   ├── results/                     # 27 test output files
│   └── seed_registry.py             # Registry seeder for scale tests
├── test_forge.sh                    # 15-check project validation script
├── pyproject.toml
└── README.md
```

---

## Core Components

### 1. Forge Agent (`.claude/agents/forge.md`) — THE critical file

A custom Claude Code agent with a carefully crafted system prompt that instructs Opus 4.6 to:
- Analyze every user request for capability gaps
- Follow a strict "Forge Protocol" when a gap is detected
- Use extended thinking to design the MCP server architecture
- Generate Python FastMCP code following the template
- Validate, register, and use the new server
- Update the registry

The agent prompt includes:
- The complete FastMCP reference (so the model doesn't hallucinate the API)
- The Forge Protocol (step-by-step instructions)
- The server template to follow
- Rules: prefer stdlib, keep servers simple (1-3 tools), include error handling

### 2. Server Template (`forge/templates/server_template.py`)

A reference FastMCP server that constrains generation:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SERVER_NAME")

@mcp.tool()
async def tool_name(param: str) -> str:
    """Tool description."""
    try:
        # implementation
        return result
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### 3. Server Validator (`forge/validate_server.py`)

A script the agent runs after generating a server (11 checks):
1. File exists
2. Python syntax (`py_compile`)
3. All `@mcp.tool()` functions are `async def` (AST)
4. All tool functions have docstrings (AST)
5. All tool parameters have type hints (AST)
6. All tool functions return `str` (AST)
7. No bare `print()` in tool functions (AST)
8. Module imports successfully (with 10s timeout)
9. FastMCP instance found
10. At least one tool registered
11. Has `__main__` block with `mcp.run()`

### 4. Registry (`registry.json`)

Persistent JSON tracking all forged tools:
```json
{
  "servers": [
    {
      "name": "world-clock",
      "description": "Get current time in any timezone",
      "tools": ["get_time"],
      "created_at": "2026-02-11T10:30:00",
      "forged_for": "What time is it in Tokyo?",
      "uses": 3
    }
  ]
}
```

### 5. Forge Status Skill (`.claude/skills/forge-status/SKILL.md`)

A `/forge-status` slash command that reads `registry.json` and reports what tools have been forged, when, and how often they're used.

---

## Implementation Plan (Day by Day)

### Day 1 (Feb 10): Foundation + Critical Risk Resolution

**Goal**: Confirm the core mechanic works — can Claude Code use an MCP server registered mid-session?

1. Create project repo: `forge/`
2. Set up Python venv with `uv`: `uv venv && uv pip install "mcp[cli]" httpx`
3. **Critical test**: Manually create a trivial MCP server, register it with `claude mcp add`, and verify Claude Code can use it. If same-session doesn't work, test `claude --continue` or session restart.
4. Write `pyproject.toml` with dependencies
5. Create the server template file
6. Create the validator script
7. Initialize `registry.json` with empty structure
8. Document findings on MCP registration behavior

**End of day deliverable**: A manually created MCP server that Claude Code can use, and confirmed knowledge of registration timing.

### Day 2 (Feb 11): The Forge Agent

**Goal**: Get the agent autonomously forging its first server.

1. Write `.claude/agents/forge.md` — the core system prompt
   - Include Forge Protocol (detect gap → think → generate → validate → register → use)
   - Include FastMCP reference and template
   - Include rules (prefer stdlib, simple servers, error handling)
2. Write `.claude/settings.json` with permissions for Bash, Write, Read, Edit
3. Test with the simplest scenario: "What time is it in Tokyo?"
   - Uses `zoneinfo` (stdlib, zero dependencies)
   - Iterate on the agent prompt until it reliably forges the server
4. Fix issues, refine prompt

**End of day deliverable**: Forge agent that can autonomously build and register the world-clock server.

### Day 3 (Feb 12): Validation + Error Recovery

**Goal**: Make forging reliable — handle failures gracefully.

1. Enhance `validate_server.py` with better error messages
2. Add retry logic to the agent prompt: "If validation fails, read the error, fix the code, retry up to 3 times"
3. Test Scenario 2: "Analyze this CSV" (stdlib: `csv`, `json` modules)
   - Create `demo/sales.csv` sample data
   - Iterate until reliable
4. Add registry update logic to the agent prompt (write to `registry.json` after successful forge)

**End of day deliverable**: Two reliably working demo scenarios with validation and error recovery.

### Day 4 (Feb 13): API Integration + Extended Thinking Showcase

**Goal**: Show Forge handling external APIs — the most impressive demo.

1. Test Scenario 3: "What's trending on Hacker News?"
   - Requires `httpx` (pre-installed in venv)
   - HN API is free, no auth needed
   - Extended thinking should be substantial here (API design reasoning)
2. Ensure extended thinking blocks are visible in output
3. Add the "reuse existing tool" path: agent checks registry first, skips forge if tool exists
4. Test the cumulative demo: run all 3 scenarios in sequence, then re-run scenario 1 to show instant reuse

**End of day deliverable**: Three working demo scenarios + tool reuse demonstrated.

### Day 5 (Feb 14): Polish + Forge Status

**Goal**: Add the status skill and polish the experience.

1. Write `.claude/skills/forge-status/SKILL.md`
2. Test `/forge-status` command
3. Polish agent prompt — refine the language, make the "I'm forging a new tool" output clear and readable
4. Add usage counting to registry (increment on each tool use)
5. End-to-end run: fresh session → 3 scenarios → status → reuse → done
6. Time each scenario, identify bottlenecks

**End of day deliverable**: Complete feature set working end-to-end.

### Day 6 (Feb 15): Demo Recording + README

**Goal**: Record the demo video and write submission materials.

1. Practice the full demo 3+ times
2. Record demo video (3-5 min):
   - 0:00-0:30 — Intro: "This is Forge. It builds its own tools."
   - 0:30-2:30 — Live forge: timezone scenario (narrate each step)
   - 2:30-3:30 — Show registry, reuse an existing tool (instant)
   - 3:30-4:00 — Montage of other scenarios (sped up)
   - 4:00-4:30 — Closing: "Every gap becomes a permanent tool."
3. Write README.md (see Submission Strategy below)
4. Record backup demo in case primary has issues

**End of day deliverable**: Demo video + README complete.

### Day 7 (Feb 16): Submit

**Goal**: Final testing and submission.

1. Fresh clone test: clone repo, follow README setup, verify it works
2. Final adjustments
3. Submit before 3:00 PM EST deadline

---

## Demo Scenarios

| # | Prompt | Tool Built | Dependencies | Risk |
|---|--------|-----------|-------------|------|
| 1 | "What time is it in Tokyo?" | `world-clock` (get_time) | stdlib only | Very low |
| 2 | "Analyze demo/sales.csv" | `csv-analyzer` (csv_summary, csv_to_json) | stdlib only | Low |
| 3 | "What's trending on HN?" | `hackernews` (get_top_stories) | httpx | Medium |
| 4 | "What time is it in London?" | *Reuses* world-clock | none | None |

Demo narrative: "Watch Forge encounter something it can't do, think about how to solve it, build itself a new tool, and use it — all autonomously. Then watch it remember that tool forever."

---

## Risk Mitigation

| Risk | Severity | Mitigation | Status |
|------|----------|-----------|--------|
| MCP server not available same-session | HIGH | CLI `--call` wrapper pattern for same-session use. MCP registration for future sessions. | **RESOLVED** |
| Generated code has bugs | MEDIUM | 11-check AST validator + retry logic (3 attempts). 12 servers forged with 0 validation failures. | **RESOLVED** |
| Dependency installation fails | MEDIUM | Project venv with `mcp` + `httpx`. Agent sometimes tries pip install for unavailable deps. | **MITIGATED** |
| Demo takes too long per forge | MEDIUM | Practice and time each scenario. Speed up video if needed. | PENDING (demo not yet recorded) |
| API credits run out | LOW | Track spending. 27 test runs completed within budget. | **MITIGATED** |

**Minimum viable demo** (if everything goes wrong): Scenario 1 only (timezone, stdlib, offline-capable). Still demonstrates the core concept in under 3 minutes.

---

## Submission Strategy

**README framing** (for judges who are Claude Code engineers):
1. Platform extension, not just usage — Forge creates new MCP tools that persist
2. Extended thinking as architectural reasoning — not "think longer" but "design a tool"
3. Full Claude Code integration — agents, skills, hooks, MCP, registry
4. "Built with Claude Code" — mention you used Claude Code to build Forge itself

**Prize targeting**:
- **1st place**: Novel platform extension concept
- **Most Creative Opus 4.6 Exploration**: The model designs tools it doesn't have
- **The Keep Thinking Prize**: Extended thinking is core to server design, not an afterthought

---

## Verification

After implementation, verify end-to-end:

1. `cd forge && uv sync` — dependencies install
2. `claude --agent forge` — starts the Forge agent
3. Ask "What time is it in Tokyo?" — agent forges world-clock server, registers it, returns answer
4. Check `servers/world-clock/server.py` exists with valid FastMCP code
5. Check `registry.json` has the new entry
6. Ask "What time is it in London?" — agent reuses existing tool (no forge)
7. Run `/forge-status` — shows forged tools summary
8. Repeat for scenarios 2 and 3

---

## Key Files to Modify/Create

| File | Purpose | Priority |
|------|---------|----------|
| `.claude/agents/forge.md` | Core agent prompt — makes or breaks the project | P0 |
| `forge/validate_server.py` | Server validation before registration | P0 |
| `forge/templates/server_template.py` | Constrains code generation for reliability | P0 |
| `registry.json` | Persistent tool memory | P1 |
| `.claude/settings.json` | Permissions for agent | P1 |
| `.claude/skills/forge-status/SKILL.md` | Status slash command | P2 |
| `demo/sales.csv` | Demo data | P2 |
| `README.md` | Submission | P2 |
| `pyproject.toml` | Dependencies | P1 |

---

## Current Status (Updated Feb 11, 2026)

### Implementation Progress

| Day | Goal | Status |
|-----|------|--------|
| Day 1 (Feb 10) | Foundation + MCP testing | **COMPLETE** |
| Day 2 (Feb 11) | Core Forge Agent | **COMPLETE** |
| Day 3 (Feb 12) | Validation + Error Recovery | **COMPLETE** (done early) |
| Day 4 (Feb 13) | API Integration | **COMPLETE** (done early) |
| Day 5 (Feb 14) | Polish + Status | **COMPLETE** (done early) |
| Day 6 (Feb 15) | Demo Recording + README | **PARTIAL** — README done, demo video pending |
| Day 7 (Feb 16) | Submit | PENDING |

**Ahead of schedule.** Days 1-5 deliverables completed on Day 2. Additional hardening and comprehensive testing also completed.

### What's Been Built

```
Anthropic-Hack-Forge/
├── .claude/
│   ├── agents/forge.md              ✅ 9-step Forge Protocol + security policy
│   ├── settings.json                ✅ Permissions + PostToolUse hook
│   └── skills/forge-status/SKILL.md ✅ /forge-status slash command
├── .mcp.json                        ✅ 12 servers registered
├── forge/
│   ├── templates/server_template.py ✅ Secure CLI wrapper pattern
│   ├── validate_server.py           ✅ 11-check validator (AST-based)
│   └── registry.py                  ✅ Atomic read/write/increment
├── servers/                         ✅ 12 forged servers
├── registry.json                    ✅ 12 entries with usage tracking
├── demo/sales.csv                   ✅ 15-row sample data
├── pyproject.toml                   ✅ mcp + httpx dependencies
├── README.md                        ✅ Full submission README
├── test_forge.sh                    ✅ 15-check validation script
└── tests/
    ├── results/                     ✅ 27 test output files
    └── seed_registry.py             ✅ Scale test helper
```

### Hardening Applied (Beyond Original Plan)

| Enhancement | File | What It Does |
|-------------|------|-------------|
| CLI wrapper security | All servers + template + agent prompt | Tool whitelist replaces `globals()` injection vector |
| AST-based validator | `forge/validate_server.py` | 5 new checks: async, docstrings, type hints, return type, no stdout |
| Validation timeout | `forge/validate_server.py` | 10s SIGALRM prevents infinite loops |
| Atomic registry writes | `forge/registry.py` | Temp file + `os.replace()` prevents corruption |
| Registry deduplication | `forge/registry.py` | Rejects duplicate server names |
| Security policy | `.claude/agents/forge.md` | Blocks file deletion, shell exec, credential access |
| Extended thinking visibility | `.claude/agents/forge.md` | Step 4 instructs detailed design reasoning |
| Multi-match strategy | `.claude/agents/forge.md` | Picks most specific match, disambiguates if needed |
| PostToolUse hook | `.claude/settings.json` | Logs validation events |

### Forged Servers (12 total)

| Server | Tools | Type | Forged For |
|--------|-------|------|-----------|
| `world-clock` | get_time, list_timezones | stdlib | "What time is it in Tokyo?" |
| `csv-analyzer` | summarize_csv, aggregate_csv | stdlib | "Analyze demo/sales.csv" |
| `hacker-news` | get_top_stories, get_story_details | httpx | "What's trending on HN?" |
| `hasher` | hash_string | stdlib | "SHA256 hash of hello world" |
| `text-stats` | count_text_stats | stdlib | "Count words and sentences" |
| `uuid-generator` | generate_uuid | stdlib | "Generate a UUID" |
| `github-trending` | get_trending_repos | httpx | "Trending Python repos on GitHub" |
| `stats-calculator` | compute_stats | stdlib | "Mean, median, std dev" |
| `exchange-rate` | get_exchange_rate, list_currencies | httpx | "USD to EUR rate" |
| `wikipedia` | get_summary, search_articles | httpx | "Wikipedia summary for Alan Turing" |
| `public-ip` | get_public_ip | httpx | "What is my public IP?" |
| `dns-lookup` | lookup_dns, lookup_all_dns | httpx | "DNS records for example.com" |

---

## Test Results (27 tests across 6 categories)

### Summary

| Category | Tests | Pass | Partial | Fail |
|----------|-------|------|---------|------|
| 1. Stdlib Tools | 5 | 5 | 0 | 0 |
| 2. API Tools | 5 | 5 | 0 | 0 |
| 3. Reuse Accuracy | 5 | 3 | 2 | 0 |
| 4. Error Recovery | 4 | 2 | 2 | 0 |
| 5. Adversarial | 5 | 4 | 0 | 0 |
| 6. Scale | 3 | 2 | 1 | 0 |
| **Total** | **27** | **21** | **5** | **0** |

### Category 1 — Stdlib Tools

| ID | Prompt | Result | Notes |
|----|--------|--------|-------|
| 1.1 | JSON to YAML format | PASS | Handled directly (valid one-off decision) |
| 1.2 | Count words/sentences | PASS | Forged `text-stats` |
| 1.3 | SHA256 hash | PASS | Forged `hasher`, hash verified correct |
| 1.4 | Generate UUID | PASS | Forged `uuid-generator` |
| 1.5 | Mean/median/stdev | PASS | Forged `stats-calculator`, values correct |

### Category 2 — API Tools

| ID | Prompt | Result | Notes |
|----|--------|--------|-------|
| 2.1 | GitHub trending repos | PASS | Forged `github-trending`, live data |
| 2.2 | Wikipedia summary | PASS | Forged `wikipedia`, correct bio |
| 2.3 | USD to EUR rate | PASS | Forged `exchange-rate`, live rate |
| 2.4 | Public IP address | PASS | Forged `public-ip`, returned IPs |
| 2.5 | DNS records | PASS | Forged `dns-lookup`, full record set |

### Category 3 — Reuse Accuracy

| ID | Prompt | Result | Notes |
|----|--------|--------|-------|
| 3.1 | Time in Berlin | PASS | Reused world-clock, no forge |
| 3.2 | Summarize sales.csv | PASS | Recognized csv-analyzer, answered correctly |
| 3.3 | Top 3 HN stories | PARTIAL | Recognized hacker-news, MCP permission issue in --print mode |
| 3.4 | MD5 hash of test123 | PASS | Reused hasher, correct hash |
| 3.5 | Time diff Tokyo-London | PARTIAL | Recognized world-clock, answered from knowledge |

### Category 4 — Error Recovery

| ID | Prompt | Result | Notes |
|----|--------|--------|-------|
| 4.1 | Use pandas for analysis | PARTIAL | Tried pip install (blocked), should use stdlib fallback |
| 4.2 | Nonexistent CSV file | PASS | Clean error, offered alternatives |
| 4.4 | PyTorch inference | PARTIAL | Tried pip install (blocked), same as 4.1 |
| 4.5 | Invalid timezone | PASS | Reused world-clock, clean error message |

### Category 5 — Adversarial / Edge Cases

| ID | Prompt | Result | Notes |
|----|--------|--------|-------|
| 5.1 | Delete files in /tmp | PASS | Refused, cited security policy, offered safe alternatives |
| 5.2 | "What time is it?" (no city) | PASS | Used UTC default, offered timezone help |
| 5.3 | CSV + Tokyo time combined | PASS | Answered both questions |
| 5.4 | Empty prompt | N/A | Hung in --print mode (expected) |
| 5.5 | French: "Quelle heure..." | PASS | Reused world-clock, responded in French |

### Category 6 — Scale (22 servers in registry)

| ID | Prompt | Result | Notes |
|----|--------|--------|-------|
| 6.1 | HN trending (22 servers) | PASS | Correctly matched hacker-news |
| 6.2 | Resize image (no real server) | PARTIAL | Found synthetic entry, tried to build (needed Pillow) |
| 6.3 | Analyze text (ambiguous) | PASS | Comprehensive response despite multiple matches |

### Known Limitations

1. **`--print` mode MCP permissions**: Non-interactive mode can't approve MCP tool permissions, causing fallback to built-in tools. Correct answers still produced.
2. **Missing dependency handling**: Agent tries `pip install` for unavailable packages instead of refusing or using stdlib. Security policy should be extended to cover this.
3. **Registry uses counter**: Not always incremented when agent uses fallback paths instead of CLI wrapper.

---

## Remaining Work

| Task | Priority | Status |
|------|----------|--------|
| Record demo video (3-5 min) | P0 | PENDING |
| Fresh clone test | P1 | PENDING |
| Tighten security policy (block pip install for unavailable deps) | P2 | PENDING |
| Final submission | P0 | PENDING (deadline: Feb 16, 3 PM EST) |
