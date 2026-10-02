import json
import os
import struct

import FreeCAD as App
import Import
import Mesh

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build_v110')
os.makedirs(OUT, exist_ok=True)

SOURCE_STEP = os.path.join(
    ROOT, 'cad', 'v100', 'STEP', 'eurobox_v100_rack_nut_retainer.step'
)


def fail(msg):
    raise RuntimeError(msg)


def require_single(shape, label):
    if shape.isNull():
        fail(f'{label}: null shape')
    if not shape.isValid():
        fail(f'{label}: invalid shape')
    if len(shape.Solids) != 1:
        fail(f'{label}: expected one solid, got {len(shape.Solids)}')
    return shape


def load_step_single(path, label):
    doc = App.newDocument('import_' + label)
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = []
    for obj in doc.Objects:
        if hasattr(obj, 'Shape') and not obj.Shape.isNull():
            shapes.extend(obj.Shape.Solids if obj.Shape.Solids else [obj.Shape])
    if not shapes:
        App.closeDocument(doc.Name)
        fail(f'{label}: STEP import produced no shape')
    shape = shapes[0].copy()
    for q in shapes[1:]:
        shape = shape.fuse(q).removeSplitter()
    App.closeDocument(doc.Name)
    return require_single(shape, label)


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
    data = open(path, 'rb').read()
    if len(data) < 84:
        fail(f'{path}: STL too short')
    triangles = struct.unpack('<I', data[80:84])[0]
    expected = 84 + 50 * triangles
    if len(data) != expected:
        fail(f'{path}: not canonical binary STL')
    return triangles


def signature(shape):
    return {
        'volume_mm3': round(shape.Volume, 6),
        'area_mm2': round(shape.Area, 6),
        'vertices': sorted(
            (
                round(v.Point.x, 6),
                round(v.Point.y, 6),
                round(v.Point.z, 6),
            )
            for v in shape.Vertexes
        ),
        'edges': len(shape.Edges),
        'faces': len(shape.Faces),
        'bounds_mm': [
            round(shape.BoundBox.XMin, 6),
            round(shape.BoundBox.XMax, 6),
            round(shape.BoundBox.YMin, 6),
            round(shape.BoundBox.YMax, 6),
            round(shape.BoundBox.ZMin, 6),
            round(shape.BoundBox.ZMax, 6),
        ],
    }


source = load_step_single(SOURCE_STEP, 'v100_standard_retainer')

# Mirror in a plane containing the thread axis (Z). This reverses thread
# chirality without reversing the axial insertion direction. The current
# v100 LEFT base was produced by the same X reflection after its female thread
# had already been cut, so this is the exact matching service retainer.
mirrored = source.copy()
q = mirrored.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))
if q is not None:
    mirrored = q
mirrored = require_single(mirrored, 'v110 left-hand rack nut retainer')

# Exact proof: reflect the service retainer back and it must recover the source
# geometry. This guards against accidental rotations/scaling while preserving
# the intentional opposite thread handedness.
back = mirrored.copy()
q = back.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))
if q is not None:
    back = q
back = require_single(back, 'v110 retainer mirrored back')
if signature(back) != signature(source):
    fail('mirrored-back retainer does not reproduce v100 source geometry')

name = 'eurobox_v110_rack_nut_retainer_left_hand'
paths = export_shape(name, mirrored)
triangles = validate_binary_stl(paths[2])

validation = {
    'version': 'v110',
    'purpose': 'service workaround for the currently mirrored LEFT base female thread',
    'source': 'cad/v100/STEP/eurobox_v100_rack_nut_retainer.step',
    'change': 'exact X reflection of the standard retainer to reverse thread chirality',
    'thread_axis': 'Z',
    'mirror_plane': 'X=0',
    'axial_insertion_direction_changed': False,
    'thread_handedness_reversed': True,
    'intended_base': 'current v100 LEFT base only',
    'standard_retainer_still_required_for': 'current v100 RIGHT base',
    'operation_note': 'tightening direction is opposite to the standard retainer',
    'mirror_back_signature_equal': True,
    'export': {
        'step_bytes': os.path.getsize(paths[0]),
        'fcstd_bytes': os.path.getsize(paths[1]),
        'stl_bytes': os.path.getsize(paths[2]),
        'stl_triangles': triangles,
    },
    'failures': [],
}

with open(os.path.join(OUT, 'VALIDATION_v110.json'), 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2, sort_keys=True)
    f.write('\n')

print(json.dumps(validation, indent=2, sort_keys=True))
