# Legal position and crawling etiquette

Not legal advice. This is the practical posture for a private, personal,
non-redistributed knowledge base. If any of this becomes commercial or public,
that is a different project and needs a Brazilian attorney.

## The defensible zone

**Private, personal, provenance-tracked, non-redistributed.** Inside that zone
you are on solid ground. The moment you redistribute, mirror, or publish
collected manuals, you leave it.

Four distinct activities, with very different exposure:

| Activity | Position |
|---|---|
| Scraping publicly available pages | Generally lawful under US CFAA case law (hiQ v. LinkedIn line); site terms of service still bind you contractually |
| Bypassing a paywall or auth wall | Do not. This is the conduct the CFAA actually targets, and it breaks terms outright |
| Keeping local copies for your own engineering work | Defensible for datasheets (that is their distributed purpose); greyer for service manuals; keep private |
| Redistributing | Do not. This is where copyright enforcement lands |

## Why service manuals are different from datasheets

Datasheets are distributed by manufacturers *so that* engineers will design with
their parts. Using one for that purpose is the intended use.

Service manuals are frequently treated as confidential and enforced
aggressively. There is a long history of takedowns against sites hosting them -
the Toshiba action against the Future Proof laptop manual archive, and Apple's
removal of service manuals from the web, which is the reason iFixit exists at
all. Take this seriously: keep them private, prefer extracted facts plus a page
reference over a stored copy, and comply immediately with any takedown.

## Right to repair - what it actually gives you

Several US states now have enforceable consumer-electronics right-to-repair
laws, and the EU has directive-level requirements. It is easy to overstate them.

**They compel manufacturers to provide parts, tools and documentation to owners
and independent repairers on fair and reasonable terms. They do not grant a
right to redistribute that documentation, and they do not authorise bulk
scraping.**

So they help you *obtain* documentation as an owner. They do not make a public
mirror lawful. Brazil has no enacted right-to-repair statute equivalent to
these; the Codigo de Defesa do Consumidor is strongly pro-consumer on warranty
and defect remedies but does not mandate documentation disclosure.

## Brazil specifics

- **Lei 9.610/98** protects manuals and datasheets as protected works. Private-copy exceptions are narrower than US fair use. Personal, non-commercial, non-shared study copies are the low-risk zone.
- **LGPD** applies if scraped pages contain personal data - forum usernames, author names. Don't store personal data you have no use for.

## Etiquette, which is also risk management

1. **Honour robots.txt.** Respect `Disallow`.
2. **Rate limit.** One request every few seconds per host. There is no deadline that justifies hammering someone's server.
3. **Honest User-Agent** with a contact address. Anonymous scraping looks like what it looks like.
4. **Prefer APIs over scraping.** Nexar resolves part numbers to official datasheet URLs. iFixit has a documented REST API with CC licensing for non-commercial use with attribution. Using the front door is both easier and safer.
5. **Cache once.** Re-fetching the same PDF weekly is rude and pointless - that is what `raw/` is for.
6. **Stop on block or takedown.** Immediately, without negotiating.

## Attribution

iFixit content is CC-licensed for non-commercial use **with attribution and
share-alike**. If anything derived from it ever leaves your private wiki, the
attribution has to travel with it. Record it at ingest time.
