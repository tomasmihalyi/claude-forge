---
name: forge-status
description: Show all forged tools and their usage stats
user-invocable: true
allowed-tools: Read, Bash
---

Read the file `registry.json` in the project root. Display a formatted summary of all forged MCP tool servers including:

- Server name
- Description
- Tools provided
- When it was created
- What user request triggered the forge
- How many times it has been used

If the registry is empty, say "No tools have been forged yet. Use the Forge agent to get started: claude --agent forge"
