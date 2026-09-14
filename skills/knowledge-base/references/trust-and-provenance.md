# Trust and provenance rules

## Why this file exists

A knowledge base's value is not what it contains, it is what you can rely on.
An entry you have to go verify anyway has cost you time rather than saved it.
So the trust model is load-bearing, and it has to be visible in the file rather
than remembered.

## Trust levels for sources

| `trust` | What qualifies | Can support `confidence: high`? |
|---|---|---|
| `high` | Manufacturer datasheet, errata, official docs, standards body | Yes |
| `medium` | Distributor data, established reference (iFixit guide), textbook | Only with corroboration |
| `low` | Forum post, blog, video, LLM output, your own untested inference | No |

## Confidence levels for entries

- **`high`** - vendor-authoritative source, or reproduced on the bench yourself. Safe to act on.
- **`medium`** - credible and corroborated, not vendor-confirmed. Verify before anything expensive or irreversible.
- **`low`** - plausible, single-sourced, or unscoped. Treat as a lead, not a fact.

## The rules

**1. The wiki never cites itself.** When updating an entry, re-read the raw
source. If an entry's only evidence is another entry, it has no evidence. This
single rule prevents the drift failure where an early misreading becomes
self-reinforcing ground truth.

**2. Corroboration does not upgrade trust by itself.** Three forums agreeing is
still `low` - forums copy each other. Only a `high`-trust source moves an entry
to `confidence: high`.

**3. Your own inference is `low` until you test it.** An agent's reasoning about
a datasheet is not the datasheet. Mark it, and mark what would confirm it.

**4. Distinguish vendor facts from your estimates in the same entry.** FMEA
severity/occurrence/detection scores are almost always yours. Say so in the body.
A reader six months from now cannot tell otherwise, and that reader is you.

**5. Retrieval date on everything.** Not because it proves correctness, but
because it makes staleness queryable instead of invisible.

**6. Never store a fact you cannot attribute.** If provenance was lost during
extraction, the fact does not enter `wiki/`. Go back and get it, or drop it.

## Anti-patterns to refuse

- Writing a fact to `wiki/` in the same session it was scraped, without review.
- Upgrading confidence because the entry has been in the wiki a long time.
- Summarising several sources into a claim none of them individually make, then citing all of them.
- Recording a number without its units, conditions, or qualifying footnote.
- Storing a service manual wholesale when a page reference and a few extracted facts would do.

## What to do when sources conflict

Record the conflict rather than resolving it silently. Two sources disagreeing
about a rating is itself valuable information - it usually means a revision
changed, or one source is derivative and wrong. Write both, note which is
higher-trust, and set `confidence: medium` until it is settled on the bench.
