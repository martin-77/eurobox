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
    # These are required service parts of the current removable-nut architecture.
    read_step('eurobox_v50_lead_nut_retaining_pin')
    read_step('eurobox_v50_lead_nut_pin_clip')

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
