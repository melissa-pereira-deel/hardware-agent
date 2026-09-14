---
name: knowledge-base
description: Create, query and maintain the hardware knowledge wiki — failure modes, diagnostics, repair procedures, part facts and vendor specs, stored as markdown in git. Use this skill whenever answering a diagnostic or repair question ("why is this board doing X", "how do I fix Y", "what usually fails on this printer"), whenever a session produces a finding worth keeping, and whenever the wiki itself needs setting up, searching, linting or pruning. Search the wiki BEFORE searching the web — the answer may already be there, already verified.
---

# Knowledge Base

Owns the wiki: its structure, its schema, its trust rules, and the gate that
decides what becomes canonical.

## Architecture, and why it's this simple

Markdown files in a git repo, searched with ripgrep. No vector database, no
embeddings, no chunking pipeline.

*Analogy: a vector database is a translator who converts every document into a
private numeric "meaning language," files it in a second cabinet, and finds
things by numeric closeness. Powerful over a huge stable corpus — but you now
maintain two copies, the second one goes stale whenever the first changes, and
when it retrieves the wrong thing you can't see why. Agentic grep is a sharp
assistant reading your actual, well-organised filing cabinet.*

At the scale of one person's hardware notes, grep wins on every axis that
matters: nothing to re-index, nothing to go stale, every retrieval step visible,
and the files stay readable by a human and by any other agent. Anthropic's own
Claude Code took this path deliberately.

**Add a vector index only against a measured failure.** If an evaluation shows
grep missing paraphrased or conceptual queries, add `sqlite-vec` or LanceDB
*alongside* the markdown — never replacing it. Until that measurement exists,
adding one is speculative complexity.

## Three tiers, and the wall between them

```
raw/       immutable cached source documents. Never edited. Never republished.
scratch/   agent-written drafts. Cheap, disposable, untrusted.
wiki/      canonical. Every entry has provenance. Gated.
```

The wall between `scratch/` and `wiki/` is the single most important thing in
this skill. An agent writing unsupervised into its own authoritative knowledge
base is how a knowledge base dies: one misreading becomes an authoritative-
looking page, later sessions cite it as ground truth, and the error is now load-
bearing. This has a name in the security literature — memory and context
poisoning — and a documented reliability equivalent where an agent gradually
internalises its own hallucinations as verified fact.

So: **you may write freely to `scratch/`. You may never write to `wiki/`
without the gate.** Canonicalisation is a T3 action.

## The gate

Before a draft becomes canonical, all of these must hold:

1. **Provenance complete** — source URL, publisher, document revision, section/page, retrieval date. All five.
2. **Re-read from the raw source**, not from another wiki page. The wiki never cites itself as evidence. This is the rule that stops drift.
3. **Trust honestly assigned** — a forum post does not become `high` confidence because it agreed with you. Elevation to `high` requires a vendor-authoritative source.
4. **Revision scoped** — never write "the ESP32 does X." Write which silicon revision, firmware version, or hardware variant it applies to.
5. **Lint passes** — `python harness/kb/lint.py wiki/`.
6. **Human approves the diff.** In practice: the agent opens a commit or PR, you read the diff, you merge. For a solo build this costs a minute and buys the entire trust model.

## Searching

Search the wiki before searching the web. Order:

```bash
rg -il "brownout" wiki/                    # which entries mention it
rg -n "rst:0xc" wiki/                      # exact error codes: keyword wins
rg -l 'symptom:.*"boot loop"' wiki/        # frontmatter field search
cat wiki/INDEX.md                          # the map, when you don't know the term
```

`INDEX.md` is the entry point and is maintained by hand (or by a gated agent
write). It's what makes grep work — it gives the agent the vocabulary of the
wiki so it knows what to grep *for*.

## Entry schema

Full schema and a worked example: `references/entry-schema.md`. Trust and
provenance rules: `references/trust-and-provenance.md`.

Failure-mode entries borrow FMEA — **RPN = Severity × Occurrence × Detection**,
each scored 1–10, so RPN runs 1–1000. It's a prioritisation device, not truth:
the point is that it forces you to separate "how bad is it" from "how often" from
"how hard is it to notice," which is exactly the decomposition that makes
diagnosis tractable. Score your own estimates honestly and mark them as yours —
a vendor doesn't supply RPNs.

## Staleness is the thing that kills knowledge bases

Hardware makes it acute. Errata and silicon revisions change behaviour, so a
fact that was true for chip rev v1.0 is false for v3.0, and nothing in the file
announces it. Countermeasures, in order of value:

1. **Scope every fact to a revision** (rule 4 above). Most staleness is really unscoped facts.
2. **Record the retrieval date and document revision.** Then staleness is queryable rather than invisible.
3. **Re-check job** — periodically re-fetch canonical sources, hash them, flag changes. `harness/kb/lint.py --stale` reports entries past their review horizon.
4. **Prune.** A wrong entry is worse than a missing one, because a missing entry sends you to the source and a wrong one doesn't. Delete aggressively.

## Connections

- `research-and-ingest` produces the drafts this skill gates.
- `circuit-design`, `firmware`, `sourcing-bom` and `manufacturing-dfm` are consumers — they query the wiki, they don't write to it.
- Failure-mode entries pair naturally with FMEA output from circuit analysis tools; curate those into entries rather than dumping them.
