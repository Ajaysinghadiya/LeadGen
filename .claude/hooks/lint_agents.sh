#!/bin/bash
# Post-tool hook: runs ruff on any file written inside backend/agents/ or backend/mcp_servers/

FILE=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('path', '') or d.get('file_path', ''))
except:
    print('')
" 2>/dev/null)

if [[ -z "$FILE" ]]; then
    exit 0
fi

# Normalize to forward slashes for matching
NORMALIZED="${FILE//\\//}"

if [[ "$NORMALIZED" == *"backend/agents/"* ]] || [[ "$NORMALIZED" == *"backend/mcp_servers/"* ]]; then
    # Only lint .py files
    if [[ "$NORMALIZED" == *.py ]]; then
        cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
        if command -v ruff &>/dev/null; then
            ruff check "$FILE" --fix --quiet 2>&1
        elif [ -f "backend/.venv/Scripts/ruff.exe" ]; then
            "backend/.venv/Scripts/ruff.exe" check "$FILE" --fix --quiet 2>&1
        elif [ -f "backend/.venv/bin/ruff" ]; then
            "backend/.venv/bin/ruff" check "$FILE" --fix --quiet 2>&1
        fi
    fi
fi
