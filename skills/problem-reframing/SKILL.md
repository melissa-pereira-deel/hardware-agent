---
name: problem-reframing
description: Restate a hardware problem in physical terms before solving it — which budget is violated (current, thermal, energy, timing, board area, RF link, cost) and whether the stated requirement is a requirement or a solution in disguise. Use this lens first whenever someone describes a symptom ("it resets", "it drifts", "it drops out", "it gets hot"), states a need as a part ("we need a bigger battery", "we need a faster MCU", "add a heatsink"), asks to "make it do X", or at the start of any new design. Also use it when a fix keeps not working — the problem was probably framed wrong.
---

# Problem Reframing

Every hardware problem is a violated budget wearing something else's clothes.
A board that "has a firmware bug" is short of current; a "flaky sensor" has a
noise source; a product that "needs a bigger battery" has an energy budget
nobody wrote down. The question is not "how do I fix the symptom" but "which
conservation law is being broken, and where."

*Analogy: a doctor who hears "I need antibiotics" does not write the
prescription — they ask what the fever is doing.*

## Model

**Budgets are the frame.** A hardware design is a set of budgets that must each
close: current (peak and average), thermal (watts in, watts out, at what
temperature), energy (mAh per day against the cell), timing (interrupt latency,
bus bandwidth, watchdog), board area and layer count, RF link (TX power, antenna
gain, path loss, sensitivity), and cost at the stated quantity. Almost every
symptom is one budget failing to close. Naming the budget collapses the search
space before any tool runs.

**Requirements arrive as solutions.** "We need a bigger battery" is a solution;
the requirement underneath is "it must run N days". "Add a heatsink" is a
solution; the requirement is "the junction stays below T_j". Solutions carry
assumptions (that the energy budget is right, that the heat has nowhere else to
go). Reframing peels the solution off and inspects the requirement.

**Constraints before design.** `AGENT.md` lists the six that must be known
before any design starts — markets, quantity, budget, enclosure, power,
timeline. A reframing that ignores them is a reframing of the wrong problem.

**A reframing is a hypothesis.** "This is a current problem" is a claim about
physics, and physics is checked with a meter. The frame directs the first
measurement; it does not replace it.

## Apply

**Which-budget test** — for any symptom, before opening any tool:
1. Restate the symptom as an observable ("resets when the strip goes white",
   not "firmware is flaky").
2. List the budgets the observable could implicate. For a reset: current,
   thermal, timing (watchdog). For drift: thermal, noise, reference stability.
3. For each, name the one measurement that would confirm or clear it. Pick the
   cheapest; all of them should be reads.
4. Write the frame in one sentence: *"Probably a current-budget problem at LED
   turn-on; 3V3 under load will tell."*

**Solution-to-requirement inversion** — when the request names a part or a fix:
- Ask "what would this solve?" until the answer is a number with units (days
  of runtime, °C, mA, metres of range).
- Attach that number to a person: whose requirement is it, and is it current
  or inherited?
- Ask "what else would satisfy that number?" — duty cycling before a bigger
  cell; a thermal path before a heatsink; a slower bus before a faster MCU.
- Ask "what breaks if the requirement is dropped?" If nothing, say so.

**Constraint check** — if any of the six constraints in `AGENT.md` is unknown
and would change the frame, ask for it once, compactly, before proceeding. Do
not guess.

**Frame first, always.** The first line of the answer is the frame. Everything
after it is the domain skill.

## Lands in

The one-sentence frame at the top of any answer, followed by the domain-skill
deliverable it selects: a current budget → `circuit-design`; an energy budget →
`firmware`; a cost question → `sourcing-bom`. For a design decision, the frame
becomes the "constraint that decided it" line.

## Tier note

Everything this lens does is T1: reading, restating, choosing a measurement.
The measurement it proposes must itself be a read (serial, meter, scope), never
a write. If the cheapest discriminating step is a device write, say so and hand
to the T2 procedure.

## Worked example

*"The ESP32 resets every time the LED strip goes to full white."* Observable:
reset correlated with maximum LED current. Budgets implicated: current (rail
sag), thermal (regulator), timing (watchdog during a long DMA transfer).
Cheapest discriminator: 3V3 at the module pin under load, on a meter. Frame:
*current budget at turn-on — a brownout, not a firmware bug.* The seeded wiki
entry `fm-esp32-brownout-boot-loop` is that frame written down, including the
trap it prevents: disabling the brownout detector "fixes" the symptom by
converting a visible reset into silent flash corruption.

## Anti-patterns

**Symptom-first debugging** — opening the firmware because the symptom appeared
in the firmware.

**Accepting the part as the requirement** — sizing the bigger battery without
ever writing the energy budget it was supposed to close.

**Frame without a measurement** — "it's probably power" followed by a fix, not
a reading. A frame that is not checked is a guess with better vocabulary.

**Reframing the constraint away** — "if we drop the battery requirement this is
easy". Sometimes true; always the owner's call, not the agent's.

**Guessing the missing constraint** — designing for 1000 units when quantity
was never stated.

## Connections

- **diagnostic-reasoning** — the frame picks the first hypothesis; diagnosis orders the rest
- **decision-framing** — the frame supplies the constraint that decides between alternatives
- **model-vs-reality** — the frame is a `low`-confidence inference until the measurement is taken
- **circuit-design** — its trap *no current budget* is this lens's most common landing
- **knowledge-base** — search the wiki for the symptom before reframing from scratch; someone may have framed it already
