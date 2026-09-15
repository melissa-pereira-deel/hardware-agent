#!/usr/bin/env python3
"""PreToolUse hook: refuse agent writes into the canonical wiki tree.

Why this exists
---------------
policy/tool-tiers.yaml has a `kb-canonicalize` rule, but it only ever sees
commands routed through the risk broker. An agent in Claude Code writes files
with Write/Edit, and runs shell commands with Bash - neither reaches the
broker. So the T3 gate on canonicalisation guarded a path the agent does not
take.

This covers both. `scratch/` stays freely writable; drafting is cheap and is
meant to be. `wiki/` is not writable by any tool. `raw/` is append-only -
creating a cached document is fine, overwriting one silently breaks the sha256
chain that every part entry depends on.

What this does NOT do
---------------------
It raises the bar against accident and habit. **It does not stop a determined
bypass.** `cd wiki/hardware && cp ../../scratch/x.md .` defeats path matching
outright; so does assembling a path in a shell variable, or a base64'd
heredoc.

**Script indirection defeats it completely, and this is the likely accidental
case.** The hook sees the command string only. `just something`, `make merge`,
`./deploy.sh` and `python3 build.py` are opaque - whatever they write happens in
a child process the hook never inspects. Any recipe or script that writes into
`wiki/` bypasses this gate without anyone intending it. That is also why the
activation canary below must be a bare `touch` typed directly: wrapping it in a
`just` target would make it pass whether or not the hook is live. Command-string inspection cannot be made airtight and this file will
not pretend otherwise - the broker README once claimed its allowlist was "what
stops rm -rf /" and that claim is why REVIEW.md section 1.1 exists.

The durable guarantee is the wiki's pre-commit lint gate plus a human reading
the diff. This is defence in depth above that, not a replacement for it.

Activation
----------
Claude Code reads hook registrations from settings.json **at session start**.
A registration added mid-session does not take effect until a new session -
verified the hard way on 2026-09-14, when a `touch` into wiki/ succeeded in the
session that had just registered the Bash matcher.

**Confirmed working in a fresh session, 2026-09-14**, on four of the five
registered surfaces. Each was a direct tool call against a throwaway target in
wiki/hardware/, each refused at PreToolUse before the tool ran, each left the
target byte-identical:

    Bash          touch CANARY2.md      -> PreToolUse:Bash          blocked
    Write         create CANARY3.md     -> PreToolUse:Write         blocked
    Edit          modify CANARY4.md     -> PreToolUse:Edit          blocked
    NotebookEdit  edit cell CANARY5     -> PreToolUse:NotebookEdit  blocked
    MultiEdit     not run live - same matcher entry, payload verified
    Read          allowed throughout, as intended

Note what it took to get that evidence. The skill layer refuses wiki writes so
reliably that the hook is never reached in normal operation - the first attempt
at this test ended with the agent classifying through the risk broker and
declining, which is correct behaviour and tells you nothing about the hook. The
canary has to explicitly authorise the attempt, or layer 1 hides layer 2.

So `just check-gate` proves this script's logic; it does not prove the hook is
wired into the session you are in. `python3 harness/kb/check_gate.py --live`
prints the canary test that does.

On segmenting vs refusing
-------------------------
The risk broker *refuses* shell metacharacters rather than parsing them,
because there a parser bug means an exploit executes. This hook splits on them
and inspects each segment, because here a parser miss is a missed block, not an
execution. The asymmetry is deliberate: parse leniently when the failure mode
is under-blocking, refuse strictly when the failure mode is running something.

Exit 0 allows, exit 2 blocks and returns stderr to the model.
Set HARDWARE_AGENT_WIKI to override the wiki location.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

DEFAULT_WIKI = Path.home() / "dev" / "wiki-hardware"
PATH_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

# Tools known to read and not write. Everything NOT in this set and not handled
# above is treated as potentially write-capable and checked for protected paths.
#
# This matters because a tool-name matcher fails OPEN: any write-capable tool
# that did not exist when the matcher was written - a new MCP server, a plugin -
# is uncovered by default. That is the same shape as the bug this whole file
# exists to fix, so the default here is refusal, matching default_tier: 3 in
# policy/tool-tiers.yaml.
#
# Dormant unless the hook is registered with a matcher that actually sees those
# tools (e.g. "*"). With the current Write|Edit|...|Bash matcher it never runs.
READ_ONLY_TOOLS = {
    "Read", "Grep", "Glob", "LS", "NotebookRead", "WebFetch", "WebSearch",
    "TodoWrite", "Task", "Agent", "ListMcpResourcesTool", "ReadMcpResourceTool",
    "ExitPlanMode", "AskUserQuestion", "BashOutput", "KillShell",
}

# Shell operators that separate one command from the next.
SEGMENT_SPLIT = re.compile(r"\|\||&&|[;\n|&]")

# Commands whose LAST non-flag argument is the destination. Their earlier
# arguments are sources, and reading out of a protected tree is not a write -
# `cp raw/cached.pdf scratch/copy.pdf` must stay allowed.
DEST_LAST_VERBS = {"cp", "mv", "rsync", "install", "ln"}
# Commands where every non-flag argument is a target that gets destroyed or
# created in place.
ALL_ARGS_VERBS = {
    "rm", "tee", "truncate", "touch", "shred", "mkdir", "rmdir",
    "chmod", "chown", "unlink",
}
# `mv` also destroys its sources, so they are checked too.
CONSUMES_SOURCES = {"mv"}
# git subcommands that mutate the working tree or the index.
GIT_WRITE_SUBCOMMANDS = {
    "add", "commit", "mv", "rm", "apply", "checkout", "restore",
    "stash", "clean", "reset", "revert", "merge", "cherry-pick",
}
# Interpreters, but only dangerous when handed inline code. `python3 lint.py
# wiki/` is the linter doing its job; `python3 -c "open(...,'w')"` is not.
INTERPRETERS = {"python", "python3", "sh", "bash", "zsh", "perl", "ruby", "node"}
INLINE_CODE_FLAGS = {"-c", "-e", "--command", "--eval"}
FETCHERS = {"curl": {"-o", "--output"}, "wget": {"-O", "--output-document"}}

REDIRECT = re.compile(r">>?\s*([^\s;|&]+)")


def wiki_root() -> Path:
    # .resolve() matters. Target paths are resolved before comparison, so a
    # root left unresolved never matches when the path crosses a symlink -
    # on macOS /var -> /private/var is enough to make the gate fall open
    # silently. Found by CI, not by any local run.
    return Path(os.environ.get("HARDWARE_AGENT_WIKI", DEFAULT_WIKI)).expanduser().resolve()


def _resolve(token: str, cwd: str | None) -> Path | None:
    token = token.strip().strip("'\"")
    if not token or token.startswith("-"):
        return None
    try:
        p = Path(token).expanduser()
        if not p.is_absolute():
            if not cwd:
                return None
            p = Path(cwd) / p
        return p.resolve()
    except (OSError, ValueError, RuntimeError):
        return None


def _under(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def classify_target(token: str, cwd: str | None) -> str | None:
    """Return 'wiki', 'raw-existing', or None for a single path token."""
    root = wiki_root()
    p = _resolve(token, cwd)

    if p is not None:
        if _under(p, root / "wiki"):
            return "wiki"
        if _under(p, root / "raw") and p.exists():
            return "raw-existing"
        return None

    # Unresolvable (relative token with no cwd). Fall back to shape, but only
    # for the configured wiki - not for any directory that happens to be
    # called wiki/, which would block unrelated projects.
    if re.search(r"(^|/)wiki/", token) and str(root) in token:
        return "wiki"
    return None


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def inspect_segment(segment: str, cwd: str | None) -> tuple[str, str] | None:
    """Return (kind, token) if this segment writes to a protected path."""
    segment = segment.strip()
    if not segment:
        return None

    # Redirects: echo x > wiki/y.md
    for m in REDIRECT.finditer(segment):
        kind = classify_target(m.group(1), cwd)
        if kind:
            return kind, m.group(1)

    tokens = _tokens(segment)
    if not tokens:
        return None

    idx = 0
    while idx < len(tokens) and "=" in tokens[idx] and not tokens[idx].startswith("-"):
        idx += 1  # skip VAR=value prefixes
    if idx >= len(tokens):
        return None

    binary = Path(tokens[idx]).name
    args = tokens[idx + 1:]

    def first_protected(candidates) -> tuple[str, str] | None:
        for tok in candidates:
            kind = classify_target(tok, cwd)
            if kind:
                return kind, tok
        return None

    if binary in DEST_LAST_VERBS:
        positional = [a for a in args if not a.startswith("-")]
        if not positional:
            return None
        # Destination first; then, for mv, the sources it removes.
        hit = first_protected(positional[-1:])
        if hit:
            return hit
        if binary in CONSUMES_SOURCES:
            return first_protected(positional[:-1])
        return None

    if binary in ALL_ARGS_VERBS:
        return first_protected([a for a in args if not a.startswith("-")])

    if binary == "dd":
        return first_protected(
            [a.split("=", 1)[1] for a in args if a.startswith("of=")]
        )

    if binary == "sed" and any(a.startswith("-i") for a in args):
        return first_protected(args)

    if binary == "git":
        sub = next((a for a in args if not a.startswith("-")), None)
        if sub in GIT_WRITE_SUBCOMMANDS:
            return first_protected(args)
        return None

    if binary in FETCHERS:
        flags = FETCHERS[binary]
        for i, a in enumerate(args):
            if a in flags and i + 1 < len(args):
                kind = classify_target(args[i + 1], cwd)
                if kind:
                    return kind, args[i + 1]
        return None

    if binary in INTERPRETERS and any(a in INLINE_CODE_FLAGS for a in args):
        return first_protected(args) or first_protected(re.findall(r"[\w./~-]+", segment))

    return None


def inspect_command(command: str, cwd: str | None) -> tuple[str, str, str] | None:
    """Return (kind, token, segment) for the first offending segment."""
    for segment in SEGMENT_SPLIT.split(command):
        hit = inspect_segment(segment, cwd)
        if hit:
            return hit[0], hit[1], segment.strip()
    return None


def _refuse_wiki(target: str, command: str | None) -> None:
    root = wiki_root()
    msg = [
        f"BLOCKED: write into the canonical wiki -> {target}",
        "",
        "Canonicalisation is T3. A wrong entry there propagates silently and "
        "later sessions cite it as ground truth, so no tool performs it - "
        "including the shell.",
        "",
        f"Draft to {root}/scratch/ instead, with full provenance, lint it, and "
        "show the diff.",
    ]
    if command:
        msg += [
            "",
            "If this has been reviewed and approved, it is the repo owner's "
            "to run, not yours. Hand it over:",
            "",
            f"    {command}",
        ]
    else:
        # No shell command to hand over, but the model still needs to know what
        # the approved route IS, not only what is forbidden.
        msg += [
            "",
            "There is no command to hand over on this path. The route is: write "
            "the same content to scratch/ under the entry's id, lint it, show "
            "the owner the diff, and let them move it across. Promotion is theirs.",
        ]
    print("\n".join(msg), file=sys.stderr)


def _refuse_raw(target: str) -> None:
    print(
        f"BLOCKED: overwrite of a cached source document -> {target}\n\n"
        "raw/ is append-only. Every part entry pins a sha256 of the bytes it "
        "was written from; replacing a cached document breaks that chain "
        "silently, and the entry keeps asserting a hash that no longer "
        "describes what is on disk.\n\n"
        "Fetch to a new filename and add a row to raw/MANIFEST.tsv. If a "
        "vendor genuinely revised the document, that is a new revision and a "
        "new entry, not an edit to the old one.",
        file=sys.stderr,
    )


def _walk_strings(node, depth: int = 0):
    """Every string value in a nested tool input, for unknown-tool inspection."""
    if depth > 6:
        return
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _walk_strings(v, depth + 1)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _walk_strings(v, depth + 1)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never block on a payload we cannot read

    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd")

    if tool in PATH_TOOLS:
        for key in ("file_path", "notebook_path", "path"):
            value = tool_input.get(key)
            if not value:
                continue
            kind = classify_target(str(value), cwd)
            if kind == "wiki":
                _refuse_wiki(str(value), None)
                return 2
            if kind == "raw-existing":
                _refuse_raw(str(value))
                return 2
        return 0

    if tool == "Bash":
        command = tool_input.get("command") or ""
        hit = inspect_command(command, cwd)
        if hit:
            kind, token, segment = hit
            if kind == "wiki":
                _refuse_wiki(token, segment)
            else:
                _refuse_raw(token)
            return 2
        return 0

    if tool in READ_ONLY_TOOLS:
        return 0

    # Unknown tool. Fail closed: if a protected path appears anywhere in its
    # input, refuse rather than assume it is a reader.
    for value in _walk_strings(tool_input):
        kind = classify_target(value, cwd)
        if kind == "wiki":
            _refuse_wiki(value, None)
            return 2
        if kind == "raw-existing":
            _refuse_raw(value)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
