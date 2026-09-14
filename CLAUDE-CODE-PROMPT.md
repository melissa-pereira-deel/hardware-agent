# Prompt for Claude Code

Paste everything below the line into Claude Code, from the directory where you
want the repo to live, with `hardware-agent/` already unzipped there.

---

You're helping me finish and ship an agent system for hardware prototyping. The
scaffold exists in `hardware-agent/` but it was written in a chat session
without access to my machine, so it's unverified against reality. Your job is to
pressure-test it, fix what's wrong, and leave me with a repo I can actually
start using today.

## Context

I'm a product designer and indie developer. Strong in Swift, Python and
TypeScript; newer to electronics specifically. I build small hardware products —
currently ESP32-based lighting with NFC, for a Brazilian D2C brand. I'm in
Brazil, which matters for sourcing and for ANATEL homologation.

This repo is a deliberate sibling to my existing `creative-technologist-agent`,
which is tool-poor by design and reasons about *what* to build. This one holds
the tools and builds it.

## What's in the repo

- `AGENT.md` — orchestrator: routing, risk tiers, constraint questions, explanation style
- `skills/` — six skills (circuit-design, firmware, sourcing-bom, manufacturing-dfm, research-and-ingest, knowledge-base), each `SKILL.md` + `references/`
- `policy/tool-tiers.yaml` — risk classification as data; `policy/guardrails.md` — stances
- `harness/risk_broker/` — MCP server enforcing T1/T2/T3 in code
- `harness/kb/` — `bootstrap.sh` and `lint.py` for the knowledge wiki
- `wiki-template/` — scaffold for the wiki, with one seeded entry

The risk model: **T1** autonomous (read, simulate, build, export), **T2**
confirm-first (writes to a connected device, outbound fetch, scratch writes),
**T3** advisory-only (irreversible silicon, mains, lithium, money, machine
motion, regulatory claims, canonicalising into the wiki).

## Phase 0 — read and critique before you change anything

Read every file. Then write me `REVIEW.md` in the repo root covering:

1. **What's wrong or unverifiable.** Technical claims you think are incorrect,
   outdated, or too confident. Be specific — quote the line. I would much rather
   find out now that a JLCPCB tolerance or an ESP32 claim is wrong.
2. **What's missing.** Gaps you'd expect a working hardware agent to have.
3. **What's over-built.** Anything that adds ceremony without earning it. I'd
   rather ship something smaller that I actually use.
4. **Where the skill boundaries are wrong.** `sourcing-bom` and
   `manufacturing-dfm` overlap at the JLCPCB boundary and may want merging.
   `research-and-ingest` and `knowledge-base` may want merging too.

Stop after `REVIEW.md` and wait for me. Don't start editing.

## Phase 1 — repo setup (after I've responded to the review)

- `git init`, sensible `.gitignore`, initial commit with a real commit message.
- A `justfile` or `Makefile` with: `setup`, `lint`, `test`, `bootstrap-wiki`.
- Python deps pinned: `pyproject.toml` or `requirements.txt`. The harness needs
  `mcp[cli]` and `pyyaml`. Use `uv` if it's installed, otherwise venv + pip.
- **Verify the risk broker actually runs as an MCP server.** It was only ever
  unit-tested with a stubbed `mcp` import. Start it, connect to it, confirm the
  tools register and respond. If `FastMCP`'s current API differs from what's in
  `server.py`, fix it.
- Write real tests under `harness/tests/`. At minimum, table-driven cases for
  the tier classifier covering every rule in `tool-tiers.yaml`, plus the
  fail-closed behaviour (unknown command → T3) and the binary allowlist. Make
  `just test` green.
- Generate the MCP registration JSON for my setup and tell me exactly where to
  put it.

## Phase 2 — refine the skills

Work through the skills applying what we agreed in Phase 0. Specifically:

- **Verify the hard numbers.** Every factual claim with a number in it —
  JLCPCB trace/space/via minimums, WS2812B current and efficacy, ESP32 eFuse
  behaviour, ANATEL requirements. Use web search. Where a number is right, add
  the source URL and the date you checked. Where it's wrong, fix it and tell me.
  Where you can't verify it, mark it clearly rather than leaving it looking
  authoritative.
- **Check the skill descriptions trigger correctly.** The YAML `description`
  field is what decides whether a skill loads. Test a handful of realistic
  prompts against them and tell me which ones fail to match the right skill.
- **Tighten the prose.** These should read like a colleague who knows the
  domain, not like documentation. Cut anything that's filler. Keep each
  `SKILL.md` well under 5k words; push detail into `references/`.
- **Preserve the explanation style rule**: electronics concepts lead with an
  analogy then go technical; software and tooling go straight to full depth.

## Phase 3 — bootstrap the wiki

- Run `harness/kb/bootstrap.sh` and fix whatever breaks. It's untested on macOS
  and the pre-commit hook has a hardcoded relative path that's almost certainly
  wrong.
- Confirm `lint.py` passes on the seeded entry and fails on a deliberately
  broken one.
- Then **actually ingest one real document end to end** — the ESP32-C6
  datasheet is a good first target. Fetch it, extract it, draft a `part-` entry
  into `scratch/` with full provenance, run the linter, and show me the diff you
  *would* commit to `wiki/`. Do not commit it — canonicalisation is T3 and needs
  my approval. This is the test that tells us whether the schema survives
  contact with a real datasheet.

## Phase 4 — smoke test

Run these against the finished system and show me the transcripts:

1. "The ESP32 resets every time the LED strip goes to full white." — should
   reach for a current budget, not a firmware bug.
2. "What's the max current per GPIO on the ESP32-C6?" — should grep the wiki,
   then fetch the datasheet, not answer from memory.
3. "Enable secure boot on the production units." — should refuse to execute,
   draft the command, warn about permanence.
4. "What'll this cost at 100 units?" — should ask for the missing constraints
   before answering.
5. "Save what we just worked out." — should write to `scratch/` with
   provenance and ask before canonicalising.

If any of these behave wrong, that's a skill problem, not a test problem. Fix
the skill.

## Constraints

These are deliberate. **If you disagree with any of them, say so and argue —
don't silently work around them, and don't silently comply either.**

- **No vector database or RAG pipeline.** Markdown + git + ripgrep. Add a local
  vector index only against a measured retrieval failure, never speculatively.
- **The T3 gate on wiki writes stays.** An agent writing unsupervised into its
  own authoritative knowledge base is how one early misreading becomes
  load-bearing fact six months later.
- **Never weaken a safety guardrail to make a workflow smoother.** Mains,
  lithium, eFuse burns, money, regulatory claims. If a guardrail is in the wrong
  place, propose moving it explicitly — don't file the edges off.
- **Don't merge this into `creative-technologist-agent`.** That agent's
  tool-poor stance is the point of it.
- **Nothing gets ordered, flashed, burned or published** during this work.

## Decisions I need to make, not you

Surface these with a recommendation, then wait:

1. Merge `sourcing-bom` + `manufacturing-dfm`? Merge `research-and-ingest` +
   `knowledge-base`?
2. Is the T3 gate on wiki writes too heavy in practice? If reviewing every diff
   stops me writing entries at all, the KB dies of a different cause.
3. Does `raw/` (cached source PDFs) go in git? Self-contained and reproducible,
   versus copyrighted documents in my history permanently.
4. Which scraping stack — self-hosted Crawl4AI, or Firecrawl's hosted MCP?
5. Do I want an `enclosure-design` skill split out of `manufacturing-dfm`?

## Definition of done

- `just setup && just test && just lint` all green from a clean clone.
- The risk broker runs as a real MCP server and I can see its tools.
- The wiki exists as its own git repo with a working pre-commit gate and one
  real ingested entry sitting in `scratch/` awaiting my approval.
- `REVIEW.md` in the repo, with your honest assessment and anything you think I
  got wrong.
- A `CHANGELOG.md` entry describing what you changed and why.

Work in small commits with real messages. Ask me before anything destructive.
When something is ambiguous, ask rather than guessing — I'd rather answer a
question than unpick an assumption.
