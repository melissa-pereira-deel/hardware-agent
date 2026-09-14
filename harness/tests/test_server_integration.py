"""Integration tests: the broker as a real MCP server over stdio.

These spawn the server as a subprocess and speak actual MCP to it. The point
is to catch exactly the class of failure that unit tests with a stubbed `mcp`
import cannot: an SDK API break, a tool that fails to register, a handler whose
signature the framework rejects.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[2]
EXPECTED_TOOLS = {
    "classify_action",
    "run_autonomous",
    "run_device_write",
    "plan_irreversible",
    "recent_actions",
}


def _text(result) -> str:
    return "\n".join(getattr(b, "text", str(b)) for b in result.content)


async def _session(tmp_audit: Path):
    env = {
        **os.environ,
        "RISK_BROKER_AUDIT": str(tmp_audit),
        "RISK_BROKER_WORKDIR": str(REPO),
    }
    return stdio_client(
        StdioServerParameters(
            command=sys.executable,
            args=["-m", "risk_broker.server"],
            cwd=str(REPO),
            env=env,
        )
    )


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def audit(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


def test_server_handshakes_and_registers_tools(audit: Path) -> None:
    async def go():
        async with await _session(audit) as (r, w):
            async with ClientSession(r, w) as s:
                init = await s.initialize()
                tools = {t.name for t in (await s.list_tools()).tools}
                return init.server_info.name, tools

    name, tools = _run(go())
    assert name == "risk-broker"
    assert tools == EXPECTED_TOOLS


def test_tier_boundaries_hold_over_the_wire(audit: Path) -> None:
    async def go():
        async with await _session(audit) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                out = {}
                out["t1"] = _text(await s.call_tool(
                    "classify_action", {"command": "kicad-cli pcb drc b.kicad_pcb"}))
                out["injection"] = _text(await s.call_tool(
                    "classify_action", {"command": "kicad-cli pcb drc b.kicad_pcb; rm -rf /tmp/x"}))
                out["t3_via_t1"] = _text(await s.call_tool(
                    "run_autonomous", {"command": "espefuse.py burn_key BLOCK_KEY0 k.bin"}))
                out["t2_via_t1"] = _text(await s.call_tool(
                    "run_autonomous", {"command": "esphome run lamp.yaml"}))
                out["t3_via_t2"] = _text(await s.call_tool(
                    "run_device_write", {"command": "espefuse.py burn_key BLOCK_KEY0 k.bin",
                                         "device": "devkit", "what_changes": "x",
                                         "recovery": "none"}))
                out["missing_ctx"] = _text(await s.call_tool(
                    "run_device_write", {"command": "esphome run lamp.yaml", "device": "",
                                         "what_changes": "", "recovery": ""}))
                out["plan"] = _text(await s.call_tool(
                    "plan_irreversible", {"command": "espefuse.py burn_key BLOCK_KEY0 k.bin"}))
                return out

    out = _run(go())
    assert json.loads(out["t1"])["tier"] == 1
    assert json.loads(out["injection"])["blocked"] == "unparseable"

    t3 = json.loads(out["t3_via_t1"])
    assert t3["refused"] is True and t3["use_instead"] == "plan_irreversible"

    t2 = json.loads(out["t2_via_t1"])
    assert t2["refused"] is True and t2["use_instead"] == "run_device_write"

    assert json.loads(out["t3_via_t2"])["refused"] is True
    assert json.loads(out["missing_ctx"])["refused"] is True

    plan = json.loads(out["plan"])
    assert plan["executed"] is False
    assert plan["tier"] == 3


def test_plan_irreversible_never_spawns_a_process(audit: Path, tmp_path: Path) -> None:
    """The strongest available assertion that T3 does not execute: give it a
    command whose only observable effect would be creating a file."""
    canary = tmp_path / "canary.txt"

    async def go():
        async with await _session(audit) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return _text(await s.call_tool(
                    "plan_irreversible",
                    {"command": f"espefuse.py burn_key {canary}"}))

    out = json.loads(_run(go()))
    assert out["executed"] is False
    assert not canary.exists()


def test_t1_executes_and_is_audited(audit: Path) -> None:
    async def go():
        async with await _session(audit) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                # python3 running the repo's own linter is T1 by policy.
                return _text(await s.call_tool(
                    "run_autonomous",
                    {"command": "python3 harness/kb/lint.py wiki-template/wiki"}))

    out = json.loads(_run(go()))
    assert "returncode" in out
    assert audit.exists(), "T1 execution should have written an audit record"
    records = [json.loads(line) for line in audit.read_text().strip().splitlines()]
    assert any(rec.get("tool") == "run_autonomous" for rec in records)
