# Wiki entry schema

Every canonical entry is a markdown file with YAML frontmatter. The frontmatter
is what makes grep powerful - it gives structured fields to search without
needing a database.

## Entry types

| `type` | Lives in | Answers |
|---|---|---|
| `failure_mode` | `wiki/hardware/` | "Why is it doing this, and how do I fix it?" |
| `part` | `wiki/parts/` | "What are this component's real specs and gotchas?" |
| `procedure` | `wiki/hardware/` | "How do I do this maintenance/repair task?" |
| `device` | `wiki/hardware/` | "What is this machine, what fails on it, what are its docs?" |

## Required frontmatter fields

```yaml
id:          # stable slug, matches filename. never reused.
type:        # failure_mode | part | procedure | device
title:       # human-readable
applies_to:  # REQUIRED. revision/version scoping. see below.
confidence:  # high | medium | low
sources:     # at least one, each with url, publisher, retrieved
updated:     # ISO date of last human review
```

For `failure_mode` entries, additionally:

```yaml
symptom:     # list of searchable symptom strings, verbatim where possible
severity:    # 1-10
occurrence:  # 1-10
detection:   # 1-10
rpn:         # severity * occurrence * detection
```

## `applies_to` is not optional

The single most common way a hardware wiki goes wrong is an unscoped fact.
"The ESP32 does X" is almost never true - it is true of a revision, a module,
a framework version. Write:

```yaml
applies_to:
  part: ESP32-WROOM-32
  silicon_revision: ">=v1.0"
  framework: "arduino-esp32 >=2.0"
```

If you genuinely don't know the scope, that is itself a finding. Write
`applies_to: {unknown: "scope not established - verify before relying"}` and
set `confidence: low`.

## Worked example

The canonical example is a real file, not a copy in this document:
**`wiki/hardware/fm-esp32-brownout-boot-loop.md`**. Read that one.

This document previously inlined a full copy of it. The two drifted — the
inline copy kept a `trust: high` citation to an errata section that does not
discuss the failure, long after the real entry was corrected. A schema
reference that duplicates its example teaches the stale version. So: frontmatter
shape below, real content in the wiki.

```yaml
---
id: fm-esp32-brownout-boot-loop      # matches filename
type: failure_mode
title: ESP32 brownout boot loop under LED inrush
applies_to:
  part: ESP32-WROOM-32
  silicon_revision: "all"
  framework: "esp-idf >=4.0, arduino-esp32 >=2.0"
symptom:                              # verbatim, and COMPLETE
  - "boot loop"
  - "Brownout detector was triggered"
  - "rst:0xc (SW_CPU_RESET)"
  - "rst:0xf (RTCWDT_BROWN_OUT_RESET)"
severity: 6                           # 1-10, yours
occurrence: 7                         # 1-10, yours
detection: 3                          # 1-10, yours
rpn: 126                              # = 6 * 7 * 3
confidence: medium
sources:
  - title: "Wrong reset cause on brownout"
    publisher: Espressif (esp-idf issue tracker)
    url: https://github.com/espressif/esp-idf/issues/10834
    section: "issue #10834"
    retrieved: 2026-09-14
    trust: medium
related: [fm-ws2812-level-shift]
updated: 2026-09-14
---
```

### Two things that example is teaching

**Symptom lists must be complete, not merely correct.** Both reset codes are
listed because both occur — the brownout handler resets via the watchdog, so
the code is sometimes `rst:0xc`. An entry listing only one is invisible to
someone grepping the other, and grep is the entire retrieval strategy.

**`confidence` tracks what the sources actually support.** That entry is
`medium` and says why in its body: no vendor document has been read that
supports the specific claim. The linter cannot catch a `trust: high` source
cited for a claim it does not make — only you can. Dropping confidence is
always available and always cheaper than being wrong.

## What makes this greppable

Because symptoms are verbatim strings in frontmatter, `rg "rst:0xc" wiki/`
finds it instantly. Because `applies_to` is structured, you can find every
entry for a part. Because `confidence` and `trust` are fields, you can filter
to vendor-backed facts only when something safety-relevant is at stake:

```bash
rg -l 'confidence: high' wiki/hardware/ | xargs rg -l 'ESP32'
```

No database required.
