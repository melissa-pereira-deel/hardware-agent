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
severity: 6
occurrence: 7
detection: 3
rpn: 126
confidence: high
sources:
  - title: "ESP32 Series SoC Errata"
    publisher: Espressif
    url: https://docs.espressif.com/projects/esp-chip-errata/en/latest/esp32/
    section: "chip revision identification"
    retrieved: 2026-09-14
    trust: high
  - title: "Community reports of brownout under WS2812 inrush"
    publisher: esp32.com (community)
    url: https://esp32.com/
    retrieved: 2026-09-14
    trust: low
related: [fm-ws2812-level-shift]
updated: 2026-09-14
---

# ESP32 brownout boot loop under LED inrush

## Symptom

Board resets repeatedly at boot. Serial at 115200 shows
`Brownout detector was triggered` and a reset reason of `rst:0xc`.
Most often when driving WS2812 strips, or on a thin USB cable.

## Mechanism

The 3V3 rail sags below the brownout threshold during current inrush - radio TX
or LED turn-on - which trips the brownout detector, resets the chip, and
repeats. This is the detector working correctly. It is a power problem wearing
a firmware problem's clothes.

## Diagnosis

1. Read serial. Confirm the brownout message. If absent, this entry does not apply.
2. Measure 3V3 under load. A dip below ~3.0 V confirms rail sag.
3. Power from a bench supply. If the loop stops, confirmed.

## Fixes

- Add bulk capacitance on 3V3 near the module (470-1000 uF).
- Use a supply and cable rated for the inrush. Thin USB cables are a common cause.
- Do not "fix" this by disabling the brownout detector. That converts a visible
  reset into silent flash corruption.

## Notes on confidence

Severity, occurrence and detection are MY estimates from bench experience, not
vendor figures - a vendor does not supply RPNs. The brownout detector behaviour
is vendor-documented. The specific WS2812 inrush correlation is corroborated by
community reports only.
