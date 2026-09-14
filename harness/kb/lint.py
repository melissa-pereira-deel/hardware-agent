#!/usr/bin/env python3
"""Lint the hardware wiki.

This is the mechanical half of the canonicalization gate. It cannot judge
whether a fact is true; it can judge whether the entry is in a state where its
truth is checkable - which is most of what goes wrong.

    python harness/kb/lint.py wiki/
    python harness/kb/lint.py wiki/ --stale 180
    python harness/kb/lint.py wiki/ --json

Exit code 1 on any error, so it can gate a commit hook or CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

REQUIRED = ["id", "type", "title", "applies_to", "confidence", "sources", "updated"]
FAILURE_MODE_REQUIRED = ["symptom", "severity", "occurrence", "detection", "rpn"]
TYPES = {"failure_mode", "part", "procedure", "device"}
CONFIDENCE = {"high", "medium", "low"}
TRUST = {"high", "medium", "low"}
SOURCE_REQUIRED = ["url", "publisher", "retrieved"]


def parse_front_matter(path: Path) -> tuple[dict | None, str | None]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, "no YAML frontmatter"
    try:
        _, fm, _ = text.split("---", 2)
    except ValueError:
        return None, "unterminated frontmatter"
    try:
        data = yaml.safe_load(fm)
    except yaml.YAMLError as exc:
        return None, f"invalid YAML: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping"
    return data, None


def as_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return None


def check(path: Path, root: Path, stale_days: int) -> list[dict]:
    problems: list[dict] = []

    def err(msg: str, level: str = "error") -> None:
        problems.append({"file": str(path.relative_to(root)), "level": level, "msg": msg})

    fm, parse_error = parse_front_matter(path)
    if parse_error:
        err(parse_error)
        return problems

    for field in REQUIRED:
        if field not in fm or fm[field] in (None, "", []):
            err(f"missing required field: {field}")

    if fm.get("id") and fm["id"] != path.stem:
        err(f"id '{fm['id']}' does not match filename '{path.stem}'")

    entry_type = fm.get("type")
    if entry_type and entry_type not in TYPES:
        err(f"unknown type '{entry_type}' (expected one of {sorted(TYPES)})")

    confidence = fm.get("confidence")
    if confidence and confidence not in CONFIDENCE:
        err(f"confidence must be one of {sorted(CONFIDENCE)}, got '{confidence}'")

    # applies_to: the unscoped-fact guard
    applies = fm.get("applies_to")
    if isinstance(applies, dict):
        if "unknown" in applies and confidence != "low":
            err("applies_to is unknown, so confidence must be low")
    elif applies is not None and not isinstance(applies, str):
        err("applies_to must be a mapping (or a string for simple cases)")

    # sources and the trust model
    sources = fm.get("sources")
    highest_trust = None
    if isinstance(sources, list) and sources:
        for i, src in enumerate(sources):
            if not isinstance(src, dict):
                err(f"sources[{i}] is not a mapping")
                continue
            for field in SOURCE_REQUIRED:
                if not src.get(field):
                    err(f"sources[{i}] missing '{field}'")
            trust = src.get("trust")
            if trust and trust not in TRUST:
                err(f"sources[{i}] trust must be one of {sorted(TRUST)}, got '{trust}'")
            if trust == "high":
                highest_trust = "high"
            elif trust == "medium" and highest_trust != "high":
                highest_trust = "medium"
            if as_date(src.get("retrieved")) is None and src.get("retrieved"):
                err(f"sources[{i}] retrieved is not an ISO date")
    elif sources is not None:
        err("sources must be a non-empty list")

    # Rule: only a high-trust source supports high confidence.
    if confidence == "high" and highest_trust != "high":
        err(
            "confidence is 'high' but no source is trust: high "
            "(bench-verified? say so explicitly with a trust: high source entry)"
        )

    # failure_mode specifics
    if entry_type == "failure_mode":
        for field in FAILURE_MODE_REQUIRED:
            if field not in fm:
                err(f"failure_mode missing '{field}'")
        s, o, d, rpn = (fm.get(k) for k in ("severity", "occurrence", "detection", "rpn"))
        for name, val in (("severity", s), ("occurrence", o), ("detection", d)):
            if isinstance(val, int) and not 1 <= val <= 10:
                err(f"{name} must be 1-10, got {val}")
        if all(isinstance(v, int) for v in (s, o, d, rpn)) and s * o * d != rpn:
            err(f"rpn {rpn} != severity*occurrence*detection ({s*o*d})")
        if fm.get("symptom") and not isinstance(fm["symptom"], list):
            err("symptom must be a list of searchable strings")

    # staleness
    updated = as_date(fm.get("updated"))
    if fm.get("updated") and updated is None:
        err("updated is not an ISO date")
    elif updated:
        age = (date.today() - updated).days
        if age > stale_days:
            level = "error" if fm.get("confidence") == "high" else "warning"
            err(f"not reviewed in {age} days (horizon {stale_days})", level=level)

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint the hardware wiki.")
    ap.add_argument("root", type=Path, help="wiki directory")
    ap.add_argument("--stale", type=int, default=365, help="review horizon in days")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    if not args.root.exists():
        print(f"no such directory: {args.root}", file=sys.stderr)
        return 2

    files = sorted(args.root.rglob("*.md"))
    files = [f for f in files if f.name not in {"INDEX.md", "README.md"}]

    problems: list[dict] = []
    for path in files:
        problems.extend(check(path, args.root, args.stale))

    errors = [p for p in problems if p["level"] == "error"]
    warnings = [p for p in problems if p["level"] == "warning"]

    if args.as_json:
        print(json.dumps({"entries": len(files), "problems": problems}, indent=2))
    else:
        for p in problems:
            mark = "ERROR  " if p["level"] == "error" else "warning"
            print(f"{mark}  {p['file']}: {p['msg']}")
        print(f"\n{len(files)} entries, {len(errors)} errors, {len(warnings)} warnings")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
