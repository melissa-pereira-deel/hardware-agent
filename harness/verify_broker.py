#!/usr/bin/env python3
"""Start risk-broker as a real MCP server and exercise it over stdio.

This is deliberately not a unit test with a stubbed `mcp`. It spawns the
server as a subprocess, performs the MCP initialize handshake, lists the
registered tools, and calls each tier boundary. If this passes, the server
genuinely works as an MCP server.

    python harness/verify_broker.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[1]


def _text(result) -> str:
    parts = []
    for block in result.content:
        parts.append(getattr(block, "text", str(block)))
    return "\n".join(parts)


async def main() -> int:
    audit = Path(tempfile.mkdtemp()) / "verify-audit.jsonl"
    env = {**os.environ, "RISK_BROKER_AUDIT": str(audit), "RISK_BROKER_WORKDIR": str(REPO)}

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "risk_broker.server"],
        cwd=str(REPO),
        env=env,
    )

    failures = 0
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"connected to: {init.server_info.name} v{init.server_info.version}")
            print()

            tools = (await session.list_tools()).tools
            print(f"{len(tools)} tools registered:")
            for t in sorted(tools, key=lambda x: x.name):
                ro = getattr(t.annotations, "read_only_hint", None) if t.annotations else None
                flag = "read-only" if ro else "executes"
                first = (t.description or "").strip().splitlines()[0]
                print(f"  - {t.name:<18} [{flag:<9}] {first}")
            print()

            checks = [
                ("T1 classifies as T1", "classify_action",
                 {"command": "kicad-cli pcb drc board.kicad_pcb"}, '"tier": 1'),
                ("injection is refused", "classify_action",
                 {"command": "kicad-cli pcb drc b.kicad_pcb; rm -rf /tmp/x"}, '"blocked": "unparseable"'),
                ("T3 efuse is T3", "classify_action",
                 {"command": "espefuse.py burn_key BLOCK_KEY0 key.bin"}, '"tier": 3'),
                ("unknown fails closed to T3", "classify_action",
                 {"command": "frobnicate --all"}, '"rule": "unmatched"'),
                ("run_autonomous refuses T3", "run_autonomous",
                 {"command": "espefuse.py burn_key BLOCK_KEY0 key.bin"}, '"refused": true'),
                ("run_autonomous refuses T2", "run_autonomous",
                 {"command": "esphome run lamp.yaml"}, '"use_instead": "run_device_write"'),
                ("device_write demands context", "run_device_write",
                 {"command": "esphome run lamp.yaml", "device": "", "what_changes": "",
                  "recovery": ""}, '"refused": true'),
                ("plan_irreversible never executes", "plan_irreversible",
                 {"command": "espefuse.py burn_key BLOCK_KEY0 key.bin"}, '"executed": false'),
            ]

            for label, tool, args, expect in checks:
                out = _text(await session.call_tool(tool, args))
                ok = expect.lower() in out.lower()
                print(f"  {'PASS' if ok else 'FAIL'}  {label}")
                if not ok:
                    failures += 1
                    print(f"        expected {expect!r} in:\n{out[:400]}")

            print()
            real = _text(await session.call_tool(
                "run_autonomous", {"command": "kicad-cli version"}))
            print("  live T1 execution (kicad-cli may be absent; both outcomes fine):")
            print("   ", real.replace("\n", " ")[:220])

    print()
    print("OK" if failures == 0 else f"{failures} FAILURES")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
