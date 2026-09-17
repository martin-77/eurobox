import json
import os

import FreeCAD as App
import Part

import apply_v60_front_final as P
import build_v60 as C
import build_v60_continuous_carrier as CC
import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

# Installed-orientation correction.  Keep the complete 160 mm clamp mechanism
# together and move it on the asymmetric carrier; do not move the rack datums.
FRONT_X_OFFSET = 40.0
PLATE_CENTER_X = FRONT_X_OFFSET
SPINDLE_X = tuple(x + FRONT_X_OFFSET for x in P.SPINDLE_X)

# v50 service architecture, applied at the corrected v60 X positions:
# the BASE contains only a smooth cradle/pocket.  The working RH8x2 female
# thread lives in a removable cartridge with a lower retaining tail.  Remove the
# external C-clip and cross-pin, unscrew/remove the spindle, then slide the
# cartridge out toward +Y through an explicit service mouth.  The cartridge is
# therefore a wear/service part; the carrier itself never has to be replaced for
# a worn lead thread.
SERVICE_BODY_CLEAR = 0.35
SERVICE_TAIL_CLEAR_X = 0.20
SERVICE_TAIL_CLEAR_Y = 0.25
SERVICE_TAIL_CLEAR_Z = 0.25
SERVICE_MOUTH_EXTRA_Y = 1.0
SERVICE_EXTRACTION_STEPS = (0.0, 2.0, 5.0, 10.0, 16.0)


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
    # Start from the canonical continuous-carrier architecture.  Rebuilding the
    # carrier here is deliberate: the front corridor is now asymmetric in X and
    # must be cut from the actual production carrier, not from the old centred
    # box-clamp BRep.
    carrier = CC.make_continuous_carrier()
    front_support = C.make_long_support(C.FRONT_CLAMP_X, C.ARM_Y0)
    rear_support = C.make_long_support(C.REAR_SUPPORT_X, 0.0)
    raw = C.fuse_seq([
        carrier,
        front_support,
        rear_support,
        CC.make_hanging_upper_station(C.FRONT_CLAMP_X),
        CC.make_hanging_upper_station(C.REAR_CLAMP_X),
        CC.make_hanging_backstop(),
        C.make_crosshead(),
    ], 'RIGHT continuous structural core for shifted box clamp')

    raw = raw.cut(shifted_main_plate_sweep()).removeSplitter()
    for sx in SPINDLE_X:
        raw = raw.cut(shifted_ear_sweep(sx)).removeSplitter()

    # Structural fusions can refill the rack-clamp service bores. Re-open the
    # canonical rack paths before adding the independent box-clamp cradle.
    for xc in C.CLAMP_X:
        raw = raw.cut(C.cyl_x(C.UPPER_SADDLE_R, 40.0, xc - 20.0, 0.0, 0.0)).removeSplitter()
        raw = raw.cut(C.cyl_x(C.PIN_HOLE_D / 2.0, 40.0, xc - 20.0, C.PIN_Y, C.PIN_Z)).removeSplitter()
        raw = raw.cut(
            Part.makeCylinder(
                C.RACK_M4_BASE_CLEAR_D / 2.0,
                12.0,
                App.Vector(xc, C.RACK_CLOSURE_Y, -1.0),
                App.Vector(0, 0, 1),
            )
        ).removeSplitter()

    print(
        'V60_FRONT_POSITION shifted continuous core solids=' + str(len(raw.Solids)) +
        ' volumes=' + str([round(s.Volume, 3) for s in raw.Solids]),
        flush=True,
    )
    C.require_single(raw, 'RIGHT continuous structural core with shifted box-clamp corridor')
    return raw


def shifted_copy(shape):
    q = shape.copy()
    q.translate(App.Vector(FRONT_X_OFFSET, 0, 0))
    return q


def make_service_cage():
    # Recreate the fixed front explicitly instead of translating P.CAGE as an
    # opaque solid.  This keeps the broad v50-style Y/Z drops but makes the two
    # screw towers service cradles whose pocket/mouth geometry is defined here.
    parts = [
        # Bed-side tie between both service towers.
        C.box(
            P.FRAME_X0 + FRONT_X_OFFSET,
            F.CAGE_Y0 - 0.10,
            F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_TIE_T,
            P.FRAME_W,
            F.CAGE_Y1 - F.CAGE_Y0 + 0.20,
            F.PRINT_FRAME_TIE_T,
        ),
        # Central low deck under the 160 mm moving face.
        C.box(
            P.DECK_X0 + FRONT_X_OFFSET,
            F.CAGE_Y0,
            F.FINAL_DECK_Z0,
            P.DECK_X1 - P.DECK_X0,
            F.PRINT_GUIDE_Y1 - F.CAGE_Y0,
            F.FINAL_DECK_Z1 - F.FINAL_DECK_Z0,
        ),
        # Only lower lateral guides; the two screws retain the plate vertically.
        C.box(
            -P.GUIDE_OUTER_X + FRONT_X_OFFSET,
            F.PRINT_GUIDE_Y0,
            P.GUIDE_Z0,
            P.GUIDE_W,
            F.PRINT_GUIDE_Y1 - F.PRINT_GUIDE_Y0,
            P.GUIDE_Z1 - P.GUIDE_Z0,
        ),
        C.box(
            P.GUIDE_INNER_X + FRONT_X_OFFSET,
            F.PRINT_GUIDE_Y0,
            P.GUIDE_Z0,
            P.GUIDE_W,
            F.PRINT_GUIDE_Y1 - F.PRINT_GUIDE_Y0,
            P.GUIDE_Z1 - P.GUIDE_Z0,
        ),
        shifted_copy(P.LEFT_OUTER_DROP),
        shifted_copy(P.RIGHT_OUTER_DROP),
    ]

    # Closed service towers are cut open afterwards with one continuous
    # cartridge/extraction path.  This is the same mechanical principle as v50:
    # fixed cradle outside, replaceable RH8x2 wear cartridge inside.
    for sx in SPINDLE_X:
        parts.append(C.box(
            sx - P.BOSS_HALF_X,
            F.CAGE_Y0,
            F.PRINT_FRAME_BOSS_Z0,
            2.0 * P.BOSS_HALF_X,
            F.CAGE_Y1 - F.CAGE_Y0,
            F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_BOSS_Z0,
        ))
        parts.append(C.box(
            sx - P.BOSS_LOWER_HALF_X,
            F.CAGE_Y0,
            F.FINAL_DECK_Z1 - 0.35,
            2.0 * P.BOSS_LOWER_HALF_X,
            F.CAGE_Y1 - F.CAGE_Y0,
            F.PRINT_FRAME_BOSS_Z0 - (F.FINAL_DECK_Z1 - 0.35) + 0.35,
        ))

    q = C.fuse_seq(parts, 'shifted-v50-service-cartridge-front-cage')
    C.require_single(q, 'shifted v50 service cartridge cage')
    return q


def service_cutters(sx):
    body_z0 = F.SPINDLE_Z - P.LEAD_NUT_BODY_HALF_Z - SERVICE_BODY_CLEAR
    body_h = 2.0 * P.LEAD_NUT_BODY_HALF_Z + 2.0 * SERVICE_BODY_CLEAR

    # Normal running pocket around the threaded cartridge body.
    nut_pocket = C.box(
        sx - P.LEAD_NUT_BODY_HALF_X - SERVICE_BODY_CLEAR,
        F.NUT_THREAD_Y0 - SERVICE_BODY_CLEAR,
        body_z0,
        2.0 * (P.LEAD_NUT_BODY_HALF_X + SERVICE_BODY_CLEAR),
        F.NUT_THREAD_LEN + 2.0 * SERVICE_BODY_CLEAR,
        body_h,
    )

    # v50-style removable lower tail.  Unlike the previous v60 pocket, this lane
    # deliberately continues all the way to the +Y service face so the complete
    # cartridge can actually be slid out after its cross-pin is removed.
    tail_lane = C.box(
        sx - P.LEAD_NUT_TAIL_HALF_X - SERVICE_TAIL_CLEAR_X,
        P.NUT_TAIL_Y0 - SERVICE_TAIL_CLEAR_Y,
        F.SPINDLE_Z + P.LEAD_NUT_TAIL_Z0 - SERVICE_TAIL_CLEAR_Z,
        2.0 * (P.LEAD_NUT_TAIL_HALF_X + SERVICE_TAIL_CLEAR_X),
        (F.CAGE_Y1 + SERVICE_MOUTH_EXTRA_Y) - (P.NUT_TAIL_Y0 - SERVICE_TAIL_CLEAR_Y),
        P.LEAD_NUT_TAIL_H + 2.0 * SERVICE_TAIL_CLEAR_Z,
    )

    # Open only the cartridge body's own section at the outer service face.  The
    # side walls and the bed-side tie remain intact and carry spindle reaction.
    body_service_mouth = C.box(
        sx - P.LEAD_NUT_BODY_HALF_X - SERVICE_BODY_CLEAR,
        F.NUT_Y0 - SERVICE_BODY_CLEAR,
        body_z0,
        2.0 * (P.LEAD_NUT_BODY_HALF_X + SERVICE_BODY_CLEAR),
        (F.CAGE_Y1 + SERVICE_MOUTH_EXTRA_Y) - (F.NUT_Y0 - SERVICE_BODY_CLEAR),
        body_h,
    )

    tunnel_y0 = F.CAGE_Y0 - 0.50
    tunnel_y1 = F.PLATE_SPINDLE_Y - F.PLATE_Y + 0.50
    spindle_tunnel = F.cyl_y(5.90, tunnel_y1 - tunnel_y0, sx, tunnel_y0, F.SPINDLE_Z)

    # Cross-pin bearing bore plus external head/clip access.  Head and clip
    # pockets stay outside the ±11 mm tower faces, just as in the final v50
    # service design, so neither retainer is buried in the printed cradle.
    pin_bore = C.cyl_x(P.LEAD_NUT_PIN_HOLE_D / 2.0, 24.0, sx - 12.0, P.PIN_Y, P.PIN_Z)
    head_service = C.cyl_x(P.NUT_PIN_HEAD_D / 2.0 + 0.30, 3.0, sx - 14.0, P.PIN_Y, P.PIN_Z)
    clip_service = C.cyl_x(P.NUT_PIN_CLIP_OUTER_R + 0.30, 4.0, sx + 11.0, P.PIN_Y, P.PIN_Z)

    return {
        'nut_pocket': nut_pocket,
        'tail_lane': tail_lane,
        'body_service_mouth': body_service_mouth,
        'spindle_tunnel': spindle_tunnel,
        'pin_bore': pin_bore,
        'head_service': head_service,
        'clip_service': clip_service,
    }


def placed_cartridge(sx, extraction_y=0.0):
    q = P.LEAD_NUT.copy()
    q.translate(App.Vector(sx, F.NUT_Y0 + extraction_y, F.SPINDLE_Z))
    return q


def placed_pin(sx):
    q = P.NUT_PIN.copy()
    q.translate(App.Vector(sx, P.PIN_Y, P.PIN_Z))
    return q


def placed_clip(sx):
    q = P.NUT_PIN_CLIP.copy()
    q.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
    q.translate(App.Vector(sx + P.NUT_PIN_CLIP_X, P.PIN_Y, P.PIN_Z))
    return q


stage('rebuild corrected front with explicit v50 removable-cartridge service paths')
_t = start_timer('box_front_position.rebuild_shifted_front')
CORE = rebuild_raw_structural_core()
CAGE = make_service_cage()
RIGHT_FULL = CORE.fuse(CAGE).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT shifted continuous core after service-cage fusion')

SERVICE_CUTTERS = {}
for sx in SPINDLE_X:
    cutters = service_cutters(sx)
    SERVICE_CUTTERS[sx] = cutters
    for name in (
        'nut_pocket', 'tail_lane', 'body_service_mouth', 'spindle_tunnel',
        'pin_bore', 'head_service', 'clip_service',
    ):
        RIGHT_FULL = RIGHT_FULL.cut(cutters[name]).removeSplitter()
    C.require_single(RIGHT_FULL, f'RIGHT service cradle after machining X={sx}')

C.require_single(RIGHT_FULL, 'RIGHT final shifted serviceable box-clamp front')
LEFT_FULL = C.mirror_x(RIGHT_FULL)
C.require_single(LEFT_FULL, 'LEFT final shifted serviceable box-clamp front')

PLATE = P.PLATE.copy()
PLATE.translate(App.Vector(FRONT_X_OFFSET, 0, 0))
C.require_single(PLATE, 'shifted 160 mm moving clamp face')
stop_timer('box_front_position.rebuild_shifted_front', _t)

stage('hard-check shifted positions, motion and cartridge serviceability')
_t = start_timer('box_front_position.hard_checks')
failures = []

if SPINDLE_X != (-48.0, 128.0):
    failures.append(f'unexpected shifted spindle positions: {SPINDLE_X}')
expected_min = -58.0
expected_max = 138.0
if abs(PLATE.BoundBox.XMin - expected_min) > 1e-6 or abs(PLATE.BoundBox.XMax - expected_max) > 1e-6:
    failures.append(f'shifted plate/ears bbox wrong: {PLATE.BoundBox.XMin:.3f}..{PLATE.BoundBox.XMax:.3f}')
if abs(SPINDLE_X[0] - C.FRONT_CLAMP_X) < 20.0:
    failures.append('left cartridge still too close to front support/angle region')
if SPINDLE_X[1] < 120.0:
    failures.append('right cartridge was not moved far enough right')

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
            failures.append(f'shifted spindle/base collision X={sx} travel={travel}: {base_common:.6f}')

service_checks = []
for sx in SPINDLE_X:
    installed = placed_cartridge(sx)
    installed_common = RIGHT_FULL.common(installed).Volume
    if installed_common > 1e-4:
        failures.append(f'service cartridge collides with BASE X={sx}: {installed_common:.6f}')

    extraction = []
    for dy in SERVICE_EXTRACTION_STEPS:
        q = placed_cartridge(sx, dy)
        common = RIGHT_FULL.common(q).Volume
        extraction.append({'travel_y_mm': dy, 'base_common_mm3': round(common, 6)})
        if common > 1e-4:
            failures.append(
                f'cartridge extraction path blocked X={sx} +Y={dy}: {common:.6f}'
            )

    pin = placed_pin(sx)
    clip = placed_clip(sx)
    pin_base_common = RIGHT_FULL.common(pin).Volume
    clip_base_common = RIGHT_FULL.common(clip).Volume
    pin_nut_common = pin.common(installed).Volume
    if pin_base_common > 1e-4:
        failures.append(f'cartridge retaining pin buried in BASE X={sx}: {pin_base_common:.6f}')
    if clip_base_common > 1e-4:
        failures.append(f'cartridge C-clip buried in BASE X={sx}: {clip_base_common:.6f}')
    if pin_nut_common > 1e-4:
        failures.append(f'cartridge retaining pin collides with cartridge X={sx}: {pin_nut_common:.6f}')

    # The service mouth itself must be fully open in the final production BRep.
    mouth_common = RIGHT_FULL.common(SERVICE_CUTTERS[sx]['body_service_mouth']).Volume
    tail_lane_common = RIGHT_FULL.common(SERVICE_CUTTERS[sx]['tail_lane']).Volume
    if mouth_common > 1e-4:
        failures.append(f'cartridge body service mouth not open X={sx}: {mouth_common:.6f}')
    if tail_lane_common > 1e-4:
        failures.append(f'cartridge tail extraction lane not open X={sx}: {tail_lane_common:.6f}')

    service_checks.append({
        'x_mm': sx,
        'installed_base_common_mm3': round(installed_common, 6),
        'pin_base_common_mm3': round(pin_base_common, 6),
        'pin_nut_common_mm3': round(pin_nut_common, 6),
        'clip_base_common_mm3': round(clip_base_common, 6),
        'service_mouth_base_common_mm3': round(mouth_common, 6),
        'tail_lane_base_common_mm3': round(tail_lane_common, 6),
        'extraction_path': extraction,
    })

if RIGHT_FULL.BoundBox.XLength > C.V60_X_TARGET_MAX + 1e-6:
    failures.append(f'RIGHT exceeds 296 mm X target after shift: {RIGHT_FULL.BoundBox.XLength:.3f}')
if RIGHT_FULL.BoundBox.YLength > C.INDX_Y_MAX + 1e-6:
    failures.append(f'RIGHT exceeds 275 mm Y target after shift: {RIGHT_FULL.BoundBox.YLength:.3f}')

stop_timer('box_front_position.hard_checks', _t, failures=len(failures))
if failures:
    raise RuntimeError('V60 FRONT POSITION/SERVICE HARD CHECKS FAILED: ' + ' | '.join(failures))

# Publish the corrected front into the canonical module namespace consumed by
# rack closure and final assembly.  Hardware remains the exact v50-derived
# removable cartridge/pin/clip geometry from apply_v60_front_final.
P.RIGHT_FULL = RIGHT_FULL
P.LEFT_FULL = LEFT_FULL
P.CAGE = CAGE
P.PLATE = PLATE
P.SPINDLE_X = SPINDLE_X

_te = start_timer('box_front_position.export_shifted_clamp_plate')
C.export_shape('eurobox_v60_clamp_plate', PLATE)
stop_timer('box_front_position.export_shifted_clamp_plate', _te)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_front_repositioned_plus40_x_serviceable_cartridges'
validation['box_clamp']['front_x_offset_mm'] = FRONT_X_OFFSET
validation['box_clamp']['main_face_x_mm'] = [-40.0, 120.0]
validation['box_clamp']['spindle_x_mm'] = list(SPINDLE_X)
validation['box_clamp']['spindle_spacing_mm'] = SPINDLE_X[1] - SPINDLE_X[0]
validation['box_clamp']['position_fix'] = (
    'complete front topology translated +40 mm in X on canonical continuous carrier; '
    'left cartridge clears front support and right cartridge is farther right'
)
validation['box_clamp']['lead_nut_service_architecture'] = {
    'mode': 'v50_drop_in_RH8x2_cartridge_lower_tail_cross_pin_external_C_clip',
    'working_thread_is_replaceable_part': True,
    'base_contains_working_lead_thread': False,
    'cartridge_extraction_axis': '+Y after spindle/pin removal',
    'body_service_mouth_open': True,
    'tail_extraction_lane_open': True,
    'pin_head_external_service': True,
    'c_clip_external_service': True,
    'service_extraction_test_max_mm': max(SERVICE_EXTRACTION_STEPS),
}
validation['box_clamp']['cartridge_checks'] = service_checks
validation['box_clamp']['serviceable_cartridge_count'] = len(SPINDLE_X)
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

stage('complete')
