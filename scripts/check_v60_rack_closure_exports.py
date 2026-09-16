import json
import os

import FreeCAD as App
import Mesh

import build_v60 as C
import run_v60_full_ci as R

print('V60_RACK_EXPORT_CHECK start', flush=True)

failures = []
right_stl = os.path.join(C.OUT, 'eurobox_v60_base_right.stl')
left_stl = os.path.join(C.OUT, 'eurobox_v60_base_left.stl')
retainer_stl = os.path.join(C.OUT, 'eurobox_v60_rack_nut_retainer.stl')
knob_stl = os.path.join(C.OUT, 'eurobox_v60_rack_hand_knob.stl')

for path in (right_stl, left_stl, retainer_stl, knob_stl):
    if not os.path.exists(path) or os.path.getsize(path) <= 84:
        failures.append('Missing or empty final rack-closure export: ' + path)

right_hash = R.sha256(right_stl)
left_hash = R.sha256(left_stl)
if right_hash == left_hash:
    failures.append('Final handed base STL files are byte-identical')

rm = Mesh.Mesh(right_stl)
lm = Mesh.Mesh(left_stl)
rbb = rm.BoundBox
lbb = lm.BoundBox
bounds_mirror_ok = (
    R.near(rbb.XMin, -lbb.XMax)
    and R.near(rbb.XMax, -lbb.XMin)
    and R.near(rbb.YMin, lbb.YMin)
    and R.near(rbb.YMax, lbb.YMax)
    and R.near(rbb.ZMin, lbb.ZMin)
    and R.near(rbb.ZMax, lbb.ZMax)
)
right_vertices_mirrored = R.canonical_vertices(rm, mirror_x=True)
left_vertices = R.canonical_vertices(lm)
vertex_mirror_ok = right_vertices_mirrored == left_vertices
right_volume, right_area = R.mesh_geometry_metrics(rm)
left_volume, left_area = R.mesh_geometry_metrics(lm)
volume_delta = abs(right_volume - left_volume)
area_delta = abs(right_area - left_area)
volume_tol = max(0.1, max(right_volume, left_volume) * 1e-7)
area_tol = max(0.1, max(right_area, left_area) * 1e-7)
facet_mirror_ok = rm.CountFacets == lm.CountFacets
geometry_mirror_ok = (
    bounds_mirror_ok
    and vertex_mirror_ok
    and facet_mirror_ok
    and volume_delta <= volume_tol
    and area_delta <= area_tol
)
if not geometry_mirror_ok:
    failures.append(
        'Final rack-closure handed meshes are not exact mirrors: '
        f'bounds={bounds_mirror_ok} vertices={vertex_mirror_ok} facets={facet_mirror_ok} '
        f'volume_delta={volume_delta:.6f}/{volume_tol:.6f} '
        f'area_delta={area_delta:.6f}/{area_tol:.6f}'
    )

# Re-run installed-orientation carrier checks on the final meshes.  The closure
# boss is local, but the production report must describe the published files.
RY = C.RACK_CTC / 2.0
LY = -C.RACK_CTC / 2.0
right_points = [App.Vector(p.x, p.y + RY, p.z) for p in R.mesh_points(rm)]
left_points = [App.Vector(-p.x, -p.y + LY, p.z) for p in R.mesh_points(lm)]
support_checks = []
for station_name, xc in (('front', C.FRONT_CLAMP_X), ('rear', C.REAR_SUPPORT_X)):
    zmin = C.ARM_BOTTOM_Z - 0.25
    zmax = C.ARM_TOP_Z + 0.25
    rpts = [p for p in right_points if abs(p.x - xc) <= 16.5 and zmin <= p.z <= zmax]
    lpts = [p for p in left_points if abs(p.x - xc) <= 16.5 and zmin <= p.z <= zmax]
    if not rpts or not lpts:
        failures.append(f'Final {station_name} carrier mesh slice is empty')
        continue
    rmin = min(p.y for p in rpts); rmax = max(p.y for p in rpts)
    lmin = min(p.y for p in lpts); lmax = max(p.y for p in lpts)
    right_outward = rmax - RY
    right_inward = RY - rmin
    left_outward = LY - lmin
    left_inward = lmax - LY
    support_checks.append({
        'station': station_name,
        'installed_x_mm': xc,
        'right_y_range_mm': [round(rmin, 3), round(rmax, 3)],
        'left_y_range_mm': [round(lmin, 3), round(lmax, 3)],
        'right_outward_extent_mm': round(right_outward, 3),
        'right_inward_extent_mm': round(right_inward, 3),
        'left_outward_extent_mm': round(left_outward, 3),
        'left_inward_extent_mm': round(left_inward, 3),
    })
    if right_outward < 210.0:
        failures.append(f'Final RIGHT {station_name} outward extent too small: {right_outward:.3f}')
    if left_outward < 210.0:
        failures.append(f'Final LEFT {station_name} outward extent too small: {left_outward:.3f}')
    if right_inward > 30.0:
        failures.append(f'Final RIGHT {station_name} inward extent too large: {right_inward:.3f}')
    if left_inward > 30.0:
        failures.append(f'Final LEFT {station_name} inward extent too large: {left_inward:.3f}')

# Simple printable-part mesh sanity gates.
for label, path in (('retainer', retainer_stl), ('rack hand knob', knob_stl)):
    mesh = Mesh.Mesh(path)
    if mesh.CountFacets < 50:
        failures.append(f'Final {label} mesh suspiciously small: {mesh.CountFacets} facets')

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as f:
    validation = json.load(f)

validation['handed_stl_export'] = {
    'right_sha256': right_hash,
    'left_sha256': left_hash,
    'byte_distinct': right_hash != left_hash,
    'mirror_geometry_ok': geometry_mirror_ok,
    'mirror_bounds_ok': bounds_mirror_ok,
    'mirror_vertex_set_ok': vertex_mirror_ok,
    'mirror_facet_count_ok': facet_mirror_ok,
    'left_stl_generation': 'exact binary STL X-mirror of final revised RIGHT print triangle mesh',
    'right_bbox_mm': [round(v, 3) for v in R.bbox_tuple(rbb)],
    'left_bbox_mm': [round(v, 3) for v in R.bbox_tuple(lbb)],
    'right_facets': rm.CountFacets,
    'left_facets': lm.CountFacets,
    'right_volume_mm3': round(right_volume, 6),
    'left_volume_mm3': round(left_volume, 6),
    'volume_delta_mm3': round(volume_delta, 6),
    'right_area_mm2': round(right_area, 6),
    'left_area_mm2': round(left_area, 6),
    'area_delta_mm2': round(area_delta, 6),
}
validation['installed_support_orientation'] = {
    'right_rack_center_y_mm': RY,
    'left_rack_center_y_mm': LY,
    'required_orientation': 'RIGHT carriers +Y outward; LEFT carriers -Y outward',
    'minimum_outward_extent_mm': 210.0,
    'maximum_inward_extent_mm': 30.0,
    'checks': support_checks,
}
validation['final_rack_closure_exports'] = {
    'retainer_stl': os.path.basename(retainer_stl),
    'rack_hand_knob_stl': os.path.basename(knob_stl),
    'checked_after_final_reexport': True,
}
if failures:
    validation['failures'].extend(failures)
with open(validation_path, 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2)

if failures:
    print(json.dumps(validation, indent=2), flush=True)
    raise SystemExit('V60 FINAL RACK EXPORT CHECKS FAILED: ' + ' | '.join(failures))

print('V60_RACK_EXPORT_CHECK final meshes and rack closure exports OK', flush=True)
