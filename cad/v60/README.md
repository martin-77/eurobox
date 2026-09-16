# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_core_final.py` and `scripts/build_v60_full.py`.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes
- `assembly/` — complete FreeCAD assembly plus installed-orientation PNG
- `validation/` — machine-readable hard-check reports

The production gate verifies closed clamp-root/wall joints, a closed rectangular backstop-to-rear-support load path, distinct geometrically X-mirrored LEFT/RIGHT STL files and outward carrier orientation on both installed sides.
