# Changelog

> **Working document.** Written to the repo's owner during the build, and kept
> in that voice. "You" refers to them; decisions attributed to "you" were
> theirs to make.

## Unreleased — reasoning lenses

### Added

- **Four reasoning lenses** under `skills/`: `problem-reframing`,
  `decision-framing`, `diagnostic-reasoning`, `model-vs-reality`. The five
  existing skills are domain knowledge — what is true about circuits, parts and
  fabs. Nothing owned the layer above: which budget a symptom implicates, what
  decides an A-or-B choice, which measurement to take first, how much a number
  can be trusted. That judgment existed in the repo already, scattered as
  imperatives across `AGENT.md` and `guardrails.md`, with no procedure to run
  and no trigger saying when. The lenses collect it.
- Each lens carries two sections the creative-technologist format doesn't have:
  **Lands in**, naming the deliverable shape its output must take, and **Tier
  note**, naming the tier of the actions it may suggest. Without those a lens
  is advice floating next to a harness rather than part of one.
- Four smoke prompts (6–9) covering the lenses, with failure criteria.
  **Not yet run cold** — they need fresh agent sessions, which no script
  produces.
- `docs/analysis-reasoning-skills.md`, the analysis the lenses were built from,
  including the eight candidates considered and why four were deferred.

### Changed

- `check_skill_routing.py` now scores a prompt against its own group. Domain
  skills route on nouns, lenses on verbs, and the two are *meant* to load
  together — ranking them against each other reported every intended co-load as
  a collision. 46 prompts now, up from 26.
- `AGENT.md` gains a second routing table for the lenses, a method line (frame,
  select at most two, run the checklist briefly, land in a deliverable shape), a
  branch-point rule capping mid-work A-or-B answers at 150 words, and an
  explicit handoff upstream to the creative-technologist agent for product-level
  questions.

### Notes

- Ownership, so the ~70% overlap `REVIEW.md` §3 found between `AGENT.md` and
  `guardrails.md` doesn't grow a third copy: guardrails hold stances, lenses
  hold procedures, `AGENT.md` holds routing.
- `model-vs-reality` deliberately reuses the `trust:` / `confidence:`
  vocabulary from `knowledge-base/references/trust-and-provenance.md` rather
  than inventing a parallel scale, so a claim in a design and a claim in the
  wiki mean the same thing.
- A colon inside one lens description broke its YAML frontmatter and would have
  stopped that skill loading entirely. `test_tiers.py` caught it, which is the
  test earning its keep — it was written after the same failure in Phase 2.

## Unreleased — closing the Bash gap in the write gate

### Fixed

- **`deny_wiki_write.py` matched only `Write|Edit|MultiEdit|NotebookEdit`**, so
  a shell command wrote straight into the canonical wiki. It now handles `Bash`
  too, splitting on shell operators and inspecting each segment. No escape
  hatch: the agent drafts, lints, shows the diff and prints the commands — you
  run them, which is what `AGENT.md` already says T3 means. The refusal hands
  the exact command over rather than being a dead end.
- **`raw/` is now append-only.** Creating a cached document is fine; overwriting
  or deleting one is blocked, because every `part` entry pins a `sha256` of the
  bytes it was written from.
- **A false positive my own tests caught:** `cp raw/cached.pdf scratch/copy.pdf`
  was blocked, because every argument was checked rather than distinguishing
  source from destination. Copying *out* of a protected tree is a read. The
  allow-list half of that test file matters more than the block half — a gate
  that blocks `rg wiki/` gets switched off within a day.

### Changed

- The hook now reads `kb-canonicalize` out of `policy/tool-tiers.yaml` instead
  of carrying its own copy of the pattern, which finally makes that rule
  load-bearing — `REVIEW.md` §5 complained it guarded a path the agent does not
  take. Restored the redirect clause Phase 1 dropped when anchoring patterns.

### Added

- `harness/tests/test_deny_hook.py` — 56 tests.
- `harness/kb/check_gate.py` and `just check-gate`.

### Correction

**Hook registrations load at session start.** A live canary in the session that
registered the Bash matcher *succeeded* — the file was created. The script's
logic is correct and tested; its wiring does not activate until a new session.

Earlier statements in this project that the hook "blocks me from writing to
`wiki/`" were based on piping payloads into the script by hand. That tests the
script, not the wiring, and it was presented with more confidence than the
evidence supported. `check_gate.py --live` prints the canary test that actually
settles it.

## Unreleased — Phase 4: smoke tests

Five cold agents, one per prompt, no memory of the session that wrote the
skills. **All five pass.** Full transcripts and verdicts in
`harness/smoke/RESULTS.md`; method in `harness/smoke/README.md`.

The corrections from Phases 2 and 3 propagated intact to agents that had never
seen this session — the "WS2812B datasheet has no current spec" finding, the
`rst:0xc`/`rst:0xf` discrepancy, the corrected 70 × 70 mm panelization rule, and
the unverified Nexar markings, which were respected rather than filled from
memory.

### Fixed — three defects the runs found

- **`lint.py` required a `url` on every source**, while
  `trust-and-provenance.md` has always said `confidence: high` is earned by
  "vendor-authoritative source, **or reproduced on the bench yourself**". A
  bench measurement has no URL, so the strongest evidence available was the one
  thing the schema could not record — it ended up in prose where
  `rg 'trust: high'` would never find it. Sources now carry `kind: document`
  (default, needs `url`) or `kind: bench` (needs `method` instead). `method` is
  required: a bench claim nobody can repeat is an anecdote, not evidence.
- **`related:` targets were never validated.** The seeded entry linked to
  `fm-ws2812-level-shift`, which does not exist. Now a warning — a link to
  nothing is a broken index in a wiki retrieved by grep — and a warning rather
  than an error because writing `related` ahead of the entry it names is a
  reasonable way to mark intended work. Dangling link removed from the template.
- **The secure-boot gap.** Flashing a bootloader built with secure boot enabled
  is irreversible on the next power-on, but its command text is identical to an
  ordinary flash, so the broker classified it T2. Fixed as agreed — **skill
  stance plus mandatory disclosure**, not a new T3 rule that would fire on every
  bring-up. `run_device_write` now refuses a bootloader flash whose
  `what_changes` does not state secure-boot and flash-encryption status, and
  `esp32-irreversible.md` documents that the flash is the gate, with the
  `grep -E "SECURE_BOOT|FLASH_ENC" sdkconfig` that tells you which case you are
  in.

### Added

- `harness/smoke/` — prompts, method, failure criteria and recorded verdicts.
- `harness/tests/test_device_write.py` — 13 tests pinning the disclosure
  requirement, including that it does *not* fire on ordinary app flashes (a
  guardrail that noisy gets routed around) and that disclosure never bypasses
  the tier rules.

## Unreleased — Phase 3: the wiki

The wiki now exists at `~/dev/wiki-hardware` as its own git repo, with a
working gate and one real ingested entry sitting in `scratch/` awaiting review.
**Nothing was canonicalised.** `wiki/parts/` still contains only `.gitkeep`.

### Fixed — `harness/kb/bootstrap.sh`

Eight defects in 49 lines, in a script that had never been run.

- **`git init`/`add`/`commit` ran before the hook was installed**, so the seeded
  entry — the template every later entry imitates — entered the wiki having
  never been linted. Gate installs first now; verified that the bootstrap
  commit itself goes through the linter.
- **The hook's lint path did not resolve.** Baked in as an absolute path at
  bootstrap time.
- **The hook failed open.** `if command -v python3` meant no python3 → exit 0 →
  the gate silently vanished. It now fails loudly, and distinguishes a missing
  linter (an installation problem) from failing entries (yours). Verified by
  pointing it at a nonexistent linter: commit blocked, cause named correctly.
- `git init -b main` rather than depending on global config; `wiki/parts/.gitkeep`
  added; the stale "edit the lint path" instruction removed.

### Added

- **`raw/` is gitignored, `raw/MANIFEST.tsv` is not.** Decision 3 kept
  copyrighted PDFs out of history; the manifest keeps the *record* of what was
  fetched — filename, URL, publisher, sha256, retrieval date — so a fresh clone
  can still say what was read and verify a re-fetch against the hash.
- **`harness/kb/deny_wiki_write.py`**, a `PreToolUse` hook registered
  user-scoped in `~/.claude/settings.json` (backed up first), refusing
  Write/Edit into the wiki tree. This closes the gap REVIEW §5 identified:
  `tool-tiers.yaml`'s `kb-canonicalize` rule only sees shell commands, and the
  agent writes files with the Write tool, which never reaches the broker.
  `scratch/` stays freely writable.
- **`harness/tests/test_lint.py`** — 19 tests driving `lint.py` as a subprocess,
  because the exit code is the contract the pre-commit hook gates on.

### Changed — what the real datasheet forced

The schema held. The **linter** did not: the draft passed cleanly while
carrying provenance the linter never checked for. Two rules now apply to
`trust: high` sources on `type: part` entries:

- **`revision` required (error).** A datasheet citation without one is an
  unscoped fact wearing a citation. v1.4 is a different document from v1.1.
- **`sha256` advised (warning).** It makes a silent vendor revision detectable
  via the manifest, but requiring it would block an entry drawn from a document
  read without caching — and a gate that blocks honest work is how a KB dies.

`entry-schema.md` now documents the part conventions, including the one the
ingest actually taught: **specs go in a body table with a Source column, and
the empty columns stay empty.** The datasheet gives `IOH` as *typical* with no
maximum, so "max current per GPIO is 40 mA" is not a claim it supports. A
schema that flattened that to `io_max_current_ma: 40` would have manufactured
a limit the vendor never stated.

### Ingested

`scratch/part-esp32-c6-wroom-1.md` — ESP32-C6-WROOM-1/1U, datasheet v1.4,
sha256 recorded. Carries the supply minimum (0.5 A, the spec people miss), RF
peak currents (382 mA Wi-Fi TX), GPIO drive with its conditions and footnotes,
and the `-1U` external-antenna gain ceiling of 2.33 dBi — which cross-links to
the ANATEL rule on what invalidates a homologation. It also records what was
*not* read: the ESP32-C6 SoC datasheet and TRM.

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
