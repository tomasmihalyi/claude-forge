#!/usr/bin/env python3
"""Seed the registry with synthetic entries for scale testing."""

import json
import sys
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "registry.json"

SYNTHETIC_SERVERS = [
    {"name": "image-resizer", "description": "Resize images to specified dimensions", "tools": ["resize_image", "get_dimensions"], "forged_for": "Resize an image", "uses": 0},
    {"name": "pdf-reader", "description": "Extract text and metadata from PDF files", "tools": ["extract_text", "get_metadata"], "forged_for": "Read a PDF", "uses": 0},
    {"name": "json-validator", "description": "Validate JSON against schemas and format JSON", "tools": ["validate_json", "format_json"], "forged_for": "Validate JSON", "uses": 0},
    {"name": "markdown-converter", "description": "Convert between Markdown and HTML formats", "tools": ["md_to_html", "html_to_md"], "forged_for": "Convert markdown", "uses": 0},
    {"name": "color-converter", "description": "Convert between color formats (hex, rgb, hsl)", "tools": ["convert_color"], "forged_for": "Convert hex to rgb", "uses": 0},
    {"name": "password-generator", "description": "Generate secure random passwords", "tools": ["generate_password"], "forged_for": "Generate a password", "uses": 0},
    {"name": "url-shortener", "description": "Shorten and expand URLs using public APIs", "tools": ["shorten_url", "expand_url"], "forged_for": "Shorten a URL", "uses": 0},
    {"name": "text-translator", "description": "Translate text between languages", "tools": ["translate", "detect_language"], "forged_for": "Translate to Spanish", "uses": 0},
    {"name": "regex-tester", "description": "Test and explain regular expressions against text", "tools": ["test_regex", "explain_regex"], "forged_for": "Test a regex", "uses": 0},
    {"name": "text-extractor", "description": "Extract structured data from text using regex patterns", "tools": ["extract_emails", "extract_urls", "extract_numbers"], "forged_for": "Extract emails from text", "uses": 0},
]


def seed(count: int = 20):
    """Add synthetic entries to registry."""
    registry = json.loads(REGISTRY_PATH.read_text())
    existing_names = {s["name"] for s in registry["servers"]}

    added = 0
    for server in SYNTHETIC_SERVERS:
        if server["name"] not in existing_names and added < count:
            server["created_at"] = "2026-02-11T00:00:00"
            registry["servers"].append(server)
            existing_names.add(server["name"])
            added += 1

    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n")
    print(f"Added {added} synthetic servers. Total: {len(registry['servers'])}")


def unseed():
    """Remove all synthetic entries from registry."""
    registry = json.loads(REGISTRY_PATH.read_text())
    synthetic_names = {s["name"] for s in SYNTHETIC_SERVERS}
    registry["servers"] = [s for s in registry["servers"] if s["name"] not in synthetic_names]
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n")
    print(f"Removed synthetic servers. Remaining: {len(registry['servers'])}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "seed"
    if cmd == "seed":
        seed()
    elif cmd == "unseed":
        unseed()
    else:
        print(f"Usage: python tests/seed_registry.py [seed|unseed]")
