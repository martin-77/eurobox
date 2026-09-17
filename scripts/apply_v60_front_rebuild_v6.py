import json
import os

import FreeCAD as App
import Part

import apply_v60_front_rebuild_v5 as V5
import apply_v60_box_clamp_prereq as Q
import build_v60 as C
import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

# Clean-front v6: service-access audit of the complete box-clamp screw stack.
# v5 fixes the wear cartridge. v6 additionally makes the 30 mm hand knob and
# its RH8x2 retaining nut physically reachable from the rear of the front beam.
# The old bay cleared the 10-AF hex but was only ~24.7 mm wide, so a Ø30 knob
# could still sit partly behind fixed front material. That is now a hard error.

SPINDLE_X = V5.SPINDLE_X
SPINDLE_SPACING = V5.SPINDLE_SPACING
PLATE_CENTER_X = V5.PLATE_CENTER_X
PLATE = V5.PLATE
MODULE = V5.MODULE
LEAD_NUT = V5.LEAD_NUT
NUT_PIN = V5.NUT_PIN
NUT_PIN_CLIP = V5.NUT_PIN_CLIP
LEAD_NUT_PIN_LOCAL_Y = V5.LEAD_NUT_PIN_LOCAL_Y
LEAD_NUT_PIN_LOCAL_Z = V5.LEAD_NUT_PIN_LOCAL_Z
NUT_PIN_CLIP_X = V5.NUT_PIN_CLIP_X
PIN_Y = V5.PIN_Y
PIN_Z = V5.PIN_Z

KNOB = F.KNOB
KNOB_CLEAR_R = 15.60
KNOB_Y_LOCAL = -(
    F.SPINDLE_LOCAL_JOURNAL + F.SPINDLE_LOCAL_SHOULDER + F.LEAD_THREAD_LEN
)
KNOB_LEN = F.KNOB.BoundBox.YLength
CAP_NUT_H = 5.8
CAP_Y_LOCAL = KNOB_Y_LOCAL - KNOB_LEN
STUD_START_POSY = (
    F.SPINDLE_LOCAL_JOURNAL + F.SPINDLE_LOCAL_SHOULDER
    + F.LEAD_THREAD_LEN + F.HEX_LEN
)
STUD_START_NEGY = -STUD_START_POSY
STUD_END_NEGY = -(STUD_START_POSY + F.OUTER_STUD_LEN)
CAP_THREAD_OVERRUN = F.THREAD_PITCH

# Rear knob corridor stops before the replaceable cassette body. It only opens
# the short rear wall segment that previously covered the sides of the knob.
HANDLE_ACCESS_Y0 = V5.V2.FRONT_Y0 - 1.0
HANDLE_ACCESS_Y1 = V5.MODULE_BODY_Y0 - 0.50


def stage(msg):
    print('V60_FRONT_REBUILD_V6 ' + msg, flush=True)


def rebuild_fixed_front_with_handle_access():
    q = V5.RIGHT_FULL
    for sx in SPINDLE_X:
        q = q.cut(F.cyl_y(
            KNOB_CLEAR_R,
            HANDLE_ACCESS_Y1 - HANDLE_ACCESS_Y0,
            sx, HANDLE_ACCESS_Y0, F.SPINDLE_Z,
        )).removeSplitter()
    C.require_single(q, 'clean-front-v6 fixed carrier with rear knob access')
    return q


def build_phase_matched_cap_nut():
    # Use the same profile clearances as the proven main RH8x2 pair. The cutter
    # spans one full pitch before the outer-stud start and far beyond the cap,
    # so no smooth end-wall can survive at either printed thread mouth.
    span = F.OUTER_STUD_LEN + CAP_NUT_H + 2.0 * CAP_THREAD_OVERRUN
    scad = os.path.join(C.OUT, 'v60_knob_retainer_matched_female_RH8x2.scad')
    F.write_thread_scad(
        scad,
        Q.FEMALE_CORE_R,
        Q.FEMALE_MAJOR_R,
        F.THREAD_PITCH,
        span,
        Q.FEMALE_ROOT_W,
        Q.FEMALE_CREST_W,
    )
    female_z = F.import_scad_shape(scad)
    female_z.translate(App.Vector(0, 0, -CAP_THREAD_OVERRUN))
    female_posy = F.z_to_y(female_z, 0, STUD_START_POSY, 0)
    female_negy = F.rotate_z180(female_posy)

    blank = F.rotate_z180(F.z_to_y(F.hex_z(13.0, CAP_NUT_H)))
    blank.translate(App.Vector(0, CAP_Y_LOCAL, 0))
    cap_installed_local = blank.cut(female_negy).removeSplitter()
    C.require_single(cap_installed_local, 'phase-matched open RH8x2 knob retainer nut')

    cap = cap_installed_local.copy()
    cap.translate(App.Vector(0, -CAP_Y_LOCAL, 0))
    C.require_single(cap, 'rebased RH8x2 knob retainer nut')
    return cap


stage('open rear handle corridors and rebuild matched knob-retainer thread')
_t = start_timer('box_front_rebuild_v6.build_geometry')
RIGHT_FULL = rebuild_fixed_front_with_handle_access()
LEFT_FULL = C.mirror_x(RIGHT_FULL)
C.require_single(LEFT_FULL, 'clean-front-v6 mirrored LEFT carrier')
CAP_NUT = build_phase_matched_cap_nut()
stop_timer('box_front_rebuild_v6.build_geometry', _t)

stage('hard-check every printed box-clamp thread and handle access')
_t = start_timer('box_front_rebuild_v6.hard_checks')
failures = []
access_checks = []
cap_fit_checks = []

# Main RH8x2 cartridge was already checked through the full travel in v5. Here
# prove the complete handle/cap assembly is not hidden behind fixed front or
# cassette material.
for sx in SPINDLE_X:
    mod = MODULE.copy(); mod.translate(App.Vector(sx, 0, 0))

    knob = KNOB.copy()
    knob.translate(App.Vector(sx, F.PLATE_SPINDLE_Y + KNOB_Y_LOCAL, F.SPINDLE_Z))
    knob_base = RIGHT_FULL.common(knob).Volume
    knob_module = mod.common(knob).Volume

    cap = CAP_NUT.copy()
    cap.translate(App.Vector(sx, F.PLATE_SPINDLE_Y + CAP_Y_LOCAL, F.SPINDLE_Z))
    cap_base = RIGHT_FULL.common(cap).Volume
    cap_module = mod.common(cap).Volume

    access_checks.append({
        'x_mm': sx,
        'knob_base_common_mm3': round(knob_base, 6),
        'knob_module_common_mm3': round(knob_module, 6),
        'cap_nut_base_common_mm3': round(cap_base, 6),
        'cap_nut_module_common_mm3': round(cap_module, 6),
    })
    if knob_base > 1e-4 or knob_module > 1e-4:
        failures.append(
            f'hand knob still behind/intersecting front wall X={sx}: '
            f'base={knob_base:.6f} module={knob_module:.6f}'
        )
    if cap_base > 1e-4 or cap_module > 1e-4:
        failures.append(
            f'RH8x2 knob-retainer nut still behind/intersecting wall X={sx}: '
            f'base={cap_base:.6f} module={cap_module:.6f}'
        )

    spindle = F.SPINDLE.copy()
    spindle.translate(App.Vector(sx, F.PLATE_SPINDLE_Y, F.SPINDLE_Z))
    correct_common = spindle.common(cap).Volume

    wrong = CAP_NUT.copy()
    wrong.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 180.0)
    wrong.translate(App.Vector(sx, F.PLATE_SPINDLE_Y + CAP_Y_LOCAL, F.SPINDLE_Z))
    wrong_common = spindle.common(wrong).Volume
    cap_fit_checks.append({
        'x_mm': sx,
        'correct_phase_common_mm3': round(correct_common, 6),
        'half_pitch_wrong_phase_common_mm3': round(wrong_common, 6),
    })
    if correct_common > 0.10:
        failures.append(
            f'knob retainer RH8x2 correct phase collides X={sx}: '
            f'{correct_common:.6f} mm3'
        )
    if wrong_common < correct_common + 0.25:
        failures.append(
            f'knob retainer RH8x2 lacks phase sensitivity X={sx}: '
            f'correct={correct_common:.6f} wrong={wrong_common:.6f}'
        )

# Mechanical engagement is 4.5 mm: the cap runs from -39 to -44.8 while the
# outer stud runs from -36.5 to -43.5 in the spindle-local Y frame.
cap_y0 = CAP_Y_LOCAL - CAP_NUT_H
cap_y1 = CAP_Y_LOCAL
stud_y0 = STUD_END_NEGY
stud_y1 = STUD_START_NEGY
stud_engagement = max(0.0, min(cap_y1, stud_y1) - max(cap_y0, stud_y0))
if stud_engagement < 4.0:
    failures.append(f'knob-retainer RH8x2 engagement too short: {stud_engagement:.3f} mm')

# Central core must be through-open across the complete nut. This catches the
# recurring failure mode where a visually threaded part still has an end wall.
through = F.cyl_y(
    Q.FEMALE_CORE_R - 0.10,
    CAP_NUT_H + 0.40,
    0.0, -CAP_NUT_H - 0.20, 0.0,
)
cap_core_block = CAP_NUT.common(through).Volume
if cap_core_block > 1e-4:
    failures.append(
        f'knob-retainer RH8x2 has a closed/end wall in its threaded bore: '
        f'{cap_core_block:.6f} mm3'
    )

stop_timer('box_front_rebuild_v6.hard_checks', _t, failures=len(failures))
if failures:
    raise RuntimeError('V60 CLEAN FRONT V6 HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('export handle and corrected open-ended retainer nut')
_t = start_timer('box_front_rebuild_v6.exports')
C.export_shape('eurobox_v60_knob', KNOB)
C.export_shape('eurobox_v60_knob_retainer_nut', CAP_NUT)
stop_timer('box_front_rebuild_v6.exports', _t)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
box = validation.setdefault('box_clamp', {})
box['architecture'] = 'clean_modular_front_v6_full_handle_and_all_RH8x2_service_access'
box['handle_access_y_mm'] = [round(HANDLE_ACCESS_Y0, 3), round(HANDLE_ACCESS_Y1, 3)]
box['handle_clearance_d_mm'] = round(2.0 * KNOB_CLEAR_R, 3)
box['handle_wall_access_checks'] = access_checks
box['knob_retainer_thread'] = {
    'standard': 'RH8x2 matched to production outer stud',
    'open_ended': True,
    'cutter_overrun_each_end_mm': CAP_THREAD_OVERRUN,
    'stud_engagement_mm': round(stud_engagement, 3),
    'core_blockage_mm3': round(cap_core_block, 6),
    'phase_fit_checks': cap_fit_checks,
}
validation['stage'] = 'full_direct_mechanism_clean_modular_front_v6'
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

stage('complete')
