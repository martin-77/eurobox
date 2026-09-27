# Eurobox V70 – integrated lead screw

V70 replaces the former separate knob / short retainer thread / plate clip stack
with one integrated lead screw plus one conical RH8x2 retainer nut.

## Changed parts

- `eurobox_v70_lead_screw_integrated`
  - integrated scalloped Ø30 x 7 mm grip
  - Ø13 x 2 mm outer thrust flange
  - Ø8.0 smooth journal
  - Ø8.4 x 0.8 mm pass-through hard-stop collar
  - unchanged RH8x2 working thread: core Ø6.5, major Ø8.0, pitch 2.0, length 24.0 mm

- `eurobox_v70_conical_retainer_nut`
  - same RH8x2 female geometry as the proven lead nut
  - Ø10.0 conical tip
  - Ø11.0 maximum outer diameter
  - two flats, 10.6 mm across flats
  - 5.4 mm total height

- `eurobox_v70_clamp_plate`
  - final V60 plate outline and hook retained
  - spindle bores changed to Ø8.8
  - former C-clip counterbores and service slots removed

## Fit budget

- Ø8.4 stop collar through Ø8.8 plate bore: 0.20 mm radial clearance
- Ø8.0 journal in Ø8.8 plate bore: 0.40 mm radial clearance
- retainer Ø10.0 tip over Ø8.8 bore: 0.60 mm radial capture
- retainer max Ø11.0 inside frozen BASE Ø11.8 spindle corridor: 0.40 mm radial clearance
- clamp axial play between flange and seated retainer: 0.15 mm
- inner clamp face to lead-nut front face: 7.8 mm
- retainer height: 5.4 mm
- nominal remaining gap before lead nut: 2.4 mm
- working-thread end from the outer clamp face: 32.15 mm
- former V60 working-thread end from the outer clamp face: 32.0 mm

## Frozen / reused V60 parts

The final V60 `base_left`, `base_right`, `rack_lower` and `lead_nut`
stay unchanged. The long RH8x2 working thread is deliberately kept on the
proven dimensions.

The old separate `knob`, `knob_retainer_nut` and `plate_retainer_clip`
are not used by the V70 box-clamp mechanism.


## Clamp v2 prototype

`eurobox_v70_clamp_v2` is the first full-width stepped clamp proposal based
on the measured underside geometry of the box:

- width: 187.30 mm
- total height: 88.57 mm
- screw axis: 15.00 mm above clamp bottom
- box underside: 30.00 mm above clamp bottom
- top of box protrusion: 63.57 mm above clamp bottom
- upper wall press height: 25.00 mm
- press-plane offset between protrusion and upper box wall: 18.50 mm
- V70 screw bores remain Ø8.80 mm at X=15.00 / 172.30 mm

The v2 STL is deliberately a robust fit prototype: the upper stepped block is
solid. Once the real box contact on both press planes is confirmed, the upper
section can be lightened without changing the contact geometry.


## Clamp / lead screw v3 prototype

V3 is an experimental redesign of the complete box-clamp spindle assembly. It
does not replace the frozen V60 base or lead nut.

### Clamp v3

- width: 187.30 mm
- total height: 88.57 mm
- screw axis remains 15.00 mm above clamp bottom
- box underside is 30.00 mm above clamp bottom
- nominal protrusion starts at 46.45 mm and ends at 63.57 mm
- protrusion pocket is 46.20..63.82 mm, giving 0.50 mm total vertical clearance
- lower contact is the primary clamp zone and projects to Z=27.00 mm
- upper 25 mm zone is secondary/stabilising and projects to Z=26.50 mm
- primary lower contact therefore reaches 0.50 mm farther toward the box
- the protrusion itself is recessed to the 8.00 mm backbone plane
- screw zone is reinforced to 10.00 mm thickness
- two 20 mm rear ribs connect the upper section to the screw stations
- spindle bores are Ø10.40 for rotating bushings

### Rotating bushing

One bushing is required for each spindle:

- body Ø10.00
- bore Ø8.35 for the Ø8.00 screw journal
- body length 10.25 mm
- clamp bearing thickness 10.00 mm
- resulting nominal axial freedom: 0.25 mm
- outer flange Ø14.00 x 2.00 mm

The screw shoulder and removable knob clamp the rotating bushing, not the
stationary clamp. This removes the previous conical retainer from the v3
prototype.

### Lead screw v3

From knob side toward the frozen lead nut:

- RH8x2 knob thread: 8.50 mm
- smooth Ø8.00 journal: 10.25 mm
- Ø10.80 x 2.00 mm shoulder
- RH8x2 working thread: 74.00 mm

The Ø10.80 shoulder remains inside the frozen Ø11.80 base spindle corridor
with 0.50 mm radial clearance. The working thread is the previous 24 mm plus
50 mm reserve so the spindle can remain engaged in the lead nut when the box
is removed.

### Knob v3

- separate scalloped Ø30 x 8 mm knob
- through female RH8x2 thread
- tightens against the rotating bushing flange

The screw-on knob is deliberately still a prototype. Its resistance to
self-loosening during repeated opening/closing must be checked physically
before this mechanism is treated as final.

### Binary STL build

Generate slicer-ready binary STLs explicitly; do not rely on GitHub text-file
serialization for STL output:

```sh
openscad --export-format binstl -o part.stl part.scad
```

All four locally rendered v3 meshes were checked as watertight, single-component
meshes before physical fit testing.


### GitHub binary STL validation

The v3 STLs committed in `cad/v70/STL/` are the exact locally validated
binary STL bytes. They were uploaded through the Git data API as base64 blobs
and then fetched again from the committed HEAD. Blob SHA and decoded byte
length matched the local files for all four parts:

- clamp v3: 42,684 bytes, blob `bc0a0dca49e2f693a67b32e8e2679b6cde894270`
- bushing v3: 76,884 bytes, blob `e368758d39aa2bbb31d311a99fd203082cdcaa78`
- lead screw v3: 717,384 bytes, blob `5c673d0054a5cbcd1952ab5690385c58cdc542ec`
- knob v3: 182,884 bytes, blob `49d15064ebe642e44e67df830a803bc18cfbb9c3`

This avoids the previous UTF-8 / ASCII STL serialization path.
