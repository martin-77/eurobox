# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_continuous_carrier.py` and `scripts/build_v60_full.py`.

Structural principle: one continuous rack-side carrier. The two rack clamps and the rear stop hang from this carrier; the long box-support holms fuse into the same load path.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes and removable clamp hardware (the rack hand knob is component-owned and published by its fast workflow)
- `assembly/` — installed-orientation PNG
- `validation/` — machine-readable hard-check and timing reports
- workflow artifact `eurobox-v60-complete` — complete generated FreeCAD assembly and all proof outputs

The box clamp uses the v50 direct architecture: the BASE is a smooth housing and the only working RH8x2 female thread is a removable lead-nut cartridge retained by cross-pin and clip. There is no intermediate clamp cassette or later front rebuild. The rack closure uses one final matched 12x3 service-retainer pair. Its complete screw-major envelope must be open at the real BASE surface, and CI inserts the actual retainer from free space before accepting the build.

`validation/TIMING_v60.json` records measured stage/operation durations from the GitHub runner so expensive OCC operations can be optimized from data rather than guesswork.
