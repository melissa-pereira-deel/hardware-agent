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

`wiki/hardware/fm-esp32-brownout-boot-loop.md`:

```markdown
---
id: fm-esp32-brownout-boot-loop
type: failure_mode
title: ESP32 brownout boot loop under LED inrush
applies_to:
  part: ESP32-WROOM-32
  silicon_revision: "all"
symptom:
  - "boot loop"
  - "Brownout detector was triggered"
  - "rst:0xc (SW_CPU_RESET)"
severity: 6       # loss of function, no safety hazard
occurrence: 7     # common on USB power with LED loads
detection: 3      # obvious in the serial log
rpn: 126
confidence: high  # reproduced on bench + vendor doc for the detector
sources:
  - title: "ESP32 Series SoC Errata"
    publisher: Espressif
    url: https://docs.espressif.com/projects/esp-chip-errata/en/latest/esp32/
    revision: "latest, retrieved rev noted below"
    section: "chip revision identification"
    retrieved: 2026-09-14
    trust: high
  - title: "Forum thread - brownout on WS2812 inrush"
    publisher: esp32.com (community)
    url: https://example-forum-thread
    retrieved: 2026-09-14
    trust: low
related: [test-3v3-rail-sag, fix-add-bulk-cap-3v3]
updated: 2026-09-14
---

# ESP32 brownout boot loop under LED inrush

## Symptom
Board resets repeatedly at boot. Serial at 115200 shows
`Brownout detector was triggered` and a reset reason of `rst:0xc`.
Most often when driving WS2812 strips, or on a thin USB cable.

## Mechanism
The 3V3 rail sags below the brownout threshold during current inrush - radio TX
or LED turn-on - which trips the brownout detector, resets the chip, and repeats.
This is the detector working correctly. It is a power problem wearing a
firmware problem's clothes.

## Diagnosis
1. Read serial. Confirm the brownout message. If absent, this entry does not apply.
2. Measure 3V3 under load. A dip below ~3.0 V confirms rail sag.
3. Power from a bench supply. If the loop stops, confirmed.

## Fixes
- Add bulk capacitance on 3V3 near the module (470-1000 uF).
- Use a supply and cable rated for the inrush; thin USB cables are a common cause.
- Level-shift the LED data line while you are in there - see fm-ws2812-level-shift.

## Notes on confidence
Severity/occurrence/detection are MY estimates from bench experience, not vendor
figures. The brownout detector behaviour is vendor-documented. The specific
WS2812 inrush correlation is corroborated by community reports only.
```

## What makes this greppable

Because symptoms are verbatim strings in frontmatter, `rg "rst:0xc" wiki/`
finds it instantly. Because `applies_to` is structured, you can find every
entry for a part. Because `confidence` and `trust` are fields, you can filter
to vendor-backed facts only when something safety-relevant is at stake:

```bash
rg -l 'confidence: high' wiki/hardware/ | xargs rg -l 'ESP32'
```

No database required.
