import json
import os

import FreeCAD as App
import Part

import apply_v60_front_rebuild_v2 as V2
import build_v60 as C
import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

# Clean-front v5.
# Keep the validated v2 carrier/plate/module datums, but rebuild the replaceable
# cassette and RH8x2 wear cartridge around the COMPLETE moving spindle envelope.
# v4 still let the full-width retaining tail overlap the 10-AF drive hex for the
# first 1 mm of travel. v5 removes that overlap by construction rather than by
# relaxing the collision gate.

SPINDLE_X = V2.SPINDLE_X
SPINDLE_SPACING = V2.SPINDLE_SPACING
PLATE_CENTER_X = V2.PLATE_CENTER_X
PLATE = V2.PLATE
RIGHT_FULL = V2.RIGHT_FULL
LEFT_FULL = V2.LEFT_FULL

MODULE_BODY_HALF_X = V2.MODULE_BODY_HALF_X
MODULE_BAY_HALF_X = V2.MODULE_BAY_HALF_X
MODULE_BODY_Y0 = F.NUT_THREAD_Y0 - 0.50
MODULE_BODY_Y1 = V2.MODULE_BODY_Y1
MODULE_BODY_Z0 = V2.MODULE_BODY_Z0
MODULE_BODY_Z1 = V2.MODULE_BODY_Z1
MODULE_FLANGE_HALF_X = V2.MODULE_FLANGE_HALF_X
MODULE_FLANGE_Y0 = V2.MODULE_FLANGE_Y0
MODULE_FLANGE_Y1 = V2.MODULE_FLANGE_Y1
MODULE_FLANGE_Z0 = V2.MODULE_FLANGE_Z0
MODULE_FLANGE_Z1 = V2.MODULE_FLANGE_Z1
MODULE_M3_X_OFFSET = V2.MODULE_M3_X_OFFSET
MODULE_M3_CLEAR_D = V2.MODULE_M3_CLEAR_D

LEAD_NUT_BODY_HALF_X = 8.0
LEAD_NUT_BODY_HALF_Z = 7.0
LEAD_NUT_TAIL_HALF_X = 8.0
# At worst preload (-0.5 mm) the forward end of the 10-AF hex is local
# Y=-15.7 relative to NUT_Y0. Starting the full-width tail at -15.0 leaves
# 0.7 mm axial clearance while still giving 6 mm overlap into the nut body.
LEAD_NUT_TAIL_LOCAL_Y0 = -15.0
LEAD_NUT_TAIL_LOCAL_Y1 = -8.0
LEAD_NUT_TAIL_Z0 = -13.0
LEAD_NUT_TAIL_Z1 = -4.8
LEAD_NUT_TAIL_H = LEAD_NUT_TAIL_Z1 - LEAD_NUT_TAIL_Z0
LEAD_NUT_PIN_HOLE_D = V2.LEAD_NUT_PIN_HOLE_D
LEAD_NUT_PIN_LOCAL_Y = -12.0
LEAD_NUT_PIN_LOCAL_Z = -9.25
NUT_TAIL_Y0 = F.NUT_Y0 + LEAD_NUT_TAIL_LOCAL_Y0
NUT_TAIL_Y1 = F.NUT_Y0 + LEAD_NUT_TAIL_LOCAL_Y1
PIN_Y = F.NUT_Y0 + LEAD_NUT_PIN_LOCAL_Y
PIN_Z = F.SPINDLE_Z + LEAD_NUT_PIN_LOCAL_Z

NUT_PIN_SHAFT_D = V2.NUT_PIN_SHAFT_D
NUT_PIN_GROOVE_D = V2.NUT_PIN_GROOVE_D
NUT_PIN_GROOVE_W = V2.NUT_PIN_GROOVE_W
NUT_PIN_HEAD_D = V2.NUT_PIN_HEAD_D
NUT_PIN_HEAD_T = V2.NUT_PIN_HEAD_T
NUT_PIN_X0 = V2.NUT_PIN_X0
NUT_PIN_GROOVE_X0 = V2.NUT_PIN_GROOVE_X0
NUT_PIN_END_X1 = V2.NUT_PIN_END_X1
NUT_PIN_CLIP_OUTER_R = V2.NUT_PIN_CLIP_OUTER_R
NUT_PIN_CLIP_INNER_R = V2.NUT_PIN_CLIP_INNER_R
NUT_PIN_CLIP_T = V2.NUT_PIN_CLIP_T
NUT_PIN_CLIP_OPENING_W = V2.NUT_PIN_CLIP_OPENING_W
NUT_PIN_CLIP_X = V2.NUT_PIN_CLIP_X


def stage(msg):
    print('V60_FRONT_REBUILD_V5 ' + msg, flush=True)


def lead_rotation_deg(travel):
    return 360.0 * travel / F.THREAD_PITCH


def build_lead_nut():
    body = C.box(
        -LEAD_NUT_BODY_HALF_X, -F.NUT_THREAD_LEN, -LEAD_NUT_BODY_HALF_Z,
        2.0 * LEAD_NUT_BODY_HALF_X, F.NUT_THREAD_LEN,
        2.0 * LEAD_NUT_BODY_HALF_Z,
    )
    tail = C.box(
        -LEAD_NUT_TAIL_HALF_X, LEAD_NUT_TAIL_LOCAL_Y0,
        LEAD_NUT_TAIL_Z0, 2.0 * LEAD_NUT_TAIL_HALF_X,
        LEAD_NUT_TAIL_LOCAL_Y1 - LEAD_NUT_TAIL_LOCAL_Y0,
        LEAD_NUT_TAIL_H,
    )
    q = body.fuse(tail).removeSplitter()
    q = q.cut(F.FEMALE_NEGY).removeSplitter()
    q = q.cut(C.cyl_x(
        LEAD_NUT_PIN_HOLE_D / 2.0, 20.0, -10.0,
        LEAD_NUT_PIN_LOCAL_Y, LEAD_NUT_PIN_LOCAL_Z,
    )).removeSplitter()
    C.require_single(q, 'clean-front-v5 reinforced removable RH8x2 cartridge')
    return q


def build_module_local():
    body = C.box(
        -MODULE_BODY_HALF_X, MODULE_BODY_Y0, MODULE_BODY_Z0,
        2.0 * MODULE_BODY_HALF_X, MODULE_BODY_Y1 - MODULE_BODY_Y0,
        MODULE_BODY_Z1 - MODULE_BODY_Z0,
    )
    flange = C.box(
        -MODULE_FLANGE_HALF_X, MODULE_FLANGE_Y0, MODULE_FLANGE_Z0,
        2.0 * MODULE_FLANGE_HALF_X, MODULE_FLANGE_Y1 - MODULE_FLANGE_Y0,
        MODULE_FLANGE_Z1 - MODULE_FLANGE_Z0,
    )
    q = body.fuse(flange).removeSplitter()

    # Smooth spindle passage and rear service opening. No working thread exists
    # in the cassette body.
    q = q.cut(F.cyl_y(
        V2.Q.SPINDLE_CLEAR_R,
        MODULE_BODY_Y1 - MODULE_BODY_Y0 + 2.0,
        0.0, MODULE_BODY_Y0 - 1.0, F.SPINDLE_Z,
    )).removeSplitter()

    # Full cartridge-body channel, open toward +Y.
    q = q.cut(C.box(
        -8.35, F.NUT_THREAD_Y0 - 0.35, F.SPINDLE_Z - 7.35,
        16.70,
        MODULE_BODY_Y1 - (F.NUT_THREAD_Y0 - 0.35) + 0.50,
        14.70,
    )).removeSplitter()

    # Lower retaining-tail channel, also open toward +Y.
    q = q.cut(C.box(
        -8.35, NUT_TAIL_Y0 - 0.35,
        F.SPINDLE_Z + LEAD_NUT_TAIL_Z0 - 0.35,
        16.70,
        MODULE_BODY_Y1 - (NUT_TAIL_Y0 - 0.35) + 0.50,
        LEAD_NUT_TAIL_H + 0.70,
    )).removeSplitter()

    # Cross-pin, head and C-clip service paths.
    q = q.cut(C.cyl_x(
        LEAD_NUT_PIN_HOLE_D / 2.0, 24.0, -12.0, PIN_Y, PIN_Z,
    )).removeSplitter()
    q = q.cut(C.cyl_x(3.55, 3.0, -14.0, PIN_Y, PIN_Z)).removeSplitter()
    q = q.cut(C.cyl_x(4.10, 4.0, 11.0, PIN_Y, PIN_Z)).removeSplitter()

    mount_y = (MODULE_FLANGE_Y0 + MODULE_FLANGE_Y1) / 2.0
    for hx in (-MODULE_M3_X_OFFSET, MODULE_M3_X_OFFSET):
        q = q.cut(Part.makeCylinder(
            MODULE_M3_CLEAR_D / 2.0,
            MODULE_FLANGE_Z1 - MODULE_FLANGE_Z0 + 1.0,
            App.Vector(hx, mount_y, MODULE_FLANGE_Z0 - 0.5),
            App.Vector(0, 0, 1),
        )).removeSplitter()
    C.require_single(q, 'clean-front-v5 rear-open replaceable clamp cassette')
    return q


def build_nut_pin():
    return V2.build_nut_pin()


stage('build spindle-envelope-clear service cartridge')
_t = start_timer('box_front_rebuild_v5.build_geometry')
MODULE = build_module_local()
LEAD_NUT = build_lead_nut()
NUT_PIN = build_nut_pin()
NUT_PIN_CLIP = V2.NUT_PIN_CLIP
stop_timer('box_front_rebuild_v5.build_geometry', _t)

stage('hard-check all clamp-thread access and motion')
_t = start_timer('box_front_rebuild_v5.hard_checks')
failures = []
module_checks = []
thread_motion = []

# Explicit analytical witness for the bug from v4: the full-width tail must
# never reach the 10-AF drive hex, including the -0.5 mm preload state.
hex_front_local_y_preload = (
    (F.PLATE_SPINDLE_Y + 0.5)
    - (F.SPINDLE_LOCAL_JOURNAL + F.SPINDLE_LOCAL_SHOULDER + F.LEAD_THREAD_LEN)
    - F.NUT_Y0
)
tail_hex_axial_clearance = LEAD_NUT_TAIL_LOCAL_Y0 - hex_front_local_y_preload
if tail_hex_axial_clearance < 0.50:
    failures.append(
        f'lead-nut tail too close to 10 AF drive hex at preload: '
        f'{tail_hex_axial_clearance:.3f} mm'
    )

# The lower body/tail bridge is deliberately below the RH8x2 major radius and
# must survive almost completely solid. It is 16 x 6 x 2.0 mm in the overlap.
bridge_probe = C.box(-8.0, -14.0, -7.0, 16.0, 6.0, 2.0)
bridge_fraction = LEAD_NUT.common(bridge_probe).Volume / bridge_probe.Volume
if bridge_fraction < 0.995:
    failures.append(
        f'lead-nut structural bridge not solid: {bridge_fraction:.6f}'
    )

# Rear access to the 10-AF drive must be open through BOTH fixed carrier and
# removable cassette, not merely numerically outside one wall.
service_probe_local = C.box(
    -6.20, V2.FRONT_Y0 - 2.0, F.SPINDLE_Z - 6.20,
    12.40, MODULE_BODY_Y0 - (V2.FRONT_Y0 - 2.0), 12.40,
)
for sx in SPINDLE_X:
    probe = service_probe_local.copy(); probe.translate(App.Vector(sx, 0, 0))
    mod = MODULE.copy(); mod.translate(App.Vector(sx, 0, 0))
    base_block = RIGHT_FULL.common(probe).Volume
    module_block = mod.common(probe).Volume
    module_checks.append({
        'x_mm': sx,
        'rear_drive_service_base_common_mm3': round(base_block, 6),
        'rear_drive_service_module_common_mm3': round(module_block, 6),
    })
    if base_block > 1e-4 or module_block > 1e-4:
        failures.append(
            f'rear drive service path blocked X={sx}: '
            f'base={base_block:.6f} module={module_block:.6f}'
        )

    if RIGHT_FULL.common(mod).Volume > 1e-4:
        failures.append(f'cassette/base overlap X={sx}')

    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx, F.NUT_Y0, F.SPINDLE_Z))
    pin = NUT_PIN.copy(); pin.translate(App.Vector(sx, PIN_Y, PIN_Z))
    clip = NUT_PIN_CLIP.copy()
    clip.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
    clip.translate(App.Vector(sx + NUT_PIN_CLIP_X, PIN_Y, PIN_Z))
    if mod.common(nut).Volume > 1e-4:
        failures.append(f'lead nut blocked in cassette X={sx}')
    if mod.common(pin).Volume > 1e-4:
        failures.append(f'lead-nut pin blocked in cassette X={sx}')
    if mod.common(clip).Volume > 1e-4:
        failures.append(f'lead-nut clip blocked in cassette X={sx}')

    # Exact production spindle against exact production base/module/cartridge.
    # Keep the 1 mm3 numerical tolerance used by the proven phase check; no
    # geometry failure is hidden or threshold-relaxed here.
    for travel in (-0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.5):
        spindle = F.SPINDLE.copy()
        spindle.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), lead_rotation_deg(travel))
        spindle.translate(App.Vector(sx, F.PLATE_SPINDLE_Y - travel, F.SPINDLE_Z))
        bc = RIGHT_FULL.common(spindle).Volume
        mc = mod.common(spindle).Volume
        nc = nut.common(spindle).Volume
        thread_motion.append({
            'x_mm': sx, 'travel_mm': travel,
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

# Keep the phase-sensitivity gates: a plain axial slide and a half-pitch wrong
# phase must collide materially more than the correctly rotated state.
ref_nut = LEAD_NUT.copy(); ref_nut.translate(App.Vector(SPINDLE_X[0], F.NUT_Y0, F.SPINDLE_Z))
axial_wrong = F.SPINDLE.copy()
axial_wrong.translate(App.Vector(SPINDLE_X[0], F.PLATE_SPINDLE_Y - 0.5, F.SPINDLE_Z))
axial_wrong_common = ref_nut.common(axial_wrong).Volume
wrong = F.SPINDLE.copy()
wrong.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), lead_rotation_deg(0.5) + 180.0)
wrong.translate(App.Vector(SPINDLE_X[0], F.PLATE_SPINDLE_Y - 0.5, F.SPINDLE_Z))
wrong_common = ref_nut.common(wrong).Volume
correct_half = next(
    q['nut_common_mm3'] for q in thread_motion
    if q['x_mm'] == SPINDLE_X[0] and q['travel_mm'] == 0.5
)
if axial_wrong_common < correct_half + 0.5:
    failures.append('RH8x2 cartridge does not reject axial slide without rotation')
if wrong_common < correct_half + 0.5:
    failures.append('RH8x2 cartridge lacks half-pitch phase sensitivity')

stop_timer('box_front_rebuild_v5.hard_checks', _t, failures=len(failures))
if failures:
    raise RuntimeError('V60 CLEAN FRONT V5 HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('re-export corrected service parts')
_t = start_timer('box_front_rebuild_v5.exports')
for name, shape in {
    'eurobox_v60_front_clamp_module': MODULE,
    'eurobox_v60_lead_nut': LEAD_NUT,
    'eurobox_v60_lead_nut_retaining_pin': NUT_PIN,
    'eurobox_v60_lead_nut_pin_clip': NUT_PIN_CLIP,
}.items():
    C.export_shape(name, shape)
stop_timer('box_front_rebuild_v5.exports', _t)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
box = validation.setdefault('box_clamp', {})
box['architecture'] = 'clean_modular_front_v5_spindle_envelope_clear_service_cartridge'
box['rear_drive_service_open'] = True
box['rear_drive_service_checks'] = module_checks
box['lead_nut_tail_local_y_mm'] = [LEAD_NUT_TAIL_LOCAL_Y0, LEAD_NUT_TAIL_LOCAL_Y1]
box['lead_nut_tail_local_z_mm'] = [LEAD_NUT_TAIL_Z0, LEAD_NUT_TAIL_Z1]
box['lead_nut_tail_to_hex_preload_clearance_mm'] = round(tail_hex_axial_clearance, 3)
box['lead_nut_body_tail_bridge_material_fraction'] = round(bridge_fraction, 6)
box['lead_nut_pin_local_y_mm'] = LEAD_NUT_PIN_LOCAL_Y
box['lead_nut_pin_local_z_mm'] = LEAD_NUT_PIN_LOCAL_Z
box['thread_motion'] = thread_motion
box['axial_slide_without_rotation_common_mm3'] = round(axial_wrong_common, 6)
box['half_pitch_wrong_phase_common_mm3'] = round(wrong_common, 6)
validation['stage'] = 'full_direct_mechanism_clean_modular_front_v5'
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

stage('complete')
