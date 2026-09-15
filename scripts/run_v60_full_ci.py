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


def direct_export_shape(name, sh):
    """Export the exact handed BREP and tessellate that shape directly."""
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

    mesh = MeshPart.meshFromShape(
        Shape=sh,
        LinearDeflection=0.08,
        AngularDeflection=0.25,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ': direct STL tessellation produced no facets')
    mesh.write(stl_path)


# The former Mesh.export([Part::Feature]) path could emit identical handed base
# meshes even though the STEP BREPs were different. Override it before exports.
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

# Validate installed orientation. RIGHT sits on +Y and both longitudinal box
# carriers must extend farther +Y than its rack tube; LEFT sits on -Y and both
# carriers must extend farther -Y. This checks the front and moved rear carrier.
RY = C.RACK_CTC / 2.0
LY = -C.RACK_CTC / 2.0
right_installed = F.RIGHT_FULL.copy()
right_installed.translate(App.Vector(0, RY, 0))
left_installed = F.LEFT_FULL.copy()
left_installed.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0)
left_installed.translate(App.Vector(0, LY, 0))

support_checks = []
for station_name, xc in (
    ('front', C.FRONT_CLAMP_X),
    ('rear', C.REAR_SUPPORT_X),
):
    z0 = C.ARM_BOTTOM_Z + 0.5
    dz = C.ARM_H - 1.0
    right_out_probe = C.box(xc - 12.0, RY + 60.0, z0, 24.0, 100.0, dz)
    right_in_probe = C.box(xc - 12.0, RY - 160.0, z0, 24.0, 100.0, dz)
    left_out_probe = C.box(xc - 12.0, LY - 160.0, z0, 24.0, 100.0, dz)
    left_in_probe = C.box(xc - 12.0, LY + 60.0, z0, 24.0, 100.0, dz)

    ro = right_installed.common(right_out_probe).Volume
    ri = right_installed.common(right_in_probe).Volume
    lo = left_installed.common(left_out_probe).Volume
    li = left_installed.common(left_in_probe).Volume
    support_checks.append({
        'station': station_name,
        'x_mm': xc,
        'right_outward_common_mm3': round(ro, 3),
        'right_inward_common_mm3': round(ri, 3),
        'left_outward_common_mm3': round(lo, 3),
        'left_inward_common_mm3': round(li, 3),
    })
    if ro < 500.0:
        extra_failures.append(
            f'RIGHT {station_name} carrier is not present outside (+Y) of its clamp'
        )
    if lo < 500.0:
        extra_failures.append(
            f'LEFT {station_name} carrier is not present outside (-Y) of its clamp'
        )
    if ri > 1.0:
        extra_failures.append(
            f'RIGHT {station_name} carrier incorrectly extends inward (-Y), {ri:.3f} mm3'
        )
    if li > 1.0:
        extra_failures.append(
            f'LEFT {station_name} carrier incorrectly extends inward (+Y), {li:.3f} mm3'
        )

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as f:
    validation = json.load(f)
validation['handed_stl_export'] = {
    'right_sha256': right_hash,
    'left_sha256': left_hash,
    'byte_distinct': right_hash != left_hash,
    'mirror_bounds_and_facets_ok': mesh_mirror_ok,
    'right_bbox_mm': [round(v, 3) for v in bbox_tuple(rbb)],
    'left_bbox_mm': [round(v, 3) for v in bbox_tuple(lbb)],
    'right_facets': rm.CountFacets,
    'left_facets': lm.CountFacets,
}
validation['installed_support_orientation'] = {
    'right_rack_center_y_mm': RY,
    'left_rack_center_y_mm': LY,
    'required_orientation': 'RIGHT carriers +Y outward; LEFT carriers -Y outward',
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
print('V60_CHECKPOINT both carrier stations point outward on both installed sides', flush=True)
