# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_continuous_carrier.py` and `scripts/build_v60_full.py`.

Structural principle: one continuous rack-side carrier. The two rack clamps and the rear stop hang from this carrier; the long box-support holms fuse into the same load path.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes and removable clamp hardware
- `assembly/` — installed-orientation PNG
- `validation/` — machine-readable hard-check and timing reports
- workflow artifact `eurobox-v60-complete` — complete generated FreeCAD assembly and all proof outputs

The box clamp keeps a 160 mm central clamp face, but its two RH8x2 drive axes are at +/-88 mm, outside that face. Narrow moving ears connect the plate to the spindles. The removable lead-nut cartridge bosses are integrated directly into the two broad outer Y/Z DROPs instead of being stacked between a guide and a separate drop. The BASE remains smooth/non-threaded in the working lead-screw corridor and the hard 600 mm Eurobox envelope remains enforced. The rack closure retains its explicit matched 12x2 service-retainer thread pair.

`validation/TIMING_v60.json` records measured stage/operation durations from the GitHub runner so expensive OCC operations can be optimized from data rather than guesswork.
