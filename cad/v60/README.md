# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_continuous_carrier.py` and `scripts/build_v60_full.py`.

Structural principle: one continuous rack-side carrier. The two rack clamps and the rear stop hang from this carrier; the long box-support holms fuse into the same load path.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes
- `assembly/` — installed-orientation PNG
- `validation/` — machine-readable hard-check reports
- workflow artifact `eurobox-v60-complete` — complete generated FreeCAD assembly and all proof outputs

The complete assembly is deliberately not committed to normal Git: detailed thread geometry can push the generated FCStd above GitHub's 100 MB object limit. Keeping it in the workflow artifact also prevents an old assembly from remaining beside newer STEP/STL outputs.

The production gate verifies the continuous carrier load path, the actual 160 mm box-clamp front with +/-65 mm spindle axes and full-depth support-free DROPs only beside/between rectangular screw blocks, distinct geometrically X-mirrored LEFT/RIGHT STL files, and an explicit matched 12x2 rack-retainer thread pair with final-BRep helix witnesses.
