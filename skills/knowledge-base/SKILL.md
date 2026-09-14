---
name: knowledge-base
description: Find, fetch and extract technical documentation — datasheets, errata, service manuals, vendor specs — and turn it into a durable, provenance-tracked knowledge wiki of failure modes, part facts, procedures and diagnostics, stored as markdown in git. Use this skill for any specific factual question about a part — max current per GPIO, absolute maximum ratings, pinout, register addresses, timing specs, supply voltage limits, a chip revision, an error code, or "what does the manufacturer actually say about this?". Use it whenever answering a diagnostic or repair question ("why is this board doing X", "what usually fails on this"), whenever a session produces a finding worth keeping ("save this", "remember this", "write this down"), and whenever the wiki needs setting up, searching, linting or pruning. Search the wiki BEFORE searching the web. Use it especially when you catch yourself about to answer a rating or a pin number from memory — retrieve the datasheet instead.
---

# Knowledge Base

One pipeline, end to end: **find → fetch → extract → draft → gate → search.**

This was previously two skills. They were merged because the handoff between
them was exactly where provenance got dropped — and because a model that loads
"how to fetch a datasheet" without also loading "what provenance a fact needs"
will happily produce a confident, unattributable note.

## Architecture, and why it's this simple

Markdown files in a git repo, searched with ripgrep. No vector database, no
embeddings, no chunking pipeline.

*Analogy: a vector database is a translator who converts every document into a
private numeric "meaning language," files it in a second cabinet, and finds
things by numeric closeness. Powerful over a huge stable corpus — but you now
maintain two copies, the second goes stale whenever the first changes, and when
it retrieves the wrong thing you cannot see why. Agentic grep is a sharp
assistant reading your actual, well-organised filing cabinet.*

At one person's scale, grep wins on every axis that matters: nothing to
re-index, nothing to go stale, every retrieval step visible, and the files stay
readable by a human and by any other agent.

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

The wall between `scratch/` and `wiki/` is the single most important thing
here. An agent writing unsupervised into its own authoritative knowledge base
is how a knowledge base dies: one misreading becomes an authoritative-looking
page, later sessions cite it as ground truth, and the error is now
load-bearing. This has a name in the security literature — memory and context
poisoning.

So: **write freely to `scratch/`. Never write to `wiki/` without the gate.**
Canonicalisation is T3.

## Search the wiki first

Before reaching for the web:

```bash
rg -il "brownout" wiki/                    # which entries mention it
rg -n "rst:0xc" wiki/                      # exact error codes: keyword wins
rg -l 'symptom:.*"boot loop"' wiki/        # frontmatter field search
cat wiki/INDEX.md                          # the map, when you don't know the term
```

`INDEX.md` is the entry point, maintained by hand. It gives you the vocabulary
of the wiki so you know what to grep *for*. An unindexed entry is an entry
nobody finds.

**Symptom strings must be verbatim and complete.** If a failure reports two
different reset codes, both go in the list. A symptom list that omits the
string someone will actually paste is a broken index, however correct the prose
below it is.

## Fetching: one document, not a site

*Analogy: you want a research librarian who fetches the one book you asked
about, not a warehouse operator who photocopies the building.*

**Default: search → fetch one document → extract → draft a note.** Crawl a
whole site only when all three hold: it's a coherent doc set you'll query
repeatedly, there's no API giving the same thing, and robots.txt and terms
permit it. Crawling is T3 — it gets asked for, not assumed.

### Source hierarchy

Climb as high as you can before settling:

1. **Manufacturer, canonical** — Espressif, NXP, TI, Microchip, Raspberry Pi. Datasheets *and* errata. Errata explain the weird behaviour and are the ones people forget.
2. **Manufacturer, via API** — resolving a manufacturer part number to its official datasheet URL beats scraping: cleaner, within terms, current revision.
3. **Repair sources with an API** — iFixit has a real REST API. CC-licensed for non-commercial use with attribution.
4. **Community, high quality** — Klipper docs, RepRap wiki, vendor forums. Practically invaluable, authoritatively weak. Tag `trust: low` and corroborate.
5. **Manual aggregator sites** — legally fraught, low provenance. Prefer almost anything else.

### Tools

**Start with the simple thing.** Your actual workload is vendor PDFs from
`docs.espressif.com` and similar — static files that need no browser:

```bash
httpx / curl        # fetch the PDF or HTML
trafilatura         # readable text from a static HTML page
pymupdf             # PDF text and tables, local and fast
```

Escalate only when a page genuinely fights back: **Firecrawl's hosted MCP** as
the escape hatch, Playwright when real interaction is unavoidable. Don't
self-host a crawler for a workload you don't have.

**Extract, tiered by document type:**

| Document | Tool | Note |
|---|---|---|
| Native-text PDF datasheet | PyMuPDF, then Docling | Fast, local, free |
| Dense electrical-characteristics or pin tables | Docling (TableFormer) | Best open table fidelity |
| Scanned service manual | Local VLM (Qwen2.5-VL via mlx-vlm) or PaddleOCR | Expect ~85–90% on clean Latin scans, worse on faded pages |
| Timing diagram | VLM description + page reference | Never trust extracted numeric timings without a human check |
| **Schematic or exploded parts diagram** | **Don't extract** | Crop the image, store a page reference, defer to a human |

That last row is the important one. Reliable schematic-to-netlist extraction is
not a solved problem, and attempting it produces confident, wrong connectivity —
worse than nothing, because it looks like an answer.

### Always capture the footnote

A footnote can turn "absolute maximum" into "do not exceed under any
condition," or scope a rating to a temperature range you're outside of. An
extracted table without its footnotes is a table that quietly lies. If the
extractor drops them, go back for them.

**And check whether the number is there at all.** A specification you expected
to find and didn't is a finding, not a gap to fill from memory. The WS2812B
datasheet contains no drive-current figure; every "60 mA per LED" in
circulation is inference. Say so when it happens.

## Drafting

Everything lands in `scratch/`, never `wiki/`. A draft must carry:

- Source URL, document title, publisher, **revision or version**, section or page
- The **retrieval date**
- A `trust` tag reflecting the hierarchy above
- The raw document cached in `raw/` with a stable filename, plus its `sha256`

A draft without provenance is not a draft, it's a rumour. Capture it at fetch
time, when you still have it.

## The gate

Before a draft becomes canonical, all of these must hold:

1. **Provenance complete** — URL, publisher, revision, section/page, retrieval date. All five.
2. **Re-read from the raw source**, not from another wiki page. The wiki never cites itself. This is the rule that stops drift.
3. **Trust honestly assigned** — and the source must support *this claim*, not merely be authoritative in general. A vendor errata page cited for a fact it doesn't discuss is not evidence.
4. **Revision scoped** — never "the ESP32 does X". Which silicon revision, framework version, hardware variant.
5. **Lint passes** — `python harness/kb/lint.py wiki/`.
6. **Human approves the diff.** The agent stages it; you read it; you merge.

Full schema and worked example: `references/entry-schema.md`. Trust rules:
`references/trust-and-provenance.md`. Legal posture and crawling etiquette:
`references/legal-and-etiquette.md` — read before your first crawl and before
caching any service manual.

## Failure-mode entries and RPN

**RPN = Severity × Occurrence × Detection**, each 1–10, so RPN runs 1–1000.
It's a prioritisation device, not truth. The point is that it forces you to
separate "how bad" from "how often" from "how hard to notice" — exactly the
decomposition that makes diagnosis tractable. Score honestly and mark the
scores as yours; a vendor does not supply RPNs.

## Staleness is what kills knowledge bases

Hardware makes it acute: errata and silicon revisions change behaviour, and
nothing in the file announces it. In order of value:

1. **Scope every fact to a revision.** Most staleness is really unscoped facts.
2. **Record retrieval date and document revision.** Staleness becomes queryable instead of invisible.
3. **Re-check periodically** — re-fetch canonical sources, compare hashes, flag changes. `harness/kb/lint.py --stale` reports entries past their horizon.
4. **Prune.** A wrong entry is worse than a missing one: a missing entry sends you to the source, a wrong one doesn't. Delete aggressively.

## Etiquette, enforced not assumed

Honour robots.txt. Rate limit — one request every few seconds per host. Send an
honest User-Agent with a contact. Never bypass a paywall or auth wall. Stop
immediately on any block or takedown.

## Connections

- `circuit-design`, `firmware`, `sourcing-bom` and `manufacturing-dfm` are consumers — they query the wiki, they don't write to it.
- Errata findings often change a `firmware` or `circuit-design` answer. Surface them rather than filing them silently.
