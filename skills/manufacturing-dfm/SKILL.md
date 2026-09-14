---
name: manufacturing-dfm
description: Get a design from "works on my bench" to something a factory can actually build — design for manufacture and assembly, fab capability rules, panelization, test points and bring-up fixtures, Gerber and assembly-file handoff to JLCPCB or PCBWay, 3D printed enclosures and slicing, and certification strategy including ANATEL homologation for Brazil, CE, FCC, RoHS and Matter. Use this skill before any board is ordered, whenever someone asks "can this be made?", "what will this cost to build?", "do we need certification?", "can we sell this in Brazil?", or "is this legal to ship?" — and whenever a Wi-Fi, BLE, Zigbee or Thread radio, a fab house, an enclosure, a panel, homologation, or selling a product in any specific country comes up.
---

# Manufacturing & DFM

## Concepts

**DFM is writing code your build system can compile.** *Analogy: a pick-and-
place machine is a CI runner with very specific opinions, and it charges you
per awkward part.* The design isn't done when it works; it's done when a
factory can build it repeatably without asking questions.

**Certification is an architecture decision made early, not paperwork done
late.** For Brazil this is sharp: Wi-Fi, BLE and Zigbee devices are classed as
restricted-radiation radiocommunication equipment and require ANATEL approval
*before importation or sale*. Foreign FCC or CE test reports are **not**
accepted — testing must happen at a lab accredited by ANATEL, and the applicant
must be a Brazilian legal entity with a valid CNPJ. Using a **pre-homologated
module** rather than a bare chip is the single largest scope reduction
available. Read `references/anatel-homologation.md` before committing to a
radio.

**Panelization is about the assembly service's minimum board size, and the
rule runs backwards from intuition.** 70 × 70 mm is a *minimum*, not a maximum —
and it applies only to JLCPCB's Standard PCBA. Economic PCBA accepts boards down
to 10 × 10 mm as-is, which for small-batch work usually means no panelization at
all. Check which service you're quoting before doing the work. `kikit` generates
panels with mouse-bites or V-cuts from KiCad files; leave rails, tooling holes
and fiducials. Details in `references/jlcpcb-capabilities.md`.

**Design for test, or debug every unit by hand.** Test points on every rail,
on reset, on boot-mode pins, and on any bus you'd want to probe. Pogo-pin
friendly pads cost nothing at design time and save hours per batch.

## Decisions

**Hand assembly or JLCPCB assembly?** Under ~10 boards with forgiving packages,
hand assembly is faster and cheaper. Anything with a QFN, a fine-pitch part, or
more than about 20 unique parts should go to assembly.

**Two-layer or four-layer at the fab?** Four-layer is now cheap enough that the
ground-plane benefit usually beats the cost delta for anything with a radio.

**Pre-homologated module or own homologation?** For Brazil, own homologation
means an accredited local lab, a CNPJ-holding applicant, and real cost and
time. A module with an existing ANATEL homologation shifts most of that burden.
Default to the module unless volume genuinely justifies otherwise.

**Certification markets.** Decide markets before layout. Brazil-only is ANATEL.
Add the EU and you add CE/RED. Add Matter and you add the CSA process — Vendor
ID, authorised test lab, DCL listing — on top of the radio certification.

## Traps

- **Sending the KiCad file instead of the Gerbers.** The fab builds the Gerbers. Open them in a viewer first.
- **Trace widths below the fab's capability.** Don't recall these — they change and they are layer-count dependent. Read `references/jlcpcb-capabilities.md`, which carries the current figures with the date they were checked.
- **No fiducials or tooling holes.** The assembler will ask, and you'll lose a week.
- **Assuming a 3D-printed enclosure handles the heat.** Design against PLA's heat-deflection temperature (~53 °C), not its glass transition (60–65 °C) — HDT is the lower number and the one a loaded part creeps at. A sealed PLA enclosure with an 18 W/m strip inside will exceed it. Fire risk, not a warranty footnote.
- **Claiming compliance.** Never state a product is FCC/CE/ANATEL compliant. State what the path is and who certifies it.
- **Changing antenna geometry or RF settings after homologation.** It invalidates the certificate.

## Tools

**T1 — run freely:**
```bash
kicad-cli pcb export gerbers board.kicad_pcb --output fab/
kicad-cli pcb export drill board.kicad_pcb --output fab/
kicad-cli pcb export pos board.kicad_pcb --format csv --units mm --output fab/cpl.csv
kikit panelize --layout 'grid; rows: 2; cols: 3' ... board.kicad_pcb panel.kicad_pcb
orcaslicer --slice 0 --load-settings profile.ini --outputdir out/ part.stl
prusa-slicer-console --export-gcode --load profile.ini part.stl
```
Gerber review with gerbv or KiCad's viewer. Generating the fab package,
checking it against capability rules, and producing the quote are all T1.

**T3 — prepare and stop:**
- Placing the PCB or assembly order (money).
- Sending a job to a 3D printer, CNC or laser (motion).
- Any statement of regulatory compliance.

## Fab handoff checklist

1. ERC and DRC pass with zero violations (not "only warnings").
2. DRC run against the *fab's* rule set, not KiCad defaults.
3. Gerbers and drill files exported and **opened in a viewer**.
4. Pick-and-place CSV with correct origin, units and rotations.
5. BOM with LCSC part numbers if using JLCPCB assembly; extended parts counted.
6. Fiducials, tooling holes, panel rails if panelized.
7. Silkscreen legible, not overlapping pads, polarity marks present.
8. Board outline on Edge.Cuts only, closed, single contour.
9. A written note of what changed since the last revision.

## Connections

- Trace widths, copper weight and via counts come from the current and thermal budgets in `circuit-design`.
- Basic/extended part status and assembly cost: `../sourcing-bom/references/lcsc-jlcpcb-parts.md`, shared with `sourcing-bom`.
- Secure boot and factory provisioning straddle this skill and `firmware`.
