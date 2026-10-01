import json
import math
import os
import struct

import FreeCAD as App
import Import
import Mesh
import Part

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build_v90')
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# V90 guide concept
# ---------------------------------------------------------------------------
# V90 changes only the box clamp and the corresponding base guide geometry.
# Everything else remains V80.
#
# The two guide pins are fully engaged through the complete box-side crosshead
# at every clamp setting.  When the clamp closes, the pins simply protrude
# farther out of the back of the base.  They therefore do not limit travel.

CLAMP_W = 187.30
CLAMP_H = 80.02
SCREW_X = (15.00, 172.30)
SCREW_Y = 15.00
SCREW_BORE_D = 10.40

# Keep the guide pins near the two screw stations to maximize their spacing,
# while retaining a large ligament around both the clamp screw holes and the
# larger fixed-base lead-nut/service pockets.
PIN_INSET_FROM_SCREW = 25.00
PIN_X = (
    SCREW_X[0] + PIN_INSET_FROM_SCREW,
    SCREW_X[1] - PIN_INSET_FROM_SCREW,
)
PIN_Y = SCREW_Y
PIN_D = 10.00
PIN_R = PIN_D / 2.0
PIN_TIP_FILLET_R = 1.00
PIN_ROOT_OVERLAP = 1.00

# Clamp local X=0 corresponds to v60/v80 installed X=-43.65 mm.
CLAMP_INSTALLED_X0 = -43.65
BASE_PIN_X = tuple(x + CLAMP_INSTALLED_X0 for x in PIN_X)
BASE_PIN_Z = 24.54

# Tight sliding fit target for the CORE One L.  This is intentionally much
# tighter than a generic FDM clearance; a separate tolerance print can be used
# to revise only this value if the real PETG pair proves too tight.
GUIDE_BORE_D = 10.15
GUIDE_BORE_R = GUIDE_BORE_D / 2.0
GUIDE_SLEEVE_WALL = 2.00
GUIDE_SLEEVE_D = GUIDE_BORE_D + 2.0 * GUIDE_SLEEVE_WALL
GUIDE_SLEEVE_R = GUIDE_SLEEVE_D / 2.0

MAX_CLAMP_GAP = 30.00
TARGET_REAR_PROTRUSION = 30.00

# V70/V80 clamp dimensions copied exactly from the released clamp source.
BOX_BOTTOM_Y = 30.00
POCKET_Y0 = 46.20
POCKET_Y1 = 63.82
BEARING_BACK = -4.00
BACKBONE_FRONT = 8.00
BACKBONE_T = BACKBONE_FRONT - BEARING_BACK
PRIMARY_FRONT = 27.00
UPPER_FRONT = 26.50
SEAT_OUTER_D = 18.40
SEAT_INNER_D = 10.40
SEAT_DEPTH = 1.60


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


def cyl_y(radius, y0, y1, x, z):
    return Part.makeCylinder(
        radius,
        y1 - y0,
        App.Vector(x, y0, z),
        App.Vector(0, 1, 0),
    )


def detect_crosshead_span(base, x, z):
    # Probe only the remote box-clamp area.  At the selected X positions there
    # is no long holm, so the material encountered on this axis is the crosshead.
    probe_y0 = 170.0
    probe_y1 = 245.0
    probe = cyl_y(0.20, probe_y0, probe_y1, x, z)
    common = base.common(probe)
    if common.isNull() or common.Volume <= 0:
        fail(f'no crosshead material found at X={x:.3f}, Z={z:.3f}')
    return common.BoundBox.YMin, common.BoundBox.YMax


def make_rounded_pin(x, y, z0, exposed_len):
    start_z = z0 - PIN_ROOT_OVERLAP
    total_len = exposed_len + PIN_ROOT_OVERLAP
    pin = Part.makeCylinder(PIN_R, total_len, App.Vector(x, y, start_z))
    tip_z = z0 + exposed_len
    tip_edges = [
        e for e in pin.Edges
        if e.BoundBox.ZLength < 1e-6 and abs(e.BoundBox.ZMax - tip_z) < 1e-6
    ]
    if len(tip_edges) != 1:
        fail(f'pin tip edge detection failed at X={x:.3f}: {len(tip_edges)} edges')
    rounded = pin.makeFillet(PIN_TIP_FILLET_R, tip_edges)
    return require_single(rounded, f'rounded guide pin X={x:.3f}')


def make_clamp(exposed_pin_len):
    parts = [
        Part.makeBox(CLAMP_W, CLAMP_H, BACKBONE_T,
                     App.Vector(0, 0, BEARING_BACK)),
        Part.makeBox(CLAMP_W, POCKET_Y0 - BOX_BOTTOM_Y,
                     PRIMARY_FRONT - BACKBONE_FRONT,
                     App.Vector(0, BOX_BOTTOM_Y, BACKBONE_FRONT)),
        Part.makeBox(CLAMP_W, CLAMP_H - POCKET_Y1,
                     UPPER_FRONT - BACKBONE_FRONT,
                     App.Vector(0, POCKET_Y1, BACKBONE_FRONT)),
    ]
    clamp = parts[0].fuse(parts[1]).fuse(parts[2]).removeSplitter()

    for x in SCREW_X:
        clamp = clamp.cut(Part.makeCylinder(
            SCREW_BORE_D / 2.0,
            BACKBONE_T + 1.0,
            App.Vector(x, SCREW_Y, BEARING_BACK - 0.5),
        )).removeSplitter()
        clamp = clamp.cut(Part.makeCone(
            SEAT_OUTER_D / 2.0,
            SEAT_INNER_D / 2.0,
            SEAT_DEPTH + 0.02,
            App.Vector(x, SCREW_Y, BEARING_BACK - 0.01),
        )).removeSplitter()
        clamp = clamp.cut(Part.makeCone(
            SEAT_INNER_D / 2.0,
            SEAT_OUTER_D / 2.0,
            SEAT_DEPTH + 0.02,
            App.Vector(x, SCREW_Y, BACKBONE_FRONT - SEAT_DEPTH - 0.01),
        )).removeSplitter()

    for x in PIN_X:
        clamp = clamp.fuse(make_rounded_pin(
            x, PIN_Y, BACKBONE_FRONT, exposed_pin_len
        )).removeSplitter()

    return require_single(clamp, 'v90 clamp')


def add_guides_to_base(base):
    spans = [detect_crosshead_span(base, x, BASE_PIN_Z) for x in BASE_PIN_X]
    y0 = min(s[0] for s in spans)
    y1 = max(s[1] for s in spans)
    if max(abs(s[0] - y0) for s in spans) > 0.05 or max(abs(s[1] - y1) for s in spans) > 0.05:
        fail(f'guide stations do not share one crosshead span: {spans!r}')
    guide_len = y1 - y0
    if guide_len < 20.0:
        fail(f'crosshead guide length unexpectedly short: {guide_len:.3f} mm')

    guided = base
    for x in BASE_PIN_X:
        # Add a complete internal bearing sleeve before boring it.  This turns
        # the hollow crosshead into a full-length cylindrical guide rather than
        # leaving contact only at its front/rear walls.
        sleeve = cyl_y(GUIDE_SLEEVE_R, y0, y1, x, BASE_PIN_Z)
        guided = guided.fuse(sleeve).removeSplitter()

    for x in BASE_PIN_X:
        bore = cyl_y(GUIDE_BORE_R, y0 - 1.0, y1 + 1.0, x, BASE_PIN_Z)
        guided = guided.cut(bore).removeSplitter()

    return require_single(guided, 'v90 guided base'), (y0, y1)


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
        fail(f'{path}: not a canonical binary STL: size={len(data)}, expected={expected}')
    return tri_count


# ---------------------------------------------------------------------------
# Build from the exact released V80 base STEP.
# ---------------------------------------------------------------------------
base_v80_path = os.path.join(
    ROOT, 'cad', 'v80', 'STEP', 'eurobox_v80_base_right.step'
)
base_right_v80 = load_step_single(base_v80_path, 'v80_base_right')
base_right_v90, guide_span = add_guides_to_base(base_right_v80)

# LEFT/RIGHT must be mirrored only across the bicycle lateral axis.
# X is the fore/aft direction: mirroring X would move the rear stop to the
# front on one side.  Mirror Y instead so both parts keep the stop at the same
# rear X position while becoming true left/right handed mates.
base_left_v90 = base_right_v90.copy()
base_left_v90.mirror(App.Vector(0, 0, 0), App.Vector(0, 1, 0))
base_left_v90 = require_single(base_left_v90, 'v90 guided base left')

# Hard handing proof: mirroring LEFT back across Y must reproduce RIGHT.
_left_back = base_left_v90.copy()
_left_back.mirror(App.Vector(0, 0, 0), App.Vector(0, 1, 0))
_left_back = require_single(_left_back, 'v90 left mirrored back to right')
_handed_common = base_right_v90.common(_left_back).Volume
_handed_delta = abs(
    base_right_v90.Volume + _left_back.Volume - 2.0 * _handed_common
)
if _handed_delta > 1e-4:
    fail(f'left/right Y-mirror mismatch: {_handed_delta:.6f} mm3')

# Fore/aft envelope must stay identical.  This explicitly guards against the
# old X-mirror regression which put the rear stop on the wrong end.
for axis_name, a, b in (
    ('XMin', base_right_v90.BoundBox.XMin, base_left_v90.BoundBox.XMin),
    ('XMax', base_right_v90.BoundBox.XMax, base_left_v90.BoundBox.XMax),
):
    if abs(a - b) > 1e-6:
        fail(f'left/right {axis_name} differs after handing: {a:.6f} != {b:.6f}')

guide_len = guide_span[1] - guide_span[0]
pin_exposed_len = MAX_CLAMP_GAP + guide_len + TARGET_REAR_PROTRUSION
clamp_v90 = make_clamp(pin_exposed_len)

# ---------------------------------------------------------------------------
# Hard geometry checks
# ---------------------------------------------------------------------------
base_height = 30.00
base_z0 = BASE_PIN_Z - base_height / 2.0
base_z1 = BASE_PIN_Z + base_height / 2.0
vertical_bore_ligament = min(
    BASE_PIN_Z - GUIDE_BORE_R - base_z0,
    base_z1 - (BASE_PIN_Z + GUIDE_BORE_R),
)
vertical_sleeve_margin = min(
    BASE_PIN_Z - GUIDE_SLEEVE_R - base_z0,
    base_z1 - (BASE_PIN_Z + GUIDE_SLEEVE_R),
)

clamp_hole_ligament = PIN_INSET_FROM_SCREW - (SCREW_BORE_D / 2.0 + PIN_R)
# Existing fixed-base corridor around the lead-screw shoulder is Ø11.8.
base_spindle_corridor_r = 5.90
base_bore_ligament = PIN_INSET_FROM_SCREW - (base_spindle_corridor_r + GUIDE_BORE_R)
# The removable lead-nut lower profile is R8 with 0.20 mm X pocket clearance.
base_lead_nut_pocket_r = 8.20
base_pocket_ligament = PIN_INSET_FROM_SCREW - (base_lead_nut_pocket_r + GUIDE_BORE_R)

if vertical_bore_ligament < 9.0:
    fail(f'vertical guide-bore ligament too small: {vertical_bore_ligament:.3f} mm')
if clamp_hole_ligament < 12.0:
    fail(f'clamp screw-to-pin ligament too small: {clamp_hole_ligament:.3f} mm')
if base_pocket_ligament < 10.0:
    fail(f'base lead-nut-pocket-to-guide ligament too small: {base_pocket_ligament:.3f} mm')

exports = {}
for name, shape in (
    ('eurobox_v90_base_right', base_right_v90),
    ('eurobox_v90_base_left', base_left_v90),
    ('eurobox_v90_clamp', clamp_v90),
):
    paths = export_shape(name, shape)
    tri_count = validate_binary_stl(paths[2])
    exports[name] = {
        'step': os.path.getsize(paths[0]),
        'fcstd': os.path.getsize(paths[1]),
        'stl': os.path.getsize(paths[2]),
        'stl_triangles': tri_count,
    }

validation = {
    'version': 'v90',
    'source': 'v80 base + v80 clamp geometry',
    'handing': {
        'left_from_right': 'mirror across Y=0 only',
        'fore_aft_axis': 'X',
        'rear_stop_x_preserved': True,
        'mirror_back_volume_delta_mm3': round(_handed_delta, 9),
        'right_x_bounds_mm': [
            round(base_right_v90.BoundBox.XMin, 6),
            round(base_right_v90.BoundBox.XMax, 6),
        ],
        'left_x_bounds_mm': [
            round(base_left_v90.BoundBox.XMin, 6),
            round(base_left_v90.BoundBox.XMax, 6),
        ],
    },
    'guide': {
        'pin_d_mm': PIN_D,
        'bore_d_mm': GUIDE_BORE_D,
        'diametral_clearance_mm': GUIDE_BORE_D - PIN_D,
        'sleeve_outer_d_mm': GUIDE_SLEEVE_D,
        'pin_tip_fillet_r_mm': PIN_TIP_FILLET_R,
        'pin_local_xy_mm': [[round(x, 6), PIN_Y] for x in PIN_X],
        'base_installed_xz_mm': [[round(x, 6), BASE_PIN_Z] for x in BASE_PIN_X],
        'pin_spacing_mm': round(PIN_X[1] - PIN_X[0], 6),
        'pin_inset_from_screw_axis_mm': PIN_INSET_FROM_SCREW,
        'crosshead_y_mm': [round(guide_span[0], 6), round(guide_span[1], 6)],
        'guide_length_mm': round(guide_len, 6),
        'max_clamp_gap_mm': MAX_CLAMP_GAP,
        'target_rear_protrusion_mm': TARGET_REAR_PROTRUSION,
        'pin_exposed_length_mm': round(pin_exposed_len, 6),
        'base_height_at_guide_mm': base_height,
        'vertical_bore_ligament_mm': round(vertical_bore_ligament, 6),
        'vertical_sleeve_margin_mm': round(vertical_sleeve_margin, 6),
        'clamp_screw_hole_to_pin_ligament_mm': round(clamp_hole_ligament, 6),
        'base_spindle_corridor_to_guide_ligament_mm': round(base_bore_ligament, 6),
        'base_lead_nut_pocket_to_guide_ligament_mm': round(base_pocket_ligament, 6),
    },
    'exports': exports,
    'failures': [],
}

with open(os.path.join(OUT, 'VALIDATION_v90.json'), 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2, sort_keys=True)
    f.write('\n')

print(json.dumps(validation, indent=2, sort_keys=True))
