#!/usr/bin/env python3
"""PreToolUse hook: refuse agent writes into the canonical wiki tree.

Why this exists
---------------
policy/tool-tiers.yaml has a `kb-canonicalize` rule, but it only ever sees
shell commands routed through the risk broker. An agent in Claude Code writes
files with the Write and Edit tools, which never reach the broker at all. So
the T3 gate on canonicalisation guarded a path the agent does not take.

This closes that. `scratch/` stays freely writable - drafting is cheap and is
meant to be. `wiki/` is not writable by a tool, only by a human moving a
reviewed draft across.

Registered user-scoped rather than project-scoped on purpose: drafts get
written from firmware repos, and a project hook only fires when the wiki
itself is the working directory - the case that matters least.

Exit 0 allows, exit 2 blocks and returns stderr to the model.
Set HARDWARE_AGENT_WIKI to override the wiki location.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_WIKI = Path.home() / "dev" / "wiki-hardware"
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}


def canonical_root() -> Path:
    root = Path(os.environ.get("HARDWARE_AGENT_WIKI", DEFAULT_WIKI)).expanduser()
    return (root / "wiki").resolve()


def target_path(payload: dict) -> Path | None:
    tool_input = payload.get("tool_input") or {}
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if value:
            return Path(str(value)).expanduser()
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Never block on a payload we cannot read.

    if payload.get("tool_name") not in WRITE_TOOLS:
        return 0

    target = target_path(payload)
    if target is None:
        return 0

    try:
        resolved = target.resolve()
        wiki = canonical_root()
    except OSError:
        return 0

    if resolved == wiki or wiki in resolved.parents:
        rel = resolved.name
        print(
            f"BLOCKED: {resolved}\n"
            f"\n"
            f"Writing into the canonical wiki is a T3 action and is not "
            f"available to a tool. A wrong entry there propagates silently and "
            f"later sessions cite it as ground truth.\n"
            f"\n"
            f"Write the draft to scratch/{rel} instead, with full provenance, "
            f"run the linter over it, and show the diff. Melissa moves it "
            f"across after reading that diff.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
