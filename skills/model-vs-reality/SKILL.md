---
name: model-vs-reality
description: Tag every load-bearing claim in a design by what it rests on — a bench measurement, a vendor document, a calculation, or an assumption — and say how it would be checked cheaply. Use whenever a number enters a design, whenever a simulation or emulator result is about to be trusted ("Wokwi runs it fine"), whenever something "should be fine" or "should work", whenever a figure is recalled from memory or a forum, when a datasheet typical is being used as a limit ("is 40 mA safe"), when two sources disagree, and before any design is called done or "ready".
---

# Model vs Reality

Every design is a stack of claims, and the claims are not equally true. A rail
measured on the bench is one kind of fact; a datasheet typical is another; a
hand calculation that ignored parasitics is a third; "it should be fine" is not
a fact at all. The first draft of this repo confidently asserted several things
that turned out to be wrong (`REVIEW.md`), and it survived because every claim
was tagged **[verified]** or **[unverified]** and the unverified ones were
chased. That habit is this lens.

*Analogy: the map is not the territory. A datasheet is the map the vendor
drew; a simulator is a map someone else drew from the vendor's map; the bench
is the territory.*

## Model

**The confidence vocabulary already exists.** `skills/knowledge-base/references/trust-and-provenance.md`
defines it and the wiki linter enforces it: sources are `trust: high | medium
| low`; entries are `confidence: high | medium | low`. A design claim uses the
same words, so a number in a schematic note and the same number in a wiki
entry mean the same thing. Do not invent a parallel scale.

**What supports what.** `high`: a vendor datasheet, errata or standard *that
actually addresses the claim*, or a bench reproduction with a recorded method.
`medium`: credible and corroborated, not vendor-confirmed — a distributor page,
a reference design, an app note. `low`: a forum, a blog, an LLM, a recalled
figure, or your own untested inference. Agreement among `low` sources does not
raise them; forums copy each other.

**Typical is not maximum.** Datasheet tables have Min / Typ / Max columns, and
the empty ones are the message. A typical quoted as a limit is the most common
single error in hobby electronics — the "40 mA per GPIO" figure the smoke tests
exist to catch. Read the column header, the test conditions and the footnote
before the number.

**Simulation is not hardware.** Wokwi, QEMU, SPICE with vendor models and
hosted emulators are calculations with someone else's assumptions baked in —
wrong RAM sizes, missing peripheral edge cases, ideal parasitics. They catch
logic errors cheaply. They do not settle timing, power or thermal questions;
the bench does.

**Inference is `low` until tested.** An agent's reasoning about a datasheet is
not the datasheet. Mark it, and mark what would confirm it.

## Apply

**Claim audit** — for each load-bearing number in a design (anything that
would change the design if it were wrong):
1. What does it rest on: bench (method recorded) · vendor document (page,
   column, conditions) · calculation (inputs named) · assumption?
2. Tag it with the shared vocabulary, plus the retrieval or measurement date.
3. If it is `low` or `medium` and the design depends on it: what is the
   cheapest check? Usually a datasheet page or a single meter reading on a dev
   board.
4. If the check cannot be done now, the tag stays on the number in the
   deliverable. A number marked unverified stays marked; repeating it without
   the tag is how it becomes fact.

**Column test** — for any datasheet figure: which column, at what conditions
(V_DD, temperature, load), with which footnote. A Typ with an empty Max is not
a limit; say so explicitly rather than silently treating it as one.

**Simulation boundary** — for any sim result: what is being asked of it. Logic
and sequencing: trust it. Timing, current, thermal, RF, peripheral edge cases:
label the result `low` and name the bench measurement that would settle it.

**Conflict rule** — when two sources disagree, record both with their trust
levels and set `medium` until the bench settles it. A disagreement usually
means a silicon revision changed or one source is derivative and wrong; do not
resolve it by picking the more convenient number.

## Lands in

Inline tags on every load-bearing number in any deliverable — circuit, BOM,
bring-up checklist, design decision — in the form the house rule already uses:
*"4 mil minimum trace, per JLCPCB's capabilities page as of 2026-09-14"*, or
*"~3.6 A/m at full white — calculated from 60 mA/LED, unverified on this
strip"*. A wiki draft inherits the tags directly as `trust` and `confidence`
fields.

## Tier note

Everything here is T1: reading documents, reading instruments, tagging. The
lens forbids one thing outright: acting on a `low`-confidence number at a T2 or
T3 rung. A device write or an irreversible step justified by a recalled figure
is the failure this lens exists to prevent.

## Worked example

*"Is 40 mA per GPIO safe on the ESP32-C6?"* The module datasheet's
output-current table gives I_OH as a Typ with the Min and Max columns empty
(`part-esp32-c6-wroom-1` in the wiki if it has been bootstrapped; otherwise
retrieve the datasheet and read the table). So "40 mA max" is a typical being
quoted as a limit — `low`, with no vendor source supporting it as a ceiling.
The honest design answer: the datasheet gives no maximum; derate hard, drive
anything real through a transistor, and if the number matters, measure on the
bench and record the method. That reading is `trust: high`, because the bench
is a first-class source.

## Anti-patterns

**Typical as limit** — the 40 mA error. Read the column.

**Confidence by age** — a number that has been in the design a long time is
not truer for it.

**Simulation as proof** — "Wokwi runs it fine" offered as evidence about
timing or current.

**Corroboration laundering** — three forums agreeing, cited as if they were
one datasheet.

**Silent resolution** — picking one of two disagreeing sources without
recording the other.

**Tag decay** — an "unverified" that quietly becomes a fact by being repeated
without its warning.

## Connections

- **problem-reframing** — a frame is a `low` inference until measured; this lens keeps it labelled
- **diagnostic-reasoning** — a reading is what moves a hypothesis's confidence; this lens says which readings count
- **decision-framing** — the deciding constraint needs a tag; a decision resting on a `low` number should be deferred or checked
- **knowledge-base** — owns the vocabulary, the linter, and where verified claims go
- **circuit-design**, **manufacturing-dfm** — their `references/` carry a source and a check date on every number; that is this lens applied to the references
- **firmware** — says *simulation is not hardware* in its own words; bring-up is where sim claims get checked
