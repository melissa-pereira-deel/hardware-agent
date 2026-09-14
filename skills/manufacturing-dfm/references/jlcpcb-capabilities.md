# JLCPCB capability rules

Check a design against these before claiming it is manufacturable. Verify against JLCPCB's current published capabilities before ordering - these change.

## Trace and space

| Board type | Minimum trace / space |
|---|---|
| 1-2 layer, 1 oz copper | 5 mil (0.127 mm) |
| Multilayer | 3.5 mil (0.0889 mm) |

Heavier copper requires wider traces and spaces. Design with margin above the minimum wherever routing allows - minimums have lower yield.

## Vias

- Minimum via hole: **0.15 mm**
- Must be paired with at least a **0.15 mm annular ring**
- Via-in-pad requires filling/capping - a paid option, not a default

## General

- Minimum solder-mask dam: ~0.2 mm
- Board outline on **Edge.Cuts only**, closed, single contour
- Silkscreen must not overlap pads
- Panelize below ~70x70 mm for assembly; leave rails, tooling holes, fiducials

## Assembly

- **Basic parts**: already loaded, no per-part setup fee
- **Extended parts**: per-unique-part-number setup fee - count these and report the total
- Check nozzle clearance around tall components
- Provide a pick-and-place CSV with correct origin, units (mm) and rotations
- Rotation conventions differ between KiCad and JLCPCB - verify against the assembly preview, this is a common source of reversed parts

## Pre-order gate

Run against every board:

```bash
kicad-cli sch erc board.kicad_sch --exit-code-violations
kicad-cli pcb drc board.kicad_pcb --exit-code-violations
```

Zero violations, not "only warnings". Then export Gerbers and **open them in a viewer** - the Gerbers are what gets built.
