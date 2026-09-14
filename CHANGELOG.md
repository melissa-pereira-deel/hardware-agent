# Changelog

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
