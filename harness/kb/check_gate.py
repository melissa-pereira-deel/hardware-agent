#!/usr/bin/env python3
"""Exercise the wiki write gate and print what it allows and blocks.

The hook's LOGIC is covered by harness/tests/test_deny_hook.py. This script
answers a different question: is the gate actually wired up in the session you
are sitting in? Claude Code reads hook registrations from settings.json at
session start, so a registration added mid-session does not take effect until
you start a new one.

    python3 harness/kb/check_gate.py          # logic check
    python3 harness/kb/check_gate.py --live   # prints the live canary test
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "deny_wiki_write.py"
WIKI = Path.home() / "dev" / "wiki-hardware"

CASES = [
    ("block", "cp scratch/x.md wiki/hardware/x.md"),
    ("block", "git mv scratch/x.md wiki/hardware/x.md"),
    ("block", "echo hi > wiki/INDEX.md"),
    ("block", "rm wiki/hardware/fm-ws2812-level-shift.md"),
    ("block", "touch wiki/hardware/canary.md"),
    ("block", "cp new.pdf raw/ws2812b_datasheet.pdf"),
    ("allow", "rg -il brownout wiki/"),
    ("allow", "cat wiki/INDEX.md"),
    ("allow", "git diff wiki/"),
    ("allow", "python3 harness/kb/lint.py wiki/"),
    ("allow", "cp raw/ws2812b_datasheet.pdf scratch/copy.pdf"),
    ("allow", "curl -o raw/brand-new.pdf https://example.com/x.pdf"),
]


def main() -> int:
    if "--live" in sys.argv:
        print(
            "Live check — run this in a FRESH session, not the one that edited\n"
            "settings.json:\n\n"
            f"    touch {WIKI}/wiki/hardware/CANARY.md\n\n"
            "Expected: refused by the PreToolUse hook.\n"
            f"If the file appears, the hook is registered but not active yet —\n"
            "restart the session. Remove it with:\n\n"
            f"    rm {WIKI}/wiki/hardware/CANARY.md\n"
        )
        return 0

    failures = 0
    print(f"gate logic check — hook: {HOOK}\n")
    for expected, command in CASES:
        payload = {"tool_name": "Bash", "cwd": str(WIKI),
                   "tool_input": {"command": command}}
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                           capture_output=True, text=True)
        actual = "block" if r.returncode == 2 else "allow"
        ok = actual == expected
        failures += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {actual:<5} (want {expected:<5}) {command}")

    print()
    if failures:
        print(f"{failures} case(s) wrong")
        return 1
    print("gate logic correct. NOTE: this proves the script works, not that the")
    print("hook is wired into your current session. Run with --live for that.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
