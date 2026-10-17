# Eurobox carrier V110 – M8 steel spindle

V110 replaces the printed box-clamp lead screws with standard M8 steel hardware while keeping the proven frozen V60 base/rack geometry. The box is still removed vertically: the clamp remains captive on the steel spindle and is pulled outward when the screw is opened.

## Hardware per spindle

- 1x M8 x 120 mm full-thread screw, DIN 933 / ISO 4017, coarse M8 x 1.25
- 2x standard M8 hex nuts in the removable lead-nut carrier
- 1x standard M8 hex nut as the inner clamp stop; secure its adjusted position with medium threadlocker

Measured hardware used for the CAD:

- M8 nut: 12.79 mm across flats x 6.20 mm high
- M8 screw head: 12.90 mm across flats x 5.50 mm high

## Box-clamp stack

From the hand-knob side toward the base:

1. V110 knob with captured M8 hex head
2. outer V110 rotating bushing half
3. V110 clamp (proven V70/V6 geometry)
4. inner V110 rotating bushing half
5. fixed M8 stop nut
6. V110 27.7 mm support sleeve
7. unchanged V60 base
8. V110 removable lead-nut carrier with two M8 nuts

The stop nut replaces the former printed spindle shoulder. It lets the steel screw pull the clamp outward during opening instead of merely moving out of the lead nut.

## Lead-nut carrier

The carrier keeps the proven V60 external cartridge and retaining-pin geometry so the existing base does not need to be reprinted.

Two measured 6.20 mm nuts form a 12.40 mm stack. They share one 13.15 mm-AF hex pocket with 12.75 mm axial length. The resulting 0.35 mm axial freedom is deliberate: the two independent nut threads can phase-align on the M8 screw instead of being clamped rigidly against one another.

The hex pocket opens through the rear face of the removable carrier. Once installed, the existing base pocket closes that face. High closing thrust therefore transfers from the rear steel nut directly into the base wall rather than through a thin printed end wall. A 1.25 mm front lip only retains the nut stack during clamp opening.

## Bushing and support

The proven V70/V5 two-half bushing geometry is retained, with these M8 changes:

- running bore: Ø8.80 mm
- outer thrust face: flat; the old printed-spindle centering recess is removed
- two halves still provide the intended small axial freedom in the 12 mm clamp bearing stack

The 27.70 mm support keeps the proven 30 x 30 mm end pads and Ø20 mm body. Its clamp-side cavity is stepped:

- Ø18.50 x 1.10 mm to clear the rotating bushing collar
- Ø15.40 out to 7.55 mm from the clamp face to clear the 12.79-AF x 6.20 mm stop nut
- Ø8.90 running bore through the remaining support

Fit check for the measured stop nut:

- a regular 12.79 mm-AF hex has about 14.77 mm across corners
- Ø15.40 relief leaves about 0.63 mm diametral / 0.315 mm radial clearance
- bushing-collar projection 0.85 mm + nut height 6.20 mm = 7.05 mm
- 7.55 mm cavity depth therefore leaves 0.50 mm axial freedom
- the nut ends about 20.65 mm before the base end of the 27.70 mm support, so it cannot reach the frozen Ø11.8 base spindle corridor
- the Ø20 support body retains about 2.30 mm radial wall around the Ø15.40 nut cavity, in addition to the 30 x 30 clamp-side pad

This lets the stop nut sit inside the existing 27.7 mm clamp-to-base distance rather than adding 6.2 mm to the assembly length.

## Knob

The proven scalloped ~Ø30 mm grip is retained. The printed RH8x2 thread is deleted.

- M8 head pocket: 13.18 mm AF
- head-pocket height: 5.70 mm
- M8 shank clearance: Ø8.70 mm
- Ø16.0 x 0.8 mm clamp-facing nose bears only on the rotating bushing collar
- separate press cap retains the screw head during handling; it is not in the structural load path

## Reused printed parts

V110 is intended to be self-contained. The canonical V110 STL set also contains the frozen V60 base/rack parts and the proven retaining hardware required by this assembly. They are copied into `cad/v110/STL/` by the V110 build workflow.

There is no printed V110 lead screw. `eurobox_v110_lead_screw.stl` is explicitly removed by the build gate.

All generated STL files are binary STL and are validated as watertight, single-component meshes before publication.
