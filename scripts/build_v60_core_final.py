import json
import os

import build_v60 as C

# Final structural closure pass for the clean v60 core.
# This is deliberately not a source-rewrite patch: it operates on the canonical
# FreeCAD solids and replaces the visible open station/root interfaces with the
# same design intent already established during v50 development.

ROOT_FACE_T = C.WEB_T
ROOT_FACE_Y0 = C.UPPER_BRIDGE_Y0
ROOT_FACE_Y1 = ROOT_FACE_Y0 + ROOT_FACE_T
INNER_SPLICE_W = 6.4
INNER_SPLICE_Y0 = -8.0
INNER_SPLICE_Y1 = 8.0
BACKSTOP_SPLICE_X0 = C.BACKSTOP_X1 - 8.0
BACKSTOP_SPLICE_X1 = C.REAR_SUPPORT_X + C.ARM_W / 2.0
BACKSTOP_SPLICE_Y0 = 0.0
BACKSTOP_SPLICE_Y1 = 12.0


def make_station_root_closure(xc):
    # Close the exposed I-beam channels at the frame-side face.  The closure is
    # entirely above the measured Ø12.42 rack tube, so the proven saddle and
    # lower-clamp kinematics remain untouched.
    face = C.box(
        xc - C.ARM_W / 2.0,
        ROOT_FACE_Y0,
        C.ARM_BOTTOM_Z,
        C.ARM_W,
        ROOT_FACE_Y1 - ROOT_FACE_Y0,
        C.ARM_H,
    )

    # Widen the actual station-to-central-wall load path.  The first v60 used
    # only a narrow edge overlap, which rendered as a visible slit/triangular
    # void.  This buried 6.4 mm splice overlaps both the 38 mm station body and
    # the full-height clamp-frame wall without changing the external envelope.
    if xc < 0.0:
        x0 = xc + C.FIXED_STATION_HALF_X - INNER_SPLICE_W
    else:
        x0 = xc - C.FIXED_STATION_HALF_X
    splice = C.box(
        x0,
        INNER_SPLICE_Y0,
        C.ARM_BOTTOM_Z,
        INNER_SPLICE_W,
        INNER_SPLICE_Y1 - INNER_SPLICE_Y0,
        C.ARM_H,
    )
    return C.fuse_seq([face, splice], f'station-root-closure@{xc}')


def make_backstop_support_splice():
    # Straight rectangular load path from the 50 mm stop plate into the moved
    # rear support.  No diagonal gusset: this simply turns the existing nominal
    # overlap into an unambiguous closed structural joint.
    return C.box(
        BACKSTOP_SPLICE_X0,
        BACKSTOP_SPLICE_Y0,
        C.ARM_BOTTOM_Z,
        BACKSTOP_SPLICE_X1 - BACKSTOP_SPLICE_X0,
        BACKSTOP_SPLICE_Y1 - BACKSTOP_SPLICE_Y0,
        C.ARM_H,
    )


_station_closures = [make_station_root_closure(xc) for xc in C.CLAMP_X]
_backstop_splice = make_backstop_support_splice()

_right = C.RIGHT
for q in _station_closures:
    _right = _right.fuse(q).removeSplitter()
    C.require_single(_right, 'RIGHT after station-root closure')
_right = _right.fuse(_backstop_splice).removeSplitter()
C.require_single(_right, 'RIGHT after backstop-support closure')

# Re-apply only functional cutters that can intersect the newly added station
# material.  Current closures start at Z=9.54, so the rack saddle/pivot remain
# below them; the M4 bore reaches upward and is therefore re-established here.
for xc in C.CLAMP_X:
    _right = _right.cut(
        __import__('Part').makeCylinder(
            C.RACK_M4_BASE_CLEAR_D / 2.0,
            12.0,
            __import__('FreeCAD').Vector(xc, C.RACK_CLOSURE_Y, -1.0),
            __import__('FreeCAD').Vector(0, 0, 1),
        )
    ).removeSplitter()
C.require_single(_right, 'RIGHT final closed structural core')

# The moving box-clamp corridor remains authoritative and must stay empty.
_right = _right.cut(C.make_plate_sweep_clearance()).removeSplitter()
C.require_single(_right, 'RIGHT final closed core after plate corridor')

C.RIGHT = _right
C.LEFT = C.mirror_x(C.RIGHT)

# Hard structural witnesses against regression back to the screenshot defects.
_failures = []
_closure_data = []
for xc, q in zip(C.CLAMP_X, _station_closures):
    frac = C.RIGHT.common(q).Volume / q.Volume
    _closure_data.append({'x_mm': xc, 'material_fraction': round(frac, 6)})
    if frac < 0.995:
        _failures.append(f'station root closure missing at X={xc}: {frac:.6f}')

_backstop_fraction = C.RIGHT.common(_backstop_splice).Volume / _backstop_splice.Volume
if _backstop_fraction < 0.995:
    _failures.append(f'backstop/rear-support closure missing: {_backstop_fraction:.6f}')

# Keep all previously proven hard constraints.
if C.RIGHT.BoundBox.XLength > C.V60_X_TARGET_MAX + 1e-6:
    _failures.append(f'closed RIGHT exceeds 296 mm X target: {C.RIGHT.BoundBox.XLength:.3f}')
if C.RIGHT.BoundBox.YLength > C.INDX_Y_MAX + 1e-6:
    _failures.append(f'closed RIGHT exceeds 275 mm Y target: {C.RIGHT.BoundBox.YLength:.3f}')
if C.RIGHT.common(C.make_plate_sweep_clearance()).Volume > 1e-4:
    _failures.append('station closure re-blocked the moving plate corridor')

# Update the core report so CI proves the actual final core rather than the
# pre-closure intermediate geometry.
report_path = os.path.join(C.OUT, 'VALIDATION_v60.json')
with open(report_path, 'r', encoding='utf-8') as f:
    report = json.load(f)
report['stage'] = 'clean_structural_core_v50_mechanics_and_root_closures_restored'
report['architecture'] = 'direct v60 geometry + v50 closed clamp roots, full wall splice, closed backstop/support load path'
report['geometry']['right_bbox_mm'] = [round(C.RIGHT.BoundBox.XLength, 3), round(C.RIGHT.BoundBox.YLength, 3), round(C.RIGHT.BoundBox.ZLength, 3)]
report['geometry']['left_bbox_mm'] = [round(C.LEFT.BoundBox.XLength, 3), round(C.LEFT.BoundBox.YLength, 3), round(C.LEFT.BoundBox.ZLength, 3)]
report['geometry']['right_volume_mm3'] = round(C.RIGHT.Volume, 3)
report['geometry']['left_volume_mm3'] = round(C.LEFT.Volume, 3)
report['geometry']['station_root_closures'] = _closure_data
report['geometry']['backstop_support_closure_fraction'] = round(_backstop_fraction, 6)
report['geometry']['root_face_y_mm'] = [ROOT_FACE_Y0, ROOT_FACE_Y1]
report['geometry']['inner_wall_splice_width_mm'] = INNER_SPLICE_W
report['geometry']['backstop_support_splice_x_mm'] = [BACKSTOP_SPLICE_X0, BACKSTOP_SPLICE_X1]
report['failures'] = list(dict.fromkeys(report.get('failures', []) + _failures))
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

if _failures:
    raise RuntimeError('Final v60 structural closure checks failed: ' + ' | '.join(_failures))
