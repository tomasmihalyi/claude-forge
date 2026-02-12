#!/bin/bash
# Forge End-to-End Validation Script
# Run from project root: bash test_forge.sh

set -euo pipefail

FORGE_ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$FORGE_ROOT/.venv/bin/python"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC}: $1"; }
fail() { echo -e "${RED}FAIL${NC}: $1"; exit 1; }

echo "=== Forge Validation ==="
echo "Root: $FORGE_ROOT"
echo ""

# 1. Python venv exists
[[ -f "$PYTHON" ]] && pass "Python venv exists" || fail "Python venv not found at $PYTHON"

# 2. Dependencies installed
$PYTHON -c "import mcp; import httpx" 2>/dev/null && pass "Dependencies (mcp, httpx) installed" || fail "Missing dependencies"

# 3. Server template is valid
$PYTHON "$FORGE_ROOT/forge/validate_server.py" "$FORGE_ROOT/forge/templates/server_template.py" > /dev/null && pass "Server template validates" || fail "Server template validation failed"

# 4. Validator catches bad files
echo "invalid python {{{{" > /tmp/_forge_test_bad.py
if $PYTHON "$FORGE_ROOT/forge/validate_server.py" /tmp/_forge_test_bad.py > /dev/null 2>&1; then
    fail "Validator should reject bad syntax"
else
    pass "Validator rejects bad syntax"
fi
rm -f /tmp/_forge_test_bad.py

# 5. Registry is valid JSON
$PYTHON -c "import json; json.load(open('$FORGE_ROOT/registry.json'))" && pass "registry.json is valid JSON" || fail "registry.json is invalid"

# 6. Agent file exists
[[ -f "$FORGE_ROOT/.claude/agents/forge.md" ]] && pass "Forge agent file exists" || fail "Agent file missing"

# 7. Settings file exists
[[ -f "$FORGE_ROOT/.claude/settings.json" ]] && pass "Settings file exists" || fail "Settings file missing"

# 8. Skill file exists
[[ -f "$FORGE_ROOT/.claude/skills/forge-status/SKILL.md" ]] && pass "Forge status skill exists" || fail "Skill file missing"

# 9. Demo data exists
[[ -f "$FORGE_ROOT/demo/sales.csv" ]] && pass "Demo sales.csv exists" || fail "Demo data missing"

# 10. Server template CLI wrapper works
RESULT=$($PYTHON "$FORGE_ROOT/forge/templates/server_template.py" --call tool_name '{"param": "test"}')
[[ "$RESULT" == "Processed: test" ]] && pass "Server template CLI wrapper works" || fail "CLI wrapper returned: $RESULT"

# 11. Project structure check
for dir in .claude/agents .claude/skills/forge-status forge/templates servers demo; do
    [[ -d "$FORGE_ROOT/$dir" ]] && pass "Directory $dir exists" || fail "Directory $dir missing"
done

echo ""
echo "=== All checks passed ==="
