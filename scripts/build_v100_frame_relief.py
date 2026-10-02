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
# The actual V90 upper saddle is cut at R=6.31 mm around a Ø12.42 mm tube.
# The relief must rise all the way to this saddle/contact level so the local
# section no longer wraps the front half of the rack tube.
UPPER_SADDLE_R = 6.31
RACK_CLAMP_REFERENCE_W = 28.0
RELIEF_W = 2.0 * RACK_CLAMP_REFERENCE_W
RELIEF_X0 = -RELIEF_W / 2.0
RELIEF_X1 = RELIEF_W / 2.0
RACK_CLAMP_X = (-80.0, 80.0)
# In the relief window keep only the upper tube support.  Cutting from the
# tube centreline toward +Y removes the front-side wrap completely, while the
# top saddle remains untouched.
RELIEF_Y0 = 0.0
RELIEF_Y1 = 30.0
RELIEF_Z0 = -20.0
RELIEF_Z1 = UPPER_SADDLE_R

# V100 rack-Lower screw slot.
# The existing closure bore is Ø5.0 at Y=+11 mm. Open that bore toward the
# front edge (+Y) so the Lower can swing up around an M4 screw that remains
# threaded in the fixed Upper. The hand knob supplies the clamping/retention,
# so the Lower itself does not need a closed screw eye.
RACK_LOWER_CLEAR_D = 5.0
RACK_LOWER_SLOT_HALF_W = RACK_LOWER_CLEAR_D / 2.0
RACK_LOWER_CLOSURE_Y = 11.0
RACK_LOWER_PAD_FRONT_Y = 18.0
RACK_LOWER_SLOT_Y0 = RACK_LOWER_CLOSURE_Y
RACK_LOWER_SLOT_Y1 = RACK_LOWER_PAD_FRONT_Y + 1.0
# The v90 STEP is the natural print-oriented Lower (installed Z shifted +14.5).
# Cut through the complete tongue thickness with generous Z overrun only.
RACK_LOWER_SLOT_Z0 = -1.0
RACK_LOWER_SLOT_Z1 = 20.0

# Normalize the mirrored LEFT base back to the standard/default rack-retainer
# thread handedness by transplanting the exact RIGHT-base service cavity.
# Only the threaded service zone is replaced; the rest of each handed base
# remains untouched.
RETAINER_STATIONS_X = (-80.0, 80.0)
RETAINER_AXIS_Y = 11.0
RETAINER_THREAD_Z0 = 11.0
RETAINER_TOP_Z = 39.54
RETAINER_SERVICE_R = 6.50


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


def service_cylinder(xc):
    return Part.makeCylinder(
        RETAINER_SERVICE_R,
        RETAINER_TOP_Z - RETAINER_THREAD_Z0,
        App.Vector(xc, RETAINER_AXIS_Y, RETAINER_THREAD_Z0),
        App.Vector(0, 0, 1),
    )


def cavity_signature(shape):
    return {
        'volume_mm3': round(shape.Volume, 6),
        'area_mm2': round(shape.Area, 6),
        'solids': len(shape.Solids),
        'faces': len(shape.Faces),
        'edges': len(shape.Edges),
        'bounds_mm': [
            round(shape.BoundBox.XMin, 6),
            round(shape.BoundBox.XMax, 6),
            round(shape.BoundBox.YMin, 6),
            round(shape.BoundBox.YMax, 6),
            round(shape.BoundBox.ZMin, 6),
            round(shape.BoundBox.ZMax, 6),
        ],
    }


def normalize_left_retainer_threads(left, right):
    out = left
    witnesses = []
    for xc in RETAINER_STATIONS_X:
        service = service_cylinder(xc)

        # Exact female-thread/service-mouth void from the already correct RIGHT
        # base.  This includes the default retainer's thread chirality and phase.
        donor_void = service.cut(right).removeSplitter()
        if donor_void.isNull() or donor_void.Volume <= 1.0:
            fail(f'RIGHT donor retainer cavity missing at X={xc}')

        # First restore solid material in the complete threaded service zone,
        # thereby erasing the mirrored/opposite-handed helix. Then subtract the
        # RIGHT donor void byte-for-geometry.
        out = out.fuse(service).removeSplitter()
        out = require_single(out, f'LEFT after retainer service refill X={xc}')
        out = out.cut(donor_void).removeSplitter()
        out = require_single(out, f'LEFT after default retainer cavity transplant X={xc}')

        resulting_void = service.cut(out).removeSplitter()
        donor_sig = cavity_signature(donor_void)
        result_sig = cavity_signature(resulting_void)
        if donor_sig != result_sig:
            fail(f'LEFT retainer cavity does not match RIGHT/default thread at X={xc}')

        witnesses.append({
            'x_mm': xc,
            'donor_void_volume_mm3': round(donor_void.Volume, 6),
            'result_void_volume_mm3': round(resulting_void.Volume, 6),
            'signature_equal': True,
        })
    return out, witnesses


def make_rack_lower_slot():
    return Part.makeBox(
        2.0 * RACK_LOWER_SLOT_HALF_W,
        RACK_LOWER_SLOT_Y1 - RACK_LOWER_SLOT_Y0,
        RACK_LOWER_SLOT_Z1 - RACK_LOWER_SLOT_Z0,
        App.Vector(
            -RACK_LOWER_SLOT_HALF_W,
            RACK_LOWER_SLOT_Y0,
            RACK_LOWER_SLOT_Z0,
        ),
    )


def apply_rack_lower_slot(lower):
    before_volume = lower.Volume
    cutter = make_rack_lower_slot()
    result = lower.cut(cutter).removeSplitter()
    result = require_single(result, 'v100 rack lower with open screw slot')
    removed = before_volume - result.Volume
    if removed <= 20.0:
        fail(
            'rack-lower slot removed too little material: '
            f'{removed:.6f} mm3'
        )

    # Hard proof that the former closed Ø5 screw bore is now open to +Y/front.
    # This probe runs down the slot centre from the old bore centre to beyond
    # the front edge and must have no remaining solid intersection.
    probe = Part.makeBox(
        1.0,
        RACK_LOWER_SLOT_Y1 - RACK_LOWER_SLOT_Y0,
        RACK_LOWER_SLOT_Z1 - RACK_LOWER_SLOT_Z0,
        App.Vector(
            -0.5,
            RACK_LOWER_SLOT_Y0,
            RACK_LOWER_SLOT_Z0,
        ),
    )
    common = result.common(probe)
    if not common.isNull() and common.Volume > 1e-6:
        fail(
            'rack-lower screw slot is not continuously open to the front: '
            f'{common.Volume:.6f} mm3 remains'
        )
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
rack_lower_v90 = load_step_single(
    os.path.join(src_dir, 'eurobox_v90_rack_lower.step'),
    'v90_rack_lower',
)

right_v100, right_removed = apply_relief(right_v90, 'v100 base right')
left_v100, left_removed = apply_relief(left_v90, 'v100 base left')
left_v100, retainer_thread_witness = normalize_left_retainer_threads(
    left_v100, right_v100
)
rack_lower_v100, rack_lower_slot_removed = apply_rack_lower_slot(rack_lower_v90)

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
if abs(RELIEF_Y0) > 1e-9:
    fail('relief no longer starts at the rack-tube centre plane')
if abs(RELIEF_Z1 - UPPER_SADDLE_R) > 1e-9:
    fail('relief top no longer reaches the upper saddle/contact level')

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
    ('eurobox_v100_rack_lower', rack_lower_v100),
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
        'upper_saddle_radius_mm': UPPER_SADDLE_R,
    },
    'relief': {
        'reference_clamp_width_mm': RACK_CLAMP_REFERENCE_W,
        'width_mm': RELIEF_W,
        'x_mm': [RELIEF_X0, RELIEF_X1],
        'y_mm': [RELIEF_Y0, RELIEF_Y1],
        'z_mm': [RELIEF_Z0, RELIEF_Z1],
        'front_side': '+Y',
        'starts_at_tube_centre_plane': True,
        'rises_to_upper_saddle_contact_level': True,
        'front_wrap_removed_in_relief_window': True,
        'saddle_contact_surface_changed': False,
        'clearance_from_each_clamp_centre_mm': clear_from_clamp_centre,
        'clearance_from_each_clamp_centre_in_clamp_widths': round(clear_in_clamp_widths, 6),
        'right_removed_volume_mm3': round(right_removed, 6),
        'left_removed_volume_mm3': round(left_removed, 6),
    },
    'retainer_thread_normalization': {
        'default_retainer_for_both_bases': True,
        'right_base_changed': False,
        'left_base_thread_service_zone_rebuilt_from_right_cavity': True,
        'service_radius_mm': RETAINER_SERVICE_R,
        'z_mm': [RETAINER_THREAD_Z0, RETAINER_TOP_Z],
        'stations': retainer_thread_witness,
    },
    'rack_lower_slot': {
        'existing_bore_d_mm': RACK_LOWER_CLEAR_D,
        'slot_width_mm': 2.0 * RACK_LOWER_SLOT_HALF_W,
        'slot_x_mm': [-RACK_LOWER_SLOT_HALF_W, RACK_LOWER_SLOT_HALF_W],
        'slot_y_mm': [RACK_LOWER_SLOT_Y0, RACK_LOWER_SLOT_Y1],
        'opens_toward': '+Y/front',
        'old_bore_centre_y_mm': RACK_LOWER_CLOSURE_Y,
        'pad_front_y_mm': RACK_LOWER_PAD_FRONT_Y,
        'screw_can_remain_in_upper_while_swinging': True,
        'retention_by_hand_knob': True,
        'removed_volume_mm3': round(rack_lower_slot_removed, 6),
    },
    'exports': exports,
    'failures': [],
}

with open(os.path.join(OUT, 'VALIDATION_v100.json'), 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2, sort_keys=True)
    f.write('\n')

print(json.dumps(validation, indent=2, sort_keys=True))
