# Hardware knowledge wiki

Private. Not for redistribution.

Markdown in git, searched with ripgrep. No database, by design - see
`hardware-agent/skills/knowledge-base/SKILL.md` for why.

## Structure

```
raw/       cached source documents. Immutable. Never edited, never republished.
scratch/   agent drafts. Untrusted, disposable.
wiki/      canonical entries. Every one has provenance. Gated by review.
```

Agents write freely to `scratch/`. Nothing reaches `wiki/` without passing the
linter and a human reading the diff.

## Searching

```bash
rg -il "brownout" wiki/
rg -n "rst:0xc" wiki/
cat wiki/INDEX.md
```

## Linting

```bash
python3 ../hardware-agent/harness/kb/lint.py wiki/
python3 ../hardware-agent/harness/kb/lint.py wiki/ --stale 180
```

The pre-commit hook runs this automatically.

## Legal posture

Private, personal, provenance-tracked, non-redistributed. Datasheets are cached
under their intended design-use purpose. Service manuals: prefer extracted facts
plus a page reference over a stored copy, keep private, honour takedowns.
iFixit-derived content carries CC attribution/share-alike obligations if it ever
leaves here.
