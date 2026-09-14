"""risk-broker: an MCP server that puts the hardware risk tiers in code.

Why this exists
---------------
Guardrails written as prose in a skill file are advisory to the model. This
server makes them structural: T3 commands are refused by the process, not by
good intentions, and every T2 action leaves an audit trail naming the physical
device it touched.

Five tools:

    classify_action    - always safe, tells you the tier and why
    run_autonomous     - executes T1 only (build, simulate, export, analyse)
    run_device_write   - executes T2 only, and demands the caller state which
                         device, what changes, and how to recover
    plan_irreversible  - never executes; returns the command plus the warning
    recent_actions     - reads the audit log

Execution model
---------------
Commands run with shell=False against a shlex-parsed argv. Shell
metacharacters are refused by the classifier rather than passed through as
literal arguments. This is the fix for the original implementation, which
classified only the first token while running the whole string under
`shell=True` - so `kicad-cli erc x; rm -rf ~` was classified T1 and would have
executed. See REVIEW.md §1.1.

Run with:  risk-broker          (console script)
       or:  python -m risk_broker.server
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .tiers import Policy

# A bootloader flash is normally T2. But flashing a bootloader built with
# secure boot or flash encryption enabled is irreversible - the next power-on
# burns the eFuse - and the command text is identical either way. The broker
# cannot tell them apart, so it requires the caller to say which it is.
BOOTLOADER_FLASH = re.compile(
    r"\bbootloader\.bin\b|\bwrite[_-]flash\b.*\b0x0*(0|1000)\b|^idf\.py\b.*\bflash\b",
    re.IGNORECASE,
)
SECURE_BOOT_DISCLOSED = re.compile(r"secure[\s_-]?boot", re.IGNORECASE)
FLASH_ENC_DISCLOSED = re.compile(r"flash[\s_-]?encrypt|encrypt", re.IGNORECASE)

mcp = MCPServer(
    "risk-broker",
    version="0.1.0",
    instructions=(
        "Enforces hardware risk tiers. Call classify_action before proposing any "
        "command. T1 runs via run_autonomous, T2 via run_device_write (which "
        "requires naming the device, the change and the recovery path), T3 is "
        "never executed - use plan_irreversible and hand the command over."
    ),
)
policy = Policy()

AUDIT = Path(os.environ.get("RISK_BROKER_AUDIT", Path.home() / ".risk-broker-audit.jsonl"))
WORKDIR = Path(os.environ.get("RISK_BROKER_WORKDIR", Path.cwd()))
TIMEOUT = int(os.environ.get("RISK_BROKER_TIMEOUT", "600"))
MAX_OUTPUT = 20_000

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False)


def _audit(**fields) -> None:
    fields["ts"] = datetime.now(timezone.utc).isoformat()
    try:
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT.open("a") as fh:
            fh.write(json.dumps(fields, default=str) + "\n")
    except OSError as exc:
        # An unwritable audit log must not silently swallow the fact that it
        # failed, but it also must not block a legitimate T1 build.
        print(f"risk-broker: audit write failed: {exc}", flush=True)


def _execute(argv: list[str], cwd: str | None) -> dict:
    """Run one already-classified command. No shell, ever."""
    started = time.time()
    try:
        proc = subprocess.run(
            argv,
            shell=False,
            cwd=cwd or WORKDIR,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "timed_out": True,
            "returncode": None,
            "stdout": (exc.stdout or "")[-MAX_OUTPUT:] if isinstance(exc.stdout, str) else "",
            "stderr": f"timed out after {TIMEOUT}s (RISK_BROKER_TIMEOUT)",
            "duration_s": round(time.time() - started, 2),
        }
    except FileNotFoundError:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"executable not found: {argv[0]}",
            "duration_s": round(time.time() - started, 2),
        }
    except OSError as exc:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"could not execute: {exc}",
            "duration_s": round(time.time() - started, 2),
        }
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[-MAX_OUTPUT:],
        "stderr": proc.stderr[-MAX_OUTPUT:],
        "duration_s": round(time.time() - started, 2),
    }


def _describe(c) -> dict:
    return {
        "tier": c.tier,
        "label": c.label,
        "rule": c.rule,
        "reason": c.reason,
        "read_first": c.see,
        "binary": c.binary,
        "binary_allowed": c.allowed_binary,
        "argv": c.argv,
        "blocked": c.blocked,
    }


@mcp.tool(annotations=READ_ONLY)
def classify_action(command: str) -> dict:
    """Return the risk tier for a hardware command without running it.

    Call this whenever you are unsure, and before proposing any command to the
    user. Costs nothing and never touches hardware.
    """
    c = policy.classify(command)
    return {"command": command, **_describe(c)}


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False))
def run_autonomous(command: str, cwd: str | None = None) -> dict:
    """Run a T1 command: build, simulate, export, analyse, or read.

    Refuses anything that writes to a device, spends money, or is irreversible.
    Use this for kicad-cli, ngspice, arduino-cli compile, pio run, idf.py build,
    esphome compile, wokwi-cli, slicers, and read-only instrument capture.

    One command per call. Pipes, redirects and chained commands are refused.
    """
    c = policy.classify(command)

    if c.blocked:
        _audit(tool="run_autonomous", command=command, outcome="refused-unparseable")
        return {"refused": True, "why": c.reason, **_describe(c)}

    if not c.allowed_binary:
        _audit(tool="run_autonomous", command=command, outcome="refused-binary")
        return {
            "refused": True,
            "why": f"Binary '{c.binary}' is not in binaries_allowed in policy/tool-tiers.yaml.",
            **_describe(c),
        }

    if c.tier != 1:
        _audit(tool="run_autonomous", command=command, outcome=f"refused-tier-{c.tier}")
        return {
            "refused": True,
            "why": f"This is {c.label}, not T1. {c.reason}",
            "use_instead": "run_device_write" if c.tier == 2 else "plan_irreversible",
            **_describe(c),
        }

    result = _execute(c.argv, cwd)
    _audit(tool="run_autonomous", command=command, rule=c.rule, rc=result["returncode"])
    return result


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True))
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
    if not all(s and s.strip() for s in (device, what_changes, recovery)):
        return {
            "refused": True,
            "why": "device, what_changes and recovery must all be stated.",
        }

    # Bootloader flashes must state secure-boot and flash-encryption status.
    # See skills/firmware/references/esp32-irreversible.md: the flash is the
    # point of no return, and the command text cannot reveal which case it is.
    if BOOTLOADER_FLASH.search(command.strip()):
        disclosed = SECURE_BOOT_DISCLOSED.search(what_changes) and FLASH_ENC_DISCLOSED.search(
            what_changes
        )
        if not disclosed:
            _audit(
                tool="run_device_write",
                command=command,
                outcome="refused-undisclosed-bootloader-flash",
            )
            return {
                "refused": True,
                "why": (
                    "This flashes a bootloader, and 'what_changes' does not state "
                    "secure-boot and flash-encryption status.\n\n"
                    "A bootloader flash is normally reversible. A bootloader built "
                    "with secure boot or flash encryption enabled is NOT: the next "
                    "power-on burns the eFuse and there is no command left to "
                    "decline. The command line is identical in both cases - the "
                    "difference is in sdkconfig, which this broker cannot see.\n\n"
                    "Check it, then say so explicitly:\n"
                    "    grep -E 'SECURE_BOOT|FLASH_ENC' sdkconfig\n\n"
                    "If either is enabled this is T3: use plan_irreversible and hand "
                    "the command over. If neither is, restate what_changes saying so "
                    "- e.g. 'secure boot disabled, flash encryption disabled, "
                    "ordinary bootloader flash'."
                ),
                "read_first": "skills/firmware/references/esp32-irreversible.md",
            }

    c = policy.classify(command)

    if c.blocked:
        _audit(tool="run_device_write", command=command, outcome="refused-unparseable")
        return {"refused": True, "why": c.reason, **_describe(c)}

    if not c.allowed_binary:
        _audit(tool="run_device_write", command=command, outcome="refused-binary")
        return {
            "refused": True,
            "why": f"Binary '{c.binary}' is not in binaries_allowed in policy/tool-tiers.yaml.",
            **_describe(c),
        }

    if c.tier == 3:
        _audit(tool="run_device_write", command=command, outcome="refused-tier-3")
        return {
            "refused": True,
            "why": f"This is T3, not T2. {c.reason}",
            "use_instead": "plan_irreversible",
            **_describe(c),
        }

    if c.tier != 2:
        return {
            "refused": True,
            "why": f"This is {c.label}. Use run_autonomous.",
            **_describe(c),
        }

    result = _execute(c.argv, cwd)
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


@mcp.tool(annotations=READ_ONLY)
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
        **_describe(c),
        "handover": (
            "This tool does not execute. Present the command, explain exactly what "
            "state the hardware will be in afterwards, name the recovery path or say "
            "there isn't one, and recommend testing on a sacrificial board first. "
            "Then stop and let the person run it."
        ),
    }


@mcp.tool(annotations=READ_ONLY)
def recent_actions(limit: int = 20) -> list[dict]:
    """Read the audit log of what this broker has run. Useful during bring-up
    when you need to reconstruct what was flashed to which board."""
    if not AUDIT.exists():
        return []
    out = []
    for line in AUDIT.read_text().strip().splitlines()[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            out.append({"unparseable": line[:500]})
    return out


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
