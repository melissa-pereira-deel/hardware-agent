"""risk-broker: an MCP server that puts the hardware risk tiers in code.

Why this exists
---------------
Guardrails written as prose in a skill file are advisory to the model. This
server makes them structural: T3 commands are refused by the process, not by
good intentions, and every T2 action leaves an audit trail naming the physical
device it touched.

Three tools, matching the three tiers:

    classify_action    - always safe, tells you the tier and why
    run_autonomous     - executes T1 only (build, simulate, export, analyse)
    run_device_write   - executes T2 only, and demands the caller state which
                         device, what changes, and how to recover
    plan_irreversible  - never executes; returns the command plus the warning

Run with:  python -m risk_broker.server
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .tiers import Policy

mcp = FastMCP("risk-broker")
policy = Policy()

AUDIT = Path(os.environ.get("RISK_BROKER_AUDIT", Path.home() / ".risk-broker-audit.jsonl"))
WORKDIR = Path(os.environ.get("RISK_BROKER_WORKDIR", Path.cwd()))
TIMEOUT = int(os.environ.get("RISK_BROKER_TIMEOUT", "600"))


def _audit(**fields) -> None:
    fields["ts"] = datetime.now(timezone.utc).isoformat()
    with AUDIT.open("a") as fh:
        fh.write(json.dumps(fields) + "\n")


def _execute(command: str, cwd: str | None) -> dict:
    started = time.time()
    proc = subprocess.run(
        command,
        shell=True,
        cwd=cwd or WORKDIR,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[-20000:],
        "stderr": proc.stderr[-20000:],
        "duration_s": round(time.time() - started, 2),
    }


@mcp.tool()
def classify_action(command: str) -> dict:
    """Return the risk tier for a hardware command without running it.

    Call this whenever you are unsure, and before proposing any command to the
    user. Costs nothing and never touches hardware.
    """
    c = policy.classify(command)
    return {
        "command": command,
        "tier": c.tier,
        "label": c.label,
        "rule": c.rule,
        "reason": c.reason,
        "read_first": c.see,
        "binary": c.binary,
        "binary_allowed": c.allowed_binary,
    }


@mcp.tool()
def run_autonomous(command: str, cwd: str | None = None) -> dict:
    """Run a T1 command: build, simulate, export, analyse, or read.

    Refuses anything that writes to a device, spends money, or is irreversible.
    Use this for kicad-cli, ngspice, arduino-cli compile, pio run, idf.py build,
    esphome compile, wokwi-cli, slicers, and read-only instrument capture.
    """
    c = policy.classify(command)

    if not c.allowed_binary:
        _audit(tool="run_autonomous", command=command, outcome="refused-binary")
        return {
            "refused": True,
            "why": f"Binary '{c.binary}' is not in binaries_allowed in policy/tool-tiers.yaml.",
        }

    if c.tier != 1:
        _audit(tool="run_autonomous", command=command, outcome=f"refused-tier-{c.tier}")
        return {
            "refused": True,
            "why": f"This is {c.label}, not T1. {c.reason}",
            "use_instead": "run_device_write" if c.tier == 2 else "plan_irreversible",
            "read_first": c.see,
        }

    result = _execute(command, cwd)
    _audit(tool="run_autonomous", command=command, rule=c.rule, rc=result["returncode"])
    return result


@mcp.tool()
def run_device_write(
    command: str,
    device: str,
    what_changes: str,
    recovery: str,
    cwd: str | None = None,
) -> dict:
    """Run a T2 command that writes to a connected physical device.

    You must state the device, what will change on it, and how to undo it.
    These are not bureaucracy: writing them down is what catches "wrong port,
    wrong board" before it happens, and they land in the audit log.

    If the device is potted, installed, or remote - anything you cannot
    physically re-flash - do not use this tool. That is T3.
    """
    if not all(s.strip() for s in (device, what_changes, recovery)):
        return {
            "refused": True,
            "why": "device, what_changes and recovery must all be stated.",
        }

    c = policy.classify(command)

    if not c.allowed_binary:
        _audit(tool="run_device_write", command=command, outcome="refused-binary")
        return {
            "refused": True,
            "why": f"Binary '{c.binary}' is not in binaries_allowed in policy/tool-tiers.yaml.",
        }

    if c.tier == 3:
        _audit(tool="run_device_write", command=command, outcome="refused-tier-3")
        return {
            "refused": True,
            "why": f"This is T3, not T2. {c.reason}",
            "use_instead": "plan_irreversible",
            "read_first": c.see,
        }

    if c.tier != 2:
        return {
            "refused": True,
            "why": f"This is {c.label}. Use run_autonomous.",
        }

    result = _execute(command, cwd)
    _audit(
        tool="run_device_write",
        command=command,
        rule=c.rule,
        device=device,
        what_changes=what_changes,
        recovery=recovery,
        rc=result["returncode"],
    )
    result["device"] = device
    result["recovery"] = recovery
    return result


@mcp.tool()
def plan_irreversible(command: str) -> dict:
    """Produce a hand-over plan for a T3 action. Never executes anything.

    Use for eFuse burns, secure boot, flash encryption, AVR fuse writes,
    placing orders, and starting machine motion. Returns the command and the
    reason it cannot be undone, for the person to run themselves.
    """
    c = policy.classify(command)
    _audit(tool="plan_irreversible", command=command, rule=c.rule, outcome="planned")
    return {
        "executed": False,
        "command": command,
        "tier": c.tier,
        "label": c.label,
        "rule": c.rule,
        "reason": c.reason,
        "read_first": c.see,
        "handover": (
            "This tool does not execute. Present the command, explain exactly what "
            "state the hardware will be in afterwards, name the recovery path or say "
            "there isn't one, and recommend testing on a sacrificial board first. "
            "Then stop and let the person run it."
        ),
    }


@mcp.tool()
def recent_actions(limit: int = 20) -> list[dict]:
    """Read the audit log of what this broker has run. Useful during bring-up
    when you need to reconstruct what was flashed to which board."""
    if not AUDIT.exists():
        return []
    lines = AUDIT.read_text().strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]]


if __name__ == "__main__":
    mcp.run()
