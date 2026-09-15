"""Tests for the PreToolUse hook that gates writes into the wiki.

Driven as a subprocess with a JSON payload on stdin, because that is exactly
how Claude Code invokes it - exit 2 blocks, exit 0 allows. Asserting on the
exit code is the contract.

The allow-list half of this file matters more than the block half. A gate that
blocks `rg wiki/` gets switched off within a day, and then nothing is gated.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / "harness" / "kb" / "deny_wiki_write.py"

BLOCK, ALLOW = 2, 0


@pytest.fixture(scope="module")
def wiki(tmp_path_factory) -> Path:
    """A throwaway wiki tree, so tests never depend on the real one."""
    root = tmp_path_factory.mktemp("wiki-hardware")
    (root / "wiki" / "hardware").mkdir(parents=True)
    (root / "wiki" / "parts").mkdir(parents=True)
    (root / "scratch").mkdir()
    (root / "raw").mkdir()
    (root / "wiki" / "hardware" / "fm-existing.md").write_text("---\nid: x\n---\n")
    (root / "raw" / "cached.pdf").write_bytes(b"%PDF-1.4 cached")
    (root / "scratch" / "draft.md").write_text("draft\n")
    return root


def run_hook(payload: dict, wiki: Path) -> subprocess.CompletedProcess:
    import os

    env = {**os.environ, "HARDWARE_AGENT_WIKI": str(wiki)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def bash(command: str, wiki: Path) -> subprocess.CompletedProcess:
    return run_hook(
        {"tool_name": "Bash", "cwd": str(wiki), "tool_input": {"command": command}}, wiki
    )


# ----------------------------------------------------------------- must block

BLOCKED = [
    "cp scratch/draft.md wiki/hardware/fm-new.md",
    "mv scratch/draft.md wiki/hardware/fm-new.md",
    "git mv scratch/draft.md wiki/hardware/fm-new.md",
    "git add wiki/",
    "git rm wiki/hardware/fm-existing.md",
    "rm wiki/hardware/fm-existing.md",
    "rm -rf wiki/",
    "tee wiki/hardware/fm-new.md",
    "echo hello > wiki/hardware/fm-new.md",
    "echo hello >> wiki/INDEX.md",
    "sed -i '' 's/a/b/' wiki/INDEX.md",
    "rsync -a scratch/ wiki/hardware/",
    "install -m644 scratch/draft.md wiki/hardware/x.md",
    "touch wiki/hardware/fm-new.md",
    "truncate -s 0 wiki/INDEX.md",
    "python3 -c \"open('wiki/hardware/x.md','w').write('hi')\"",
    "sh -c 'cp scratch/draft.md wiki/hardware/x.md'",
    "curl -o wiki/hardware/x.md https://example.com/x",
    "cd /tmp && cp /tmp/a.md wiki/hardware/x.md",
    "lint.py wiki/ ; cp scratch/draft.md wiki/hardware/x.md",
    "cp scratch/draft.md wiki/hardware/x.md && echo done",
]


@pytest.mark.parametrize("command", BLOCKED, ids=BLOCKED)
def test_writes_into_wiki_are_blocked(command: str, wiki: Path) -> None:
    r = bash(command, wiki)
    assert r.returncode == BLOCK, f"NOT blocked: {command}\n{r.stderr}"
    assert "BLOCKED" in r.stderr


def test_block_message_hands_the_command_over(wiki: Path) -> None:
    """A refusal should be the T3 handover shape, not a dead end."""
    cmd = "git mv scratch/draft.md wiki/hardware/fm-new.md"
    r = bash(cmd, wiki)
    assert cmd in r.stderr
    assert "owner's to run" in r.stderr


# ----------------------------------------------------------------- must allow

ALLOWED = [
    "rg -il brownout wiki/",
    "rg -n 'rst:0xc' wiki/",
    "grep -r brownout wiki/",
    "cat wiki/INDEX.md",
    "head -20 wiki/hardware/fm-existing.md",
    "find wiki -type f",
    "ls -la wiki/parts/",
    "wc -l wiki/INDEX.md",
    "git diff wiki/",
    "git log --oneline wiki/",
    "git status --short",
    "git show HEAD:wiki/INDEX.md",
    "python3 harness/kb/lint.py wiki/",
    "python3 harness/kb/lint.py wiki/ --stale 180",
    "diff -u wiki/hardware/fm-existing.md scratch/draft.md",
    "cp raw/cached.pdf /tmp/copy.pdf",
    "rg brownout wiki/ | head -5",
    "cat wiki/INDEX.md > /tmp/index-copy.md",
]


@pytest.mark.parametrize("command", ALLOWED, ids=ALLOWED)
def test_reads_and_unrelated_writes_are_allowed(command: str, wiki: Path) -> None:
    r = bash(command, wiki)
    assert r.returncode == ALLOW, f"WRONGLY blocked: {command}\n{r.stderr}"


SCRATCH_WRITES = [
    "cp raw/cached.pdf scratch/copy.pdf",
    "echo draft > scratch/new.md",
    "tee scratch/new.md",
    "sed -i '' 's/a/b/' scratch/draft.md",
    "rm scratch/draft.md",
    "git mv scratch/a.md scratch/b.md",
]


@pytest.mark.parametrize("command", SCRATCH_WRITES, ids=SCRATCH_WRITES)
def test_scratch_is_freely_writable(command: str, wiki: Path) -> None:
    r = bash(command, wiki)
    assert r.returncode == ALLOW, f"scratch/ must stay free: {command}\n{r.stderr}"


# ------------------------------------------------------------ raw/ append-only


def test_overwriting_an_existing_cached_document_is_blocked(wiki: Path) -> None:
    r = bash("cp /tmp/new.pdf raw/cached.pdf", wiki)
    assert r.returncode == BLOCK, r.stderr
    assert "append-only" in r.stderr
    assert "sha256" in r.stderr


def test_deleting_a_cached_document_is_blocked(wiki: Path) -> None:
    assert bash("rm raw/cached.pdf", wiki).returncode == BLOCK


@pytest.mark.parametrize(
    "command",
    [
        "curl -o raw/brand-new.pdf https://example.com/ds.pdf",
        "cp /tmp/x.pdf raw/brand-new.pdf",
        "wget -O raw/another-new.pdf https://example.com/y.pdf",
    ],
)
def test_creating_a_new_cached_document_is_allowed(command: str, wiki: Path) -> None:
    """Ingest must keep working - blocking new fetches breaks the pipeline."""
    r = bash(command, wiki)
    assert r.returncode == ALLOW, f"ingest broken: {command}\n{r.stderr}"


# ------------------------------------------------------- path-tool half intact


def test_write_tool_into_wiki_still_blocked(wiki: Path) -> None:
    r = run_hook(
        {"tool_name": "Write", "cwd": str(wiki),
         "tool_input": {"file_path": str(wiki / "wiki" / "parts" / "p.md")}},
        wiki,
    )
    assert r.returncode == BLOCK


def test_write_tool_into_scratch_still_allowed(wiki: Path) -> None:
    r = run_hook(
        {"tool_name": "Write", "cwd": str(wiki),
         "tool_input": {"file_path": str(wiki / "scratch" / "p.md")}},
        wiki,
    )
    assert r.returncode == ALLOW


def test_read_tool_is_never_blocked(wiki: Path) -> None:
    r = run_hook(
        {"tool_name": "Read", "cwd": str(wiki),
         "tool_input": {"file_path": str(wiki / "wiki" / "INDEX.md")}},
        wiki,
    )
    assert r.returncode == ALLOW


def test_unreadable_payload_does_not_block(wiki: Path) -> None:
    import os

    env = {**os.environ, "HARDWARE_AGENT_WIKI": str(wiki)}
    r = subprocess.run(
        [sys.executable, str(HOOK)], input="not json", capture_output=True,
        text=True, env=env,
    )
    assert r.returncode == ALLOW


def test_other_projects_wiki_directories_are_not_blocked(tmp_path, wiki: Path) -> None:
    """Over-blocking is how a guardrail gets switched off. An unrelated
    project with a wiki/ folder must be untouched."""
    other = tmp_path / "some-other-project"
    (other / "wiki").mkdir(parents=True)
    r = run_hook(
        {"tool_name": "Bash", "cwd": str(other),
         "tool_input": {"command": "cp notes.md wiki/notes.md"}},
        wiki,
    )
    assert r.returncode == ALLOW, r.stderr


# ------------------------------------------- unknown tools fail closed

def test_unknown_write_capable_tool_is_blocked(wiki: Path) -> None:
    """A tool-name matcher fails open. Anything not known to be a reader gets
    its inputs checked, so a future MCP write tool is covered by default."""
    r = run_hook(
        {"tool_name": "mcp__somedrive__create_file", "cwd": str(wiki),
         "tool_input": {"path": str(wiki / "wiki" / "parts" / "p.md"),
                        "content": "x"}},
        wiki,
    )
    assert r.returncode == BLOCK, r.stderr


def test_unknown_tool_with_nested_path_is_blocked(wiki: Path) -> None:
    r = run_hook(
        {"tool_name": "mcp__x__batch", "cwd": str(wiki),
         "tool_input": {"ops": [{"dest": str(wiki / "wiki" / "INDEX.md")}]}},
        wiki,
    )
    assert r.returncode == BLOCK, r.stderr


@pytest.mark.parametrize("tool", ["Read", "Grep", "Glob", "WebFetch", "Task"])
def test_known_read_tools_are_never_blocked(tool: str, wiki: Path) -> None:
    r = run_hook(
        {"tool_name": tool, "cwd": str(wiki),
         "tool_input": {"file_path": str(wiki / "wiki" / "INDEX.md")}},
        wiki,
    )
    assert r.returncode == ALLOW, f"{tool} must stay free\n{r.stderr}"


def test_unknown_tool_untouching_the_wiki_is_allowed(wiki: Path) -> None:
    r = run_hook(
        {"tool_name": "mcp__somedrive__create_file", "cwd": str(wiki),
         "tool_input": {"path": "/tmp/unrelated.md", "content": "x"}},
        wiki,
    )
    assert r.returncode == ALLOW, r.stderr
