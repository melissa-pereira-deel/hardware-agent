# JLCPCB capability rules

Check a design against these before claiming it is manufacturable.

**These change.** Everything below was read off JLCPCB's published capabilities
pages on **2026-09-14** (links at the bottom). Re-read them before you order —
that is a two-minute check against a several-hundred-real mistake.

## Trace and space

| Board type (1 oz copper) | Min. track width / spacing |
|---|---|
| 1–2 layer | **0.10 / 0.10 mm (4 / 4 mil)** |
| Multilayer (4+) | **0.09 / 0.09 mm (3.5 / 3.5 mil)** — 3 mil accepted in BGA fan-outs |

Heavier copper requires wider traces and spaces. Design with margin above the
minimum wherever routing allows; minimums have lower yield.

> Corrected 2026-09-14. This file previously said 5 mil (0.127 mm) for 1–2
> layer, which was outdated and over-conservative by a full mil.

## Drills, vias and annular rings

| | 1 layer | 2+ layers |
|---|---|---|
| Drill diameter range | 0.3 – 6.3 mm | **0.15** – 6.3 mm |
| Min. via | 0.3 mm hole / 0.5 mm diameter | **0.15 mm hole / 0.25 mm diameter** |

The 0.15 mm drill is explicitly flagged by JLCPCB as **"more costly"**. It is
available, not free. Use 0.3 mm vias unless density genuinely forces smaller.

**Annular rings.** JLCPCB publishes **PTH annular ring ≥ 0.20 mm** and **NPTH
pad annular ring ≥ 0.45 mm**, while also publishing a minimum via of 0.15 mm
hole in a 0.25 mm pad — which is 0.05 mm of ring per side. Those two figures
describe different classes of hole (component through-holes versus vias) and
JLCPCB does not spell out the boundary. **Do not resolve this from memory:
check the DRC profile for your specific order type.**

> Corrected 2026-09-14. This file previously asserted a flat "0.15 mm annular
> ring" minimum, which matches neither published figure and was wrong in the
> direction that makes a non-compliant board look compliant.

## Solder mask

Min. pad spacing for a mask dam: **0.10 mm at 1 oz**, **0.20 mm at 2 oz**
(standard mask colours).

## General

- Board outline on **Edge.Cuts only**, closed, single contour
- Silkscreen must not overlap pads
- Provide a pick-and-place CSV with correct origin, units (mm) and rotations
- **Rotation conventions differ between KiCad and JLCPCB.** Verify against the
  assembly preview. This is the most common source of reversed parts.

## Assembly: board size and panelization

This is the rule most often stated backwards, including in earlier versions of
this file. It runs the opposite way to intuition:

| Service | Min. single board | Panelized range |
|---|---|---|
| **Economic PCBA** | **10 × 10 mm** | 10 × 10 – 250 × 250 mm |
| **Standard PCBA** | **70 × 70 mm** | 70 × 70 – 250 × 250 mm |

**70 × 70 mm is a *minimum*, not a maximum.** A board smaller than that must be
panelized or given process edges to *reach* 70 × 70 — but only if you are using
Standard PCBA. Economic PCBA takes boards down to 10 × 10 mm as-is.

For a small-batch product, Economic is usually the service you want, and a
small board may need no panelization at all. Check which service you are
quoting before doing panelization work you don't need.

Other panelization facts:

- Panelization **recommended** below 50 × 50 mm, **mandatory** below 10 × 10 mm
- **V-cut requires a panel of at least 70 × 70 mm**
- Economic PCBA: mouse-bites only. Standard PCBA: mouse-bites or V-cut
- Leave rails, tooling holes and fiducials

## Parts

Basic vs extended part selection, setup fees and the LCSC library live in
`../../sourcing-bom/references/lcsc-jlcpcb-parts.md` — one file, because it is
simultaneously a sourcing decision and an assembly cost line.

## Pre-order gate

Run against every board:

```bash
kicad-cli sch erc board.kicad_sch --exit-code-violations
kicad-cli pcb drc board.kicad_pcb --exit-code-violations
```

Zero violations, not "only warnings". Run DRC against the **fab's** rule set,
not KiCad defaults. Then export Gerbers and **open them in a viewer** — the
Gerbers are what gets built.

---

## Sources

All `trust: high` (vendor-published), all checked **2026-09-14**:

- [PCB manufacturing capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) — trace/space, drills, vias, annular rings, solder mask
- [PCB assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) — Economic vs Standard board sizes
- [Panelizing your PCB for assembly](https://jlcpcb.com/help/article/panelizing-your-pcb-for-assembly)
- [PCB dimensions](https://jlcpcb.com/help/article/pcb-dimensions)
