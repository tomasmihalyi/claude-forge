"""
CSV Analyzer — Forge MCP server for loading, summarizing, and aggregating CSV files.
"""

import csv
import io
import sys
from collections import defaultdict
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("csv-analyzer")


def _load_csv(file_path: str) -> list[dict]:
    """Load CSV file and return list of row dicts."""
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _try_float(value: str) -> float | None:
    """Try to convert a string to float, return None if not possible."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


@mcp.tool()
async def summarize_csv(file_path: str) -> str:
    """Load a CSV file and return an overview: column names, row count, data types, and a sample of the first 5 rows.

    Args:
        file_path: Absolute or relative path to the CSV file.
    """
    try:
        rows = _load_csv(file_path)
        if not rows:
            return "CSV file is empty (no data rows)."

        columns = list(rows[0].keys())
        num_rows = len(rows)

        # Detect numeric columns
        numeric_cols = []
        for col in columns:
            values = [_try_float(r[col]) for r in rows if r[col].strip()]
            if values and all(v is not None for v in values):
                numeric_cols.append(col)

        # Sample rows
        sample = rows[:5]
        sample_lines = []
        for r in sample:
            sample_lines.append(" | ".join(f"{k}: {v}" for k, v in r.items()))

        result = (
            f"📊 CSV Summary: {file_path}\n"
            f"{'─' * 50}\n"
            f"Rows: {num_rows}\n"
            f"Columns ({len(columns)}): {', '.join(columns)}\n"
            f"Numeric columns: {', '.join(numeric_cols) if numeric_cols else 'none detected'}\n"
            f"\nFirst {min(5, num_rows)} rows:\n"
        )
        for i, line in enumerate(sample_lines, 1):
            result += f"  {i}. {line}\n"

        return result
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def aggregate_csv(
    file_path: str,
    group_by: str,
    value_column: str,
    operation: str = "sum",
) -> str:
    """Aggregate a CSV file by grouping on one or more columns and applying an operation to a numeric column.

    Args:
        file_path: Absolute or relative path to the CSV file.
        group_by: Comma-separated column names to group by (e.g. "product,region").
        value_column: The numeric column to aggregate (e.g. "revenue").
        operation: Aggregation operation — one of: sum, count, mean, min, max. Default is sum.
    """
    try:
        rows = _load_csv(file_path)
        if not rows:
            return "CSV file is empty (no data rows)."

        group_cols = [c.strip() for c in group_by.split(",")]

        # Validate columns exist
        available = list(rows[0].keys())
        for col in group_cols + [value_column]:
            if col not in available:
                return f"Error: Column '{col}' not found. Available columns: {', '.join(available)}"

        # Group data
        groups: dict[tuple, list[float]] = defaultdict(list)
        for row in rows:
            key = tuple(row[c] for c in group_cols)
            val = _try_float(row[value_column])
            if val is not None:
                groups[key].append(val)

        # Apply operation
        op = operation.lower()
        results: list[tuple[tuple, float]] = []
        for key, values in groups.items():
            if op == "sum":
                agg = sum(values)
            elif op == "count":
                agg = len(values)
            elif op == "mean":
                agg = sum(values) / len(values) if values else 0
            elif op == "min":
                agg = min(values) if values else 0
            elif op == "max":
                agg = max(values) if values else 0
            else:
                return f"Error: Unknown operation '{operation}'. Use: sum, count, mean, min, max."
            results.append((key, agg))

        # Sort by aggregate value descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Format output
        header = f"📈 {op.upper()}({value_column}) grouped by [{', '.join(group_cols)}]"
        output = f"{header}\n{'─' * len(header)}\n"

        # Calculate grand total for percentages
        grand_total = sum(v for _, v in results)

        for key, agg in results:
            label = " / ".join(str(k) for k in key)
            if op in ("sum", "mean", "min", "max") and grand_total > 0:
                pct = (agg / grand_total) * 100
                if agg == int(agg):
                    output += f"  {label:30s}  {int(agg):>10,}  ({pct:.1f}%)\n"
                else:
                    output += f"  {label:30s}  {agg:>12,.2f}  ({pct:.1f}%)\n"
            else:
                output += f"  {label:30s}  {agg:>10}\n"

        if op == "sum":
            output += f"{'─' * 56}\n"
            if grand_total == int(grand_total):
                output += f"  {'TOTAL':30s}  {int(grand_total):>10,}\n"
            else:
                output += f"  {'TOTAL':30s}  {grand_total:>12,.2f}\n"

        return output
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
