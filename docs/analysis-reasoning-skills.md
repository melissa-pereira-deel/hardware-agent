# Analysis — reasoning skills for the hardware agent

> **Discovery document, 2026-09-15.** Not a spec. It answers three questions:
> which high-level reasoning skills the hardware agent should have, why, and
> how they fit the repo as it stands. Written after reading `AGENT.md`,
> `policy/guardrails.md`, `REVIEW.md`, `harness/smoke/`, the five domain
> skills, and the creative-technologist agent and its 19 lenses.

## 1. The ask, restated

The five skills in `skills/` are domain knowledge: what is true about
circuits, firmware, sourcing, fab and the wiki. They make the agent a
competent operator. The ask is to make it an engineer — someone who reframes
the problem before solving it, estimates before selecting, chooses what to
measure, decides what to build first and what not to build, and knows the
limits of their own knowledge.

That difference is judgment, not knowledge. The creative-technologist agent
already encodes judgment as *lenses*: named ways of seeing, each with a core
question, a model, an apply checklist, anti-patterns and connections. The
question is which lenses a hardware engineer needs, and whether the CT ones
transfer.

## 2. Critical reflection before designing anything

### 2.1 The repo already has a stance on this, and it says the opposite

`AGENT.md` opens with: *"Companion to the creative-technologist thinking agent
— that one stays tool-poor and reasons about what to build; this one holds the
tools and builds it."* The CT agent, in turn, is tool-poor "by design" because
a thinker with tools "stops being a thinking partner and becomes a dashboard".

So the original architecture deliberately split thinking from doing. Adding
thinking skills to the doer is a change to that architecture, and it deserves
an explicit answer rather than a quiet drift.

The answer I would give: the split is right at the *product* level and wrong
at the *engineering* level. "Should this lamp exist, for whom, at what price"
belongs to CT and its lenses. "The board resets at full white — is that a
firmware bug or a current budget" does not: it needs physics, it needs the
tools (a meter, a datasheet), and it needs the T1/T2/T3 posture. CT cannot
answer it and should not be taught to. There is a layer of reasoning between
"what to build" and "which command to run", and today nobody owns it.

**Recommendation:** keep CT as the upstream for product framing, add an
*engineering* reasoning layer to the hardware agent, and make the handoff
between them explicit in `AGENT.md`. Do not copy CT's lenses across.

### 2.2 Most CT lenses do not transfer, and forcing them would hurt

Of the 19 CT lenses, the ones about markets, incentives, experience and
learning have no purchase on a circuit:

| CT lens | Transfers? | Why |
|---|---|---|
| First-Principles Reduction | **Yes, adapted** | Questioning requirements and deleting parts is exactly how good hardware gets cheaper and more reliable. But hardware first principles are physics, not rhetoric; the lens must end in a number or a test. |
| Constraint Propagation | **Yes, closest fit** | Its reversibility analysis is what the T1/T2/T3 tiers already enforce in code. Hardware adds a concrete reversibility ladder (breadboard → dev board → PCB rev → potted/certified). |
| Analogical Reasoning | **Yes, with a guard** | The creative move ("a GPIO is a capacitive sensor", "an LED is a photodiode"). Dangerous when the analogy carries wrong physics, so it must land in a measurement. |
| Adjacent Possible | **Partly** | "What does this platform unlock" is useful at platform choice; fold into decision-framing rather than a standalone lens. |
| Temporal Reasoning (pace layers) | **Partly** | Hardware has real pace layers: silicon < PCB < enclosure < firmware < config. Also lifecycle/EOL and certification cycles. Fold into decision-framing. |
| Signal Discrimination | **Partly** | "Which measurement is actually predictive" is the core of diagnosis. Fold into diagnostic-reasoning and model-vs-reality. |
| Deep Deliberation | **Partly** | The T2 pause already institutionalises it. Keep as a stance, not a skill. |
| Evolutionary Design | **Partly** | "Design rev 1 so rev 2 is cheap" is real. Fold into decision-framing. |
| Economic Model Design | **Partly** | Unit economics at quantity breaks is a *budget*, so it lives in budgets-and-margins; the incentive/pricing half stays with CT. |
| Coherence, Legibility, Trust Architecture, Progressive Expertise, Tools for Thought, Performance as Experience, Game Structure, Mechanism Design, Network Dynamics, Information Entropy | **No** | Product and experience lenses. Route to CT when the question is about them. |

What transfers cleanly is CT's *format* and *method*: the SKILL.md shape
(epigraph → model → apply → anti-patterns → connections, a deliberate port
of Alexander's pattern format), the Frame → Select → Apply → Synthesize loop,
the 2–4 lenses per problem discipline, and the named failure modes
("skill-name dropping is theater", "if your output looks like a skill recited
back, you've failed").

CT's own contributing rules settle the "copy or adapt" question from the
other side: a skill with ~40% overlap with an existing one should sharpen
that one instead, and domain-specific skills do not belong in CT. Hardware
reasoning lenses are domain-specific by construction, so they belong here,
not upstream.

### 2.3 The hardware agent already has proto-lenses, scattered as stances

Reading `AGENT.md` and `guardrails.md` as if they were skills:

| Existing stance | Which lens it is the seed of |
|---|---|
| "Before designing anything, establish constraints" (markets, quantity, budget, enclosure, power, timeline) | problem-reframing (requirements step) |
| "Deliverable shape: design decision → decision, 2–3 alternatives, the constraint that decided it" | decision-framing |
| "Grounding: no numbers from memory; draft → cite → validate → test" | model-vs-reality |
| "Simulation is not hardware" | model-vs-reality |
| "Lighting products fail hot: current budget and thermal note, every time, unprompted" | budgets-and-margins, failure-mode-thinking |
| T2: "state which device, what changes, how to undo it" | decision-framing (reversibility) |
| REVIEW.md's `[verified]` / `[unverified]` convention | model-vs-reality (confidence tagging) |
| `knowledge-base/references/trust-and-provenance.md`: trust levels for sources, confidence levels for entries | model-vs-reality (already a scheme; reuse it) |
| `knowledge-base` "Failure-mode entries and RPN" section | failure-mode-thinking (already a scoring scheme; reuse it) |
| Smoke test #1: "ESP32 resets at full white → reach for a current budget, not a firmware bug" | problem-reframing, diagnostic-reasoning |

Two conclusions. First, the repo already values judgment: smoke test #1 tests
*reasoning*, not a tool, and the authors built a cold-agent method to test it.
Second, the judgment exists only as scattered imperatives. There is no
procedure to run, no trigger that says *now* is the moment, and the routing
table in `AGENT.md` routes by domain (circuits, firmware, …) and never by kind
of thinking (framing, diagnosing, deciding, verifying). The domain skills each
have a `Decisions` and a `Traps` section, which is the domain-local version of
the same thing, again without a cross-cutting method.

So the work is less "add thinking" than "collect the thinking that is already
implied, give each piece a name, a trigger, a checklist and a deliverable
shape, and route to it".

### 2.4 The specific risks of doing this badly

The repo's whole value proposition is *not overclaiming*. Reasoning skills
threaten that in three ways, and the design has to answer each:

1. **Verbosity theater.** An agent that narrates five lenses before producing
   a Gerber is worse than the operator it replaced. CT's fix: 2–4 lenses max,
   apply out loud *briefly*, and a 150-word branch-point mode for mid-work
   decisions. Adopt all three.
2. **Confident creativity with wrong physics.** "Reframe from first
   principles" can produce a plausible, elegant, wrong circuit. The guard is
   that every lens must terminate in one of the existing deliverable shapes,
   and any number it introduces still falls under the grounding rule. A
   reframing is a hypothesis until measured.
3. **A third copy of the stances.** `REVIEW.md` §3 already found that
   `AGENT.md` and `policy/guardrails.md` restate each other at roughly 70%
   and prescribed the split: AGENT.md owns routing and tiers, guardrails owns
   stances, once. Reasoning skills are an obvious third place for the same
   sentences to reappear. The rule has to be set up front: guardrails hold
   *stances*, lenses hold *procedures*, AGENT.md holds *routing*. A lens may
   cite a guardrail; it may not restate it.
4. **Breaking skill routing.** `harness/check_skill_routing.py` is a TF-IDF
   proxy that scores 26 realistic prompts against every SKILL.md description
   and asserts the expected skill ranks first; CI runs it. The five domain
   skills route on nouns (parts, tools, file types). Lenses route on verbs
   and situations ("should we", "why is it", "is there a simpler way"). A
   greedy lens description will start winning prompts meant for
   `circuit-design`, and a narrow one will never load. Every lens needs its
   own prompts in that file, and the existing 26 must still pass.
5. **Overlap with generic process skills.** Superpowers ships
   `systematic-debugging` and `brainstorming`. This repo is a standalone agent
   and cannot assume they are installed, and the hardware versions differ in
   substance (measurements cost money, some are destructive, order matters,
   reads are T1 and writes are T2). The overlap is a reason to keep the
   hardware lenses short and specific, not a reason to skip them.

## 3. The proposed lenses

Organising principle: each lens is one judgment that separates an engineer
from an operator. Eight are proposed, ranked by leverage. Each entry gives the
core question, why hardware specifically needs it, the trigger, what it
borrows from CT, and where its output lands.

### 3.1 `problem-reframing` — *What is the actual problem, in physical terms?*

- **Why hardware needs it.** Almost every hardware problem is a violated
  budget: current, thermal, energy, timing, board area, RF link, BOM cost.
  Symptoms arrive described as something else ("the firmware is flaky", "we
  need a bigger battery"). Restating the problem as *which budget, which
  conservation law* collapses most of the search space before any tool runs.
- **Trigger.** Any symptom; any requirement stated as a solution ("we need
  X"); any "make it do Y"; project start.
- **Borrows.** CT First-Principles Reduction steps 1–2 (question the
  requirement, attach a name to it, delete before optimising).
- **Adds.** The budget frame; the constraints-before-design list from
  `AGENT.md` as step one; the rule that a reframing is a hypothesis.
- **Lands in.** A one-sentence frame at the top of the answer, then the
  domain skill. This is the lens smoke test #1 already exercises.

### 3.2 `decision-framing` — *What are the alternatives, what decides, and can it be undone?*

- **Why hardware needs it.** Module vs bare chip, buy vs build, LDO vs buck,
  one PCB vs two: these recur constantly and the cost of a wrong call rises
  roughly tenfold per stage. Engineers make the alternatives explicit, name
  the deciding constraint, and know when to defer a decision with a cheap
  experiment (order both, breadboard first).
- **Trigger.** "Should we use A or B", any part or architecture choice, any
  "let's switch to".
- **Borrows.** CT Constraint Propagation (first/second-order effects,
  reversibility), Adjacent Possible (what a platform unlocks), Temporal
  Reasoning (pace layers), Evolutionary Design (make rev 2 cheap).
- **Adds.** The hardware reversibility ladder — breadboard → dev board →
  custom PCB rev → potted / installed / certified — with cost of change per
  rung, and option value: "which choice keeps the most doors open at the
  next rung". T2/T3 are the bottom rungs of this ladder.
- **Lands in.** The existing "design decision" deliverable shape, now with a
  reversibility line. Mid-work: a branch-point answer under 150 words.

### 3.3 `diagnostic-reasoning` — *What is the cheapest measurement that discriminates between hypotheses?*

- **Why hardware needs it.** Debugging hardware is differential diagnosis
  where each test has a cost and some tests are destructive. Order matters:
  power and ground first, one variable at a time, replicate before fixing.
  Reads are T1 and free; writes are T2. A good engineer bisects physically
  and refuses to change anything until the fault is reproduced.
- **Trigger.** "Why is X", "not working", "intermittent", "sometimes".
- **Borrows.** CT Signal Discrimination (which observation is actually
  predictive); the generic hypothesis-test loop.
- **Adds.** The hardware ordering (power → clocks → reset → comms → logic),
  probe-placement thinking, the distinction between measurement and
  intervention, and "one board is an anecdote" (swap boards, swap cables,
  swap supplies before swapping theories).
- **Lands in.** The "bring-up" deliverable shape: an ordered checklist with
  the expected measurement at each step.

### 3.4 `budgets-and-margins` — *What is the number, roughly, and how far is it from the limit?*

- **Why hardware needs it.** Fermi estimation before part selection catches
  most gross errors at zero cost. Derating and margin are a stance, not a
  step: 60 A of LEDs at 5 V over a 24 AWG wire is decided by arithmetic, not
  by a datasheet. Unit economics at quantity breaks is the same habit applied
  to money.
- **Trigger.** Any part selection; "will it work"; "getting hot"; any
  quantity or cost question.
- **Borrows.** CT Economic Model Design (the unit-economics half only).
- **Adds.** Order-of-magnitude first, then ground the one number that
  decides; derating defaults; the ratio-to-limit as the reported quantity.
- **Lands in.** The current budget and thermal note the guardrails already
  require for LED products, generalised to every design.
- **Grounding interaction.** The estimate is T1 and may come from reasoning;
  the load-bearing number that confirms or refutes it must cite a document.
  The lens makes that sequence explicit instead of implicit.

### 3.5 `failure-mode-thinking` — *How does this fail, how would I know, and what does it cost?*

- **Why hardware needs it.** Hardware failures are physical, latent (thermal
  cycling, ESD, connector wear, part EOL) and discovered late, sometimes as
  fire. A pre-mortem ranked by severity × detectability is what the
  guardrails are trying to induce one case at a time ("lighting fails hot",
  "lithium is advisory").
- **Trigger.** Before any design is called done; before any T2 write; "ship
  it"; any enclosure or thermal decision.
- **Borrows.** CT Constraint Propagation's reversibility triage
  ("propagation without triage" anti-pattern).
- **Adds.** "What does the failure look like from outside the box"; latent
  vs immediate; the recovery-path question already required for T3.
- **Reuses.** The `knowledge-base` skill already defines failure-mode wiki
  entries scored by RPN (severity × occurrence × detectability). The lens
  must use that scheme, not invent a two-axis one, so that a failure mode
  found during design can become a wiki entry without translation. The
  distinction: `knowledge-base` *records* failure modes as knowledge; this
  lens *generates* them for the design in hand.
- **Lands in.** A short RPN-ranked table appended to circuit and bring-up
  deliverables; the T3 response shape ("why it cannot be undone"); candidate
  `fm-` entries for `scratch/`.

### 3.6 `model-vs-reality` — *Which of my claims are measured, which are calculated, which are assumed?*

- **Why hardware needs it.** Datasheet typicals are not minimums, simulators
  diverge from silicon, hand calculations skip parasitics, vendor pages omit
  errata. `REVIEW.md` exists because the first draft of this repo
  "confidently asserted several things that turned out to be wrong". The
  `[verified]` / `[unverified]` convention it introduced is this lens.
- **Trigger.** Any number entering a design; any simulation result; "should
  be fine"; any claim drawn from memory.
- **Borrows.** CT Signal Discrimination.
- **Adds.** "How would I check this cheaply" for every load-bearing claim.
  Turns the Grounding and Simulation-is-not-hardware stances into a
  procedure.
- **Reuses.** `knowledge-base/references/trust-and-provenance.md` already
  defines trust levels for sources and confidence levels for wiki entries.
  The lens should tag design claims with *that* confidence vocabulary rather
  than a new measured/calculated/assumed triple, so a claim in a design and
  a claim in the wiki mean the same thing.
- **Lands in.** Inline tags in every deliverable; the wiki's provenance
  requirement.

### 3.7 `analogical-transfer` — *What does this structurally resemble, and what could an existing part do that it was not sold for?*

- **Why hardware needs it.** This is the creative dimension the ask names:
  seeing a USB-PD trigger board as a bench supply, a GPIO as a touch sensor,
  an enclosure as a heatsink, a software pattern (watchdog, backpressure) as
  a hardware one. It is where CT's stance transfers most directly.
- **Trigger.** Stuck; "is there a simpler way"; exotic requirement; cost or
  part-count pressure; a requirement that seems to need a part that does not
  exist.
- **Borrows.** CT Analogical Reasoning and the affordance stance.
- **Adds.** The guard: an analogy imports a model, and the model may carry
  the wrong physics. Every proposal from this lens ends as a cheap T1
  experiment or measurement, never as a design decision on its own.
- **Lands in.** A candidate plus the test that would validate it.

### 3.8 `risk-retirement-sequencing` — *What should be built or measured first to retire the largest uncertainty?*

- **Why hardware needs it.** Prototype programmes are sequences of
  experiments with lead times. Building the riskiest subsystem first, on the
  cheapest rung of the reversibility ladder, is what separates a three-week
  prototype from a three-month one. One channel before sixty; dev board
  before custom PCB; RF link measured before enclosure is designed.
- **Trigger.** Project start; "what next"; any plan or timeline.
- **Borrows.** Nothing directly from CT; this is engineering programme
  management.
- **Adds.** Rank uncertainties by (cost if wrong × probability), map each to
  the cheapest experiment, order by lead time.
- **Lands in.** An ordered experiment list with what each one retires.

### 3.9 What is deliberately not proposed

- A general "creativity" or "brainstorming" skill. Creativity without a
  landing shape is the verbosity-theater failure. The creative move lives in
  `analogical-transfer` and `problem-reframing`, each of which terminates in
  a test.
- Product-level lenses (economics, incentives, experience). Route to CT.
- A "deep deliberation" skill. The T2 confirmation step already forces the
  pause, in code.

## 4. How they fit the repo

### 4.1 Skill format

Use the CT SKILL.md shape, which is close to the existing hardware skills'
`Concepts / Decisions / Traps / Tools / Connections` layout (the
`knowledge-base` skill already shows the house template can be departed from
when the content demands it):

```
---
name: <Lens Name>
description: "<one-line gloss>. Trigger on: <6–10 verbatim user phrases and situations>."
---
# <Lens Name>
<2–4 sentence opening: the core question, plus one anecdote or number>
## Model            3–5 bolded named sub-concepts as paragraph leads, not headings
## Apply            3–6 named tests/checklists; questions with a decision rule attached
## Lands in         which deliverable shape the output takes   (hardware-specific)
## Tier note        which suggested actions are T1/T2/T3       (hardware-specific)
## Anti-patterns    4–6 bolded named failure modes, one line each
## Connections      reciprocal links to other lenses AND to the domain skills
```

Three CT conventions to keep exactly: triggers live *only* in the
frontmatter, as phrases a user would actually type, because that is what the
routing proxy scores; sub-concepts are bolded leads, not sub-headings; no
agent-coordination content (handoffs, grounding requests) inside a skill —
that stays in `AGENT.md`, which keeps the lenses portable.

One deliberate departure: include **one worked example** per lens. CT's own
backlog lists missing worked examples as its top open item, and hardware
is concrete enough to supply them cheaply — the seeded
`fm-esp32-brownout-boot-loop` wiki entry is a ready-made example for three of
the lenses.

Keep each under ~100 lines (CT's median is 74; the hardware skills run
87–190). The two added sections are what stops a lens from floating free of
the harness.

### 4.2 Where they live and how they route

Keep skills flat under `skills/<name>/SKILL.md` for discovery, and add a
second axis to the routing table in `AGENT.md`:

```
| The thinking is about                       | Load                          |
|---|---|
| A symptom, or a requirement stated as a fix | skills/problem-reframing      |
| A or B, buy or build, module or chip        | skills/decision-framing       |
| "Why is it doing that"                      | skills/diagnostic-reasoning   |
| Will it work, will it get hot, what does it cost | skills/budgets-and-margins |
| Before calling anything done or writing to a device | skills/failure-mode-thinking |
| Any number, any sim result                  | skills/model-vs-reality       |
| Stuck, or "is there a simpler way"          | skills/analogical-transfer    |
| What to build or measure first              | skills/risk-retirement-sequencing |
```

Lenses and domain skills compose: a lens says *how to think*, a domain skill
says *what is true*. A "smart lamp resets at full white" question loads
`problem-reframing` + `budgets-and-margins` + `circuit-design`, in that order.

Each lens also needs 4–6 prompts added to `harness/check_skill_routing.py`,
and `just check-routing` must still pass for the original 26. Because lenses
and domain skills are meant to load *together*, the assertion for a lens
prompt should be "the lens ranks first among lenses" rather than "first
overall", or the proxy will report every co-loading case as a collision.
That is a small change to the checker and should be part of the first slice.

### 4.3 Changes to `AGENT.md`

Small and additive:

1. A **Method** paragraph borrowed from CT: *Frame → Select 2–4 lenses →
   Apply briefly → land in a deliverable shape.* One-sentence frame first,
   always.
2. The second routing table above.
3. An explicit **handoff to the creative-technologist** for product-level
   questions ("should this exist", "for whom", "at what price"), in the
   format CT already uses for its own handoffs.
4. A **branch-point mode**: mid-work decisions answered in under 150 words
   with one lens and one reversibility note.
5. Two anti-patterns added to the explanation-style section: skill-name
   dropping without running the checklist; philosophising when a Gerber was
   asked for.

The existing constraints-before-design list, deliverable shapes and grounding
rules stay where they are; the lenses reference them rather than restating
them. Ownership, stated once so the 70% overlap `REVIEW.md` found does not
grow a third copy: `policy/guardrails.md` owns stances, `skills/<lens>` owns
procedures, `AGENT.md` owns routing and tiers.

### 4.4 Testing, using the repo's own method

`harness/smoke/` already tests judgment with cold agents paired with a
deterministic assertion. Extend it with one prompt per lens:

| Prompt | Should | Deterministic pair |
|---|---|---|
| "We need a bigger battery." | Question the requirement; produce an energy budget before a battery | Response contains a mAh or Wh figure with a source or an "unverified" tag |
| "ESP32 module or bare chip for 200 units with a radio, sold in Brazil?" | Decision shape: alternatives, deciding constraint (ANATEL pre-certification), reversibility line | Response names ANATEL and a reversibility rung |
| "I2C sensor drops out about once an hour." | Ordered diagnostic list, measurement before intervention, no firmware edit proposed first | First suggested action classifies T1 in the broker |
| "Can the aluminium enclosure double as the heatsink?" | A candidate plus the measurement that validates it, not a yes | Response ends with a T1 measurement step |
| "Is this design ready for fab?" | A ranked failure-mode table, thermal and current lines present | Response contains a severity-ranked list |

The pairs are deliberately weak, as in the existing suite; the verdict still
rests mostly on reading the transcript. That is the honest state of testing
prose. The suite's own rule applies unchanged: a failure is a skill problem,
not a test problem — fix the lens, re-run cold, keep both transcripts.

### 4.5 Sequencing the work

Do not write all eight at once. The first slice should be the four with the
most existing evidence and the clearest tests:

1. `problem-reframing` — smoke test #1 already covers it.
2. `decision-framing` — formalises an existing deliverable shape.
3. `model-vs-reality` — formalises Grounding and the REVIEW.md convention.
4. `diagnostic-reasoning` — the most common real request.

Then `budgets-and-margins` and `failure-mode-thinking`, which generalise
guardrails that today apply only to LEDs and lithium. Then
`analogical-transfer` and `risk-retirement-sequencing`, which are the most
novel and therefore the most in need of cold-agent testing before they are
trusted.

Each slice: write the skill, add the routing row in `AGENT.md`, add its
prompts to `check_skill_routing.py`, add the smoke prompt, run it cold,
record the result in `harness/smoke/RESULTS.md`. That is the loop this repo
already uses and it should not change for these.

## 5. Open questions for the owner

1. **CT handoff mechanics.** Should the hardware agent *invoke* the CT agent
   (subagent) or *recommend* the user run it? The CT agent's handoff blocks
   assume a human in the loop. Recommending is the safer default.
2. **Naming.** Lenses vs skills. CT calls them skills; the distinction in this
   doc is expository. One word in the repo.
3. **Where the reversibility ladder is authoritative.** It could live in
   `decision-framing` or in `policy/guardrails.md`. Policy is the better
   home if the broker will ever consult it; the skill should reference it.
