# Eurobox carrier V120 – frozen M8 steel-spindle set

V120 is the self-contained production package for the validated M8 steel-spindle box clamp. It promotes the working V110 geometry without changing the frozen base/rack interfaces and collects every printed part needed for the assembly under one version.

## Hardware per box-clamp spindle

- 1x M8 x 120 mm full-thread steel screw, DIN 933 / ISO 4017, coarse M8 x 1.25
- 2x standard M8 hex nuts in the removable lead-nut carrier
- 1x standard M8 hex nut as the inner clamp stop; secure its adjusted position with medium threadlocker

CAD was sized from measured hardware:

- M8 nut: 12.79 mm across flats x 6.20 mm high
- M8 screw head: 12.90 mm across flats x 5.50 mm high

## Box-clamp stack

From the hand-knob side toward the base:

1. V120 knob with captured M8 hex head
2. outer V120 rotating bushing half
3. V120 clamp
4. inner V120 rotating bushing half
5. fixed M8 stop nut
6. V120 27.7 mm support sleeve
7. frozen base
8. V120 removable lead-nut carrier with two M8 nuts

The stop nut replaces the former printed spindle shoulder and pulls the clamp outward when opening.

## Critical fits

Lead-nut carrier:
- two 6.20 mm nuts = 12.40 mm stack
- common pocket length = 12.75 mm
- intentional axial phase/alignment freedom = 0.35 mm
- pocket = 13.15 mm AF

Support sleeve:
- overall length = 27.70 mm
- end pads = 30 x 30 mm
- body = Ø20 mm
- bushing-collar relief = Ø18.50 x 1.10 mm
- stop-nut relief = Ø15.40 to 7.55 mm from clamp face
- running bore = Ø8.90 mm
- measured M8 nut corner diameter ≈ 14.77 mm, leaving ≈ 0.63 mm diametral clearance
- bushing collar + 6.20 mm stop nut use 7.05 mm of the 7.55 mm cavity, leaving 0.50 mm axial clearance
- stop nut ends about 20.65 mm before the base-side end of the support, clear of the frozen Ø11.8 mm base spindle corridor

Knob:
- M8 head pocket = 13.18 mm AF
- head-pocket height = 5.70 mm
- shank clearance = Ø8.70 mm
- separate cap only retains the screw head during handling and is not in the structural load path

Bushing:
- running bore = Ø8.80 mm
- two halves retain the established small axial freedom in the clamp bearing stack

## Canonical V120 printed set

`cad/v120/STL/` is the print set. It contains:

- base left / right
- clamp
- 2x bushing half per spindle
- knob + knob cap
- removable M8 lead-nut carrier
- 27.7 mm spindle support sleeve
- lead-nut retaining pin + clip
- rack lower
- rack hand knob
- rack nut retainer
- rack nut retainer left-hand variant
- rack pin + clip

There is intentionally **no printed lead screw** in V120. The spindle is the M8 x 120 steel screw.

## Source/CAD policy

The new M8-specific printable parts are maintained as OpenSCAD under `cad/v120/SCAD/`. Frozen base/rack parts keep their available FCStd/STEP source copies under `cad/v120/FCStd/` and `cad/v120/STEP/`. We do not carry stale pre-M8 FCStd/STEP files for the clamp, lead nut, knob or bushing under V120.

The V120 build workflow regenerates the OpenSCAD-derived binary STLs, copies the frozen base/rack production meshes, preserves the left-hand rack retainer, and validates generated meshes plus critical dimensions before committing output.
