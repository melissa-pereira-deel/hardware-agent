---
name: diagnostic-reasoning
description: Hypothesis-driven hardware debugging — turn "why is it doing that" into a ranked set of causes and the cheapest measurement that discriminates between them, taken before anything is changed. Use whenever something is not working, fails intermittently or "sometimes", worked yesterday and not today, behaves differently on one board, or when the person asks "why is it...", "what's wrong with...", "how do I debug this", "it drops out", "it keeps crashing". Also use before proposing any fix — no fix without a reproduced fault and a reading that implicates the cause.
---

# Diagnostic Reasoning

Debugging hardware is differential diagnosis with a budget. Every test costs
time or money, some tests are destructive, and the order matters because a
wrong early assumption sends the next three hours down the wrong bus. The
discipline: reproduce, hypothesise as a set, measure the cheapest
discriminator, update, repeat. Change nothing until a reading points at the
cause.

*Analogy: a mechanic who hears a noise does not start replacing parts — they
drive the car, listen at each wheel, and swap the tyre to the other side to
see whether the noise follows it.*

## Model

**Reproduce before anything.** A fault that cannot be triggered on demand
cannot be confirmed fixed. Find the trigger first — load, temperature, time
since boot, a specific command, a specific cable. "Intermittent" usually means
"correlated with something not yet observed".

**Hypothesis sets, not a hypothesis.** List every cause that could produce the
observable, then rank by prior probability and by cost to test. The frame from
`problem-reframing` supplies the first entries; the domain skills' `Traps`
sections supply the priors (no current budget, decoupling loop area, ground
pour under the antenna, a typical quoted as a maximum).

**Discriminating measurements.** The best next measurement is the one that
splits the hypothesis set most evenly at the lowest cost — not the one that
confirms the favourite. Reads are free: serial, meter, scope, logic analyser,
`i2cdetect`. Interventions cost more and change the system. Prefer reads until
the set is down to one or two.

**The hardware order.** Power → clocks and reset → communications → logic.
`firmware`'s bring-up order is the same list: rails with a meter, idle current
against the budget, blink, one peripheral at a time, radio last. A fault higher
in the list masquerades as everything below it — a sagging rail looks like a
firmware bug, a bus error and a flaky sensor all at once.

**Physical bisection.** Halve the system, not the code. Swap the cable, the
supply, the board, the sensor — one at a time — and see whether the fault
follows the part. One board is an anecdote; a fault that follows a swapped part
is evidence.

## Apply

**Diagnostic loop** — run out loud, briefly:
1. The observable in measurable terms, plus the trigger that reproduces it.
   If there is no trigger yet, finding one is step one.
2. Hypothesis set: three to six causes, each with a prior (a domain-skill
   trap, a wiki entry, or "no particular reason to expect it").
3. For each, the measurement that would clear or confirm it, its cost, and
   its tier.
4. Pick the cheapest T1 measurement that discriminates most. State the
   expected reading under each hypothesis *before* taking it.
5. Update the set. Repeat until one cause remains and a reading implicates it.
6. Only then propose a fix — together with the measurement that will show the
   fix worked.

**Swap test** — for "only this board" or "only sometimes": swap cable, supply,
board and peripheral in turn. The fault following one of them ends the search;
following none of them points at firmware or environment.

**Wiki first** — grep the wiki for the symptom string before building the set.
An `fm-` entry with a matching symptom is a ranked hypothesis set someone
already paid for, and its `detection` score says how hard the confirming
measurement is.

**Fix verification** — a fix is confirmed when the original trigger no longer
produces the observable, measured the same way. Not by "it seems fine now".

## Lands in

The **bring-up** deliverable shape in `AGENT.md`: an ordered checklist with the
expected reading at each step. For an intermittent, a trigger and a swap
sequence. For a confirmed cause, a candidate `fm-` entry for `scratch/` with
symptom, mechanism, diagnosis steps, and RPN estimates marked as yours.

## Tier note

Steps 1–5 are T1 by construction. If the cheapest discriminator is a device
write — a register poke, a GPIO toggle, a test firmware — it is T2 and the
*which device / what changes / how to undo it* statement applies. A fix that
touches a potted or installed device is T3. Never disable a protection
mechanism (brownout detector, watchdog, over-current limit) as a diagnostic
step: that hides the reading you need.

## Worked example

*"The I2C sensor drops out about once an hour."* Trigger unknown, so first: log
timestamps and correlate with temperature, Wi-Fi TX and time since boot.
Hypothesis set: rail sag during radio TX (prior high — a `circuit-design` trap,
and the wiki has the brownout pattern); pull-ups too weak for the bus
capacitance; a second device at a clashing address responding to noise;
firmware not recovering from a NACK. Cheapest discriminator: scope SDA, SCL
and 3V3 with the trigger set on the dropout. Expected readings: a sag on 3V3
coincident with the dropout → power; rounded edges → pull-ups; a NACK on clean
signals → firmware. All T1. No pull-up gets changed and no driver gets
rewritten until the trace says which.

## Anti-patterns

**Fix-first** — changing a pull-up value because pull-ups are a known cause.
A known cause is a hypothesis, not a diagnosis.

**Confirming the favourite** — choosing the measurement that would prove the
current theory instead of the one that would split the set.

**Debugging below the fault** — three hours in the I2C driver while the rail
sags.

**One board, one theory** — concluding from a single unit without swapping
anything.

**Disabling the alarm** — turning off the brownout detector or the watchdog
to "get past" the symptom. The symptom was the diagnosis.

**"Seems fine now"** — declaring a fix without re-running the trigger.

## Connections

- **problem-reframing** — supplies the first hypothesis and the budget it lives in
- **model-vs-reality** — each hypothesis carries a confidence; a reading moves it, a hunch does not
- **decision-framing** — when two fixes remain, choosing between them is a decision with a rung
- **firmware** — its `Bring-up order` is the canonical hardware order; flashing a test image is T2
- **circuit-design** — its `Traps` are the highest-prior hypotheses for anything electrical
- **knowledge-base** — `fm-` entries are pre-built hypothesis sets; a confirmed cause becomes one
