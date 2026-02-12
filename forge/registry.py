#!/usr/bin/env python3
"""
Forge Registry Helper

Provides atomic read/write operations for registry.json.
Used by the Forge agent via Bash to safely manage the tool registry.

Usage:
    python forge/registry.py read
    python forge/registry.py add '{"name": "...", "description": "...", "tools": [...], "forged_for": "..."}'
    python forge/registry.py increment <server-name>
    python forge/registry.py check <server-name>
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "registry.json"


def read_registry() -> dict:
    """Read the registry. Returns {"servers": [...]} or empty structure."""
    if not REGISTRY_PATH.exists():
        return {"servers": []}
    try:
        return json.loads(REGISTRY_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {"servers": []}


def _write_registry(data: dict) -> None:
    """Write registry atomically via temp file + rename."""
    content = json.dumps(data, indent=2) + "\n"
    fd, tmp_path = tempfile.mkstemp(
        dir=REGISTRY_PATH.parent, suffix=".tmp", prefix=".registry_"
    )
    try:
        os.write(fd, content.encode())
        os.close(fd)
        os.replace(tmp_path, REGISTRY_PATH)
    except Exception:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def add_server(entry: dict) -> str:
    """Add a server entry. Returns 'ok' or 'error: ...'."""
    registry = read_registry()

    # Dedup check
    for existing in registry["servers"]:
        if existing["name"] == entry["name"]:
            return f"error: Server '{entry['name']}' already exists in registry"

    # Add timestamp if missing
    if "created_at" not in entry:
        entry["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    if "uses" not in entry:
        entry["uses"] = 0

    registry["servers"].append(entry)
    _write_registry(registry)
    return "ok"


def increment_uses(server_name: str) -> str:
    """Increment the uses counter for a server. Returns 'ok' or 'error: ...'."""
    registry = read_registry()
    for server in registry["servers"]:
        if server["name"] == server_name:
            server["uses"] = server.get("uses", 0) + 1
            _write_registry(registry)
            return "ok"
    return f"error: Server '{server_name}' not found"


def check_exists(server_name: str) -> str:
    """Check if a server exists. Returns 'exists' or 'not_found'."""
    registry = read_registry()
    for server in registry["servers"]:
        if server["name"] == server_name:
            return "exists"
    return "not_found"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python forge/registry.py <command> [args]")
        print("Commands: read, add, increment, check")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "read":
        print(json.dumps(read_registry(), indent=2))
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("error: Missing JSON entry argument")
            sys.exit(1)
        try:
            entry = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            print(f"error: Invalid JSON: {e}")
            sys.exit(1)
        result = add_server(entry)
        print(result)
        sys.exit(0 if result == "ok" else 1)
    elif cmd == "increment":
        if len(sys.argv) < 3:
            print("error: Missing server name")
            sys.exit(1)
        result = increment_uses(sys.argv[2])
        print(result)
        sys.exit(0 if result == "ok" else 1)
    elif cmd == "check":
        if len(sys.argv) < 3:
            print("error: Missing server name")
            sys.exit(1)
        print(check_exists(sys.argv[2]))
    else:
        print(f"error: Unknown command '{cmd}'")
        sys.exit(1)
