import json
import os
import sys
import traceback

OUT = os.environ.get('EUROBOX_BUILD_DIR', 'build_v50')
os.makedirs(OUT, exist_ok=True)


def bootstrap(stage, extra=None):
    payload = {'diagnostic_only': True, 'stage': stage}
    if extra is not None:
        payload['extra'] = extra
    with open(os.path.join(OUT, 'BOX_CLAMP_VALIDATION.json'), 'w') as f:
        json.dump(payload, f, indent=2)
    print('[box-clamp] ' + stage, flush=True)


bootstrap('bootstrap:stdlib', {'argv': sys.argv, 'out': OUT})

try:
    import faulthandler
    try:
        faulthandler.enable()
    except Exception as exc:
        print('[box-clamp] faulthandler unavailable: ' + repr(exc), flush=True)
except Exception as exc:
    print('[box-clamp] faulthandler import unavailable: ' + repr(exc), flush=True)

bootstrap('bootstrap:before_freecad_import')

try:
    import FreeCAD as App
    import Part
except BaseException as exc:
    failure = {
        'diagnostic_only': True,
        'stage': 'bootstrap:freecad_import_failed',
        'exception_type': type(exc).__name__,
        'exception': str(exc),
        'traceback': traceback.format_exc(),
    }
    with open(os.path.join(OUT, 'BOX_CLAMP_VALIDATION.json'), 'w') as f:
        json.dump(failure, f, indent=2)
    with open(os.path.join(OUT, 'BOX_CLAMP_EXCEPTION.json'), 'w') as f:
        json.dump(failure, f, indent=2)
    print('[box-clamp] EXCEPTION=' + json.dumps(failure), file=sys.stderr, flush=True)
    raise

bootstrap('bootstrap:freecad_imported', {'freecad_version': App.Version()})

BOX_EDGE_Y = 244.665
BOX_RIM_INNER_Y = 228.215
RIM_BOTTOM_Z = 23.09
RIM_Y = 16.45
RIM_H = 16.45
SPINDLE_X = -42.0
SPINDLE_Z = 31.0
THREAD_PITCH = 2.0
NUT_Y0 = 260.465
PLATE_OPEN = 5.5
CLAMP_PRELOAD = 0.5
UNDERHOOK = 4.2
PLATE_HOLE_D = 6.5
JOURNAL_D = 6.0
SHOULDER_D = 11.0
PLATE_COUNTERBORE_D = 12.0

# Lead-nut service-hardware datums from the final v50 architecture pass.
LEAD_NUT_PIN_Y = 7.0
LEAD_NUT_PIN_Z = 10.0
NUT_PIN_GROOVE_X0 = 11.4
SPINDLE_LOCAL_JOURNAL = 8.0
SPINDLE_LOCAL_SHOULDER = 1.8
LEAD_THREAD_LEN = 23.0
LEAD_DRIVE_LEN = 4.5
LEAD_KNOB_LEN = 7.0
OUTER_STUD_LEN = 7.0
LEAD_DRIVE_Y0 = SPINDLE_LOCAL_JOURNAL + SPINDLE_LOCAL_SHOULDER + LEAD_THREAD_LEN
OUTER_STUD_Y0 = LEAD_DRIVE_Y0 + LEAD_DRIVE_LEN
CAP_NUT_Y0 = LEAD_DRIVE_Y0 + LEAD_KNOB_LEN
CAP_NUT_PHASE_DEG = -360.0 * (CAP_NUT_Y0-OUTER_STUD_Y0) / THREAD_PITCH


def log(message):
    print('[box-clamp] ' + message, flush=True)


def checkpoint(stage, extra=None):
    payload = {'diagnostic_only': True, 'stage': stage}
    if extra is not None:
        payload['extra'] = extra
    with open(os.path.join(OUT, 'BOX_CLAMP_CHECKPOINT.json'), 'w') as f:
        json.dump(payload, f, indent=2)
    with open(os.path.join(OUT, 'BOX_CLAMP_VALIDATION.json'), 'w') as f:
        json.dump(payload, f, indent=2)
    log(stage)


def read_step(name):
    p = os.path.join(OUT, name + '.step')
    checkpoint('read_step:start:' + name, {'path': p})
    if not os.path.exists(p):
        raise RuntimeError('Missing STEP: ' + p)
    s = Part.Shape()
    s.read(p)
    info = {
        'is_null': s.isNull(),
        'is_valid': s.isValid() if not s.isNull() else False,
        'solids': len(s.Solids) if not s.isNull() else 0,
        'volume_mm3': round(s.Volume, 6) if not s.isNull() else 0.0,
    }
    checkpoint('read_step:done:' + name, info)
    if s.isNull() or not s.isValid() or len(s.Solids) != 1:
        raise RuntimeError('Invalid STEP solid: ' + p + ' ' + repr(info))
    return s


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


def common_volume(a, b, name):
    checkpoint('common:start:' + name)
    result = a.common(b)
    volume = result.Volume
    checkpoint('common:done:' + name, {'volume_mm3': round(volume, 6)})
    return volume


def run_validation():
    checkpoint('validator:start', {'freecad_version': App.Version(), 'out': OUT})

    base = read_step('eurobox_v50_base')
    plate = read_step('eurobox_v50_clamp_plate')
    spindle = read_step('eurobox_v50_lead_screw_print')
    lead_nut = read_step('eurobox_v50_lead_nut_print')
    retainer_pin = read_step('eurobox_v50_lead_nut_retaining_pin')
    pin_clip = read_step('eurobox_v50_lead_nut_pin_clip')
    knob_retainer_nut = read_step('eurobox_v50_knob_retainer_nut')

    checkpoint('inputs:loaded')
    rim = box(-200.0, BOX_RIM_INNER_Y, RIM_BOTTOM_Z, 400.0, RIM_Y, RIM_H)

    report = {
        'version': 'v50',
        'plate_open_mm': PLATE_OPEN,
        'clamp_preload_mm': CLAMP_PRELOAD,
        'lead_nut_mode': 'separate_RH_8x2_printed_cartridge',
        'checks': {},
        'measurements': {},
        'failed': [],
    }

    report['checks']['separate_lead_nut_exported_valid'] = True
    report['checks']['lead_nut_retaining_pin_exported_valid'] = True
    report['checks']['lead_nut_pin_clip_exported_valid'] = True
    report['checks']['knob_retainer_nut_exported_valid'] = True

    report['measurements']['plate_journal_diametral_clearance_mm'] = round(PLATE_HOLE_D - JOURNAL_D, 3)
    report['measurements']['shoulder_counterbore_diametral_clearance_mm'] = round(PLATE_COUNTERBORE_D - SHOULDER_D, 3)
    report['checks']['plate_journal_clearance_positive'] = (PLATE_HOLE_D - JOURNAL_D) >= 0.4
    report['checks']['shoulder_counterbore_clearance_positive'] = (PLATE_COUNTERBORE_D - SHOULDER_D) >= 0.8

    closed_hook_inner_y = BOX_EDGE_Y - UNDERHOOK
    report['measurements']['closed_underhook_inner_y_mm'] = round(closed_hook_inner_y, 3)
    report['measurements']['closed_underhook_capture_depth_mm'] = round(BOX_EDGE_Y - closed_hook_inner_y, 3)
    report['checks']['closed_hook_captures_box_edge'] = closed_hook_inner_y < BOX_EDGE_Y
    report['checks']['closed_plate_does_not_interpenetrate_rim'] = common_volume(plate, rim, 'closed_plate_vs_rim') < 1e-4

    open_hook_inner_y = closed_hook_inner_y + PLATE_OPEN
    open_clearance = open_hook_inner_y - BOX_EDGE_Y
    report['measurements']['open_underhook_inner_y_mm'] = round(open_hook_inner_y, 3)
    report['measurements']['open_box_edge_clearance_mm'] = round(open_clearance, 3)
    report['checks']['open_clearance_at_least_1mm'] = open_clearance >= 1.0
    pl_open = plate.copy()
    pl_open.translate(App.Vector(0, PLATE_OPEN, 0))
    report['checks']['plate_open_position_clear_of_base'] = common_volume(pl_open, base, 'open_plate_vs_base') < 1e-4
    report['checks']['plate_open_position_clear_of_rim'] = common_volume(pl_open, rim, 'open_plate_vs_rim') < 1e-4

    pl_clamp = plate.copy()
    pl_clamp.translate(App.Vector(0, -CLAMP_PRELOAD, 0))
    clamp_rim_overlap = common_volume(pl_clamp, rim, 'preload_plate_vs_rim')
    clamp_base_overlap = common_volume(pl_clamp, base, 'preload_plate_vs_base')
    report['measurements']['preload_rim_overlap_mm3'] = round(clamp_rim_overlap, 6)
    report['measurements']['preload_base_overlap_mm3'] = round(clamp_base_overlap, 6)
    report['checks']['preload_reaches_box_rim'] = clamp_rim_overlap > 1.0
    report['checks']['preload_does_not_hit_base'] = clamp_base_overlap < 1e-4

    def placed_spindle(travel_mm, rotate_deg):
        q = spindle.copy()
        q.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), rotate_deg)
        q.translate(App.Vector(SPINDLE_X, BOX_EDGE_Y + travel_mm, SPINDLE_Z))
        return q

    nut = lead_nut.copy()
    nut.translate(App.Vector(SPINDLE_X, NUT_Y0, SPINDLE_Z))
    nut_base_common = common_volume(base, nut, 'separate_lead_nut_vs_base')
    checkpoint('distance:start:separate_lead_nut_vs_base')
    nut_base_distance = base.distToShape(nut)[0]
    checkpoint('distance:done:separate_lead_nut_vs_base', {'distance_mm': round(nut_base_distance, 6)})
    report['measurements']['lead_nut_base_common_mm3'] = round(nut_base_common, 6)
    report['measurements']['lead_nut_base_distance_mm'] = round(nut_base_distance, 6)
    report['checks']['separate_lead_nut_fits_base_pocket'] = nut_base_common < 1e-4 and nut_base_distance <= 0.5

    # Validate the actual cartridge retention assembly, not just file existence.
    pin = retainer_pin.copy()
    pin.translate(App.Vector(SPINDLE_X,
                             NUT_Y0+LEAD_NUT_PIN_Y,
                             SPINDLE_Z+LEAD_NUT_PIN_Z))
    pin_base_common = common_volume(base, pin, 'lead_nut_retainer_pin_vs_base')
    pin_nut_common = common_volume(nut, pin, 'lead_nut_retainer_pin_vs_nut')
    report['measurements']['lead_nut_retainer_pin_base_common_mm3'] = round(pin_base_common, 6)
    report['measurements']['lead_nut_retainer_pin_nut_common_mm3'] = round(pin_nut_common, 6)
    report['measurements']['lead_nut_retainer_pin_right_protrusion_mm'] = round(
        pin.BoundBox.XMax-(SPINDLE_X+11.0), 3)
    report['checks']['lead_nut_retainer_pin_passes_base_bore'] = pin_base_common < 1e-4
    report['checks']['lead_nut_retainer_pin_passes_cartridge_bore'] = pin_nut_common < 1e-4
    report['checks']['lead_nut_retainer_pin_protrudes_for_clip'] = (
        report['measurements']['lead_nut_retainer_pin_right_protrusion_mm'] >= 3.0)

    clip = pin_clip.copy()
    clip.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90.0)
    clip.translate(App.Vector(SPINDLE_X+NUT_PIN_GROOVE_X0,
                              NUT_Y0+LEAD_NUT_PIN_Y,
                              SPINDLE_Z+LEAD_NUT_PIN_Z))
    clip_base_common = common_volume(base, clip, 'lead_nut_pin_clip_vs_base')
    clip_pin_common = common_volume(pin, clip, 'lead_nut_pin_clip_vs_pin')
    checkpoint('distance:start:lead_nut_pin_clip_vs_pin')
    clip_pin_distance = pin.distToShape(clip)[0]
    checkpoint('distance:done:lead_nut_pin_clip_vs_pin', {'distance_mm': round(clip_pin_distance, 6)})
    report['measurements']['lead_nut_pin_clip_base_common_mm3'] = round(clip_base_common, 6)
    report['measurements']['lead_nut_pin_clip_pin_common_mm3'] = round(clip_pin_common, 6)
    report['measurements']['lead_nut_pin_clip_radial_clearance_mm'] = round(clip_pin_distance, 6)
    report['checks']['lead_nut_pin_clip_is_outside_base'] = clip_base_common < 1e-4
    report['checks']['lead_nut_pin_clip_fits_groove_without_collision'] = (
        clip_pin_common < 1e-4 and 0.04 <= clip_pin_distance <= 0.16)

    # Correct screw motion is translation plus the matching RH 8x2 rotation.
    # BASE is intentionally smooth: thread engagement must be exclusively between
    # the spindle and the removable lead-nut cartridge.
    thread_states = []
    for travel in (-CLAMP_PRELOAD, 0.0, 0.5, 1.0, 2.0, 4.0, PLATE_OPEN):
        rot = -360.0 * travel / THREAD_PITCH
        q = placed_spindle(travel, rot)
        n_common = common_volume(nut, q, 'separate_thread_nut_vs_spindle_travel_' + str(travel))
        b_common = common_volume(base, q, 'smooth_base_vs_spindle_travel_' + str(travel))
        thread_states.append({
            'travel_mm': travel,
            'rotation_deg': rot,
            'nut_common_mm3': round(n_common, 6),
            'base_common_mm3': round(b_common, 6),
        })
    report['thread_states'] = thread_states
    report['checks']['correct_separate_thread_phase_collision_free'] = all(
        x['nut_common_mm3'] < 0.5 for x in thread_states
    )
    report['checks']['smooth_base_clear_over_full_spindle_travel'] = all(
        x['base_common_mm3'] < 1e-4 for x in thread_states
    )

    # A real female thread must reject axial motion if the screw does not rotate.
    q_slide = placed_spindle(0.5, 0.0)
    slide_interference = common_volume(nut, q_slide, 'separate_thread_axial_slide_without_rotation')
    report['measurements']['axial_slide_without_rotation_interference_mm3'] = round(slide_interference, 6)
    report['checks']['separate_thread_blocks_axial_slide_without_rotation'] = slide_interference > 1.0

    # At +0.5 mm travel the correct rotation is -90 deg. +90 deg is 180 deg out
    # of phase and must visibly intersect a developed RH 8x2 female thread.
    q_wrong = placed_spindle(0.5, 90.0)
    wrong_interference = common_volume(nut, q_wrong, 'separate_thread_wrong_phase')
    report['measurements']['wrong_phase_interference_mm3'] = round(wrong_interference, 6)
    report['checks']['separate_thread_has_phase_sensitive_engagement'] = wrong_interference > 1.0

    # The knob-retainer nut must use the same RH8x2 profile as the outer stud.
    # At its actual axial contact position the nut needs the corresponding phase;
    # half a pitch out of phase must create interference.
    cap = knob_retainer_nut.copy()
    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG)
    cap.translate(App.Vector(0, CAP_NUT_Y0, 0))
    cap_common = common_volume(spindle, cap, 'knob_retainer_nut_correct_phase')
    cap_wrong = knob_retainer_nut.copy()
    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG+180.0)
    cap_wrong.translate(App.Vector(0, CAP_NUT_Y0, 0))
    cap_wrong_common = common_volume(spindle, cap_wrong, 'knob_retainer_nut_half_pitch_wrong_phase')
    cap_engagement = max(0.0, min(knob_retainer_nut.BoundBox.YLength,
                                  OUTER_STUD_Y0+OUTER_STUD_LEN-CAP_NUT_Y0))
    report['measurements']['knob_retainer_nut_phase_deg'] = round(CAP_NUT_PHASE_DEG, 3)
    report['measurements']['knob_retainer_nut_correct_phase_common_mm3'] = round(cap_common, 6)
    report['measurements']['knob_retainer_nut_wrong_phase_common_mm3'] = round(cap_wrong_common, 6)
    report['measurements']['knob_retainer_nut_actual_engagement_mm'] = round(cap_engagement, 3)
    report['checks']['knob_retainer_nut_matches_outer_stud'] = cap_common < 0.02
    report['checks']['knob_retainer_nut_has_phase_sensitive_thread'] = cap_wrong_common > 0.25
    report['checks']['knob_retainer_nut_engagement_at_least_4mm'] = cap_engagement >= 4.0

    q0 = placed_spindle(0.0, 0.0)
    spindle_plate_overlap = common_volume(q0, plate, 'nominal_spindle_vs_plate')
    checkpoint('distance:start:nominal_spindle_vs_plate')
    spindle_plate_distance = q0.distToShape(plate)[0]
    checkpoint('distance:done:nominal_spindle_vs_plate', {'distance_mm': round(spindle_plate_distance, 6)})
    report['measurements']['spindle_plate_overlap_mm3'] = round(spindle_plate_overlap, 6)
    report['measurements']['spindle_plate_min_distance_mm'] = round(spindle_plate_distance, 6)
    report['checks']['spindle_passes_plate_hole'] = spindle_plate_overlap < 1e-4
    report['checks']['spindle_thrust_face_reaches_plate'] = spindle_plate_distance < 0.05

    for name, ok in report['checks'].items():
        if not ok:
            report['failed'].append(name)

    path = os.path.join(OUT, 'BOX_CLAMP_VALIDATION.json')
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2), flush=True)
    if report['failed']:
        raise RuntimeError('BOX CLAMP VALIDATION FAILED: ' + ' | '.join(report['failed']))


try:
    run_validation()
except BaseException as exc:
    failure = {
        'exception_type': type(exc).__name__,
        'exception': str(exc),
        'traceback': traceback.format_exc(),
    }
    try:
        with open(os.path.join(OUT, 'BOX_CLAMP_EXCEPTION.json'), 'w') as f:
            json.dump(failure, f, indent=2)
    finally:
        print('[box-clamp] EXCEPTION=' + json.dumps(failure), file=sys.stderr, flush=True)
    raise
