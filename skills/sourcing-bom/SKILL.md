---
name: sourcing-bom
description: Find, price and de-risk electronic components, and build proper bills of materials — stock and lifecycle checks, second sources and alternates, cost at quantity, footprint and 3D model retrieval, distributor and LCSC/JLCPCB part selection, and landed cost for imports into Brazil. Use this skill whenever a part number, a price, "can we get this?", "what does this cost at 100 units?", "what's a cheaper alternative to X", or a BOM comes up — and use it *before* footprints get committed in a layout, because an unobtainable part is a respin.
---

# Sourcing & BOM

## Concepts

**Availability is a design constraint, not a purchasing detail.** *Analogy:
choosing a part with no stock is like building on a library that was
unpublished last year — the code compiles fine, nobody can install it.* Check
stock and lifecycle before the footprint lands in the layout, not after the
Gerbers ship.

**Sticker price is not cost.** Landed cost = unit price + shipping + import
duty + taxes + customs handling + the cost of the delay. For Brazil this gap is
large enough to invert decisions: a part 40% cheaper at LCSC can lose to a
local distributor once import time and taxes are counted, especially at
prototype quantities. See `references/brazil-sourcing.md`.

**"Basic" versus "extended" at JLCPCB is a real cost line.** Basic parts sit
on the machine already; extended parts incur **$3 per unique part number** for
feeder loading — per part number, not per placement. Twenty different extended
parts is $60 before a single component price. There is also a *Preferred
Extended* class that waives the fee on Economic PCBA, which is not obvious from
the part number. See `references/lcsc-jlcpcb-parts.md`, shared with
`manufacturing-dfm`.

**A BOM line without an alternate is a single point of failure.** Every
critical line needs at least one qualified second source, or an explicit note
that none exists and why that's acceptable.

## Decisions

**Where to source.** DigiKey/Mouser for speed, data quality and genuine parts —
best for prototypes and anything safety-relevant. LCSC for cost and for parts
that JLCPCB will assemble. Local Brazilian distributors when time or import
friction dominates.

**Module versus discrete implementation.** A pre-certified radio module costs
more per unit than a bare chip and saves an RF layout, a homologation scope,
and typically months. Below roughly a thousand units the module wins almost
every time.

**When to lock a part.** Lock when the footprint is committed. Before that,
keep two candidates alive.

## Traps

- **Designing around a part on allocation.** Check lead time, not just "in stock".
- **Trusting a scraped footprint.** Verify pad dimensions against the datasheet drawing. A wrong footprint is a dead board.
- **Ignoring lifecycle status.** NRND (not recommended for new designs) parts will strand you.
- **Quoting single-unit price in a product conversation.** Price at the actual target quantity or the number is meaningless.
- **Counterfeits from grey-market sellers.** For anything with a radio, a regulator, or a lithium cell, buy from an authorised distributor.
- **Forgetting the CPF/CNPJ requirement.** LCSC and most Chinese suppliers require the consignee's Brazilian tax ID, and the buyer pays duties on import.

## Tools

**T1 — read freely:**
- **Nexar GraphQL API** (`api.nexar.com/graphql`) for Octopart data. ⚠️ **Unverified (checked 2026-09-14):** earlier notes here claimed a 1,000-part *lifetime* evaluation limit, new apps defaulting to 0, and roughly $500/month for ~2,000 parts. Nexar does not publish pricing publicly and none of this could be confirmed. Treat the free tier as *tight and worth checking before you depend on it*, and get current limits from your own account dashboard. Do not quote these figures to anyone.
- **DigiKey and Mouser APIs** — often the better default given the Nexar limits.
- **LCSC / JLCPCB parts library** for assembly-compatible parts and basic/extended status.
- **SnapEDA, Ultra Librarian, Component Search Engine** for symbols, footprints and 3D models — always verified against the datasheet.
- Datasheet retrieval and PDF parsing.

The public Octopart web UI is bot-blocked; use the API rather than scraping.

**T3 — never execute:** placing orders, checking out a cart, spending money.
Build the cart, produce the quote, and hand it over.

## BOM format

Always produce these columns. A BOM missing lifecycle or an alternate is not
finished.

| Ref | Qty | Value / Description | Manufacturer | MPN | Distributor | Dist. PN | Unit price @ qty | Lifecycle | Alternate MPN | Notes |
|---|---|---|---|---|---|---|---|---|---|---|

Add a summary line with total cost at the target quantity, the count of
extended parts, and the longest lead time on the board.

## Connections

- Part choices constrain `circuit-design` (footprints, thermal, pinout).
- Basic/extended status and package choice feed `manufacturing-dfm` assembly cost, via the shared `references/lcsc-jlcpcb-parts.md`.
- Module selection is jointly a certification decision — see the ANATEL reference in `manufacturing-dfm`.
