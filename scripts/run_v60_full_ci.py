import hashlib
import json
import os
import sys

import FreeCAD as App
import Mesh
import MeshPart

sys.path.insert(0, 'scripts')
import build_v60 as C

_original_require_single = C.require_single


def traced_require_single(shape, label):
    print(f'V60_CHECKPOINT require_single START {label}', flush=True)
    print(
        f'V60_CHECKPOINT shape {label}: null={shape.isNull()} '
        f'valid={shape.isValid()} solids={len(shape.Solids)}',
        flush=True,
    )
    result = _original_require_single(shape, label)
    print(f'V60_CHECKPOINT require_single OK {label}', flush=True)
    return result


C.require_single = traced_require_single

# Keep the already-proven OCC handed construction for STEP/FCStd and its exact
# construction-mirror gate.  The old problem is specifically that OCC's mirrored
# location was discarded by STL tessellation.  Therefore the printable LEFT STL
# is made as an explicit coordinate mirror of the tessellated RIGHT print mesh.
_base_right_mesh_topology = None


def mirrored_mesh_x(mesh):
    points, facets = mesh.Topology
    mirrored_points = [App.Vector(-p.x, p.y, p.z) for p in points]
    # Reflection reverses handedness; reverse triangle winding so the STL keeps
    # outward normals/manifold orientation.
    mirrored_facets = [(f[0], f[2], f[1]) for f in facets]
    return Mesh.Mesh((mirrored_points, mirrored_facets))


def direct_export_shape(name, sh):
    global _base_right_mesh_topology
    C.require_single(sh, name + ' export source')
    step_path = os.path.join(C.OUT, name + '.step')
    fcstd_path = os.path.join(C.OUT, name + '.FCStd')
    stl_path = os.path.join(C.OUT, name + '.stl')

    sh.exportStep(step_path)
    doc = App.newDocument('export_' + name)
    obj = doc.addObject('Part::Feature', name)
    obj.Shape = sh.copy()
    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc.Name)

    if name == 'eurobox_v60_base_left':
        if _base_right_mesh_topology is None:
            raise RuntimeError('LEFT base export occurred before RIGHT mesh reference')
        right_ref = Mesh.Mesh(_base_right_mesh_topology)
        mesh = mirrored_mesh_x(right_ref)
    else:
        mesh = MeshPart.meshFromShape(
            Shape=sh,
            LinearDeflection=0.08,
            AngularDeflection=0.25,
            Relative=False,
        )
        if name == 'eurobox_v60_base_right':
            _base_right_mesh_topology = mesh.Topology

    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ': direct STL tessellation produced no facets')
    mesh.write(stl_path)


C.export_shape = direct_export_shape

print('V60_CHECKPOINT core import complete', flush=True)
import build_v60_full as F
print('V60_CHECKPOINT full module complete', flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def bbox_tuple(bb):
    return (
        bb.XMin, bb.XMax,
        bb.YMin, bb.YMax,
        bb.ZMin, bb.ZMax,
    )


def near(a, b, tol=0.12):
    return abs(a - b) <= tol


def mesh_points(mesh):
    points, _facets = mesh.Topology
    return points


extra_failures = []
right_stl = os.path.join(C.OUT, 'eurobox_v60_base_right.stl')
left_stl = os.path.join(C.OUT, 'eurobox_v60_base_left.stl')
right_hash = sha256(right_stl)
left_hash = sha256(left_stl)
if right_hash == left_hash:
    extra_failures.append('Handed base STL files are byte-identical')

rm = Mesh.Mesh(right_stl)
lm = Mesh.Mesh(left_stl)
rbb = rm.BoundBox
lbb = lm.BoundBox
mesh_mirror_ok = (
    near(rbb.XMin, -lbb.XMax)
    and near(rbb.XMax, -lbb.XMin)
    and near(rbb.YMin, lbb.YMin)
    and near(rbb.YMax, lbb.YMax)
    and near(rbb.ZMin, lbb.ZMin)
    and near(rbb.ZMax, lbb.ZMax)
    and rm.CountFacets == lm.CountFacets
)
if not mesh_mirror_ok:
    extra_failures.append(
        'Handed base STL bounds/facet count are not an X-mirrored pair: '
        f'R={bbox_tuple(rbb)} L={bbox_tuple(lbb)} '
        f'facets={rm.CountFacets}/{lm.CountFacets}'
    )

# Validate the meshes exactly as they are installed. RIGHT is translated onto
# the +Y rack tube. LEFT is the handed print mesh rotated 180 deg about Z and
# translated onto the -Y rack tube. At both long-carrier X stations, material
# must reach >210 mm outward from its tube while no long carrier may project
# more than 30 mm inward of that tube.
RY = C.RACK_CTC / 2.0
LY = -C.RACK_CTC / 2.0
right_installed_points = [
    App.Vector(p.x, p.y + RY, p.z) for p in mesh_points(rm)
]
left_installed_points = [
    App.Vector(-p.x, -p.y + LY, p.z) for p in mesh_points(lm)
]

support_checks = []
for station_name, xc in (
    ('front', C.FRONT_CLAMP_X),
    ('rear', C.REAR_SUPPORT_X),
):
    zmin = C.ARM_BOTTOM_Z - 0.25
    zmax = C.ARM_TOP_Z + 0.25
    rpts = [
        p for p in right_installed_points
        if abs(p.x - xc) <= 16.5 and zmin <= p.z <= zmax
    ]
    lpts = [
        p for p in left_installed_points
        if abs(p.x - xc) <= 16.5 and zmin <= p.z <= zmax
    ]
    if not rpts or not lpts:
        extra_failures.append(f'{station_name} carrier mesh slice is empty')
        continue

    rmin = min(p.y for p in rpts)
    rmax = max(p.y for p in rpts)
    lmin = min(p.y for p in lpts)
    lmax = max(p.y for p in lpts)
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
        extra_failures.append(
            f'RIGHT {station_name} carrier does not extend outward +Y far enough: '
            f'{right_outward:.3f} mm'
        )
    if left_outward < 210.0:
        extra_failures.append(
            f'LEFT {station_name} carrier does not extend outward -Y far enough: '
            f'{left_outward:.3f} mm'
        )
    if right_inward > 30.0:
        extra_failures.append(
            f'RIGHT {station_name} has a long inward carrier: {right_inward:.3f} mm'
        )
    if left_inward > 30.0:
        extra_failures.append(
            f'LEFT {station_name} has a long inward carrier: {left_inward:.3f} mm'
        )

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as f:
    validation = json.load(f)
validation['handed_stl_export'] = {
    'right_sha256': right_hash,
    'left_sha256': left_hash,
    'byte_distinct': right_hash != left_hash,
    'mirror_bounds_and_facets_ok': mesh_mirror_ok,
    'left_stl_generation': 'explicit coordinate mirror of validated RIGHT print mesh',
    'right_bbox_mm': [round(v, 3) for v in bbox_tuple(rbb)],
    'left_bbox_mm': [round(v, 3) for v in bbox_tuple(lbb)],
    'right_facets': rm.CountFacets,
    'left_facets': lm.CountFacets,
}
validation['installed_support_orientation'] = {
    'right_rack_center_y_mm': RY,
    'left_rack_center_y_mm': LY,
    'required_orientation': 'RIGHT carriers +Y outward; LEFT carriers -Y outward',
    'minimum_outward_extent_mm': 210.0,
    'maximum_inward_extent_mm': 30.0,
    'checks': support_checks,
}
if extra_failures:
    validation['failures'].extend(extra_failures)
with open(validation_path, 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2)

if extra_failures:
    print(json.dumps(validation, indent=2), flush=True)
    raise SystemExit('V60 HANDED/INSTALLED HARD CHECKS FAILED: ' + ' | '.join(extra_failures))

print('V60_CHECKPOINT handed STL exports distinct and mirrored', flush=True)
print('V60_CHECKPOINT front and rear carriers are outward on both installed sides', flush=True)
