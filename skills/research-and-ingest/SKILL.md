---
name: research-and-ingest
description: Find, fetch and extract technical documentation — datasheets, errata, service manuals, user guides, repair guides and vendor specs — and turn them into structured draft notes. Use this skill whenever an answer depends on a document you don't have: an unfamiliar part number, an error code, a chip revision, a printer or instrument you're diagnosing, or any "what does the manufacturer actually say about this?" question. Also use it when you catch yourself about to answer from memory about a specific part's pinout, ratings or behaviour — retrieve the document instead.
---

# Research & Ingest

Turns documents on the internet into draft notes in `scratch/`. It never writes
to the canonical wiki — that gate belongs to `knowledge-base`.

## The default is fetch-one, not crawl-everything

*Analogy: you want a research librarian who fetches the one book you asked
about, not a warehouse operator who photocopies the building.*

Bulk crawling is what fills a knowledge base with staleness, burns goodwill
with the sites you depend on, and creates the legal exposure. **Default:
search → fetch one document → extract → draft a note.** Crawl a whole site only
when all three hold:

1. It's a coherent doc set you'll query repeatedly (Klipper docs, RepRap wiki).
2. There's no API that would give you the same thing.
3. robots.txt and terms permit it.

Crawling is T3. It gets asked for, not assumed.

## Source hierarchy

Always climb as high up this list as you can before settling:

1. **Manufacturer, canonical** — Espressif, NXP, TI, Microchip, Raspberry Pi. Datasheets *and* errata. Errata are the ones people forget and the ones that explain the weird behaviour.
2. **Manufacturer, via API** — the Nexar/Octopart API resolves a manufacturer part number to its official datasheet URL. Resolving beats scraping: it's cleaner, it's within terms, and it gives you the current revision.
3. **Repair sources with an API** — iFixit has a real REST API (`https://www.ifixit.com/api/2.0/`). Content is CC-licensed for non-commercial use with attribution. This is the best-behaved repair source available.
4. **Community, high quality** — Klipper docs, RepRap wiki, Marlin docs, vendor forums. Practically invaluable, authoritatively weak. Tag as `trust: low` and corroborate before anything depends on it.
5. **Manual aggregator sites** — legally fraught and low provenance. Prefer almost anything else. See `references/legal-and-etiquette.md`.

## Tools

**Search.** Use semantic search (Exa in `auto` mode) for obscure things — errata,
service manuals, a symptom described in prose. Use keyword search (Brave) for
exact part numbers and error codes, where precision beats recall. Searching for
`ESP32-S3 "rst:0xc"` is a keyword job; searching for "why does my printer's
first layer lift on one corner only" is a semantic one.

**Fetch.** Crawl4AI self-hosted as the default (free, local, respects your
infrastructure). Firecrawl MCP as the escape hatch for pages that fight back.
Playwright MCP when real interaction is needed. `trafilatura` or `httpx` for
plain static pages — don't start a browser to read an HTML table.

**Extract, tiered by document type:**

| Document | Tool | Note |
|---|---|---|
| Native-text PDF datasheet | PyMuPDF4LLM, then Docling | Fast, local, free |
| Dense electrical-characteristics or pin tables | Docling (TableFormer) | Best open table fidelity |
| Scanned service manual | Local VLM (Qwen2.5-VL via mlx-vlm) or PaddleOCR | Expect ~85–90% on clean Latin scans, worse on faded pages |
| Timing diagram | VLM description + page reference | Never trust extracted numeric timings without a human check |
| **Schematic or exploded parts diagram** | **Don't extract** | Crop the image, store a page reference, defer to a human or a VLM at query time |

That last row is the important one. Reliable schematic-to-netlist extraction is
not a solved problem. Attempting it produces confident, wrong connectivity —
which is worse than having nothing, because it looks like an answer.

## Always capture the footnote

A footnote can turn "absolute maximum" into "do not exceed under any
condition," or scope a rating to a temperature range you're outside of. An
extracted table without its footnotes is a table that quietly lies. If the
extractor drops them, go back for them.

## Draft note output

Everything lands in `scratch/`, never `wiki/`. A draft note must carry:

- The source URL, document title, publisher, **revision or version**, and section or page.
- The **retrieval date**.
- A `trust` tag reflecting where in the hierarchy above it came from.
- The raw document cached in `raw/` if you needed the PDF, with a stable filename.

A draft without provenance is not a draft, it's a rumour. `knowledge-base`
will reject it at the gate, so capture it at fetch time when you still have it.

## Etiquette, enforced not assumed

- Honour robots.txt.
- Rate limit — one request every few seconds per host, not as fast as the network allows.
- Send an honest, descriptive User-Agent with a contact.
- Never bypass a paywall or an auth wall. Public pages only.
- Stop immediately on any takedown or block.

Read `references/legal-and-etiquette.md` before your first crawl and before
caching any service manual.

## Connections

- Hands drafts to `knowledge-base`, which owns the schema and the gate.
- Feeds part data into `sourcing-bom` (the Nexar API serves both).
- Errata findings often change a `firmware` or `circuit-design` answer — surface them rather than filing them silently.
