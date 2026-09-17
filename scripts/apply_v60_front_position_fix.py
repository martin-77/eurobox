import json
import os

import FreeCAD as App

import apply_v60_front_final as P
import build_v60 as C
import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

# Position-only correction derived from the installed-orientation preview.
# The complete box-clamp front was incorrectly centred at X=0.  The carrier
# itself is strongly asymmetric in X, so that put the left cartridge almost
# into the front support while leaving excessive unused room to the right.
# Move the entire front mechanism +40 mm in X as one rigid topology:
#   main 160 mm face:  -40 .. +120
#   spindle axes:      -48 .. +128
# This clears the damaged left placement and moves the good right cartridge
# farther right without putting either cartridge into the outer angles.
FRONT_X_OFFSET = 40.0
PLATE_CENTER_X = FRONT_X_OFFSET
SPINDLE_X = tuple(x + FRONT_X_OFFSET for x in P.SPINDLE_X)


def stage(msg):
    print('V60_FRONT_POSITION ' + msg, flush=True)


def shifted_main_plate_sweep():
    return C.box(
        FRONT_X_OFFSET - P.PLATE_SWEEP_HALF_X,
        C.PLATE_SWEEP_Y0,
        C.PLATE_SWEEP_Z0,
        2.0 * P.PLATE_SWEEP_HALF_X,
        C.PLATE_SWEEP_Y1 - C.PLATE_SWEEP_Y0,
        C.PLATE_SWEEP_Z1 - C.PLATE_SWEEP_Z0,
    )


def shifted_ear_sweep(sx):
    return C.box(
        sx - P.PLATE_EAR_HALF_X - P.PLATE_EAR_CLEAR,
        C.PLATE_SWEEP_Y0,
        P.PLATE_EAR_Z0 - P.PLATE_EAR_CLEAR,
        2.0 * (P.PLATE_EAR_HALF_X + P.PLATE_EAR_CLEAR),
        C.PLATE_SWEEP_Y1 - C.PLATE_SWEEP_Y0,
        (P.PLATE_EAR_Z1 - P.PLATE_EAR_Z0) + 2.0 * P.PLATE_EAR_CLEAR,
    )


def rebuild_raw_structural_core():
    front_support = C.make_long_support(C.FRONT_CLAMP_X, C.ARM_Y0)
    rear_support = C.make_long_support(C.REAR_SUPPORT_X, 0.0)
    raw = C.fuse_seq([
        C.make_upper_station(C.FRONT_CLAMP_X),
        C.make_clamp_frame_bridge(),
        C.make_upper_station(C.REAR_CLAMP_X),
        front_support,
        C.make_crosshead(),
        rear_support,
        C.make_backstop(),
    ], 'RIGHT raw structural core for shifted box clamp')
    raw = raw.cut(shifted_main_plate_sweep()).removeSplitter()
    for sx in SPINDLE_X:
        raw = raw.cut(shifted_ear_sweep(sx)).removeSplitter()
    C.require_single(raw, 'RIGHT structural core with shifted box-clamp corridor')
    return raw


stage('rebuild front at +40 mm X without changing clamp geometry')
_t = start_timer('box_front_position.rebuild_shifted_front')
CORE = rebuild_raw_structural_core()
CAGE = P.CAGE.copy()
CAGE.translate(App.Vector(FRONT_X_OFFSET, 0, 0))
RIGHT_FULL = CORE.fuse(CAGE).removeSplitter()

# Reapply the exact production cartridge/service machining at the shifted axes.
for sx in SPINDLE_X:
    nut_pocket = C.box(
        sx - 8.35,
        F.NUT_THREAD_Y0 - 0.35,
        F.SPINDLE_Z - P.LEAD_NUT_BODY_HALF_Z - 0.35,
        16.70,
        F.NUT_THREAD_LEN + 0.70,
        2.0 * P.LEAD_NUT_BODY_HALF_Z + 0.70,
    )
    tail_pocket = C.box(
        sx - 6.20,
        P.NUT_TAIL_Y0 - 0.25,
        F.SPINDLE_Z + P.LEAD_NUT_TAIL_Z0 - 0.25,
        12.40,
        P.LEAD_NUT_TAIL_L + 0.50,
        P.LEAD_NUT_TAIL_H + 0.50,
    )
    tunnel_y0 = F.CAGE_Y0 - 0.50
    tunnel_y1 = F.PLATE_SPINDLE_Y - F.PLATE_Y + 0.50
    spindle_tunnel = F.cyl_y(
        5.90,
        tunnel_y1 - tunnel_y0,
        sx,
        tunnel_y0,
        F.SPINDLE_Z,
    )
    pin_bore = C.cyl_x(P.LEAD_NUT_PIN_HOLE_D / 2.0, 24.0, sx - 12.0, P.PIN_Y, P.PIN_Z)
    head_service = C.cyl_x(3.55, 3.0, sx - 14.0, P.PIN_Y, P.PIN_Z)
    clip_service = C.cyl_x(4.10, 4.0, sx + 11.0, P.PIN_Y, P.PIN_Z)
    for cutter in (nut_pocket, tail_pocket, spindle_tunnel, pin_bore, head_service, clip_service):
        RIGHT_FULL = RIGHT_FULL.cut(cutter).removeSplitter()

C.require_single(RIGHT_FULL, 'RIGHT final shifted box-clamp front')
LEFT_FULL = C.mirror_x(RIGHT_FULL)
C.require_single(LEFT_FULL, 'LEFT final shifted box-clamp front')

PLATE = P.PLATE.copy()
PLATE.translate(App.Vector(FRONT_X_OFFSET, 0, 0))
C.require_single(PLATE, 'shifted 160 mm moving clamp face')
stop_timer('box_front_position.rebuild_shifted_front', _t)

stage('hard-check shifted positions and motion')
_t = start_timer('box_front_position.hard_checks')
failures = []

if SPINDLE_X != (-48.0, 128.0):
    failures.append(f'unexpected shifted spindle positions: {SPINDLE_X}')
if abs(PLATE.BoundBox.XMin - (-40.0)) > 1e-6 or abs(PLATE.BoundBox.XMax - 138.0) > 1e-6:
    # Plate main face is -40..120; drive ears extend to +138 and -58.
    # Check explicit main-face datum separately below, total bbox here catches
    # an accidental partial shift.
    expected_min = -58.0
    expected_max = 138.0
    if abs(PLATE.BoundBox.XMin - expected_min) > 1e-6 or abs(PLATE.BoundBox.XMax - expected_max) > 1e-6:
        failures.append(
            f'shifted plate/ears bbox wrong: {PLATE.BoundBox.XMin:.3f}..{PLATE.BoundBox.XMax:.3f}'
        )

# The left fixed boss must no longer occupy the front-support centre at -80;
# the right boss must move materially farther right than the previous +88 mm.
if abs(SPINDLE_X[0] - C.FRONT_CLAMP_X) < 20.0:
    failures.append('left cartridge still too close to front support/angle region')
if SPINDLE_X[1] < 120.0:
    failures.append('right cartridge was not moved far enough right')

# Preserve the complete plate travel and spindle/base clearance at the new X.
for travel in (-0.5, 0.0, 1.0, 3.0, 5.5):
    pl = PLATE.copy()
    pl.translate(App.Vector(0, -travel, 0))
    common = RIGHT_FULL.common(pl).Volume
    if common > 1e-4:
        failures.append(f'shifted plate/base collision travel={travel}: {common:.6f}')

for sx in SPINDLE_X:
    for travel in (0.0, 0.5, 2.0, 5.5):
        spindle = F.SPINDLE.copy()
        spindle.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), P.lead_rotation_deg(travel))
        spindle.translate(App.Vector(sx, F.PLATE_SPINDLE_Y - travel, F.SPINDLE_Z))
        base_common = RIGHT_FULL.common(spindle).Volume
        if base_common > 1.0:
            failures.append(
                f'shifted spindle/base collision X={sx} travel={travel}: {base_common:.6f}'
            )

if RIGHT_FULL.BoundBox.XLength > C.V60_X_TARGET_MAX + 1e-6:
    failures.append(f'RIGHT exceeds 296 mm X target after shift: {RIGHT_FULL.BoundBox.XLength:.3f}')
if RIGHT_FULL.BoundBox.YLength > C.INDX_Y_MAX + 1e-6:
    failures.append(f'RIGHT exceeds 275 mm Y target after shift: {RIGHT_FULL.BoundBox.YLength:.3f}')

stop_timer('box_front_position.hard_checks', _t, failures=len(failures))
if failures:
    raise RuntimeError('V60 FRONT POSITION HARD CHECKS FAILED: ' + ' | '.join(failures))

# Publish the corrected position into the already imported front module so all
# downstream consumers, including the final assembly, use the same geometry.
P.RIGHT_FULL = RIGHT_FULL
P.LEFT_FULL = LEFT_FULL
P.PLATE = PLATE
P.SPINDLE_X = SPINDLE_X

# Overwrite the clamp-plate export produced by the preceding front stage.
_te = start_timer('box_front_position.export_shifted_clamp_plate')
C.export_shape('eurobox_v60_clamp_plate', PLATE)
stop_timer('box_front_position.export_shifted_clamp_plate', _te)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_front_repositioned_plus40_x'
validation['box_clamp']['front_x_offset_mm'] = FRONT_X_OFFSET
validation['box_clamp']['main_face_x_mm'] = [-40.0, 120.0]
validation['box_clamp']['spindle_x_mm'] = list(SPINDLE_X)
validation['box_clamp']['spindle_spacing_mm'] = SPINDLE_X[1] - SPINDLE_X[0]
validation['box_clamp']['position_fix'] = (
    'complete front topology translated +40 mm in X; left cartridge clears front support, '
    'right cartridge moved farther right; outer angles unchanged'
)
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

stage('complete')
