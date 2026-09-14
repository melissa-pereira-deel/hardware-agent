# risk-broker

An MCP server that makes the hardware risk tiers structural instead of
advisory. Guardrails written as prose in a skill file are suggestions to the
model; this process refuses T3 commands outright and forces every device write
to name the board it touched.

## Install

From the repo root:

```bash
just setup
```

That creates `.venv` and installs the pinned dependencies. The pin matters:
**MCP Python SDK 2.0.0 removed `mcp.server.fastmcp` and renamed `FastMCP` to
`MCPServer`.** An unpinned `pip install "mcp[cli]"` is what made the original
server unimportable. `pyproject.toml` pins `mcp[cli]>=2.2,<3`.

## Register with Claude Code

A project-scoped `.mcp.json` is committed at the repo root and is picked up
automatically when you work in this directory:

```json
{
  "mcpServers": {
    "risk-broker": {
      "command": "${HOME}/dev/hardware-agent/.venv/bin/python",
      "args": ["-m", "risk_broker.server"],
      "cwd": "${HOME}/dev/hardware-agent",
      "env": {
        "RISK_BROKER_AUDIT": "${HOME}/dev/hardware-agent/.audit.jsonl",
        "RISK_BROKER_TIMEOUT": "600"
      }
    }
  }
}
```

To use it from *other* projects (your firmware repos), register it once at user
scope instead:

```bash
claude mcp add --scope user risk-broker \
  -- "$HOME/dev/hardware-agent/.venv/bin/python" -m risk_broker.server
```

### Environment

| Variable | Default | Notes |
|---|---|---|
| `RISK_BROKER_AUDIT` | `~/.risk-broker-audit.jsonl` | Append-only JSONL record of every call |
| `RISK_BROKER_WORKDIR` | the server's cwd | Default working directory for executed commands |
| `RISK_BROKER_TIMEOUT` | `600` | Seconds before a command is killed |
| `RISK_BROKER_POLICY` | `policy/tool-tiers.yaml` | Override for testing an alternate policy |

`RISK_BROKER_WORKDIR` sets the *default*; `run_autonomous` and
`run_device_write` both take a per-call `cwd`, which is what you want when the
broker lives here and the firmware lives elsewhere.

## Tools

| Tool | Executes? | For |
|---|---|---|
| `classify_action` | no | Check the tier of any command before proposing it |
| `run_autonomous` | T1 only | Build, simulate, export, analyse, read |
| `run_device_write` | T2 only | Flash and device I/O; requires device, what_changes, recovery |
| `plan_irreversible` | never | eFuse burns, orders, machine motion - returns a handover plan |
| `recent_actions` | no | Audit log; reconstruct what was flashed to which board |

## Three layers of defence

1. **Structural parse.** Shell metacharacters (`; | & \` $( ${ > <` and
   newlines) are refused before any tiering happens, and the command is parsed
   to an argv list. One call is exactly one command.
2. **Binary allowlist.** `argv[0]` must be in `binaries_allowed`, whatever tier
   the command would otherwise match.
3. **Tier rules.** First match wins, T3 patterns listed first, anything
   unmatched defaults to T3.

Execution is `shell=False` against the parsed argv. Layers 1 and 3 exist
because layer 2 alone was not enough: the original implementation classified
only the first token while running the whole string through a shell, so
`kicad-cli sch erc b.kicad_sch; rm -rf ~/Documents` classified as T1 with an
allowed binary. See `REVIEW.md` §1.1.

Because `default_tier` is 3, **narrowing a rule in `tool-tiers.yaml` is always
safe** - anything that stops matching falls through to refusal. Widening one is
not, and deserves the same scrutiny as any other guardrail edit.

## Editing the policy

All of it lives in `policy/tool-tiers.yaml`. Add a rule rather than working
around a refusal - a refusal you routed around is a rule you disagreed with,
and it should be visible in the file. `harness/tests/test_tiers.py` fails if a
rule has no test case, so a new rule needs a new case.

## Testing

```bash
just test            # 73 tests: classifier table, fail-closed, allowlist, injection, MCP stdio
just verify-broker   # spawn the server, handshake, list tools, probe every tier boundary
```

`verify-broker` is the one that matters. The original was only ever tested
against a stubbed `mcp` import, which is precisely how the v2 API break went
unnoticed.
