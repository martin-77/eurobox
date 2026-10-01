import json
import os
import struct

import FreeCAD as App
import Import
import Mesh
import Part

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build_v100')
os.makedirs(OUT, exist_ok=True)

RACK_TUBE_D = 12.42
RACK_TUBE_R = RACK_TUBE_D / 2.0
RACK_CLAMP_REFERENCE_W = 28.0
RELIEF_W = 2.0 * RACK_CLAMP_REFERENCE_W
RELIEF_X0 = -RELIEF_W / 2.0
RELIEF_X1 = RELIEF_W / 2.0
RACK_CLAMP_X = (-80.0, 80.0)
RELIEF_Y0 = RACK_TUBE_R
RELIEF_Y1 = 30.0
RELIEF_Z0 = -20.0
RELIEF_Z1 = RACK_TUBE_R


def fail(msg):
    raise RuntimeError(msg)


def require_single(shape, label):
    if shape.isNull():
        fail(f'{label}: null shape')
    if not shape.isValid():
        fail(f'{label}: invalid shape')
    solids = shape.Solids
    if len(solids) != 1:
        fail(f'{label}: expected one solid, got {len(solids)}')
    return shape


def load_step_single(path, label):
    doc = App.newDocument(f'import_{label}')
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = []
    for obj in doc.Objects:
        if hasattr(obj, 'Shape') and not obj.Shape.isNull():
            shapes.extend(obj.Shape.Solids if obj.Shape.Solids else [obj.Shape])
    if not shapes:
        App.closeDocument(doc.Name)
        fail(f'{label}: STEP import produced no shapes')
    shape = shapes[0].copy()
    for q in shapes[1:]:
        shape = shape.fuse(q).removeSplitter()
    App.closeDocument(doc.Name)
    return require_single(shape, label)


def make_relief():
    return Part.makeBox(
        RELIEF_X1 - RELIEF_X0,
        RELIEF_Y1 - RELIEF_Y0,
        RELIEF_Z1 - RELIEF_Z0,
        App.Vector(RELIEF_X0, RELIEF_Y0, RELIEF_Z0),
    )


def apply_relief(base, label):
    before_volume = base.Volume
    result = base.cut(make_relief()).removeSplitter()
    result = require_single(result, label)
    removed = before_volume - result.Volume
    if removed <= 1.0:
        fail(f'{label}: relief removed too little material: {removed:.6f} mm3')
    return result, removed


def export_shape(name, shape):
    step_path = os.path.join(OUT, name + '.step')
    fcstd_path = os.path.join(OUT, name + '.FCStd')
    stl_path = os.path.join(OUT, name + '.stl')

    shape.exportStep(step_path)
    doc = App.newDocument(name)
    obj = doc.addObject('Part::Feature', name)
    obj.Shape = shape
    doc.recompute()
    doc.saveAs(fcstd_path)
    Mesh.export([obj], stl_path)
    App.closeDocument(doc.Name)
    return step_path, fcstd_path, stl_path


def validate_binary_stl(path):
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) < 84:
        fail(f'{path}: STL too short')
    tri_count = struct.unpack('<I', data[80:84])[0]
    expected = 84 + 50 * tri_count
    if expected != len(data):
        fail(f'{path}: not canonical binary STL: size={len(data)}, expected={expected}')
    return tri_count


src_dir = os.path.join(ROOT, 'cad', 'v90', 'STEP')
right_v90 = load_step_single(
    os.path.join(src_dir, 'eurobox_v90_base_right.step'),
    'v90_base_right',
)
left_v90 = load_step_single(
    os.path.join(src_dir, 'eurobox_v90_base_left.step'),
    'v90_base_left',
)

right_v100, right_removed = apply_relief(right_v90, 'v100 base right')
left_v100, left_removed = apply_relief(left_v90, 'v100 base left')

for label, before, after in (
    ('right', right_v90, right_v100),
    ('left', left_v90, left_v100),
):
    for axis, a, b in (
        ('XMin', before.BoundBox.XMin, after.BoundBox.XMin),
        ('XMax', before.BoundBox.XMax, after.BoundBox.XMax),
        ('YMin', before.BoundBox.YMin, after.BoundBox.YMin),
        ('YMax', before.BoundBox.YMax, after.BoundBox.YMax),
        ('ZMin', before.BoundBox.ZMin, after.BoundBox.ZMin),
        ('ZMax', before.BoundBox.ZMax, after.BoundBox.ZMax),
    ):
        if abs(a - b) > 1e-6:
            fail(f'{label}: local relief changed outer {axis}: {a:.6f} -> {b:.6f}')

if abs(right_removed - left_removed) > 1e-3:
    fail(
        'left/right relief volume differs: '
        f'{right_removed:.6f} vs {left_removed:.6f} mm3'
    )

if abs(RELIEF_W - 2.0 * RACK_CLAMP_REFERENCE_W) > 1e-9:
    fail('relief is not exactly two reference clamp widths')
if abs(RELIEF_Y0 - RACK_TUBE_R) > 1e-9:
    fail('relief no longer starts at the rack-tube front tangent')
if abs(RELIEF_Z1 - RACK_TUBE_R) > 1e-9:
    fail('relief top no longer matches rack-tube tangent height')

clear_from_clamp_centre = abs(RACK_CLAMP_X[0] - RELIEF_X0)
clear_in_clamp_widths = clear_from_clamp_centre / RACK_CLAMP_REFERENCE_W
if clear_in_clamp_widths < 1.80:
    fail(
        f'relief begins too close to clamp centre: '
        f'{clear_in_clamp_widths:.3f} clamp widths'
    )

exports = {}
for name, shape in (
    ('eurobox_v100_base_right', right_v100),
    ('eurobox_v100_base_left', left_v100),
):
    paths = export_shape(name, shape)
    exports[name] = {
        'step_bytes': os.path.getsize(paths[0]),
        'fcstd_bytes': os.path.getsize(paths[1]),
        'stl_bytes': os.path.getsize(paths[2]),
        'stl_triangles': validate_binary_stl(paths[2]),
    }

validation = {
    'version': 'v100',
    'source': 'released v90 handed base STEP files',
    'change': 'local front-side rack-frame/pin relief only',
    'rack_tube': {
        'diameter_mm': RACK_TUBE_D,
        'radius_mm': RACK_TUBE_R,
    },
    'relief': {
        'reference_clamp_width_mm': RACK_CLAMP_REFERENCE_W,
        'width_mm': RELIEF_W,
        'x_mm': [RELIEF_X0, RELIEF_X1],
        'y_mm': [RELIEF_Y0, RELIEF_Y1],
        'z_mm': [RELIEF_Z0, RELIEF_Z1],
        'front_side': '+Y',
        'starts_at_tube_tangent': True,
        'saddle_contact_surface_changed': False,
        'clearance_from_each_clamp_centre_mm': clear_from_clamp_centre,
        'clearance_from_each_clamp_centre_in_clamp_widths': round(clear_in_clamp_widths, 6),
        'right_removed_volume_mm3': round(right_removed, 6),
        'left_removed_volume_mm3': round(left_removed, 6),
    },
    'exports': exports,
    'failures': [],
}

with open(os.path.join(OUT, 'VALIDATION_v100.json'), 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2, sort_keys=True)
    f.write('\n')

print(json.dumps(validation, indent=2, sort_keys=True))
