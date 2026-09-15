---
name: decision-framing
description: Structure a hardware design decision — the alternatives, the constraint that decides between them, and how reversible each is on the ladder from breadboard to certified product. Use whenever the question is A or B ("module or bare chip", "LDO or buck", "two layers or four", "buy or build", "ESP32 or RP2040"), whenever someone proposes to switch or change a platform, part or architecture, whenever a decision could be deferred with a cheap experiment, and for mid-work gut checks ("I'm stuck between X and Y", "should we go with"). Produces the design-decision deliverable shape.
---

# Decision Framing

The cost of changing a hardware decision rises roughly tenfold at each stage:
a breadboard rewire costs minutes, a PCB respin costs weeks and a fab run, a
change after certification costs the certification. So an engineer's first
question about any choice is not "which is better" but "at which rung am I
deciding this, and can I decide it one rung lower."

*Analogy: a two-way door you can walk back through; a one-way door locks
behind you. Spend the deliberation on the one-way doors.*

## Model

**The reversibility ladder.** Breadboard or dev board → custom PCB rev 1 →
rev N with parts committed → potted, installed or remote → certified (ANATEL,
CE, FCC). Each rung multiplies the cost of change. The risk tiers in `AGENT.md`
are the bottom of this ladder made mechanical: T2 is a device write the owner
can re-flash; T3 is a rung nobody can climb back down. Take a decision at the
lowest rung that can actually test it.

**The deciding constraint.** Most A-or-B choices are not close once the right
constraint is named. Module vs chip is decided by quantity and homologation
scope, not by preference; LDO vs buck by the dropout × current product, not by
noise folklore. The `Decisions` sections of the domain skills hold the defaults
and the thresholds that flip them. This lens finds which constraint is doing
the deciding and says so.

**Second-order effects.** A choice propagates: a bare chip pulls in RF layout,
a four-layer stack, an RF engineer and a longer certification. Trace one level
past the obvious before committing. Usually one propagated effect is the
deal-breaker; find that one rather than listing fifteen.

**Option value.** When the deciding constraint is not yet known, the right
decision is often to not decide: order both parts, breadboard both, design the
footprint to accept either. Deferral has a cost — time, a second footprint —
and it should be stated, but it is frequently cheaper than being wrong one
rung up.

**Pace layers.** Silicon changes slowest, then PCB, then enclosure, then
firmware, then configuration. Put a decision at the layer that matches how
often it will need to change: anything likely to change after the boards
arrive belongs in firmware or a jumper, not in copper.

## Apply

**Decision shape** — every answer to an A-or-B question carries:
1. The alternatives, two or three, including the one not being taken.
2. The deciding constraint, named, with the number or threshold that flips it
   (cite the domain skill or the datasheet).
3. The rung the decision is taken at, and the cost of changing it one rung
   later.
4. One second-order effect per alternative — the one most likely to surprise.
5. The recommendation, in one sentence.

**Pull-one-thread test** — for a proposed switch ("let's move to a bare
chip"): state the constraint it adds; ask what breaks first; follow that to
what it forces; ask whether that outcome is acceptable. If not, the switch is
wrong regardless of its first-order appeal.

**Defer-or-decide test** — if the deciding constraint is unknown: can a T1
experiment (breadboard, dev board, simulation, a quote) settle it in less time
than the decision would take to reverse? If yes, propose the experiment and
the footprint or plan that keeps both options open. Say what the deferral
costs.

**Branch-point mode** — mid-work, when the person is in flow: under 150 words.
One deciding constraint, the recommendation, one reversibility line. No survey.

## Lands in

The **design decision** deliverable shape in `AGENT.md`, extended with a
reversibility line: *decision · alternatives considered · the constraint that
decided it · the rung and the cost of reversal.* For a switch proposal, the
pull-one-thread result. For a deferral, the experiment and what it keeps open.

## Tier note

Framing is T1. Experiments this lens proposes in order to defer a decision must
be T1 (breadboard, dev board, simulation, quote). A decision that lands on the
potted / installed / certified rung is T3 by `AGENT.md`'s own rule: state it,
draft it, hand it over.

## Worked example

*"ESP32 module or bare chip? 200 units, Wi-Fi, sold in Brazil."* Alternatives:
pre-certified WROOM module; bare chip with own antenna; module now on a
footprint that also accepts the chip later. Deciding constraint: ANATEL
homologation scope — a pre-certified module shrinks it dramatically, and
`circuit-design` puts the bare-chip threshold at roughly a thousand units with
an RF engineer involved. Rung: PCB rev 1; changing later means new RF layout
and re-homologation, the top of the ladder. Second-order: the bare chip forces
a four-layer stack and antenna keep-outs. Recommendation: module. No deferral
needed; the constraint is known.

## Anti-patterns

**Preference as constraint** — "I like the RP2040" is not a deciding
constraint. Name the number.

**Deciding at the wrong rung** — committing copper to something a jumper or a
firmware flag could carry.

**Flattening the tradeoff** — a recommendation with no alternative shown.
`AGENT.md` forbids this outright.

**Deferral as avoidance** — ordering both parts forever. Deferral has a stated
cost and an end condition.

**Fifteen second-order effects** — listing without triage. One is the
deal-breaker; find it.

**Treating every door as two-way** — the potted-device write, the eFuse, the
certification. These get the scrutiny; the pull-up value does not.

## Connections

- **problem-reframing** — supplies the constraint that decides; a decision framed against the wrong problem is confidently wrong
- **model-vs-reality** — the deciding number needs a confidence tag; a decision resting on a `low` number is a deferred decision in disguise
- **diagnostic-reasoning** — a defer-or-decide experiment is a discriminating measurement by another name
- **circuit-design**, **firmware** — their `Decisions` sections hold the defaults and flip thresholds this lens names
- **manufacturing-dfm** — owns the certification rung and what invalidates it
- **sourcing-bom** — quantity and lifecycle are the most common deciding constraints
