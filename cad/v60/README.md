# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_continuous_carrier.py` and `scripts/build_v60_full.py`.

Structural principle: one continuous rack-side carrier. The two rack clamps and the rear stop hang from this carrier; the long box-support holms fuse into the same load path.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes
- `assembly/` — complete FreeCAD assembly plus installed-orientation PNG
- `validation/` — machine-readable hard-check reports

The production gate verifies the continuous carrier load path, distinct geometrically X-mirrored LEFT/RIGHT STL files and outward carrier orientation on both installed sides.
