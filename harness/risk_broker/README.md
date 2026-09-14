# risk-broker

An MCP server that makes the hardware risk tiers structural instead of
advisory. Guardrails written as prose in a skill file are suggestions to the
model; this process refuses T3 commands outright and forces every device write
to name the board it touched.

## Install

```bash
pip install "mcp[cli]" pyyaml
```

## Register with Claude Code

```json
{
  "mcpServers": {
    "risk-broker": {
      "command": "python",
      "args": ["-m", "risk_broker.server"],
      "cwd": "/path/to/hardware-agent/harness",
      "env": {
        "RISK_BROKER_WORKDIR": "/path/to/your/project",
        "RISK_BROKER_AUDIT": "/path/to/hardware-agent/.audit.jsonl"
      }
    }
  }
}
```

## Tools

| Tool | Executes? | For |
|---|---|---|
| `classify_action` | no | Check the tier of any command before proposing it |
| `run_autonomous` | T1 only | Build, simulate, export, analyse, read |
| `run_device_write` | T2 only | Flash and device I/O; requires device, what_changes, recovery |
| `plan_irreversible` | never | eFuse burns, orders, machine motion - returns a handover plan |
| `recent_actions` | no | Audit log; reconstruct what was flashed to which board |

## Two layers of defence

1. **Binary allowlist.** Anything whose executable isn't in `binaries_allowed`
   is refused regardless of tier. This is what stops `rm -rf /` and anything
   else that wanders in.
2. **Tier rules.** First match wins, T3 patterns listed first, and anything
   unmatched defaults to T3. It fails closed, which is the right default when
   real hardware is on the other end of the USB cable.

## Editing the policy

All of it lives in `policy/tool-tiers.yaml`. Add a rule rather than working
around a refusal - a refusal you routed around is a rule you disagreed with,
and it should be visible in the file.

## Testing

```bash
python -m pytest tests/          # if you add them
python -c "from risk_broker.tiers import Policy; \
  print(Policy().classify('espefuse.py burn_key ...').tier)"   # -> 3
```
