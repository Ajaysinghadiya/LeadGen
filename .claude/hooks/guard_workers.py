#!/usr/bin/env python3
"""
Pre-tool hook: blocks any Write/Edit/Create targeting backend/workers/.
Workers are complete and locked. All new code goes in backend/agents/.
"""
import json, sys, os

tool_input = json.loads(os.environ.get("CLAUDE_TOOL_INPUT", "{}"))
path = tool_input.get("path", "") or tool_input.get("file_path", "")

LOCKED_PATHS = [
    "backend/workers/",
    "backend\\workers\\",
]

LOCKED_FILES = [
    "backend/database.py",
    "backend/config.py",
]
# NOTE: models.py + schemas.py removed from lock — schema evolves with features
# (e.g., max_leads per job). Always wipe data/leadgen.db after model changes
# since SQLite + SQLAlchemy create_all() does not migrate existing tables.

for locked in LOCKED_PATHS:
    if locked in path:
        print(f"BLOCKED: {path}")
        print(f"backend/workers/ is locked — all 6 workers are complete.")
        print(f"Build the agentic layer in backend/agents/ instead.")
        print(f"If you genuinely need to fix a worker bug, remove this hook temporarily.")
        sys.exit(1)

for locked in LOCKED_FILES:
    if path.endswith(locked) or path == locked:
        print(f"BLOCKED: {path}")
        print(f"Core models/schema/db files are locked.")
        print(f"To extend models, discuss the change first — DB schema changes need migrations.")
        sys.exit(1)
