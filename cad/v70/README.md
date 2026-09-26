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
