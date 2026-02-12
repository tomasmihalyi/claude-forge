#!/usr/bin/env python3
"""
Forge Server Validator

Validates a generated MCP server file before registration.
Used by the Forge agent after generating a new server.

Usage:
    python forge/validate_server.py servers/my-server/server.py

Exit codes:
    0 = all checks passed
    1 = validation failed (details printed to stdout)
"""

import ast
import importlib.util
import json
import py_compile
import signal
import sys
from pathlib import Path

VALIDATION_TIMEOUT = 10  # seconds


def _get_mcp_tool_functions(tree: ast.Module) -> list[ast.AsyncFunctionDef]:
    """Find all functions decorated with @mcp.tool() in the AST."""
    tool_funcs = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            # Match @mcp.tool() — a Call whose func is an Attribute
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if (isinstance(func, ast.Attribute) and func.attr == "tool"
                        and isinstance(func.value, ast.Name) and func.value.id == "mcp"):
                    tool_funcs.append(node)
    return tool_funcs


def _check_no_bare_prints(tree: ast.Module) -> list[str]:
    """Check for print() calls that don't use file=sys.stderr."""
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Match print(...)
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            # Check if it has file=sys.stderr
            has_stderr = False
            for kw in node.keywords:
                if kw.arg == "file":
                    has_stderr = True
                    break
            if not has_stderr:
                # Allow prints inside if __name__ == "__main__" blocks
                # We'll check by line range — skip this for now and only flag
                # prints in the main module body and tool functions
                violations.append(f"line {node.lineno}")
    return violations


def validate(server_path: str) -> dict:
    """Validate a server file. Returns {"ok": bool, "checks": [...], "error": str|None}."""
    path = Path(server_path).resolve()
    checks = []

    # Check 1: File exists
    if not path.exists():
        return {"ok": False, "checks": checks, "error": f"File not found: {path}"}
    checks.append("file_exists: PASS")

    # Check 2: Python syntax
    try:
        py_compile.compile(str(path), doraise=True)
        checks.append("syntax: PASS")
    except py_compile.PyCompileError as e:
        return {"ok": False, "checks": checks, "error": f"Syntax error: {e}"}

    # --- AST-based structural checks (checks 7-11) ---
    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"ok": False, "checks": checks, "error": f"AST parse error: {e}"}

    tool_funcs = _get_mcp_tool_functions(tree)

    # Check 7: All @mcp.tool() functions are async
    sync_tools = [f.name for f in tool_funcs if isinstance(f, ast.FunctionDef)]
    if sync_tools:
        return {"ok": False, "checks": checks,
                "error": f"Tool functions must be async: {', '.join(sync_tools)}"}
    checks.append(f"async_tools: PASS ({len(tool_funcs)} tools)")

    # Check 8: All tool functions have docstrings
    no_docs = [f.name for f in tool_funcs
                if not (f.body and isinstance(f.body[0], ast.Expr)
                        and isinstance(f.body[0].value, ast.Constant))]
    if no_docs:
        return {"ok": False, "checks": checks,
                "error": f"Tool functions missing docstrings: {', '.join(no_docs)}"}
    checks.append("docstrings: PASS")

    # Check 9: All tool functions have type-hinted parameters
    no_hints = []
    for f in tool_funcs:
        for arg in f.args.args:
            if arg.arg == "self":
                continue
            if arg.annotation is None:
                no_hints.append(f"{f.name}({arg.arg})")
    if no_hints:
        return {"ok": False, "checks": checks,
                "error": f"Parameters missing type hints: {', '.join(no_hints)}"}
    checks.append("type_hints: PASS")

    # Check 10: All tool functions have -> str return annotation
    no_return = []
    for f in tool_funcs:
        if f.returns is None:
            no_return.append(f.name)
        elif isinstance(f.returns, ast.Constant) and f.returns.value != str:
            no_return.append(f.name)
        elif isinstance(f.returns, ast.Name) and f.returns.id != "str":
            no_return.append(f.name)
    if no_return:
        return {"ok": False, "checks": checks,
                "error": f"Tool functions must return str: {', '.join(no_return)}"}
    checks.append("return_type: PASS")

    # Check 11: No bare print() calls in tool functions
    # We only flag prints inside tool function bodies (not in __main__ block)
    tool_line_ranges = []
    for f in tool_funcs:
        end_line = f.end_lineno or f.lineno + 100
        tool_line_ranges.append((f.lineno, end_line))

    bare_prints_in_tools = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            has_stderr = any(kw.arg == "file" for kw in node.keywords)
            if not has_stderr:
                for start, end in tool_line_ranges:
                    if start <= node.lineno <= end:
                        bare_prints_in_tools.append(f"line {node.lineno}")
                        break
    if bare_prints_in_tools:
        return {"ok": False, "checks": checks,
                "error": f"print() in tool functions breaks stdio transport (use file=sys.stderr): {', '.join(bare_prints_in_tools)}"}
    checks.append("no_stdout_in_tools: PASS")

    # Check 3: Module imports successfully (with timeout)
    def _timeout_handler(signum, frame):
        raise TimeoutError("Module import took too long (possible infinite loop)")

    try:
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(VALIDATION_TIMEOUT)
        try:
            spec = importlib.util.spec_from_file_location("_forge_test_server", str(path))
            if spec is None or spec.loader is None:
                return {"ok": False, "checks": checks, "error": "Could not create module spec"}
            module = importlib.util.module_from_spec(spec)
            import unittest.mock
            with unittest.mock.patch.object(sys, "argv", ["test"]):
                spec.loader.exec_module(module)
            checks.append("imports: PASS")
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    except TimeoutError as e:
        return {"ok": False, "checks": checks, "error": str(e)}
    except Exception as e:
        return {"ok": False, "checks": checks, "error": f"Import error: {type(e).__name__}: {e}"}

    # Check 4: Has a FastMCP instance
    mcp_instance = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if type(attr).__name__ == "FastMCP":
            mcp_instance = attr
            break

    if mcp_instance is None:
        return {"ok": False, "checks": checks, "error": "No FastMCP instance found"}
    checks.append("fastmcp_instance: PASS")

    # Check 5: Has at least one tool registered
    try:
        tools = list(mcp_instance._tool_manager._tools.keys())
        if not tools:
            return {"ok": False, "checks": checks, "error": "No tools registered (use @mcp.tool() decorator)"}
        checks.append(f"tools_registered: PASS ({', '.join(tools)})")
    except Exception as e:
        return {"ok": False, "checks": checks, "error": f"Could not inspect tools: {e}"}

    # Check 6: Has __main__ block with mcp.run
    if 'if __name__ == "__main__"' not in source and "if __name__ == '__main__'" not in source:
        return {"ok": False, "checks": checks, "error": "Missing if __name__ == '__main__' block"}
    if "mcp.run(" not in source:
        return {"ok": False, "checks": checks, "error": "Missing mcp.run() call"}
    checks.append("main_block: PASS")

    return {"ok": True, "checks": checks, "error": None}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python forge/validate_server.py <server_path>")
        sys.exit(1)

    result = validate(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)
