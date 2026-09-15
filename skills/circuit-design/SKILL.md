---
name: circuit-design
description: Design and review electronic circuits and PCBs — schematic capture, component selection, power supplies, LED and lighting drive, level shifting, protection, antennas and RF keep-outs, thermal management, and KiCad layout. Use this skill whenever a schematic, PCB, breadboard, component value, voltage rail, LED strip, sensor hookup, NFC antenna, or "why is this circuit not working / getting hot / browning out" comes up — including when someone just describes a physical behaviour they want and hasn't drawn anything yet. Also use it to run ERC/DRC and to sanity-check a design before it goes to a fab.
---

# Circuit Design

## Concepts

**Current is what actually kills designs.** Voltage is the easy part — the
regulator holds it. Current is where budgets blow up, traces melt, regulators
overheat and batteries die early. *Analogy: voltage is water pressure, current
is flow rate, resistance is how narrow the pipe is.* Every design gets a
current budget before it gets a layout: worst-case draw per rail, per branch,
summed, with a margin.

**Power supply choice is a heat question.** *Analogy: an LDO is a valve that
throttles pressure by burning the excess off as heat; a buck converter is a
gearbox that trades voltage for current with very little waste.* An LDO
dropping 5 V → 3.3 V at 500 mA dissipates 0.85 W as heat in a package the size
of a grain of rice. Choose LDO for low-noise, low-current, small-drop rails
(analog, RF); choose a buck for anything above a few hundred mA or with a large
drop. Always: 0.1 µF ceramic as close as physically possible to each IC power
pin, plus bulk capacitance on the rail.

**Addressable LEDs are a thermal product, not a lighting effect.** A 60 LED/m
WS2812B strip at full white draws about 3.6 A/m — roughly 18 W at 5 V — and
almost all of that becomes heat, straight into the flexible PCB, because there
is no integrated heatsink. Efficacy is poor too: order of 30–40 lm/W against
120–160 lm/W for a plain 2835 white strip. So for a lighting *product*,
addressable LEDs are a colour-effect layer, not the main light source.

Two caveats that matter more than the numbers: **the 60 mA/LED figure is not in
the WS2812B datasheet** — it contains no current spec at all — and the efficacy
figures are industry-reported, not vendor-published. Both are sound enough to
design against and worth measuring on the strip you actually bought. See
`references/led-power-thermal.md`, which carries the provenance for each.

**Level shifting between 3.3 V and 5 V is the classic silent failure.** An
ESP32 outputs 3.3 V logic. The WS2812B datasheet specifies V_IH = 0.7 × VDD, so
a 5 V-powered strip needs 3.5 V for a guaranteed high — 3.3 V is out of spec.
It usually works anyway, which is precisely the danger: the bench passes and
the field fails, or it fails at temperature. Use a proper level shifter
(74AHCT125), power the strip at ~4.5 V, or sacrifice the first LED as a buffer.

**Antennas need quiet space.** *Analogy: a microphone next to a wall picks up
mush; cup your hand over it and it's worse.* Every ESP32 module datasheet
specifies a keep-out region. Put the antenna at a board edge, keep all copper —
including ground pour and inner layers — out of the keep-out, and keep metal
and batteries away from it in the enclosure. Moving an antenna on a certified
design invalidates the certification.

**NFC is an inductive link, not a radio link.** A 13.56 MHz tag antenna is a
tuned coil; the tuning capacitor and coil geometry must resonate correctly or
read range collapses. NXP's AN11276 and the free NXP NFC Antenna Design Tool
cover NTAG213 and NTAG I²C Plus. For a lamp that should react to a phone tap,
NTAG I²C Plus is the interesting part: it has energy harvesting and a
field-detect pin that can wake a sleeping MCU.

## Decisions

**Module or bare chip?** Default to a pre-certified module (ESP32-C6-WROOM,
ESP32-S3-WROOM). It removes RF layout risk entirely and, for Brazil, shrinks
the homologation scope dramatically. Go bare-chip only above roughly a thousand
units with a real RF engineer involved.

**Two layers or four?** Two layers is fine for low-speed, low-current boards.
Go to four the moment you have a radio, fast digital, or a sensitive analog
front end — the continuous ground plane is the point, not the routing space.

**Constant-current driver or series resistor?** Resistors for indicator LEDs.
Constant-current drivers for anything that is actually lighting something,
because LED forward voltage drifts with temperature and binning, and a resistor
lets brightness and current drift with it.

**PWM or analog dimming?** PWM keeps colour temperature stable and is easy from
an MCU; go above ~1 kHz to avoid visible flicker, and well above that if a
camera will ever point at it. Analog dimming shifts colour temperature but is
flicker-free. Note that low PWM duty does not meaningfully extend LED lifespan.

## Traps

- **No current budget.** The most common cause of "it resets when the LEDs turn on". Brownout, not a firmware bug.
- **Decoupling caps placed "nearby".** The loop area is what matters, not the schematic. Millimetres.
- **Ground pour under an antenna.** Kills range; often discovered after the boards arrive.
- **Assuming the regulator can source peak current.** Check inrush and worst-case simultaneous load, not average.
- **No thermal relief on high-current pads.** Either the part cooks or the pad is impossible to hand-solder.
- **Trusting a recalled pin number.** Pull the datasheet. Always.
- **Designing mains circuitry.** Don't. Specify a certified external adapter or LED driver. This is a T3 boundary, not a preference.

## Tools

Install, licence and tier for every tool named here: `TOOLS.md`.
`just doctor` says which are present on this machine.

**T1 — run freely:**
```bash
kicad-cli sch erc board.kicad_sch --output erc.rpt --exit-code-violations
kicad-cli pcb drc board.kicad_pcb --output drc.rpt --exit-code-violations
kicad-cli pcb export gerbers board.kicad_pcb --output gerbers/
kicad-cli pcb export drill board.kicad_pcb --output gerbers/
kicad-cli pcb export pos board.kicad_pcb --format csv --units mm --output pos.csv
kicad-cli pcb export step board.kicad_pcb --output board.step
kicad-cli sch export bom board.kicad_sch --output bom.csv
ngspice -b sim.cir
```
Also T1: `pcbnew` Python scripting, `kikit` panelization, InteractiveHtmlBom,
Falstad for quick intuition, FreeCAD/OpenSCAD for enclosures, gerbv for
reviewing the actual output files.

**T2 — confirm first:** reading is free, but writing to a bench instrument or
driving a circuit under test (GPIO, I2C/SPI writes) is a device write.

**T3 — never execute:** mains, lithium charging circuits, ordering boards.

Always run ERC and DRC before calling a board finished, and always open the
exported Gerbers in a viewer — the Gerbers are what the fab builds, not the
KiCad file.

## Connections

- Thermal and current budgets feed directly into `manufacturing-dfm` (copper weight, trace width, via count).
- Part choices must be checked for stock and lifecycle in `sourcing-bom` *before* the footprint is committed.
- Pin assignments and bus choices are a contract with `firmware` — freeze them explicitly and write them down.
