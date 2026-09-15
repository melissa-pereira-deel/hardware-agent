#!/usr/bin/env python3
"""Check that each skill's YAML `description` carries the vocabulary its
triggering prompts actually use.

This is a PROXY, not the real matcher. The host decides skill loading with a
model, not TF-IDF. What this catches is the failure that actually happens: a
description that omits the words a realistic prompt is phrased in. If the right
skill does not rank first here, the description is probably too narrow - and if
it ranks first by a wide margin on a prompt meant for another skill, it is
probably too greedy.

Skills come in two groups. Domain skills (circuit-design, firmware, ...) say
what is true and route on nouns; reasoning lenses (problem-reframing, ...) say
how to think and route on verbs and situations. They are meant to load
*together*, so a prompt is scored against its own group: a lens prompt must
rank its lens first among lenses, a domain prompt its skill first among domain
skills. Ranking across both groups would report every intended co-load as a
collision.

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

# Reasoning lenses. Everything else under skills/ is a domain skill.
LENSES = {
    "problem-reframing",
    "decision-framing",
    "diagnostic-reasoning",
    "model-vs-reality",
}

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

    # --- reasoning lenses: scored against each other, not against domain skills
    ("We need a bigger battery, this thing dies too fast", "problem-reframing"),
    ("Can you add a heatsink to the regulator?", "problem-reframing"),
    ("We need a faster MCU, the control loop cannot keep up", "problem-reframing"),
    ("Make the lamp respond faster when it gets a command", "problem-reframing"),
    ("I've tried three fixes and it still resets", "problem-reframing"),

    ("Should I use a module or a bare chip?", "decision-framing"),
    ("LDO or buck for this 3.3V rail?", "decision-framing"),
    ("I'm stuck between the ESP32 and the RP2040 for this", "decision-framing"),
    ("Let's switch the whole design to a four layer board", "decision-framing"),
    ("Buy a driver board or build our own?", "decision-framing"),

    ("The I2C sensor drops out about once an hour", "diagnostic-reasoning"),
    ("Why does it only fail on one of the boards?", "diagnostic-reasoning"),
    ("It worked yesterday and now it doesn't", "diagnostic-reasoning"),
    ("How do I debug this? The serial output just stops", "diagnostic-reasoning"),
    ("It keeps crashing but only sometimes", "diagnostic-reasoning"),

    ("Is 40 mA per GPIO safe?", "model-vs-reality"),
    ("Wokwi runs it fine, so we're good to order boards, right?", "model-vs-reality"),
    ("This should be fine at 2 A according to the forum", "model-vs-reality"),
    ("The datasheet and the distributor page disagree on the rating", "model-vs-reality"),
    ("Is this design done? Anything I should double check?", "model-vs-reality"),
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

    unknown = LENSES - set(docs)
    if unknown:
        print(f"LENSES names skills that do not exist: {sorted(unknown)}")
        return 1

    def group(name: str) -> set[str]:
        return {s for s in docs if (s in LENSES) == (name in LENSES)}

    failures = []
    print(f"{len(PROMPTS)} prompts against {n} skill descriptions "
          f"({len(LENSES)} lenses, {n - len(LENSES)} domain)\n")
    for prompt, expected in PROMPTS:
        peers = group(expected)
        ranked = sorted(((score(prompt, s), s) for s in peers), reverse=True)
        top = ranked[0][1]
        rank = [s for _, s in ranked].index(expected) + 1
        ok = top == expected
        if not ok:
            failures.append((prompt, expected, top, rank))
        mark = "ok  " if ok else "MISS"
        print(f"  {mark} [{expected:<20}] {prompt}")
        if not ok or args.verbose:
            detail = "  ".join(f"{s}={v:.3f}" for v, s in ranked[:3])
            print(f"       -> top={top} (expected rank {rank}/{len(peers)})   {detail}")

    print()
    if failures:
        print(f"{len(failures)} prompt(s) did not rank the expected skill first:")
        for prompt, expected, top, rank in failures:
            print(f"  - {prompt!r}\n      expected {expected}, got {top} (expected at rank {rank})")
        return 1
    print("every prompt ranked its expected skill first within its group")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
