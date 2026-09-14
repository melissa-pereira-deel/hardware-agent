# Changelog

## Unreleased — Phase 2: skills

Every factual claim in the skills now carries a source URL and the date it was
checked, or is explicitly marked unverified.

### Corrected, with sources

- **WS2812B drive current has no datasheet basis.** Verified by extracting the
  datasheet directly: it contains zero occurrences of "mA". The 60 mA/LED
  figure the entire current budget rests on is an inference from the
  WS2811-family ~18.5 mA/channel design; bench tests measure ~50 mA. Kept 60 mA
  as the sizing figure — it is the safe end — but relabelled as an assumption
  to measure rather than a vendor fact. V_IH = 0.7 × VDD *is* datasheet-backed
  and is now cited as such.
- **JLCPCB 1–2 layer trace/space** is 4/4 mil (0.10 mm), not 5 mil.
- **JLCPCB annular ring.** The flat "0.15 mm" previously asserted matches
  neither published figure (PTH ≥0.20 mm, NPTH ≥0.45 mm, vs a 0.15 mm via in a
  0.25 mm pad). Wrong in the direction that makes a non-compliant board look
  compliant. The ambiguity between hole classes is now flagged rather than
  resolved from memory.
- **The 70 × 70 mm panelization rule was stated backwards.** It is a *minimum*
  board size and applies only to Standard PCBA; Economic PCBA accepts 10 × 10
  mm. For small-batch work this often means no panelization at all.
- **`idf.py secure-boot-enable` does not exist.** Replaced with the real flow,
  including the safety-relevant detail the file omitted: `ABS_DONE_1` is burned
  by the bootloader on *first boot*, so the point of no return is a power-on,
  not a command you can decline to run.
- **Flash offsets are part-family specific** (0x1000 on ESP32/S2, 0x0 on
  C3/C6/H2/S3). The old `write_flash 0x0` example produced a non-booting ESP32
  classic.
- **esptool v5** deprecated the `.py` suffixes and moved to hyphenated
  subcommands.
- **PLA**: design against heat-deflection temperature (~53 °C), not glass
  transition (60–65 °C). HDT is lower and is where a loaded part creeps.
- **ANATEL**: cited Resolução 715/2019 and the actual applicant documentation
  requirement.
- **Nexar API limits could not be verified** and are now marked unverified with
  an explicit instruction not to quote them.
- **The seeded wiki entry cited a `trust: high` source for a claim it does not
  make** (ESP32 errata, "chip revision identification", for a brownout
  failure). Dropped to `confidence: medium`, re-sourced to Espressif's own
  issue tracker, and the body now explains the mis-citation as the worked
  example of why a linter cannot catch this. Added the missing `rst:0xf`
  symptom — an incomplete symptom list is invisible to grep, which is the
  entire retrieval strategy.

### Changed

- **Merged `research-and-ingest` into `knowledge-base`** (decision 1). Six
  skills become five. They were one pipeline split at exactly the seam where
  provenance got dropped.
- **Fetch tooling** now defaults to `httpx`/`trafilatura`/`pymupdf` for the
  static vendor PDFs that are the real workload, with Firecrawl's hosted MCP as
  the escape hatch (decision 4). No self-hosted crawler.
- **Added `skills/sourcing-bom/references/lcsc-jlcpcb-parts.md`**, shared by
  `sourcing-bom` and `manufacturing-dfm`, so the basic/extended overlap lives
  in one file rather than drifting in two. Documents the $3-per-unique-extended
  -part feeder fee and the Preferred Extended class that waives it on Economic.
- **`entry-schema.md` no longer inlines a copy of the worked example.** The
  copy had already drifted from the real entry. It now points at the file.
- Skill descriptions rewritten for triggering (below).

### Added

- `harness/check_skill_routing.py` and `just check-routing`. Scores realistic
  prompts against each skill's YAML description. A proxy for the real matcher,
  but it catches the failure that actually happens: a description missing the
  vocabulary a prompt uses. It found four misses, two of them among your five
  smoke tests, and one a regression the merge had just introduced.
- A test asserting every `SKILL.md` frontmatter parses and its `name` matches
  its directory. Added after an unquoted `": "` inside a description broke the
  YAML of three skills at once — which would have stopped them loading
  entirely.

### Known and deliberate

- Efficacy figures (30–40 lm/W addressable vs 120–160 lm/W for 2835) are
  `trust: medium`: corroborated across industry sources, but no manufacturer
  publishes a lm/W figure for the WS2812B. The mechanism is sound; the exact
  numbers are not vendor-backed and are labelled that way.
- `AGENT.md` and `policy/guardrails.md` still overlap substantially on the
  safety stances. `REVIEW.md` §3 called this over-built; on reflection,
  duplicated safety content is defensible redundancy and removing it was not
  among the decisions you signed off. Left alone.

## Unreleased — Phase 1: repo setup and harness correctness

Phase 0 produced `REVIEW.md`. This is the work that followed from it. Skills
(Phase 2), wiki bootstrap (Phase 3) and smoke tests (Phase 4) are not yet done.

### Fixed

- **Closed a shell-injection hole in the risk broker that defeated both
  advertised layers of defence.** `tiers.py::_binary` classified only the first
  shlex token while `server.py::_execute` ran the entire string under
  `shell=True`. `kicad-cli sch erc b.kicad_sch; rm -rf ~/Documents` classified
  as T1 with an allowed binary and would have executed. Verified against the
  original code: 5 of 6 representative injections classified T1-and-runnable,
  and the sixth was reachable through `run_device_write`.

  The fix is structural, not a pattern blocklist. Commands are now parsed to an
  argv list, shell metacharacters are refused before any tiering happens, and
  execution is `shell=False`. One call is exactly one command.

- **Migrated the server to MCP Python SDK v2.** SDK 2.0.0 removed
  `mcp.server.fastmcp` and renamed `FastMCP` to `MCPServer`, so `server.py`
  could not import against any current install. Dependencies are now pinned
  (`mcp[cli]>=2.2,<3`); the unpinned `pip install` in the old README was the
  root cause. Tools now also carry read-only/destructive annotations.

- **Made the broker survive its own failure modes.** `subprocess.TimeoutExpired`
  was uncaught and would raise through the tool call; `FileNotFoundError` on a
  missing binary did the same. Both now return a structured result. An
  unwritable audit log reports itself instead of failing a legitimate build.

- **Tightened every rule in `policy/tool-tiers.yaml`.** Patterns now match
  against normalized argv and anchor at `^` where they identify a binary —
  only safe now that one call is guaranteed to be one command. Previously
  `grep` matched anywhere in a pipeline, and `lint\.py` matched *any* path
  ending in `lint.py`, which made `python3 /tmp/lint.py` a T1 arbitrary-code
  -execution path. Rule names and count are unchanged (18) so the policy stays
  diffable against the original.

  Every change narrows rather than widens. That is safe here specifically
  because `default_tier` is 3: anything that stops matching falls through to
  refusal.

### Added

- `pyproject.toml` with pinned dependencies and `uv.lock`; `risk_broker`
  installs as an editable package so `python -m risk_broker.server` resolves
  from anywhere while the repo-relative policy path still points at the tree.
- `justfile` with `setup`, `test`, `lint`, `verify-broker`, `bootstrap-wiki`
  and `check`. `setup` uses `uv` when present and falls back to venv + pip.
- `harness/tests/` — 73 tests. `test_tiers.py` is table-driven over every rule
  in the policy, and `test_every_rule_is_covered` fails the build if a rule has
  no case, which is the gap that let the injection hole survive. Includes an
  explicit regression test for the injection, and coverage of fail-closed
  behaviour and the binary allowlist.
- `harness/tests/test_server_integration.py` — spawns the server and speaks
  real MCP over stdio. An SDK API break now fails the suite rather than being
  discovered in use.
- `harness/verify_broker.py` — standalone handshake check; prints the
  registered tools and probes every tier boundary.
- `.mcp.json` — project-scoped registration, verified against the actual
  interpreter path it specifies.
- `RISK_BROKER_POLICY` environment override, so tests can load an alternate
  policy without mutating the real one.
- `.gitignore`.

### Changed

- Repo moved from `~/Downloads/hardware agent/hardware-agent/` to
  `~/dev/hardware-agent` and initialised as a git repo. The first commit is the
  scaffold exactly as received, so every subsequent change is diffable against
  it.
- `harness/risk_broker/README.md` rewritten: the install command it documented
  produced an unimportable server, and its claim that the binary allowlist was
  "what stops `rm -rf /`" was false.

### Removed

- `CLAUDE-CODE-PROMPT.md` from the repo. An identical copy remains outside the
  tree, and it is recoverable from the initial commit.

### Known and deliberate

- `esptool.py read_flash` classifies T3 (`unmatched`) rather than T1/T2. It is a
  read, so this is a false positive, but fixing it means *adding* a rule that
  permits a device connection — a widening, and therefore your call rather than
  mine. Raised for Phase 2.
- `python` and `python3` remain on the binary allowlist. They are inherently
  broad; the constraint is the tier rules, which now only admit the repo's own
  linter by path.
- `recent_actions` is still registered. `REVIEW.md` §3 argues it duplicates
  `tail` and should be cut, but that was not among the five decisions you
  signed off, so it stays until you say otherwise.
