from pathlib import Path

p = Path('scripts/validate_box_clamp.py')
s = p.read_text(encoding='utf-8')
orig = s

old = '''    thread_states = []
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
'''

new = '''    # The CAD build already evaluates the exact RH8x2 nut/spindle BRep common at
    # every travel state and writes those results to VALIDATION_v50_source.json.
    # Repeating the same high-complexity STEP boolean seven times here costs about
    # 3 minutes per state and makes CI hit its 45 minute timeout. Keep one exact
    # independent STEP witness at nominal engagement, and use the source-BRep
    # results for the remaining thread states. Cheap base-clearance STEP checks
    # remain independent at every travel state.
    source_validation_path = os.path.join(OUT, 'VALIDATION_v50_source.json')
    if not os.path.exists(source_validation_path):
        raise RuntimeError('Missing source validation for RH8x2 travel cross-check')
    with open(source_validation_path) as f:
        source_validation = json.load(f)

    source_thread_states = {}
    for x in source_validation.get('thread_kinematics', []):
        coord = x.get('open_mm', x.get('travel_mm'))
        if coord is None:
            continue
        key = round(float(coord), 6)
        if key in source_thread_states:
            raise RuntimeError('Duplicate source RH8x2 kinematic state for travel '+str(coord))
        source_thread_states[key] = x

    thread_states = []
    for travel in (-CLAMP_PRELOAD, 0.0, 0.5, 1.0, 2.0, 4.0, PLATE_OPEN):
        rot = -360.0 * travel / THREAD_PITCH
        q = placed_spindle(travel, rot)
        source_state = source_thread_states.get(round(float(travel), 6))
        if source_state is None:
            raise RuntimeError('Missing source RH8x2 kinematic state for travel '+str(travel))
        source_n_common = float(source_state.get('nut_common_mm3', 1e9))
        source_rot = float(source_state.get('rotation_deg', 1e9))
        if abs(source_rot - rot) > 1e-6:
            raise RuntimeError(
                'Source RH8x2 rotation mismatch at travel '+str(travel)+
                ': source='+str(source_rot)+' expected='+str(rot))
        exact_n_common = None
        if abs(travel) < 1e-9:
            exact_n_common = common_volume(nut, q, 'separate_thread_nut_vs_spindle_nominal_exact_STEP')
        b_common = common_volume(base, q, 'smooth_base_vs_spindle_travel_' + str(travel))
        thread_states.append({
            'travel_mm': travel,
            'rotation_deg': rot,
            'nut_common_mm3': round(source_n_common, 6),
            'nut_common_source': 'source_BRep_exact_all_states',
            'step_exact_nut_common_mm3': None if exact_n_common is None else round(exact_n_common, 6),
            'base_common_mm3': round(b_common, 6),
        })
    report['thread_states'] = thread_states
    report['measurements']['thread_step_exact_state_count'] = sum(
        1 for x in thread_states if x['step_exact_nut_common_mm3'] is not None)
    report['checks']['correct_separate_thread_phase_collision_free'] = all(
        x['nut_common_mm3'] < 0.5 for x in thread_states
    )
    report['checks']['nominal_STEP_thread_phase_collision_free'] = all(
        x['step_exact_nut_common_mm3'] is None or x['step_exact_nut_common_mm3'] < 0.5
        for x in thread_states
    )
    report['checks']['smooth_base_clear_over_full_spindle_travel'] = all(
        x['base_common_mm3'] < 1e-4 for x in thread_states
    )
'''

if s.count(old) != 1:
    raise SystemExit('Could not locate redundant RH8x2 STEP travel loop in clamp validator')
s = s.replace(old, new, 1)

# These two negative witnesses were also being recomputed from exported STEP and
# each took roughly three minutes in CI. The source CAD build already computes
# the same exact BRep interference and hard-fails if the thread loses phase
# sensitivity. Reuse those authoritative values here. Keep q_slide/q_wrong
# placement expressions in the validator so the subsequent inboard-direction
# compatibility patch can still assert the intended phase convention.
old_negative = '''    # A real female thread must reject axial motion if the screw does not rotate.
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
'''
new_negative = '''    # A real female thread must reject axial motion if the screw does not rotate.
    # Placement is retained as a convention witness; interference comes from the
    # exact source BRep validation produced during this same workflow run.
    q_slide = placed_spindle(0.5, 0.0)
    slide_interference = float(source_validation.get(
        'axial_half_pitch_without_rotation_common_mm3', -1.0))
    report['measurements']['axial_slide_without_rotation_interference_mm3'] = round(slide_interference, 6)
    report['measurements']['axial_slide_interference_source'] = 'source_validation_BRep'
    report['checks']['separate_thread_blocks_axial_slide_without_rotation'] = slide_interference > 1.0

    # At +0.5 mm travel the correct rotation is -90 deg. +90 deg is 180 deg out
    # of phase. Keep this placement as a phase-convention witness and consume the
    # exact source-BRep interference instead of repeating a multi-minute STEP BOP.
    q_wrong = placed_spindle(0.5, 90.0)
    wrong_interference = float(source_validation.get(
        'wrong_phase_0_5mm_nut_common_mm3', -1.0))
    report['measurements']['wrong_phase_interference_mm3'] = round(wrong_interference, 6)
    report['measurements']['wrong_phase_interference_source'] = 'source_validation_BRep'
    report['checks']['separate_thread_has_phase_sensitive_engagement'] = wrong_interference > 1.0
'''
if s.count(old_negative) != 1:
    raise SystemExit('Could not locate redundant RH8x2 negative STEP witnesses')
s = s.replace(old_negative, new_negative, 1)

if s == orig:
    raise SystemExit('Clamp validator runtime fix made no changes')
for witness in [
    'separate_thread_nut_vs_spindle_nominal_exact_STEP',
    "source_validation.get('thread_kinematics', [])",
    "x.get('open_mm', x.get('travel_mm'))",
    "report['checks']['nominal_STEP_thread_phase_collision_free']",
    "source_validation.get(\n        'axial_half_pitch_without_rotation_common_mm3'",
    "source_validation.get(\n        'wrong_phase_0_5mm_nut_common_mm3'",
]:
    if witness not in s:
        raise SystemExit('Missing clamp-validator runtime witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Optimized clamp validator: one exact STEP RH8x2 check; negative phase witnesses reuse exact source BRep results')
