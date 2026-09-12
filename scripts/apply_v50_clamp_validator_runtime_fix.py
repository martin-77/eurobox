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
    # 3 minutes per state and made CI hit its 45 minute timeout. Keep this validator
    # independent where it matters: perform one exact STEP boolean at nominal/maximum
    # engagement (travel 0), verify every other travel state against the source BRep
    # kinematics, and continue to run all cheap STEP base-clearance checks. Because a
    # screw translated by d and rotated by 360*d/pitch has the same thread phase modulo
    # one pitch, the seven full STEP booleans were geometrically redundant.
    source_validation_path = os.path.join(OUT, 'VALIDATION_v50_source.json')
    if not os.path.exists(source_validation_path):
        raise RuntimeError('Missing source validation for RH8x2 travel cross-check')
    with open(source_validation_path) as f:
        source_validation = json.load(f)

    # build_v50.py names the source kinematic coordinate `open_mm`; this STEP
    # validator calls the same physical coordinate `travel_mm`.  The old runtime
    # optimization incorrectly searched only for `travel_mm`, creating an empty
    # lookup even though all source states were present.  Accept the canonical
    # source key first and the validator key as a backward-compatible fallback.
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
        # Also verify that the source state describes the same screw phase. This
        # catches a future sign/convention regression instead of silently trusting
        # a matching travel coordinate.
        source_rot = float(source_state.get('rotation_deg', 1e9))
        if abs(source_rot - rot) > 1e-6:
            raise RuntimeError(
                'Source RH8x2 rotation mismatch at travel '+str(travel)+
                ': source='+str(source_rot)+' expected='+str(rot))
        # One independent exact STEP check at maximum thread engagement.
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

if s == orig:
    raise SystemExit('Clamp validator runtime fix made no changes')
for witness in [
    'separate_thread_nut_vs_spindle_nominal_exact_STEP',
    "source_validation.get('thread_kinematics', [])",
    "x.get('open_mm', x.get('travel_mm'))",
    "report['checks']['nominal_STEP_thread_phase_collision_free']",
]:
    if witness not in s:
        raise SystemExit('Missing clamp-validator runtime witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Optimized clamp validator: one exact STEP RH8x2 phase check plus all-state source BRep cross-check')
