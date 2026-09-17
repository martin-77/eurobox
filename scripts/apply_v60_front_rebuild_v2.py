import json
import os

import FreeCAD as App
import Part

import apply_v60_box_clamp_prereq as Q
import build_v60 as C
import build_v60_continuous_carrier as CC
import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

# ---------------------------------------------------------------------------
# Clean v60 front, designed from scratch.
# ---------------------------------------------------------------------------
# Fixed structure: one closed cross-carrier, using the same simple structural
# language as the v60 side holms.  It has exactly two rectangular service bays.
# Clamp mechanics: two separately printable top-load cassettes.  Each cassette
# contains the proven v50 replaceable RH8x2 wear cartridge retained by a cross
# pin + external C-clip.  No working lead thread exists in the fixed carrier or
# in the cassette body itself.

SPINDLE_X = (-48.0, 128.0)
SPINDLE_SPACING = 176.0
PLATE_CENTER_X = 40.0
PLATE_X = 160.0
PLATE_X0 = -40.0
PLATE_X1 = 120.0
PLATE_EAR_HALF_X = 10.0
PLATE_EAR_Z0 = F.SPINDLE_Z - 7.5
PLATE_EAR_Z1 = F.SPINDLE_Z + 7.5
PLATE_HOOK_Y0 = C.BOX_RIM_INNER_Y - 0.20
PLATE_HOOK_Y1 = C.BOX_RIM_INNER_Y + F.UNDERHOOK

FRONT_X0 = C.FRONT_CLAMP_X - C.ARM_W / 2.0
FRONT_X1 = C.REAR_SUPPORT_X + C.ARM_W / 2.0
FRONT_Y0 = F.CAGE_Y0
# The plate opens 5.5 mm toward -Y.  The fixed carrier therefore ends behind
# the complete opening envelope, not merely behind the closed plate position.
FRONT_Y1 = F.PLATE_SPINDLE_Y - F.PLATE_Y - F.PLATE_OPEN - 0.40
FRONT_Z0 = C.ARM_BOTTOM_Z
FRONT_Z1 = C.ARM_TOP_Z

# Replaceable top-load cassette.  0.35 mm running clearance in X/Y and 0.40 mm
# below the carrier top.  The body rises 0.30 mm into the open bay above the
# carrier and overlaps its own flange; the flange begins exactly on the carrier
# top plane and therefore seats without volumetric interference.
MODULE_BODY_HALF_X = 12.0
MODULE_BAY_HALF_X = 12.35
MODULE_BODY_Y0 = FRONT_Y0 + 0.35
MODULE_BODY_Y1 = FRONT_Y1 - 0.35
MODULE_BODY_Z0 = 16.0
MODULE_BODY_Z1 = FRONT_Z1 + 0.30
MODULE_BAY_Z0 = 15.60
MODULE_FLANGE_HALF_X = 19.0
MODULE_FLANGE_Y0 = FRONT_Y0 + 1.0
MODULE_FLANGE_Y1 = FRONT_Y1 - 1.0
MODULE_FLANGE_Z0 = FRONT_Z1
MODULE_FLANGE_Z1 = FRONT_Z1 + 4.0
MODULE_M3_X_OFFSET = 15.5
MODULE_M3_CLEAR_D = 3.4
MODULE_M3_INSERT_D = 4.8
MODULE_M3_INSERT_DEPTH = 5.5

# v50 service cartridge interface.
LEAD_NUT_BODY_HALF_X = 8.0
LEAD_NUT_BODY_HALF_Z = 7.0
LEAD_NUT_TAIL_L = 5.5
LEAD_NUT_TAIL_HALF_X = 6.0
LEAD_NUT_TAIL_Z0 = -12.0
LEAD_NUT_TAIL_H = 5.5
LEAD_NUT_PIN_HOLE_D = 3.4
LEAD_NUT_PIN_LOCAL_Y = -(F.NUT_THREAD_LEN + 2.75)
LEAD_NUT_PIN_LOCAL_Z = -9.25
NUT_TAIL_Y0 = F.NUT_THREAD_Y0 - LEAD_NUT_TAIL_L
PIN_Y = F.NUT_Y0 + LEAD_NUT_PIN_LOCAL_Y
PIN_Z = F.SPINDLE_Z + LEAD_NUT_PIN_LOCAL_Z

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
    print('V60_FRONT_REBUILD_V2 ' + msg, flush=True)


def lead_rotation_deg(travel):
    return 360.0 * travel / F.THREAD_PITCH


def build_lead_nut():
    body = C.box(-8.0, -F.NUT_THREAD_LEN, -7.0, 16.0, F.NUT_THREAD_LEN, 14.0)
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
    q = q.cut(C.cyl_x(
        LEAD_NUT_PIN_HOLE_D / 2.0,
        20.0,
        -10.0,
        LEAD_NUT_PIN_LOCAL_Y,
        LEAD_NUT_PIN_LOCAL_Z,
    )).removeSplitter()
    C.require_single(q, 'clean-front-v2 removable RH8x2 cartridge')
    return q


def build_nut_pin():
    q = C.fuse_seq([
        C.cyl_x(NUT_PIN_SHAFT_D / 2.0,
                NUT_PIN_GROOVE_X0 - NUT_PIN_X0,
                NUT_PIN_X0, 0, 0),
        C.cyl_x(NUT_PIN_GROOVE_D / 2.0,
                NUT_PIN_GROOVE_W,
                NUT_PIN_GROOVE_X0, 0, 0),
        C.cyl_x(NUT_PIN_SHAFT_D / 2.0,
                NUT_PIN_END_X1 - (NUT_PIN_GROOVE_X0 + NUT_PIN_GROOVE_W),
                NUT_PIN_GROOVE_X0 + NUT_PIN_GROOVE_W, 0, 0),
        C.cyl_x(NUT_PIN_HEAD_D / 2.0,
                NUT_PIN_HEAD_T,
                NUT_PIN_X0 - NUT_PIN_HEAD_T, 0, 0),
    ], 'clean-front-v2 cartridge retaining pin')
    C.require_single(q, 'clean-front-v2 cartridge retaining pin')
    return q


def build_module_local():
    body = C.box(
        -MODULE_BODY_HALF_X,
        MODULE_BODY_Y0,
        MODULE_BODY_Z0,
        2.0 * MODULE_BODY_HALF_X,
        MODULE_BODY_Y1 - MODULE_BODY_Y0,
        MODULE_BODY_Z1 - MODULE_BODY_Z0,
    )
    flange = C.box(
        -MODULE_FLANGE_HALF_X,
        MODULE_FLANGE_Y0,
        MODULE_FLANGE_Z0,
        2.0 * MODULE_FLANGE_HALF_X,
        MODULE_FLANGE_Y1 - MODULE_FLANGE_Y0,
        MODULE_FLANGE_Z1 - MODULE_FLANGE_Z0,
    )
    q = body.fuse(flange).removeSplitter()

    # Smooth spindle passage through the cassette only.
    q = q.cut(F.cyl_y(
        Q.SPINDLE_CLEAR_R,
        FRONT_Y1 - FRONT_Y0 + 2.0,
        0.0,
        FRONT_Y0 - 1.0,
        F.SPINDLE_Z,
    )).removeSplitter()

    # Cartridge body/tail channels are open at +Y.  With spindle, clip and pin
    # removed the RH8x2 cartridge can be pulled straight out without replacing
    # the cassette or carrier.
    q = q.cut(C.box(
        -8.35,
        F.NUT_THREAD_Y0 - 0.35,
        F.SPINDLE_Z - 7.35,
        16.70,
        MODULE_BODY_Y1 - (F.NUT_THREAD_Y0 - 0.35) + 0.50,
        14.70,
    )).removeSplitter()
    q = q.cut(C.box(
        -6.20,
        NUT_TAIL_Y0 - 0.25,
        F.SPINDLE_Z + LEAD_NUT_TAIL_Z0 - 0.25,
        12.40,
        MODULE_BODY_Y1 - (NUT_TAIL_Y0 - 0.25) + 0.50,
        LEAD_NUT_TAIL_H + 0.50,
    )).removeSplitter()

    q = q.cut(C.cyl_x(
        LEAD_NUT_PIN_HOLE_D / 2.0,
        24.0,
        -12.0,
        PIN_Y,
        PIN_Z,
    )).removeSplitter()
    q = q.cut(C.cyl_x(3.55, 3.0, -14.0, PIN_Y, PIN_Z)).removeSplitter()
    q = q.cut(C.cyl_x(4.10, 4.0, 11.0, PIN_Y, PIN_Z)).removeSplitter()

    # Cassette mounting screws.  The matching heat-set insert pockets remain in
    # the fixed beam outside the rectangular cassette bay.
    mount_y = (MODULE_FLANGE_Y0 + MODULE_FLANGE_Y1) / 2.0
    for hx in (-MODULE_M3_X_OFFSET, MODULE_M3_X_OFFSET):
        q = q.cut(Part.makeCylinder(
            MODULE_M3_CLEAR_D / 2.0,
            MODULE_FLANGE_Z1 - MODULE_FLANGE_Z0 + 1.0,
            App.Vector(hx, mount_y, MODULE_FLANGE_Z0 - 0.5),
            App.Vector(0, 0, 1),
        )).removeSplitter()

    C.require_single(q, 'clean-front-v2 replaceable clamp cassette')
    return q


def build_plate():
    body_y0 = F.PLATE_SPINDLE_Y - F.PLATE_Y
    q = C.box(
        PLATE_X0,
        body_y0,
        F.PLATE_Z0,
        PLATE_X,
        F.PLATE_Y,
        F.PLATE_Z1 - F.PLATE_Z0,
    )
    q = q.fuse(C.box(
        PLATE_X0,
        PLATE_HOOK_Y0,
        F.RIM_BOTTOM_Z - F.UNDERHOOK_T,
        PLATE_X,
        PLATE_HOOK_Y1 - PLATE_HOOK_Y0,
        F.UNDERHOOK_T,
    )).removeSplitter()
    for sx in SPINDLE_X:
        q = q.fuse(C.box(
            sx - PLATE_EAR_HALF_X,
            body_y0,
            PLATE_EAR_Z0,
            2.0 * PLATE_EAR_HALF_X,
            F.PLATE_Y,
            PLATE_EAR_Z1 - PLATE_EAR_Z0,
        )).removeSplitter()
        q = q.cut(F.cyl_y(
            F.PLATE_HOLE_D / 2.0,
            F.PLATE_Y + 1.0,
            sx,
            body_y0 - 0.5,
            F.SPINDLE_Z,
        )).removeSplitter()
        q = q.cut(F.cyl_y(
            6.0,
            2.0,
            sx,
            body_y0,
            F.SPINDLE_Z,
        )).removeSplitter()
    C.require_single(q, 'clean-front-v2 160 mm clamp plate')
    return q


def rebuild_fixed_carrier():
    # Intentionally omit every legacy front/crosshead/cage object.
    core = C.fuse_seq([
        CC.make_continuous_carrier(),
        C.make_long_support(C.FRONT_CLAMP_X, C.ARM_Y0),
        C.make_long_support(C.REAR_SUPPORT_X, 0.0),
        CC.make_hanging_upper_station(C.FRONT_CLAMP_X),
        CC.make_hanging_upper_station(C.REAR_CLAMP_X),
        CC.make_hanging_backstop(),
    ], 'clean-front-v2 structural core without legacy front')

    beam = C.box(
        FRONT_X0,
        FRONT_Y0,
        FRONT_Z0,
        FRONT_X1 - FRONT_X0,
        FRONT_Y1 - FRONT_Y0,
        FRONT_Z1 - FRONT_Z0,
    )
    core = core.fuse(beam).removeSplitter()
    C.require_single(core, 'clean-front-v2 closed cross carrier before bays')

    # Re-open canonical rack service paths possibly refilled by fusions.
    for xc in C.CLAMP_X:
        core = core.cut(C.cyl_x(
            C.UPPER_SADDLE_R, 40.0, xc - 20.0, 0.0, 0.0
        )).removeSplitter()
        core = core.cut(C.cyl_x(
            C.PIN_HOLE_D / 2.0, 40.0, xc - 20.0, C.PIN_Y, C.PIN_Z
        )).removeSplitter()
        core = core.cut(Part.makeCylinder(
            C.RACK_M4_BASE_CLEAR_D / 2.0,
            12.0,
            App.Vector(xc, C.RACK_CLOSURE_Y, -1.0),
            App.Vector(0, 0, 1),
        )).removeSplitter()

    # Only two simple rectangular cassette bays plus four insert pockets.
    insert_y = (MODULE_FLANGE_Y0 + MODULE_FLANGE_Y1) / 2.0
    for sx in SPINDLE_X:
        core = core.cut(C.box(
            sx - MODULE_BAY_HALF_X,
            FRONT_Y0 - 0.5,
            MODULE_BAY_Z0,
            2.0 * MODULE_BAY_HALF_X,
            FRONT_Y1 - FRONT_Y0 + 1.0,
            FRONT_Z1 - MODULE_BAY_Z0 + 1.0,
        )).removeSplitter()
        for hx in (-MODULE_M3_X_OFFSET, MODULE_M3_X_OFFSET):
            core = core.cut(Part.makeCylinder(
                MODULE_M3_INSERT_D / 2.0,
                MODULE_M3_INSERT_DEPTH,
                App.Vector(
                    sx + hx,
                    insert_y,
                    FRONT_Z1 - MODULE_M3_INSERT_DEPTH,
                ),
                App.Vector(0, 0, 1),
            )).removeSplitter()

    C.require_single(core, 'clean-front-v2 fixed carrier after two cassette bays')
    return core


stage('build side-style fixed front and two service cassettes')
_t = start_timer('box_front_rebuild_v2.build_geometry')
RIGHT_FULL = rebuild_fixed_carrier()
LEFT_FULL = C.mirror_x(RIGHT_FULL)
MODULE = build_module_local()
LEAD_NUT = build_lead_nut()
NUT_PIN = build_nut_pin()
NUT_PIN_CLIP = F.make_c_clip(
    NUT_PIN_CLIP_OUTER_R,
    NUT_PIN_CLIP_INNER_R,
    NUT_PIN_CLIP_T,
    NUT_PIN_CLIP_OPENING_W,
)
PLATE = build_plate()
stop_timer('box_front_rebuild_v2.build_geometry', _t)

stage('hard-check cassette fit, v50 service path and clamp motion')
_t = start_timer('box_front_rebuild_v2.hard_checks')
failures = []
module_checks = []
cartridge_checks = []
plate_motion = []
thread_motion = []

if SPINDLE_X != Q.SPINDLE_X:
    failures.append(f'front/prerequisite axis mismatch: {SPINDLE_X} != {Q.SPINDLE_X}')

# Installed cassette and nested cartridge hardware must fit without material
# overlap.  Face contact at the flange seat is allowed and has zero volume.
for sx in SPINDLE_X:
    mod = MODULE.copy()
    mod.translate(App.Vector(sx, 0, 0))
    base_common = RIGHT_FULL.common(mod).Volume
    module_checks.append({'x_mm': sx, 'base_common_mm3': round(base_common, 6)})
    if base_common > 1e-4:
        failures.append(f'cassette/base overlap X={sx}: {base_common:.6f}')

    nut = LEAD_NUT.copy()
    nut.translate(App.Vector(sx, F.NUT_Y0, F.SPINDLE_Z))
    pin = NUT_PIN.copy()
    pin.translate(App.Vector(sx, PIN_Y, PIN_Z))
    clip = NUT_PIN_CLIP.copy()
    clip.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
    clip.translate(App.Vector(sx + NUT_PIN_CLIP_X, PIN_Y, PIN_Z))
    nmc = mod.common(nut).Volume
    pmc = mod.common(pin).Volume
    cmc = mod.common(clip).Volume
    cartridge_checks.append({
        'x_mm': sx,
        'nut_module_common_mm3': round(nmc, 6),
        'pin_module_common_mm3': round(pmc, 6),
        'clip_module_common_mm3': round(cmc, 6),
    })
    if nmc > 1e-4 or pmc > 1e-4 or cmc > 1e-4:
        failures.append(f'v50 service hardware blocked in cassette X={sx}')

# Cartridge removal witness through the +Y service mouth.
extraction = []
mod0 = MODULE.copy()
mod0.translate(App.Vector(SPINDLE_X[0], 0, 0))
for dy in (0.0, 2.0, 5.0, 10.0, 16.0):
    nut = LEAD_NUT.copy()
    nut.translate(App.Vector(SPINDLE_X[0], F.NUT_Y0 + dy, F.SPINDLE_Z))
    common = mod0.common(nut).Volume
    extraction.append({'travel_y_mm': dy, 'module_common_mm3': round(common, 6)})
    if common > 1e-4:
        failures.append(f'cartridge extraction blocked dy={dy}: {common:.6f}')

# Proven opening direction remains -Y.  The entire fixed front is deliberately
# recessed by PLATE_OPEN+0.40, so no special plate-shaped cutout is needed.
for travel in (-0.5, 0.0, 1.0, 3.0, 5.5):
    plate = PLATE.copy()
    plate.translate(App.Vector(0, -travel, 0))
    bc = RIGHT_FULL.common(plate).Volume
    mc = 0.0
    for sx in SPINDLE_X:
        mod = MODULE.copy()
        mod.translate(App.Vector(sx, 0, 0))
        mc += mod.common(plate).Volume
    plate_motion.append({
        'travel_mm': travel,
        'base_common_mm3': round(bc, 6),
        'modules_common_mm3': round(mc, 6),
    })
    if bc > 1e-4 or mc > 1e-4:
        failures.append(
            f'plate collision travel={travel}: base={bc:.6f} modules={mc:.6f}'
        )

# RH8x2 motion uses the exact proven production spindle and matched female
# master.  Fixed carrier, cassette housing and wear cartridge are all checked.
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy()
    nut.translate(App.Vector(sx, F.NUT_Y0, F.SPINDLE_Z))
    mod = MODULE.copy()
    mod.translate(App.Vector(sx, 0, 0))
    for travel in (-0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.5):
        spindle = F.SPINDLE.copy()
        spindle.rotate(
            App.Vector(0, 0, 0), App.Vector(0, 1, 0), lead_rotation_deg(travel)
        )
        spindle.translate(App.Vector(
            sx, F.PLATE_SPINDLE_Y - travel, F.SPINDLE_Z
        ))
        bc = RIGHT_FULL.common(spindle).Volume
        mc = mod.common(spindle).Volume
        nc = nut.common(spindle).Volume
        thread_motion.append({
            'x_mm': sx,
            'travel_mm': travel,
            'rotation_deg': lead_rotation_deg(travel),
            'base_common_mm3': round(bc, 6),
            'module_common_mm3': round(mc, 6),
            'nut_common_mm3': round(nc, 6),
        })
        if bc > 1.0 or mc > 1.0 or nc > 1.0:
            failures.append(
                f'RH8x2 collision X={sx} travel={travel}: '
                f'base={bc:.6f} module={mc:.6f} nut={nc:.6f}'
            )

# Phase discrimination cannot be weakened merely to make CI green.
ref_nut = LEAD_NUT.copy()
ref_nut.translate(App.Vector(SPINDLE_X[0], F.NUT_Y0, F.SPINDLE_Z))
axial_wrong = F.SPINDLE.copy()
axial_wrong.translate(App.Vector(
    SPINDLE_X[0], F.PLATE_SPINDLE_Y - 0.5, F.SPINDLE_Z
))
axial_wrong_common = ref_nut.common(axial_wrong).Volume
wrong = F.SPINDLE.copy()
wrong.rotate(
    App.Vector(0, 0, 0), App.Vector(0, 1, 0), lead_rotation_deg(0.5) + 180.0
)
wrong.translate(App.Vector(
    SPINDLE_X[0], F.PLATE_SPINDLE_Y - 0.5, F.SPINDLE_Z
))
wrong_common = ref_nut.common(wrong).Volume
correct_half = next(
    q['nut_common_mm3'] for q in thread_motion
    if q['x_mm'] == SPINDLE_X[0] and q['travel_mm'] == 0.5
)
if axial_wrong_common < correct_half + 0.5:
    failures.append('RH8x2 cartridge does not reject axial slide without rotation')
if wrong_common < correct_half + 0.5:
    failures.append('RH8x2 cartridge lacks half-pitch phase sensitivity')

if RIGHT_FULL.BoundBox.XLength > C.V60_X_TARGET_MAX + 1e-6:
    failures.append(f'RIGHT exceeds 296 mm X target: {RIGHT_FULL.BoundBox.XLength:.3f}')
if RIGHT_FULL.BoundBox.YLength > C.INDX_Y_MAX + 1e-6:
    failures.append(f'RIGHT exceeds 275 mm Y target: {RIGHT_FULL.BoundBox.YLength:.3f}')

stop_timer('box_front_rebuild_v2.hard_checks', _t, failures=len(failures))
if failures:
    raise RuntimeError('V60 CLEAN FRONT V2 HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('export clean front and service parts')
_te = start_timer('box_front_rebuild_v2.exports')
for name, shape in {
    'eurobox_v60_clamp_plate': PLATE,
    'eurobox_v60_front_clamp_module': MODULE,
    'eurobox_v60_lead_nut': LEAD_NUT,
    # Preserve established artifact names for downstream consumers.
    'eurobox_v60_lead_nut_retaining_pin': NUT_PIN,
    'eurobox_v60_lead_nut_pin_clip': NUT_PIN_CLIP,
}.items():
    C.export_shape(name, shape)
stop_timer('box_front_rebuild_v2.exports', _te)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_clean_modular_front'
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
validation['box_clamp'] = {
    'architecture': 'closed_v60_front_carrier_with_two_replaceable_clamp_cassettes',
    'front_carrier_x_mm': [FRONT_X0, FRONT_X1],
    'front_carrier_y_mm': [round(FRONT_Y0, 3), round(FRONT_Y1, 3)],
    'front_carrier_z_mm': [FRONT_Z0, FRONT_Z1],
    'front_recess_for_plate_travel_mm': F.PLATE_OPEN + 0.40,
    'plate_width_mm': PLATE_X,
    'plate_main_x_mm': [PLATE_X0, PLATE_X1],
    'plate_travel_mm': F.PLATE_OPEN,
    'plate_motion': plate_motion,
    'spindle_x_mm': list(SPINDLE_X),
    'spindle_spacing_mm': SPINDLE_SPACING,
    'spindle_z_mm': F.SPINDLE_Z,
    'lead_nut_mode': 'separate_RH8x2_cartridge_cross_pin_external_C_clip_inside_replaceable_module',
    'integral_female_threads': False,
    'base_has_working_lead_thread': False,
    'module_has_working_lead_thread': False,
    'module_attachment': 'top-drop cassette, two M3 screws into heat-set inserts per module',
    'module_count_per_base': 2,
    'module_bay_half_x_mm': MODULE_BAY_HALF_X,
    'module_flange_half_x_mm': MODULE_FLANGE_HALF_X,
    'module_m3_centres_local_x_mm': [-MODULE_M3_X_OFFSET, MODULE_M3_X_OFFSET],
    'module_checks': module_checks,
    'cartridge_checks': cartridge_checks,
    'cartridge_extraction_plus_y': extraction,
    'thread_motion': thread_motion,
    'axial_slide_without_rotation_common_mm3': round(axial_wrong_common, 6),
    'half_pitch_wrong_phase_common_mm3': round(wrong_common, 6),
    'effective_total_width_mm': max(
        600.0,
        validation.get('box_clamp', {}).get('effective_total_width_mm', 600.0),
    ),
    'final_assembly_contains_separate_lead_nut_hardware': True,
    'final_assembly_lead_nut_cartridge_count': 4,
    'final_assembly_lead_nut_pin_count': 4,
    'final_assembly_lead_nut_clip_count': 4,
    'final_assembly_replaceable_module_count': 4,
}
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

stage('complete')
