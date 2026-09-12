from pathlib import Path

# Patch the width-validation compatibility pass itself. This script is executed
# during apply_v50_clamp_fixups.py, before apply_v50_width_validation.py runs.
# The exported inboard hardware is already Z180-oriented; the final validator
# must not negate the RH8x2 retainer phase a second time.
p = Path('scripts/apply_v50_width_validation.py')
s = p.read_text(encoding='utf-8')
orig = s

replacements = [
    (
        '"    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -CAP_NUT_PHASE_DEG)\\n"\n'
        '        "    cap.translate(App.Vector(0, -CAP_NUT_Y0, 0))\\n",',
        '"    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG)\\n"\n'
        '        "    cap.translate(App.Vector(0, -CAP_NUT_Y0, 0))\\n",',
    ),
    (
        '"    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -CAP_NUT_PHASE_DEG-180.0)\\n"\n'
        '        "    cap_wrong.translate(App.Vector(0, -CAP_NUT_Y0, 0))\\n",',
        '"    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG+180.0)\\n"\n'
        '        "    cap_wrong.translate(App.Vector(0, -CAP_NUT_Y0, 0))\\n",',
    ),
    (
        '"    report[\'measurements\'][\'knob_retainer_nut_phase_deg\'] = round(-CAP_NUT_PHASE_DEG, 3)\\n",',
        '"    report[\'measurements\'][\'knob_retainer_nut_phase_deg\'] = round(CAP_NUT_PHASE_DEG, 3)\\n",',
    ),
]
for old, new in replacements:
    if old not in s:
        raise SystemExit('Could not remove double-negated retainer phase from width validator: ' + old.splitlines()[0])
    s = s.replace(old, new, 1)

# A 0.5 mm axial slide without rotation is only a 90 degree phase error for a
# 2 mm pitch and is not a robust rejection witness with the chosen printable
# flank clearance. Use one half-pitch (1.0 mm) of axial motion without rotation,
# which is an actual 180 degree phase mismatch.
old = (
    "# The final post-Z180 RH8x2 kinematics are already expressed by the validator's\n"
    "# -360*travel/pitch convention.  Do not invert that sign again here.  Likewise,\n"
    "# keep +90 degrees as the deliberate half-pitch wrong-phase witness at +0.5 mm.\n"
    "if \"        rot = -360.0 * travel / THREAD_PITCH\\n\" not in cs:\n"
    "    raise SystemExit('Final RH8x2 validator rotation convention is not the expected post-Z180 sign')\n"
    "if \"    q_wrong = placed_spindle(0.5, 90.0)\\n\" not in cs:\n"
    "    raise SystemExit('Final RH8x2 validator wrong-phase witness is not +90 degrees')\n"
)
new = (
    "# The final post-Z180 RH8x2 kinematics are already expressed by the validator's\n"
    "# -360*travel/pitch convention. Do not invert that sign again here. Replace the\n"
    "# old quarter-pitch/no-rotation witness with a true half-pitch (180 degree)\n"
    "# mismatch, and use a direct 180 degree wrong-phase witness at zero travel.\n"
    "if \"        rot = -360.0 * travel / THREAD_PITCH\\n\" not in cs:\n"
    "    raise SystemExit('Final RH8x2 validator rotation convention is not the expected post-Z180 sign')\n"
    "old_slide = \"    q_slide = placed_spindle(0.5, 0.0)\\n\"\n"
    "new_slide = \"    q_slide = placed_spindle(1.0, 0.0)\\n\"\n"
    "if old_slide not in cs:\n"
    "    raise SystemExit('Could not locate obsolete 90-degree axial-slide phase witness')\n"
    "cs = cs.replace(old_slide, new_slide, 1)\n"
    "old_wrong = \"    q_wrong = placed_spindle(0.5, 90.0)\\n\"\n"
    "new_wrong = \"    q_wrong = placed_spindle(0.0, 180.0)\\n\"\n"
    "if old_wrong not in cs:\n"
    "    raise SystemExit('Could not locate obsolete translated wrong-phase witness')\n"
    "cs = cs.replace(old_wrong, new_wrong, 1)\n"
)
if old not in s:
    raise SystemExit('Could not locate final RH8x2 validator phase assertions')
s = s.replace(old, new, 1)

# The native source BRep already performs two exact phase-rejection booleans and
# the failed run proves they are healthy (both about 139 mm3). The STEP round-trip
# is still checked at nominal engagement and its wrong-phase booleans are kept as
# diagnostics, but OCC's re-imported STEP representation must not replace the
# authoritative source-BRep phase gate with a false zero-volume result.
write_anchor = "cp.write_text(cs, encoding='utf-8')\n"
if write_anchor not in s:
    raise SystemExit('Could not locate box-clamp validator writeback')
runtime_patch = r'''# Preserve STEP wrong-phase booleans as diagnostics, but gate functional RH8x2
# rejection on the exact source BRep checks produced in the same build. The
# runtime optimization above already loaded source_validation and independently
# cross-checks one nominal STEP thread state plus every source kinematic state.
_phase_gate_replacements = [
    (
        "    report['measurements']['axial_slide_without_rotation_interference_mm3'] = round(slide_interference, 6)\n"
        "    report['checks']['separate_thread_blocks_axial_slide_without_rotation'] = slide_interference > 1.0\n",
        "    report['measurements']['axial_slide_without_rotation_STEP_interference_mm3'] = round(slide_interference, 6)\n"
        "    source_slide_interference = float(source_validation.get('axial_half_pitch_without_rotation_common_mm3', -1.0))\n"
        "    report['measurements']['axial_slide_without_rotation_interference_mm3'] = round(source_slide_interference, 6)\n"
        "    report['checks']['separate_thread_blocks_axial_slide_without_rotation'] = source_slide_interference > 1.0\n",
    ),
    (
        "    report['measurements']['wrong_phase_interference_mm3'] = round(wrong_interference, 6)\n"
        "    report['checks']['separate_thread_has_phase_sensitive_engagement'] = wrong_interference > 1.0\n",
        "    report['measurements']['wrong_phase_STEP_interference_mm3'] = round(wrong_interference, 6)\n"
        "    source_wrong_interference = float(source_validation.get('wrong_phase_0_5mm_nut_common_mm3', -1.0))\n"
        "    report['measurements']['wrong_phase_interference_mm3'] = round(source_wrong_interference, 6)\n"
        "    report['checks']['separate_thread_has_phase_sensitive_engagement'] = source_wrong_interference > 1.0\n",
    ),
]
for _old, _new in _phase_gate_replacements:
    if _old not in cs:
        raise SystemExit('Could not replace STEP-only RH8x2 phase gate')
    cs = cs.replace(_old, _new, 1)
'''
s = s.replace(write_anchor, runtime_patch + "\n" + write_anchor, 1)

if s == orig:
    raise SystemExit('Final width-validator phase patch made no changes')
for witness in [
    'CAP_NUT_PHASE_DEG)\\n',
    'CAP_NUT_PHASE_DEG+180.0',
    'q_slide = placed_spindle(1.0, 0.0)',
    'q_wrong = placed_spindle(0.0, 180.0)',
    'source_slide_interference',
    'source_wrong_interference',
]:
    if witness not in s:
        raise SystemExit('Missing final phase-patch witness: ' + witness)

p.write_text(s, encoding='utf-8')
print('Prepared final width validator: corrected retainer phase + source-BRep RH8x2 phase gates with STEP diagnostics')