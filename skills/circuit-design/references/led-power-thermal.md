# LED power and thermal reference

Read before specifying any LED strip or lighting engine.

## Numbers that decide designs

- **WS2812B at full white: ~60 mA per LED.** A 60 LED/m strip therefore draws ~3.6 A/m at full white.
- **Dissipation: ~18 W per metre** for a 60 LED/m strip at full white.
- **No integrated heatsink.** That heat conducts directly into the flexible PCB and then into whatever the strip is stuck to.
- **Efficacy: ~30-40 lm/W** for WS2812B, versus **120+ lm/W** for a plain 2835 SMD white strip.

## What follows from those numbers

1. **Addressable LEDs are a colour-effect layer, not a primary light source.** For a lamp that must actually illuminate a room, use an efficient white engine driven by a constant-current driver, and add addressable LEDs for accent if the product wants colour.
2. **Power supply sizing.** Size for worst case (all LEDs, full white), not typical. Firmware-limited brightness is not a safety margin - firmware can crash.
3. **Wire and trace gauge.** 3.6 A/m adds up fast on long runs. Inject power at both ends, or at intervals, for runs over ~1 m.
4. **Thermal path.** The strip needs somewhere to dump heat - an aluminium channel, a metal core, or contact with the enclosure. PLA softens around 60 C.
5. **Lifespan.** LEDs degrade with junction temperature. Low PWM duty cycle does **not** meaningfully extend life - thermal design does.

## Protocol choice

| | WS2812B / SK6812 | APA102 / SK9822 |
|---|---|---|
| Wires | 1 (data) | 2 (clock + data) |
| Timing | Critical, ~800 kHz, interrupt-sensitive | Clocked, timing-tolerant |
| Refresh rate | Limited | High - good for POV, camera work, smooth dimming |
| Cost | Lower | Higher |

SK6812 RGBW is usually the better choice over WS2812B RGB where white output matters, because a dedicated white die beats mixing R+G+B for both efficacy and colour quality.

## Level shifting

ESP32 outputs 3.3 V. A 5 V-powered WS2812 wants roughly 0.7 x VDD = 3.5 V for a logic high. Options, best first:

1. A proper level shifter (74AHCT125 is the standard answer).
2. Power the strip at ~4.5 V so the logic threshold drops.
3. Sacrifice the first LED as a signal buffer (works, but fragile).

"It worked on the bench at room temperature" is not evidence that this is fine.

## Safety boundary

Lighting products fail hot. Treat sustained full-white operation of dense strips, enclosed strips with no thermal path, and any mains-side LED driver design as escalation points, not implementation details. Specify a certified external LED driver rather than designing the mains side.
