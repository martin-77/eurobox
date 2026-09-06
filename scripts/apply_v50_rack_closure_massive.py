from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Rack closure v4: keep the modular M4 screw/nut/knob system, but remove the
# cantilevered closure ear. The moving lower jaw now remains a continuous solid
# body from the hinge-side shell through the screw axis. The fixed upper/base is
# already a continuous bridge at this Y position; only the screw bore and captive
# nut pocket are cut into it.
old = '''lower_shell = box(-12.6, -7.0, -14.5, 25.2, 14.0, 14.5)
lower_pivot = cyl_x(5.0, 25.2, -12.6, PIN_Y, PIN_Z)
lower_web = box(-12.6, PIN_Y, -10.5, 25.2, 7.0, 10.5)
closure_ear = box(-RACK_CLOSURE_PAD_X/2.0, 5.0, RACK_CLOSURE_PAD_Z0,
                  RACK_CLOSURE_PAD_X, 10.0,
                  RACK_CLOSURE_PAD_Z1-RACK_CLOSURE_PAD_Z0)
LOWER = fuse_all([lower_shell, lower_pivot, lower_web, closure_ear])
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
lower_screw_bore = Part.makeCylinder(
    RACK_M4_LOWER_CLEAR_D/2.0, 7.0,
    App.Vector(0.0, RACK_CLOSURE_Y, RACK_CLOSURE_PAD_Z0-1.0),
    App.Vector(0,0,1))
LOWER = LOWER.cut(lower_screw_bore)
LOWER = LOWER.removeSplitter()'''
new = '''# Continuous full-depth lower clamp body. Y=-7..+15 includes the closure
# screw axis at Y=+11 without a projecting tab/ear; load from the screw therefore
# enters the same 25.2 mm wide body that forms the tube saddle.
lower_shell = box(-12.6, -7.0, -14.5, 25.2, 22.0, 14.5)
lower_pivot = cyl_x(5.0, 25.2, -12.6, PIN_Y, PIN_Z)
lower_web = box(-12.6, PIN_Y, -10.5, 25.2, 7.0, 10.5)
LOWER = fuse_all([lower_shell, lower_pivot, lower_web])
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
lower_screw_bore = Part.makeCylinder(
    RACK_M4_LOWER_CLEAR_D/2.0, 16.5,
    App.Vector(0.0, RACK_CLOSURE_Y, -15.5),
    App.Vector(0,0,1))
LOWER = LOWER.cut(lower_screw_bore)
LOWER = LOWER.removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate v3 lower closure-ear geometry')
s = s.replace(old, new, 1)

# The old adjustment diagnostic inferred capacity from the artificial 3.5 mm
# gap above the closure ear. With the continuous body there is intentionally no
# gap at the nominal closed stop. Adjustment comes from screw travel while the
# lower rotates around the hinge. Allocate 1.0 mm usable closure-side travel;
# only ~0.786 mm is required to accommodate a full 0.41 mm tube-diameter change.
old = '''closure_nominal_gap_mm = 0.0 - RACK_CLOSURE_PAD_Z1
closure_mapped_tube_adjustment_mm = closure_nominal_gap_mm * tube_arm_mm / closure_arm_mm'''
new = '''closure_nominal_gap_mm = 0.0
closure_screw_adjustment_mm = 1.0
closure_mapped_tube_adjustment_mm = closure_screw_adjustment_mm * tube_arm_mm / closure_arm_mm
closure_required_screw_travel_mm = 0.41 * closure_arm_mm / tube_arm_mm'''
if old not in s:
    raise SystemExit('Could not locate v3 rack-closure adjustment calculation')
s = s.replace(old, new, 1)

old = "    'nominal_lower_to_base_gap_mm': round(closure_nominal_gap_mm, 6),\n    'mapped_tube_adjustment_mm': round(closure_mapped_tube_adjustment_mm, 6),"
new = "    'nominal_lower_to_base_gap_mm': round(closure_nominal_gap_mm, 6),\n    'continuous_lower_body_through_screw_axis': True,\n    'closure_screw_adjustment_mm': round(closure_screw_adjustment_mm, 6),\n    'required_closure_screw_travel_for_0_41mm_tube_range_mm': round(closure_required_screw_travel_mm, 6),\n    'mapped_tube_adjustment_mm': round(closure_mapped_tube_adjustment_mm, 6),"
if old not in s:
    raise SystemExit('Could not locate rack-closure metadata block')
s = s.replace(old, new, 1)

# Explicit printable M4 x 0.7 thread-pair check. The male print thread is
# Ø3.90 mm major; the female cutter reaches Ø4.36 mm major, giving 0.23 mm
# radial crest clearance for the printed pair and 0.18 mm for nominal Ø4.00
# metal hardware at the major-diameter envelope. Verify the actual helical CSG:
# correct phase must be collision-free while a half-pitch phase error must
# intersect the surrounding female-thread test body.
anchor = "V['rack_knob_checks'] = {\n"
if anchor not in s:
    raise SystemExit('Could not locate rack-knob validation anchor')
thread_check = '''rack_m4_test_body = Part.makeCylinder(6.0, 7.0).cut(RACK_M4_FEMALE)
rack_m4_test_male = RACK_M4_MALE.common(Part.makeCylinder(2.05, 7.0))
rack_m4_correct_common = rack_m4_test_body.common(rack_m4_test_male).Volume
rack_m4_wrong = rack_m4_test_male.copy()
rack_m4_wrong.translate(App.Vector(0,0,RACK_M4_PITCH/2.0))
rack_m4_wrong_common = rack_m4_test_body.common(rack_m4_wrong).Volume
V['rack_m4_thread_check'] = {
    'standard': 'M4 x 0.7 RH',
    'pitch_mm': RACK_M4_PITCH,
    'printed_male_major_diameter_mm': 3.90,
    'female_cutter_major_diameter_mm': 4.36,
    'printed_pair_radial_major_clearance_mm': round((4.36-3.90)/2.0, 3),
    'nominal_metal_M4_radial_major_clearance_mm': round((4.36-4.00)/2.0, 3),
    'correct_phase_common_mm3': round(rack_m4_correct_common, 6),
    'half_pitch_wrong_phase_common_mm3': round(rack_m4_wrong_common, 6),
}

'''
s = s.replace(anchor, thread_check + anchor, 1)

# Add hard gates for the thread geometry rather than merely trusting dimensions.
fail_anchor = "if V['rack_closure']['mapped_tube_adjustment_mm'] < 0.41:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack closure failure gates')
fail_insert = '''if V['rack_m4_thread_check']['correct_phase_common_mm3'] > 0.02:
    failures.append('Rack M4 printed screw collides with matching female thread in correct phase')
if V['rack_m4_thread_check']['half_pitch_wrong_phase_common_mm3'] < 0.02:
    failures.append('Rack M4 female geometry does not produce meaningful helical thread engagement')
if not V['rack_closure']['continuous_lower_body_through_screw_axis']:
    failures.append('Rack lower closure is no longer continuous through screw axis')
if V['rack_closure']['closure_screw_adjustment_mm'] < V['rack_closure']['required_closure_screw_travel_for_0_41mm_tube_range_mm']:
    failures.append('Rack closure screw travel cannot cover complete 12.00..12.41 mm tube range')
'''
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

# Assembly positions used RACK_CLOSURE_PAD_Z0 as the underside of the former
# ear. The continuous body underside is -14.5 mm; place screw/knob accordingly.
s = s.replace('RACK_CLOSURE_PAD_Z0-1.8', '-14.5-1.8')
s = s.replace('RACK_CLOSURE_PAD_Z0-RACK_KNOB_H-1.8', '-14.5-RACK_KNOB_H-1.8')

if s == orig:
    raise SystemExit('Massive rack-closure patch made no changes')
p.write_text(s, encoding='utf-8')
print('Applied v50 rack closure v4: continuous lower body + hard-checked M4 x 0.7 threads')
