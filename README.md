# hardware-agent

A risk-tiered agent system for hardware prototyping — electronics, PCBs,
firmware, sourcing and manufacturability — built for Claude Code.

It is two things: a set of skills that know the domain, and a harness that
stops the agent doing irreversible things with them. The second half is most of
the work, because hardware is unforgiving in a way software isn't. A bad deploy
rolls back in ninety seconds; a bad eFuse burn is a dead chip.

## The risk model

Every action is one of three tiers:

- **T1 — autonomous.** Read, analyse, simulate, build, export. Runs freely. Nothing changes state on real hardware and nothing costs money.
- **T2 — confirm first.** Anything that writes to a connected device. The agent must state *which* device, *what* changes, and *how to undo it* before it runs.
- **T3 — advisory only.** Irreversible silicon (eFuse, secure boot), mains voltage, lithium charging, spending money, machine motion, regulatory claims, and promoting knowledge into the canonical wiki. Drafted and handed over, never executed.

Enforced in three places, because prose alone is advisory to a model:

| Layer | Covers | Fails |
|---|---|---|
| Skills (`AGENT.md`, `skills/`) | Reasoning — the agent declines before it reaches for a tool | Open: it's persuasion |
| Risk broker (`harness/risk_broker/`) | Commands routed through its MCP tools | Closed: unmatched → T3 |
| `PreToolUse` hook (`harness/kb/`) | Write/Edit/MultiEdit/NotebookEdit/Bash into the wiki | Closed for known tools |

## What's here

```
AGENT.md                  orchestrator: routing, tiers, constraint questions, explanation style
policy/tool-tiers.yaml    risk classification as reviewable data
policy/guardrails.md      stances that apply when no command is involved
skills/                   circuit-design, firmware, sourcing-bom, manufacturing-dfm, knowledge-base
harness/risk_broker/      MCP server enforcing the tiers in code
harness/kb/               wiki bootstrap, linter, write gate
harness/smoke/            five behavioural tests and their recorded results
TOOLS.md                  tool catalogue: purpose, tier, licence, install
wiki-template/            scaffold for the knowledge wiki
```

Every number in `skills/*/references/` carries a source URL and the date it was
checked, or is explicitly marked unverified. That discipline exists because the
first draft of these files confidently asserted several things that turned out
to be wrong — see `REVIEW.md`.

## Install

Requires Python 3.10+, [`just`](https://github.com/casey/just), and ideally
[`uv`](https://docs.astral.sh/uv/) (falls back to venv + pip).

```bash
git clone https://github.com/melissa-pereira-deel/hardware-agent
cd hardware-agent
just setup
just test          # 181 tests
just doctor        # which allowlisted tools are actually installed
```

`TOOLS.md` catalogues every tool the agent can drive — purpose, risk tier,
licence and install command. Being allowlisted is not the same as being
installed; `just doctor` reports the difference.

### Register the risk broker

A project-scoped `.mcp.json` is included and uses a relative interpreter path,
so it works wherever you cloned to. To use the broker from *other* projects,
register it at user scope instead:

```bash
claude mcp add --scope user risk-broker -- "$(pwd)/.venv/bin/python" -m risk_broker.server
```

```bash
just verify-broker   # starts it over stdio, lists tools, probes every tier boundary
```

### Create a knowledge wiki

```bash
just bootstrap-wiki ~/dev/wiki-hardware
```

Markdown in git, searched with ripgrep. No vector database — at one person's
scale grep wins on maintenance, staleness and debuggability. Three tiers with a
wall between them:

```
raw/       cached sources. Immutable, gitignored; raw/MANIFEST.tsv records what was fetched.
scratch/   agent drafts. Untrusted, freely writable.
wiki/      canonical. Provenance required. Gated.
```

The wall is the point. An agent writing unsupervised into its own authoritative
knowledge base is how one early misreading becomes load-bearing fact six months
later.

### Optional: the write gate

A `PreToolUse` hook that refuses tool writes into `wiki/`, so canonicalisation
stays a human action. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash",
      "hooks": [{ "type": "command",
                  "command": "python3 /absolute/path/to/hardware-agent/harness/kb/deny_wiki_write.py" }]
    }]
  }
}
```

Set `HARDWARE_AGENT_WIKI` if your wiki isn't at `~/dev/wiki-hardware`.

**Hook registrations load at session start** — one added mid-session is inert
until you restart. Verify with `just check-gate` (logic) and
`python3 harness/kb/check_gate.py --live` (wiring).

## What this does not do

Stated plainly because the repo's own subject is not overclaiming about
guardrails:

- **The write gate is bar-raising, not airtight.** It inspects command strings, so `cd wiki/hardware && cp ../../x.md .` defeats it, and anything a *child process* writes — via `just`, `make`, a shell script — is invisible to it.
- **Unknown tools fail open** until the matcher is widened. A fail-closed path is implemented and tested but dormant; see `harness/kb/deny_wiki_write.py`.
- **The broker only sees what's routed through it.** A direct `Bash` call doesn't reach it. That is why the hook exists.
- **Simulation is not hardware.** Wokwi and friends diverge from real silicon.
- **Nothing here is legal or compliance advice.** The ANATEL and licensing material is direction, not a substitute for an accredited lab.

The durable guarantee is the wiki's pre-commit lint gate plus a human reading
the diff. Everything else is defence in depth above it.

## Evidence

`harness/smoke/` holds five behavioural tests, run against cold agents with no
memory of the session that wrote the skills, plus what each one found.
`REVIEW.md` is the original audit of the scaffold. `CHANGELOG.md` says what
changed and why.

## Provenance

Built with [Claude Code](https://claude.com/claude-code); the commit history
carries `Co-Authored-By` trailers throughout. The knowledge wiki it manages is a
separate, private repository by design — see
`skills/knowledge-base/references/legal-and-etiquette.md` for the reasoning.

## Licence

MIT — see [LICENSE](LICENSE).
