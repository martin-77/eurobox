# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_continuous_carrier.py` and `scripts/build_v60_full.py`.

Structural principle: one continuous rack-side carrier. The two rack clamps and the rear stop hang from this carrier; the long box-support holms fuse into the same load path.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes and removable clamp hardware
- `assembly/` — installed-orientation PNG
- `validation/` — machine-readable hard-check reports
- workflow artifact `eurobox-v60-complete` — complete generated FreeCAD assembly and all proof outputs

The complete assembly is deliberately not committed to normal Git: detailed thread geometry can push the generated FCStd above GitHub's 100 MB object limit. Keeping it in the workflow artifact also prevents an old assembly from remaining beside newer STEP/STL outputs.

The box clamp restores the proven v50 function: a 160 mm moving plate on two +/-65 mm RH8x2 spindles, separate removable threaded lead-nut cartridges retained by cross-pins and C-clips, a smooth/non-threaded BASE, and two outer Y/Z support DROPs instead of the rejected row of triangular front teeth. The hard 600 mm Eurobox envelope remains enforced. The rack closure retains its explicit matched 12x2 service-retainer thread pair with final-BRep helix witnesses.
