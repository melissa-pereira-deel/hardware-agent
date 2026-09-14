---
id: fm-esp32-brownout-boot-loop
type: failure_mode
title: ESP32 brownout boot loop under LED inrush
applies_to:
  part: ESP32-WROOM-32
  silicon_revision: "all"
  framework: "esp-idf >=4.0, arduino-esp32 >=2.0"
symptom:
  - "boot loop"
  - "Brownout detector was triggered"
  - "rst:0xc (SW_CPU_RESET)"
  - "rst:0xf (RTCWDT_BROWN_OUT_RESET)"
  - "ESP_RST_WDT"
severity: 6
occurrence: 7
detection: 3
rpn: 126
confidence: medium
sources:
  - title: "Wrong reset cause on brownout (ESP_RST_WDT instead of ESP_RST_BROWNOUT)"
    publisher: Espressif (esp-idf issue tracker)
    url: https://github.com/espressif/esp-idf/issues/10834
    section: "issue #10834, assigned to maintainer"
    retrieved: 2026-09-14
    trust: medium
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
`Brownout detector was triggered`. Most often when driving WS2812 strips, or on
a thin USB cable.

**The reset code you see varies, and that is itself documented behaviour.** You
may see `rst:0xf (RTCWDT_BROWN_OUT_RESET)`, which is the expected one — or
`rst:0xc (SW_CPU_RESET)`, because the brownout handler resets the CPU via the
watchdog and the watchdog's reason overwrites the brownout reason
(espressif/esp-idf#10834). `esp_reset_reason()` may correspondingly return
`ESP_RST_WDT` rather than `ESP_RST_BROWNOUT`.

So: **trust the printed message, not the reset code.** A watchdog reset code
does not rule this out.

## Mechanism

The 3V3 rail sags below the brownout threshold during current inrush — radio TX
or LED turn-on — which trips the brownout detector, resets the chip, and
repeats. This is the detector working correctly. It is a power problem wearing
a firmware problem's clothes.

## Diagnosis

1. Read serial. Confirm the brownout message. If absent, this entry does not apply.
2. Measure 3V3 under load. A dip below ~3.0 V confirms rail sag.
3. Power from a bench supply. If the loop stops, confirmed.

## Fixes

- Add bulk capacitance on 3V3 near the module (470–1000 µF).
- Use a supply and cable rated for the inrush. Thin USB cables are a common cause.
- Budget the LED current properly — a 60 LED/m WS2812B strip at full white is
  ~3.6 A/m. See `circuit-design/references/led-power-thermal.md`.
- Do **not** "fix" this by disabling the brownout detector. That converts a
  visible reset into silent flash corruption.

## Notes on confidence

`medium`, deliberately, and this entry is the worked example of why.

An earlier version of this entry was `confidence: high`, citing the *ESP32
Series SoC Errata*, section "chip revision identification". That source is
vendor-authoritative — and says nothing about brownout behaviour. It was a
`trust: high` citation attached to a claim it does not support, which is the
exact failure the trust model exists to prevent. It passed the linter, because
a linter can check that a source *exists*, not that it is *relevant*.

What is actually established:

- The reset-reason discrepancy is documented in Espressif's own issue tracker (`trust: medium` — an issue, not a specification).
- The brownout detector's existence and behaviour are documented in the ESP32 Technical Reference Manual. **That section has not been read for this entry.** Reading it is what would justify `high`.
- The specific WS2812-inrush correlation is corroborated by community reports only (`trust: low`).

Severity, occurrence and detection are **my estimates from bench experience**,
not vendor figures. A vendor does not supply RPNs.
