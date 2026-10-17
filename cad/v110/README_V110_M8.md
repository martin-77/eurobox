# Eurobox V110 – M8 steel spindle redesign

V110 keeps the proven base/rack geometry but replaces the printed RH8x2 spindle load path with standard M8 steel hardware.

## Design targets

- Standard M8 x 120 full-thread steel screw, coarse M8 x 1.25
- Captured hex head in a new printed hand knob
- New lead-nut carrier using two standard M8 hex nuts in one common pocket
- Existing base geometry remains unchanged
- Existing clamp geometry is retained where possible
- Existing 27.7 mm spindle support concept is retained and adapted to the steel spindle / inner stop nut
- Clamp must remain captive on the screw and move outward when unscrewed, so the Eurobox can be lifted vertically without removing the clamp

## Measured hardware

- M8 nut: 12.79 mm across flats x 6.20 mm high
- M8 screw head: 12.90 mm across flats x 5.50 mm high

## Nut stack concept

Two normal M8 nuts are used instead of a long coupling nut because the available axial depth is about 13 mm.

- two nuts nominal stack: 12.40 mm
- common hex pocket, not two independently phased pockets
- axial clearance is intentional so the two nuts can self-align on the M8 thread rather than being forced into a mismatched phase

## Clamp capture concept

The steel screw must both push and pull the clamp.

Planned axial stack from knob side:

1. captured M8 screw head in printed knob
2. outer clamp bushing
3. clamp
4. inner clamp bushing
5. fixed M8 stop nut on the screw
6. 27.7 mm support sleeve / distance support
7. unchanged base
8. new lead-nut carrier with two M8 nuts

The inner M8 stop nut replaces the former printed spindle shoulder as the pull-out stop when opening the clamp.

## Repository policy

V110 is intended to be self-contained: every printed part actually used by the V110 assembly is copied or regenerated under `cad/v110/` rather than depending on files from older version folders.
