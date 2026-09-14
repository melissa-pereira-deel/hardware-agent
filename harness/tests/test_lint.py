"""Tests for harness/kb/lint.py.

Run as a subprocess rather than by import, because the exit code is the whole
contract: the wiki's pre-commit hook gates on it, and an assertion about a
return value would not catch a linter that reported errors and still exited 0.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LINT = REPO / "harness" / "kb" / "lint.py"
SEEDED = REPO / "wiki-template" / "wiki"

GOOD_FAILURE_MODE = """\
---
id: fm-test-good
type: failure_mode
title: A well-formed failure mode
applies_to:
  part: ESP32-C6-WROOM-1
  silicon_revision: "all"
symptom:
  - "some verbatim string"
severity: 4
occurrence: 3
detection: 2
rpn: 24
confidence: medium
sources:
  - title: "Vendor datasheet"
    publisher: Espressif
    url: https://example.com/ds.pdf
    retrieved: 2026-09-14
    trust: high
updated: 2026-09-14
---
Body.
"""

GOOD_PART = """\
---
id: part-test-good
type: part
title: A well-formed part entry
applies_to:
  part: ESP32-C6-WROOM-1
  revision: "v1.3"
confidence: high
sources:
  - title: "ESP32-C6-WROOM-1 Datasheet"
    publisher: Espressif
    url: https://example.com/ds.pdf
    revision: "v1.3"
    section: "Section 4, Table 6"
    retrieved: 2026-09-14
    sha256: "0000000000000000000000000000000000000000000000000000000000000000"
    trust: high
updated: 2026-09-14
---
Body.
"""


def run_lint(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), str(root)],
        capture_output=True, text=True,
    )


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ------------------------------------------------------------------ passes


def test_seeded_entry_passes() -> None:
    """The entry bootstrap.sh installs must pass the gate it installs."""
    r = run_lint(SEEDED)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 errors" in r.stdout


def test_well_formed_failure_mode_passes(tmp_path: Path) -> None:
    write(tmp_path, "fm-test-good.md", GOOD_FAILURE_MODE)
    r = run_lint(tmp_path)
    assert r.returncode == 0, r.stdout


def test_well_formed_part_passes(tmp_path: Path) -> None:
    """A part entry with complete provenance is accepted."""
    write(tmp_path, "part-test-good.md", GOOD_PART)
    r = run_lint(tmp_path)
    assert r.returncode == 0, r.stdout


# ------------------------------------------------------------------ failures

BROKEN: list[tuple[str, str, str, str]] = [
    (
        "missing-required-field",
        "part-missing-field.md",
        GOOD_PART.replace("applies_to:\n  part: ESP32-C6-WROOM-1\n  revision: \"v1.3\"\n", ""),
        "missing required field: applies_to",
    ),
    (
        "id-filename-mismatch",
        "part-wrong-name.md",
        GOOD_PART,
        "does not match filename",
    ),
    (
        "high-confidence-without-high-trust",
        "part-test-good.md",
        GOOD_PART.replace("trust: high", "trust: low"),
        "no source is trust: high",
    ),
    (
        "rpn-arithmetic",
        "fm-test-good.md",
        GOOD_FAILURE_MODE.replace("rpn: 24", "rpn: 999"),
        "rpn 999 !=",
    ),
    (
        "unknown-type",
        "part-test-good.md",
        GOOD_PART.replace("type: part", "type: gubbins"),
        "unknown type",
    ),
    (
        "no-frontmatter",
        "part-no-fm.md",
        "Just a markdown file with no frontmatter at all.\n",
        "no YAML frontmatter",
    ),
    (
        # The real-world case: an unquoted ": " inside a value. This is exactly
        # what broke three SKILL.md frontmatters during Phase 2.
        "invalid-yaml-colon-in-value",
        "part-bad-yaml.md",
        "---\nid: part-bad-yaml\ntype: part\ntitle: a part: with a colon\n---\nBody.\n",
        "invalid YAML",
    ),
    (
        "invalid-yaml-unclosed-flow",
        "part-bad-flow.md",
        "---\nid: part-bad-flow\ntype: part\nrelated: [a, b\n---\nBody.\n",
        "invalid YAML",
    ),
    (
        "score-out-of-range",
        "fm-test-good.md",
        GOOD_FAILURE_MODE.replace("severity: 4", "severity: 44").replace("rpn: 24", "rpn: 264"),
        "severity must be 1-10",
    ),
    (
        "sources-not-a-list",
        "part-test-good.md",
        GOOD_PART.replace(
            'sources:\n  - title: "ESP32-C6-WROOM-1 Datasheet"',
            'sources: "just a string"\n  - title: "ESP32-C6-WROOM-1 Datasheet"'),
        "",
    ),
]


@pytest.mark.parametrize(
    "label,filename,content,expected",
    BROKEN,
    ids=[b[0] for b in BROKEN],
)
def test_broken_entries_fail(
    tmp_path: Path, label: str, filename: str, content: str, expected: str
) -> None:
    write(tmp_path, filename, content)
    r = run_lint(tmp_path)
    assert r.returncode == 1, f"{label}: expected exit 1, got {r.returncode}\n{r.stdout}"
    if expected:
        assert expected in r.stdout, f"{label}: {expected!r} not in:\n{r.stdout}"


def test_index_and_readme_are_skipped(tmp_path: Path) -> None:
    """INDEX.md and README.md are prose, not entries, and must not be linted."""
    (tmp_path / "INDEX.md").write_text("# Index\nNo frontmatter here.\n")
    (tmp_path / "README.md").write_text("# Readme\nAlso none.\n")
    r = run_lint(tmp_path)
    assert r.returncode == 0, r.stdout


def test_missing_directory_exits_two(tmp_path: Path) -> None:
    r = run_lint(tmp_path / "does-not-exist")
    assert r.returncode == 2


# ---------------------------------------------- part-entry provenance rules


def test_part_entry_high_trust_source_requires_revision(tmp_path: Path) -> None:
    """A datasheet citation with no revision is an unscoped fact wearing a
    citation. Vendors revise silently; v1.4 is a different document from v1.1."""
    write(tmp_path, "part-test-good.md", GOOD_PART.replace('    revision: "v1.3"\n', "", 1))
    r = run_lint(tmp_path)
    assert r.returncode == 1, r.stdout
    assert "has no 'revision'" in r.stdout


def test_part_entry_missing_sha256_warns_but_passes(tmp_path: Path) -> None:
    """sha256 is advisory: it enables change detection against raw/MANIFEST.tsv,
    but requiring it would block an entry drawn from a document read uncached."""
    content = "\n".join(
        line for line in GOOD_PART.splitlines() if not line.strip().startswith("sha256:")
    ) + "\n"
    write(tmp_path, "part-test-good.md", content)
    r = run_lint(tmp_path)
    assert r.returncode == 0, r.stdout
    assert "1 warnings" in r.stdout
    assert "sha256" in r.stdout


def test_revision_rule_does_not_apply_to_low_trust_sources(tmp_path: Path) -> None:
    """A forum post has no revision to cite. The rule targets vendor documents."""
    content = GOOD_PART.replace("trust: high", "trust: low").replace(
        '    revision: "v1.3"\n', "", 1
    ).replace("confidence: high", "confidence: low")
    write(tmp_path, "part-test-good.md", content)
    r = run_lint(tmp_path)
    assert r.returncode == 0, r.stdout


def test_revision_rule_does_not_apply_to_failure_modes(tmp_path: Path) -> None:
    """Failure modes cite issue trackers and bench work, not document revisions."""
    write(tmp_path, "fm-test-good.md", GOOD_FAILURE_MODE)
    r = run_lint(tmp_path)
    assert r.returncode == 0, r.stdout
