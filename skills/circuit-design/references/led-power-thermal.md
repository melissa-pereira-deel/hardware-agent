# LED power and thermal reference

Read before specifying any LED strip or lighting engine.

Every number here carries its provenance, because these are the numbers that
size a power supply and decide whether an enclosure melts. `trust: high` means
a manufacturer datasheet. Anything lower is flagged inline — treat those as
design assumptions to check on the bench, not as facts.

## Current — and an honest note about where 60 mA comes from

**The WS2812B datasheet does not specify drive current.** It contains no
current figure at all beyond a ±1 µA input leakage spec. This matters, because
the current budget is the single most load-bearing calculation in an
addressable-LED product, and its headline number is not a vendor number.

| Figure | Value | Provenance |
|---|---|---|
| Design ceiling, full white | **~60 mA/LED** | 3 × ~20 mA, inferred from the WS2811-family constant-current design (18.5 mA/channel). `trust: low` — inference, not datasheet |
| Bench measurement, full white | **~50 mA/LED** | Third-party measured. `trust: medium` |
| Typical animated content | **~20–40 mA/LED** | Widely reported working figure. `trust: low` |
| Logic threshold V<sub>IH</sub> | **0.7 × V<sub>DD</sub>** (3.5 V at V<sub>DD</sub>=5 V) | **Datasheet, Electrical Characteristics.** `trust: high` |
| Supply voltage, absolute max | **+3.5 to +5.3 V** | **Datasheet, Absolute Maximum Ratings.** `trust: high` |
| Operating junction temperature | **−25 to +80 °C** | **Datasheet, Absolute Maximum Ratings.** `trust: high` |

**Size the supply against 60 mA/LED.** It is the conservative end of a range
whose true value depends on the strip you actually bought — and clone strips
vary. Then measure your strip at full white and write the measurement down.
That measurement is worth more than everything above it in this table.

At 60 LED/m and 60 mA: **3.6 A/m at full white**, so **~18 W/m drawn** at 5 V.

**"Drawn", not "dissipated"** — but the distinction is nearly academic here.
At the efficacy figures below, something like 10–15% of that leaves as light
and the rest becomes heat in the strip. For thermal purposes, treat ~18 W/m as
heat.

## Efficacy — why addressable is an accent layer, not a light source

| | WS2812B (RGB mixed to white) | Plain 2835 white strip |
|---|---|---|
| Efficacy | ~30–40 lm/W | ~120–160 lm/W |

`trust: medium` — corroborated across multiple industry sources, but no
manufacturer publishes a lm/W figure for the WS2812B, and the datasheet gives
only per-die luminous intensity (R 390–420 mcd, G 660–720 mcd, B 180–200 mcd),
which cannot be converted to lumens without a viewing-angle assumption.

The mechanism is solid even where the exact numbers aren't: the integrated
controller burns power continuously, and mixing R+G+B to white is inherently
worse than a dedicated white die with phosphor.

**So: for a lamp that must actually light a room, use an efficient white engine
on a constant-current driver, and add addressable LEDs for colour accent.** If
the product's whole identity is colour, that is a legitimate reason to accept
the efficacy cost — but accept it knowingly and size the thermal path for it.

## What follows

1. **Size for worst case** (all LEDs, full white), not typical. Firmware-limited
   brightness is not a safety margin — firmware crashes.
2. **Wire and trace gauge.** 3.6 A/m adds up fast. Inject power at both ends,
   or at intervals, for runs over ~1 m.
3. **Thermal path.** The strip needs somewhere to dump heat: an aluminium
   channel, a metal core, or contact with the enclosure.
4. **Lifespan is a thermal question.** LEDs degrade with junction temperature.
   Low PWM duty does **not** meaningfully extend life — thermal design does.

## Enclosure temperature limits

| Material | Glass transition (T<sub>g</sub>) | Heat deflection (HDT) |
|---|---|---|
| PLA | 60–65 °C | **~53 °C** |

`trust: medium` — materials literature, not a single vendor datasheet; check
your specific filament's TDS.

**Design against the HDT (~53 °C), not the T<sub>g</sub>.** HDT is where a
loaded part starts to creep, and it is the lower number. FDM-printed PLA
performs worse than injection-moulded PLA of the same grade, because printing
suppresses the crystallinity that would otherwise help above T<sub>g</sub>.

A sealed PLA enclosure with an 18 W/m strip inside will exceed this. That is a
fire and deformation risk, not a warranty footnote. PETG or ABS, a vented
design, or an aluminium channel — pick one before printing.

## Protocol choice

| | WS2812B / SK6812 | APA102 / SK9822 |
|---|---|---|
| Wires | 1 (data) | 2 (clock + data) |
| Timing | Critical, ~800 kHz, interrupt-sensitive | Clocked, timing-tolerant |
| Refresh rate | Limited | High — good for POV, camera work, smooth dimming |
| Cost | Lower | Higher |

SK6812 RGBW is usually the better choice over WS2812B RGB where white output
matters: a dedicated white die beats mixing R+G+B on both efficacy and colour
quality.

## Level shifting

An ESP32 outputs 3.3 V. The WS2812B datasheet specifies
**V<sub>IH</sub> = 0.7 × V<sub>DD</sub>**, so a 5 V-powered strip needs **3.5 V**
for a guaranteed logic high. 3.3 V is below spec. It very often works anyway,
which is exactly what makes it dangerous — it is an out-of-spec design that
passes on the bench and fails at temperature or on a long line.

Options, best first:

1. A proper level shifter — **74AHCT125** is the standard answer (HCT inputs are
   TTL-threshold, so 3.3 V is a solid high).
2. Power the strip at ~4.5 V, dropping the threshold to 3.15 V.
3. Sacrifice the first LED as a signal buffer. Works, but fragile.

## Safety boundary

Lighting products fail hot. Sustained full-white operation of dense strips,
enclosed strips with no thermal path, and any mains-side LED driver design are
escalation points, not implementation details. Specify a certified external LED
driver rather than designing the mains side.

---

## Sources

| Claim | Source | Trust | Checked |
|---|---|---|---|
| V<sub>IH</sub>, V<sub>DD</sub> range, T<sub>opt</sub>, luminous intensity | [WS2812B datasheet (Worldsemi, via Adafruit)](https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf) — extracted directly, Electrical Characteristics and Absolute Maximum Ratings tables | high | 2026-09-14 |
| Absence of any current spec in the datasheet | Same document, full-text search: zero occurrences of "mA" | high | 2026-09-14 |
| ~18.5 mA/channel constant current | WS2811 driver IC family spec | low | 2026-09-14 |
| ~50 mA measured at full white | [Zaitronics WS2812B power guide](https://zaitronics.com.au/blogs/guides/ws2812b-led-power-requirements-rgb-strips-rings-matrices) | medium | 2026-09-14 |
| Efficacy 30–40 vs 120–160 lm/W | [ElectricalFlux WS2812B driver guide](https://electricalflux.com/learn-components/ws2812b-addressable-led-circuit-driver-guide); corroborated by strip-manufacturer datasheets | medium | 2026-09-14 |
| PLA T<sub>g</sub> 60–65 °C, HDT ~53 °C | [JLC3DP PLA temperature resistance](https://jlc3dp.com/blog/pla-temperature-resistance); materials literature | medium | 2026-09-14 |
