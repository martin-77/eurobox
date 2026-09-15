# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py` and `scripts/build_v60_full.py`.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes
- `assembly/` — complete FreeCAD assembly plus installed-orientation PNG
- `validation/` — machine-readable hard-check reports

The production gate verifies that LEFT/RIGHT STL files are distinct geometrically X-mirrored exports and that, in installed orientation, both longitudinal carrier stations project outward from the rack: RIGHT toward +Y and LEFT toward -Y.
