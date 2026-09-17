import json
import math
import os

import FreeCAD as App
import Part

import build_v60_full_baseline as F

C = F.C

# ---------------------------------------------------------------------------
# Final v60 box-clamp front
# ---------------------------------------------------------------------------
# v50's final mechanism is the authority for the clamp FUNCTION:
#   * the moving plate is driven by two RH8x2 spindles;
#   * the BASE itself has NO working lead thread;
#   * each spindle runs in a separate removable threaded lead-nut cartridge;
#   * the cartridge is positively retained by a cross-pin + external C-clip.
#
# v60 keeps the requested 160 mm plate and +/-65 mm spindle axes, but restores
# that v50 architecture.  The previous v60 front also filled every free X-field
# with triangular/V-shaped DROPs.  Those are intentionally gone.  The front is
# supported by two v50-style outer Y/Z DROPs located outside the moving plate's
# X envelope, plus the rectangular screw-cartridge housings.

PLATE_X = 160.0
SPINDLE_X = (-65.0, 65.0)
SPINDLE_SPACING = SPINDLE_X[1] - SPINDLE_X[0]
PLATE_EDGE_MARGIN = PLATE_X / 2.0 - abs(SPINDLE_X[1])
PLATE_SWEEP_HALF_X = PLATE_X / 2.0 + 0.40
GUIDE_W = 7.60
FRAME_X0 = -PLATE_SWEEP_HALF_X - GUIDE_W
FRAME_X1 = PLATE_SWEEP_HALF_X + GUIDE_W
FRAME_W = FRAME_X1 - FRAME_X0
DECK_X0 = -PLATE_SWEEP_HALF_X
DECK_X1 = PLATE_SWEEP_HALF_X

BOSS_HALF_X = 11.0
BOSS_LOWER_HALF_X = 11.35

# v50-style outer supports.  Keep them outside the 160 mm moving plate in X,
# but do NOT resurrect the obsolete outboard-in-Y cage that exceeded 600 mm.
OUTER_DROP_OVERLAP_X = 0.80
OUTER_DROP_X_LIMIT = abs(C.FRONT_CLAMP_X - C.FIXED_STATION_HALF_X) - 0.50
LEFT_DROP_X0 = -OUTER_DROP_X_LIMIT
LEFT_DROP_X1 = DECK_X0 + OUTER_DROP_OVERLAP_X
RIGHT_DROP_X0 = DECK_X1 - OUTER_DROP_OVERLAP_X
RIGHT_DROP_X1 = OUTER_DROP_X_LIMIT
DROP_TOP_Y0 = F.CAGE_Y0
DROP_TOP_Y1 = F.CAGE_Y0 + 4.0
DROP_SLOPE_Y1 = F.CAGE_Y1 - 0.50
DROP_LOW_Y1 = F.PRINT_GUIDE_Y1
DROP_TOP_Z = F.PRINT_BASE_PLANE_Z
DROP_LOW_Z1 = F.FINAL_DECK_Z1
DROP_LOW_Z0 = F.FINAL_DECK_Z0
DROP_RISE = DROP_TOP_Z - DROP_LOW_Z1
DROP_RUN = DROP_SLOPE_Y1 - DROP_TOP_Y1
DROP_FLANK_ANGLE = math.degrees(math.atan2(DROP_RISE, DROP_RUN))

# Separate lead-nut cartridge, copied from the final v50 architecture and
# re-oriented for the already-inboard v60 spindle direction.  v50's lower tail
# cleared an 8x8 drive by 0.5 mm.  v60 uses the larger 10 AF hex drive, whose
# vertex reaches 5.7735 mm below the spindle axis.  Lower the tail/pin together
# so the retainer has >0.7 mm real clearance to that drive at nominal phase.
LEAD_NUT_BODY_HALF_X = 8.0
LEAD_NUT_BODY_HALF_Z = 7.0
LEAD_NUT_TAIL_L = 5.5
LEAD_NUT_TAIL_HALF_X = 6.0
LEAD_NUT_TAIL_Z0 = -12.0
LEAD_NUT_TAIL_H = 5.5
LEAD_NUT_PIN_HOLE_D = 3.4
LEAD_NUT_PIN_LOCAL_Y = -(F.NUT_THREAD_LEN + 2.75)
LEAD_NUT_PIN_LOCAL_Z = -9.25

NUT_PIN_SHAFT_D = 3.0
NUT_PIN_GROOVE_D = 2.4
NUT_PIN_GROOVE_W = 1.6
NUT_PIN_HEAD_D = 6.5
NUT_PIN_HEAD_T = 2.0
NUT_PIN_X0 = -11.4
NUT_PIN_GROOVE_X0 = 11.4
NUT_PIN_END_X1 = 14.5
NUT_PIN_CLIP_OUTER_R = 3.8
NUT_PIN_CLIP_INNER_R = 1.30
NUT_PIN_CLIP_T = 1.4
NUT_PIN_CLIP_OPENING_W = 1.90
NUT_PIN_CLIP_X = NUT_PIN_GROOVE_X0 + (NUT_PIN_GROOVE_W - NUT_PIN_CLIP_T) / 2.0


def stage(msg):
    print('V60_BOX_CLAMP_FINAL ' + msg, flush=True)


def lead_rotation_deg(travel):
    # The production spindle master is already rotated 180 degrees about Z.
    # In that final installed coordinate system, opening in -Y follows the
    # RH8x2 helix with positive rotation about global +Y.  This is also the
    # direction proven by the baseline thread-motion gate.
    return 360.0 * travel / F.THREAD_PITCH


def wider_plate_sweep():
    return C.box(
        -PLATE_SWEEP_HALF_X,
        C.PLATE_SWEEP_Y0,
        C.PLATE_SWEEP_Z0,
        2.0 * PLATE_SWEEP_HALF_X,
        C.PLATE_SWEEP_Y1 - C.PLATE_SWEEP_Y0,
        C.PLATE_SWEEP_Z1 - C.PLATE_SWEEP_Z0,
    )


def make_outer_drop(x0, x1, label):
    # This is the v50 printability concept: a broad outer connector descends in
    # Y/Z with one support-free flank.  It is not a row of X/Z triangles.
    pts = [
        App.Vector(x0, DROP_TOP_Y0, DROP_TOP_Z),
        App.Vector(x0, DROP_TOP_Y1, DROP_TOP_Z),
        App.Vector(x0, DROP_SLOPE_Y1, DROP_LOW_Z1),
        App.Vector(x0, DROP_LOW_Y1, DROP_LOW_Z1),
        App.Vector(x0, DROP_LOW_Y1, DROP_LOW_Z0),
        App.Vector(x0, DROP_TOP_Y0, DROP_LOW_Z0),
        App.Vector(x0, DROP_TOP_Y0, DROP_TOP_Z),
    ]
    q = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(x1 - x0, 0, 0)).removeSplitter()
    C.require_single(q, label)
    return q


def build_lead_nut():
    body = C.box(
        -LEAD_NUT_BODY_HALF_X,
        -F.NUT_THREAD_LEN,
        -LEAD_NUT_BODY_HALF_Z,
        2.0 * LEAD_NUT_BODY_HALF_X,
        F.NUT_THREAD_LEN,
        2.0 * LEAD_NUT_BODY_HALF_Z,
    )
    tail = C.box(
        -LEAD_NUT_TAIL_HALF_X,
        -F.NUT_THREAD_LEN - LEAD_NUT_TAIL_L,
        LEAD_NUT_TAIL_Z0,
        2.0 * LEAD_NUT_TAIL_HALF_X,
        LEAD_NUT_TAIL_L,
        LEAD_NUT_TAIL_H,
    )
    q = body.fuse(tail).removeSplitter()
    q = q.cut(F.FEMALE_NEGY).removeSplitter()
    q = q.cut(
        C.cyl_x(
            LEAD_NUT_PIN_HOLE_D / 2.0,
            20.0,
            -10.0,
            LEAD_NUT_PIN_LOCAL_Y,
            LEAD_NUT_PIN_LOCAL_Z,
        )
    ).removeSplitter()
    C.require_single(q, 'separate RH8x2 lead-nut cartridge')
    return q


def build_nut_pin():
    q = C.fuse_seq(
        [
            C.cyl_x(NUT_PIN_SHAFT_D / 2.0, NUT_PIN_GROOVE_X0 - NUT_PIN_X0,
                    NUT_PIN_X0, 0, 0),
            C.cyl_x(NUT_PIN_GROOVE_D / 2.0, NUT_PIN_GROOVE_W,
                    NUT_PIN_GROOVE_X0, 0, 0),
            C.cyl_x(
                NUT_PIN_SHAFT_D / 2.0,
                NUT_PIN_END_X1 - (NUT_PIN_GROOVE_X0 + NUT_PIN_GROOVE_W),
                NUT_PIN_GROOVE_X0 + NUT_PIN_GROOVE_W,
                0,
                0,
            ),
            C.cyl_x(NUT_PIN_HEAD_D / 2.0, NUT_PIN_HEAD_T,
                    NUT_PIN_X0 - NUT_PIN_HEAD_T, 0, 0),
        ],
        'lead-nut retaining pin',
    )
    C.require_single(q, 'lead-nut retaining pin')
    return q


stage('rebuild clean 160mm front from structural core')
CORE = C.RIGHT.cut(wider_plate_sweep()).removeSplitter()
C.require_single(CORE, 'RIGHT core with 160mm moving-plate corridor')

LEFT_OUTER_DROP = make_outer_drop(LEFT_DROP_X0, LEFT_DROP_X1, 'left outer v50-style DROP')
RIGHT_OUTER_DROP = make_outer_drop(RIGHT_DROP_X0, RIGHT_DROP_X1, 'right outer v50-style DROP')

parts = [
    C.box(FRAME_X0, F.PRINT_GUIDE_Y0, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y1 - F.PRINT_GUIDE_Y0,
          F.PRINT_BASE_PLANE_Z - F.PRINT_GUIDE_Z0),
    C.box(PLATE_SWEEP_HALF_X, F.PRINT_GUIDE_Y0, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y1 - F.PRINT_GUIDE_Y0,
          F.PRINT_BASE_PLANE_Z - F.PRINT_GUIDE_Z0),
    C.box(FRAME_X0, F.CAGE_Y0 - 0.10,
          F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_TIE_T,
          FRAME_W, F.CAGE_Y1 - F.CAGE_Y0 + 0.20, F.PRINT_FRAME_TIE_T),
    C.box(DECK_X0, F.CAGE_Y0, F.FINAL_DECK_Z0,
          DECK_X1 - DECK_X0, F.PRINT_GUIDE_Y1 - F.CAGE_Y0,
          F.FINAL_DECK_Z1 - F.FINAL_DECK_Z0),
    C.box(FRAME_X0, F.CAGE_Y0 - 0.10, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y0 - (F.CAGE_Y0 - 0.10) + 0.35,
          F.PRINT_BASE_PLANE_Z - F.PRINT_GUIDE_Z0),
    C.box(PLATE_SWEEP_HALF_X, F.CAGE_Y0 - 0.10, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y0 - (F.CAGE_Y0 - 0.10) + 0.35,
          F.PRINT_BASE_PLANE_Z - F.PRINT_GUIDE_Z0),
    C.box(-PLATE_SWEEP_HALF_X - F.GUIDE_STITCH_OVERLAP,
          F.CAGE_Y0, F.FINAL_DECK_Z1 - F.GUIDE_STITCH_OVERLAP,
          2.0 * F.GUIDE_STITCH_OVERLAP,
          F.PRINT_GUIDE_Y1 - F.CAGE_Y0,
          2.0 * F.GUIDE_STITCH_OVERLAP),
    C.box(PLATE_SWEEP_HALF_X - F.GUIDE_STITCH_OVERLAP,
          F.CAGE_Y0, F.FINAL_DECK_Z1 - F.GUIDE_STITCH_OVERLAP,
          2.0 * F.GUIDE_STITCH_OVERLAP,
          F.PRINT_GUIDE_Y1 - F.CAGE_Y0,
          2.0 * F.GUIDE_STITCH_OVERLAP),
    LEFT_OUTER_DROP,
    RIGHT_OUTER_DROP,
]

for sx in SPINDLE_X:
    parts.append(C.box(
        sx - BOSS_HALF_X,
        F.CAGE_Y0,
        F.PRINT_FRAME_BOSS_Z0,
        2.0 * BOSS_HALF_X,
        F.CAGE_Y1 - F.CAGE_Y0,
        F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_BOSS_Z0,
    ))
    parts.append(C.box(
        sx - BOSS_LOWER_HALF_X,
        F.CAGE_Y0,
        F.FINAL_DECK_Z1 - 0.35,
        2.0 * BOSS_LOWER_HALF_X,
        F.CAGE_Y1 - F.CAGE_Y0,
        F.PRINT_FRAME_BOSS_Z0 - (F.FINAL_DECK_Z1 - 0.35) + 0.35,
    ))

CAGE = C.fuse_seq(parts, 'v60-v50-style-separate-nut-box-clamp-cage')
RIGHT_FULL = CORE.fuse(CAGE).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT front before cartridge pockets')

stage('machine smooth cartridge pockets and service access')
LEAD_NUT = build_lead_nut()
NUT_PIN = build_nut_pin()
NUT_PIN_CLIP = F.make_c_clip(
    NUT_PIN_CLIP_OUTER_R,
    NUT_PIN_CLIP_INNER_R,
    NUT_PIN_CLIP_T,
    NUT_PIN_CLIP_OPENING_W,
)

NUT_TAIL_Y0 = F.NUT_THREAD_Y0 - LEAD_NUT_TAIL_L
PIN_Y = F.NUT_Y0 + LEAD_NUT_PIN_LOCAL_Y
PIN_Z = F.SPINDLE_Z + LEAD_NUT_PIN_LOCAL_Z

for sx in SPINDLE_X:
    nut_pocket = C.box(
        sx - 8.35,
        F.NUT_THREAD_Y0 - 0.35,
        F.SPINDLE_Z - LEAD_NUT_BODY_HALF_Z - 0.35,
        16.70,
        F.NUT_THREAD_LEN + 0.70,
        2.0 * LEAD_NUT_BODY_HALF_Z + 0.70,
    )
    tail_pocket = C.box(
        sx - 6.20,
        NUT_TAIL_Y0 - 0.25,
        F.SPINDLE_Z + LEAD_NUT_TAIL_Z0 - 0.25,
        12.40,
        LEAD_NUT_TAIL_L + 0.50,
        LEAD_NUT_TAIL_H + 0.50,
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
    pin_bore = C.cyl_x(LEAD_NUT_PIN_HOLE_D / 2.0, 24.0, sx - 12.0, PIN_Y, PIN_Z)
    head_service = C.cyl_x(3.55, 3.0, sx - 14.0, PIN_Y, PIN_Z)
    clip_service = C.cyl_x(4.10, 4.0, sx + 11.0, PIN_Y, PIN_Z)
    for cutter in (nut_pocket, tail_pocket, spindle_tunnel,
                   pin_bore, head_service, clip_service):
        RIGHT_FULL = RIGHT_FULL.cut(cutter).removeSplitter()

C.require_single(RIGHT_FULL, 'RIGHT final v50-style separate-nut front')
LEFT_FULL = C.mirror_x(RIGHT_FULL)
C.require_single(LEFT_FULL, 'LEFT final v50-style separate-nut front')

stage('build 160mm moving clamp plate')
PLATE_BODY_Y0 = C.BOX_RIM_INNER_Y - F.PLATE_Y
PLATE_HOOK_Y0 = C.BOX_RIM_INNER_Y - F.WIDTH_RIM_CLEAR
PLATE_HOOK_Y1 = C.BOX_RIM_INNER_Y + F.UNDERHOOK
PLATE = C.box(
    -PLATE_X / 2.0,
    PLATE_BODY_Y0,
    F.PLATE_Z0,
    PLATE_X,
    F.PLATE_Y,
    F.PLATE_Z1 - F.PLATE_Z0,
)
PLATE = PLATE.fuse(C.box(
    -PLATE_X / 2.0,
    PLATE_HOOK_Y0,
    F.RIM_BOTTOM_Z - F.UNDERHOOK_T,
    PLATE_X,
    PLATE_HOOK_Y1 - PLATE_HOOK_Y0,
    F.UNDERHOOK_T,
))
for sx in SPINDLE_X:
    PLATE = PLATE.cut(F.cyl_y(
        F.PLATE_HOLE_D / 2.0,
        F.PLATE_Y + 1.0,
        sx,
        PLATE_BODY_Y0 - 0.5,
        F.SPINDLE_Z,
    ))
    PLATE = PLATE.cut(F.cyl_y(
        6.0,
        2.0,
        sx,
        F.PLATE_SPINDLE_Y - 2.0,
        F.SPINDLE_Z,
    ))
PLATE = PLATE.removeSplitter()
C.require_single(PLATE, '160mm moving box-clamp plate')

stage('hard-check mechanical function')
failures = []


def fail(msg):
    failures.append(msg)


if tuple(SPINDLE_X) != (-65.0, 65.0):
    fail('final screw axes are not +/-65 mm')
if abs(PLATE_X - 160.0) > 1e-9:
    fail('final clamp plate is not 160 mm wide')
if abs(PLATE_EDGE_MARGIN - 15.0) > 1e-9:
    fail('final spindle edge margin is not 15 mm')
if DROP_FLANK_ANGLE < 45.0:
    fail(f'outer support DROP is not support-free: {DROP_FLANK_ANGLE:.3f} deg')

outer_drop_checks = []
for side, drop, x0, x1 in (
    ('left', LEFT_OUTER_DROP, LEFT_DROP_X0, LEFT_DROP_X1),
    ('right', RIGHT_OUTER_DROP, RIGHT_DROP_X0, RIGHT_DROP_X1),
):
    frac = RIGHT_FULL.common(drop).Volume / drop.Volume
    outside_plate = (x1 <= -PLATE_X / 2.0 + OUTER_DROP_OVERLAP_X + 1e-6
                     if side == 'left'
                     else x0 >= PLATE_X / 2.0 - OUTER_DROP_OVERLAP_X - 1e-6)
    outer_drop_checks.append({
        'side': side,
        'x_mm': [round(x0, 3), round(x1, 3)],
        'outside_plate_x': bool(outside_plate),
        'y_mm': [round(DROP_TOP_Y0, 3), round(DROP_LOW_Y1, 3)],
        'flank_angle_from_horizontal_deg': round(DROP_FLANK_ANGLE, 3),
        'material_fraction': round(frac, 6),
    })
    if not outside_plate:
        fail(f'{side} outer DROP moved into moving plate X envelope')
    if frac < 0.995:
        fail(f'{side} outer DROP not materially fused: {frac:.6f}')

rim = C.box(-220.0, C.BOX_RIM_INNER_Y, F.RIM_BOTTOM_Z, 440.0, C.RIM_Y, C.RIM_H)
plate_motion = []
for travel in (-0.5, 0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 5.5):
    pl = PLATE.copy()
    pl.translate(App.Vector(0, -travel, 0))
    base_common = RIGHT_FULL.common(pl).Volume
    rim_common = rim.common(pl).Volume
    plate_motion.append({
        'travel_mm': travel,
        'base_common_mm3': round(base_common, 6),
        'rim_common_mm3': round(rim_common, 6),
    })
    if base_common > 1e-4:
        fail(f'plate/base collision at travel={travel}: {base_common:.6f}')
    if travel >= 0.0 and rim_common > 1e-4:
        fail(f'plate/rim collision at open travel={travel}: {rim_common:.6f}')
    if travel < 0.0 and rim_common < 1.0:
        fail('0.5mm preload does not reach the box rim')

base_thread_void = []
for sx in SPINDLE_X:
    probe = F.cyl_y(
        F.THREAD_FEMALE_MAJOR_R + 0.15,
        F.NUT_THREAD_LEN - 0.4,
        sx,
        F.NUT_THREAD_Y0 + 0.2,
        F.SPINDLE_Z,
    )
    common = RIGHT_FULL.common(probe).Volume
    base_thread_void.append({'x_mm': sx, 'base_common_mm3': round(common, 6)})
    if common > 1e-4:
        fail(f'BASE still contains material in separate lead-nut working-thread volume X={sx}: {common:.6f}')

cartridge_checks = []
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy()
    nut.translate(App.Vector(sx, F.NUT_Y0, F.SPINDLE_Z))
    nut_base_common = RIGHT_FULL.common(nut).Volume
    nut_base_distance = RIGHT_FULL.distToShape(nut)[0]

    pin = NUT_PIN.copy()
    pin.translate(App.Vector(sx, PIN_Y, PIN_Z))
    pin_base_common = RIGHT_FULL.common(pin).Volume
    pin_nut_common = nut.common(pin).Volume

    clip = NUT_PIN_CLIP.copy()
    clip.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
    clip.translate(App.Vector(sx + NUT_PIN_CLIP_X, PIN_Y, PIN_Z))
    clip_base_common = RIGHT_FULL.common(clip).Volume
    clip_pin_common = pin.common(clip).Volume
    clip_pin_distance = pin.distToShape(clip)[0]

    cartridge_checks.append({
        'x_mm': sx,
        'nut_base_common_mm3': round(nut_base_common, 6),
        'nut_base_distance_mm': round(nut_base_distance, 6),
        'pin_base_common_mm3': round(pin_base_common, 6),
        'pin_nut_common_mm3': round(pin_nut_common, 6),
        'clip_base_common_mm3': round(clip_base_common, 6),
        'clip_pin_common_mm3': round(clip_pin_common, 6),
        'clip_pin_distance_mm': round(clip_pin_distance, 6),
    })
    if nut_base_common > 1e-4 or nut_base_distance > 0.60:
        fail(f'lead-nut cartridge does not fit/locate in BASE pocket X={sx}')
    if pin_base_common > 1e-4 or pin_nut_common > 1e-4:
        fail(f'lead-nut retaining pin is blocked X={sx}')
    if clip_base_common > 1e-4 or clip_pin_common > 1e-4:
        fail(f'lead-nut retaining clip collides X={sx}')
    if not (0.04 <= clip_pin_distance <= 0.18):
        fail(f'lead-nut clip/groove radial clearance implausible X={sx}: {clip_pin_distance:.6f}')

thread_motion = []
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy()
    nut.translate(App.Vector(sx, F.NUT_Y0, F.SPINDLE_Z))
    for travel in (-0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.5):
        spindle = F.SPINDLE.copy()
        rotation = lead_rotation_deg(travel)
        spindle.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), rotation)
        spindle.translate(App.Vector(sx, F.PLATE_SPINDLE_Y - travel, F.SPINDLE_Z))
        nut_common = nut.common(spindle).Volume
        base_common = RIGHT_FULL.common(spindle).Volume
        thread_motion.append({
            'x_mm': sx,
            'travel_mm': travel,
            'rotation_deg': rotation,
            'nut_common_mm3': round(nut_common, 6),
            'base_common_mm3': round(base_common, 6),
        })
        if nut_common > 1.0:
            fail(f'correct RH8x2 cartridge phase collides X={sx} travel={travel}: {nut_common:.6f}')
        if base_common > 1.0:
            fail(f'spindle collides with smooth BASE X={sx} travel={travel}: {base_common:.6f}')

nut0 = LEAD_NUT.copy()
nut0.translate(App.Vector(SPINDLE_X[0], F.NUT_Y0, F.SPINDLE_Z))
axial_wrong = F.SPINDLE.copy()
axial_wrong.translate(App.Vector(SPINDLE_X[0], F.PLATE_SPINDLE_Y - 0.5, F.SPINDLE_Z))
axial_wrong_common = nut0.common(axial_wrong).Volume
wrong_phase = F.SPINDLE.copy()
wrong_phase_rotation = lead_rotation_deg(0.5) + 180.0
wrong_phase.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), wrong_phase_rotation)
wrong_phase.translate(App.Vector(SPINDLE_X[0], F.PLATE_SPINDLE_Y - 0.5, F.SPINDLE_Z))
wrong_phase_common = nut0.common(wrong_phase).Volume
correct_half = next(q['nut_common_mm3'] for q in thread_motion
                    if q['x_mm'] == SPINDLE_X[0] and q['travel_mm'] == 0.5)
if axial_wrong_common < correct_half + 0.50:
    fail(f'lead-nut cartridge does not reject axial slide without rotation: {axial_wrong_common:.6f}')
if wrong_phase_common < correct_half + 0.50:
    fail(f'lead-nut cartridge lacks phase-sensitive RH8x2 engagement: {wrong_phase_common:.6f}')

left_back = C.mirror_x(LEFT_FULL)
mirror_delta = abs(RIGHT_FULL.Volume - left_back.Volume)
if mirror_delta > 1e-4:
    fail(f'handed bases not exact mirrors: {mirror_delta:.6f}')


def local_y_extent(travel):
    plate = PLATE.copy(); plate.translate(App.Vector(0, -travel, 0))
    spindle = F.SPINDLE.copy()
    spindle.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), lead_rotation_deg(travel))
    spindle.translate(App.Vector(0, F.PLATE_SPINDLE_Y - travel, F.SPINDLE_Z))
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(0, F.NUT_Y0, F.SPINDLE_Z))
    pin = NUT_PIN.copy(); pin.translate(App.Vector(0, PIN_Y, PIN_Z))
    clip = NUT_PIN_CLIP.copy(); clip.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
    clip.translate(App.Vector(NUT_PIN_CLIP_X, PIN_Y, PIN_Z))
    return max(sh.BoundBox.YMax for sh in (RIGHT_FULL, plate, spindle, nut, pin, clip))


width_states = {str(v): local_y_extent(v) for v in (-0.5, 0.0, 5.5)}
holder_half = C.RACK_CTC / 2.0 + max(width_states.values())
effective_width = max(C.BOX_W, 2.0 * holder_half)
if holder_half > C.BOX_W / 2.0 + 0.02:
    fail(f'complete holder exceeds 600 mm Eurobox width: {2.0 * holder_half:.3f} mm')

for side, shape in (('RIGHT', RIGHT_FULL), ('LEFT', LEFT_FULL)):
    if shape.BoundBox.XLength > C.V60_X_TARGET_MAX + 1e-6:
        fail(f'{side} exceeds 296 mm X target: {shape.BoundBox.XLength:.3f}')
    if shape.BoundBox.YLength > C.INDX_Y_MAX + 1e-6:
        fail(f'{side} exceeds 275 mm Y target: {shape.BoundBox.YLength:.3f}')

if failures:
    raise RuntimeError('V60 FINAL BOX CLAMP HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('publish canonical front variables and exports')
F.RIGHT_FULL = RIGHT_FULL
F.LEFT_FULL = LEFT_FULL
F.PLATE = PLATE
F.SPINDLE_X = SPINDLE_X

for name, shape in (
    ('eurobox_v60_clamp_plate', PLATE),
    ('eurobox_v60_lead_nut', LEAD_NUT),
    ('eurobox_v60_lead_nut_retaining_pin', NUT_PIN),
    ('eurobox_v60_lead_nut_pin_clip', NUT_PIN_CLIP),
):
    C.require_single(shape, name)
    C.export_shape(name, shape)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_v50_separate_lead_nut_outer_drops'
validation['base']['right_bbox_mm'] = [
    round(RIGHT_FULL.BoundBox.XLength, 3),
    round(RIGHT_FULL.BoundBox.YLength, 3),
    round(RIGHT_FULL.BoundBox.ZLength, 3),
]
validation['base']['left_bbox_mm'] = [
    round(LEFT_FULL.BoundBox.XLength, 3),
    round(LEFT_FULL.BoundBox.YLength, 3),
    round(LEFT_FULL.BoundBox.ZLength, 3),
]
validation['base']['mirror_delta_mm3'] = round(mirror_delta, 9)
validation['box_clamp'] = {
    'architecture': 'v50 separate RH8x2 lead-nut cartridge; smooth BASE; outer Y/Z support DROPs',
    'plate_width_mm': PLATE_X,
    'plate_travel_mm': F.PLATE_OPEN,
    'plate_preload_mm': 0.5,
    'spindle_x_mm': list(SPINDLE_X),
    'spindle_spacing_mm': SPINDLE_SPACING,
    'spindle_z_mm': F.SPINDLE_Z,
    'plate_screw_edge_margin_mm': PLATE_EDGE_MARGIN,
    'lead_nut_mode': 'separate_RH8x2_cartridge_cross_pin_external_C_clip',
    'integral_female_threads': False,
    'base_has_working_lead_thread': False,
    'triangular_front_drops': False,
    'outer_guide_blocks_outside_plate_x': True,
    'outer_support_drops': outer_drop_checks,
    'base_thread_void_checks': base_thread_void,
    'cartridge_checks': cartridge_checks,
    'thread_motion': thread_motion,
    'axial_slide_without_rotation_common_mm3': round(axial_wrong_common, 6),
    'half_pitch_wrong_phase_common_mm3': round(wrong_phase_common, 6),
    'plate_motion': plate_motion,
    'width_states_local_y_mm': {k: round(v, 3) for k, v in width_states.items()},
    'effective_total_width_mm': round(effective_width, 3),
}
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

with open(os.path.join(C.OUT, 'README_BUILD_v60_full.txt'), 'a', encoding='utf-8') as fh:
    fh.write(
        '\nFinal box clamp: v50 separate RH8x2 lead-nut cartridge with cross-pin/C-clip; '
        'smooth BASE; 160 mm plate at +/-65 mm; two outer Y/Z DROPs and no triangular front teeth.\n'
    )

stage('complete')
