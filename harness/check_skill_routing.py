#!/usr/bin/env python3
"""Check that each skill's YAML `description` carries the vocabulary its
triggering prompts actually use.

This is a PROXY, not the real matcher. The host decides skill loading with a
model, not TF-IDF. What this catches is the failure that actually happens: a
description that omits the words a realistic prompt is phrased in. If the right
skill does not rank first here, the description is probably too narrow - and if
it ranks first by a wide margin on a prompt meant for another skill, it is
probably too greedy.

    python harness/check_skill_routing.py
    python harness/check_skill_routing.py --verbose
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"

STOP = set("""a an and are as at be been before but by can do does for from has have if in into is it
its of on or that the their them then there these this to use used uses using was what when where
which who why will with you your about also any even how just like more most not now one only other
out over own same some such than too very whenever whether while
we us our i me my mine he she they them his her theirs ours yours get got need want
actually really just still yet here""".split())

# prompt -> the skill that should load. Realistic phrasings, including the
# five smoke tests from the brief.
PROMPTS: list[tuple[str, str]] = [
    ("The ESP32 resets every time the LED strip goes to full white", "circuit-design"),
    ("Why is this board getting hot?", "circuit-design"),
    ("My NFC tag read range is terrible, what's wrong with the antenna?", "circuit-design"),
    ("What value resistor do I need for this indicator LED?", "circuit-design"),
    ("Level shifting between the ESP32 and a 5V strip", "circuit-design"),

    ("Enable secure boot on the production units", "firmware"),
    ("Flash this firmware to the board on /dev/cu.usbmodem1101", "firmware"),
    ("Should I use Arduino or ESP-IDF for this?", "firmware"),
    ("The device drains its battery in two days", "firmware"),
    ("Set up OTA updates with rollback", "firmware"),

    ("What'll this cost at 100 units?", "sourcing-bom"),
    ("Is there a cheaper alternative to this regulator?", "sourcing-bom"),
    ("Can we actually get this part?", "sourcing-bom"),
    ("How much will import duty be on this LCSC order?", "sourcing-bom"),
    ("Build me a BOM with alternates", "sourcing-bom"),

    ("Can we sell this Wi-Fi lamp in Brazil?", "manufacturing-dfm"),
    ("Is this board ready to send to the fab?", "manufacturing-dfm"),
    ("Do we need certification for this?", "manufacturing-dfm"),
    ("Design a 3D printed diffuser for this strip", "manufacturing-dfm"),
    ("Should I panelize this board for assembly?", "manufacturing-dfm"),

    ("What's the max current per GPIO on the ESP32-C6?", "knowledge-base"),
    ("Save what we just worked out about the brownout issue", "knowledge-base"),
    ("What usually fails on this printer?", "knowledge-base"),
    ("Find me the datasheet for the NTAG I2C Plus", "knowledge-base"),
    ("What does the manufacturer actually say about this rating?", "knowledge-base"),
    ("Search the wiki for anything about boot loops", "knowledge-base"),
]


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9][a-z0-9\-/+.]*", text.lower())
    out = []
    for w in raw:
        w = w.strip(".-/")
        if len(w) < 2 or w in STOP:
            continue
        out.append(w)
        if w.endswith("s") and len(w) > 3:
            out.append(w[:-1])  # crude singularisation
    return out


def load_descriptions() -> dict[str, str]:
    desc = {}
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        _, fm, _ = text.split("---", 2)
        meta = yaml.safe_load(fm)
        desc[meta["name"]] = meta["description"]
    return desc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    desc = load_descriptions()
    docs = {name: Counter(tokens(d)) for name, d in desc.items()}
    n = len(docs)
    df = Counter()
    for c in docs.values():
        df.update(c.keys())
    idf = {w: math.log((n + 1) / (df[w] + 1)) + 1 for w in df}

    def score(prompt: str, name: str) -> float:
        q = Counter(tokens(prompt))
        d = docs[name]
        num = sum(q[w] * d.get(w, 0) * idf.get(w, 1.0) ** 2 for w in q)
        dn = math.sqrt(sum((d[w] * idf.get(w, 1.0)) ** 2 for w in d)) or 1.0
        qn = math.sqrt(sum((q[w] * idf.get(w, 1.0)) ** 2 for w in q)) or 1.0
        return num / (dn * qn)

    failures = []
    print(f"{len(PROMPTS)} prompts against {n} skill descriptions\n")
    for prompt, expected in PROMPTS:
        ranked = sorted(((score(prompt, s), s) for s in docs), reverse=True)
        top = ranked[0][1]
        rank = [s for _, s in ranked].index(expected) + 1
        ok = top == expected
        if not ok:
            failures.append((prompt, expected, top, rank))
        mark = "ok  " if ok else "MISS"
        print(f"  {mark} [{expected:<17}] {prompt}")
        if not ok or args.verbose:
            detail = "  ".join(f"{s}={v:.3f}" for v, s in ranked[:3])
            print(f"       -> top={top} (expected rank {rank}/{n})   {detail}")

    print()
    if failures:
        print(f"{len(failures)} prompt(s) did not rank the expected skill first:")
        for prompt, expected, top, rank in failures:
            print(f"  - {prompt!r}\n      expected {expected}, got {top} (expected at rank {rank})")
    else:
        print("every prompt ranked its expected skill first")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
