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

# The clamp-runtime optimization already replaced the two expensive exported-STEP
# negative booleans with the exact source-BRep phase-rejection values. Do not try
# to patch those legacy STEP-only blocks a second time here; that stale second
# rewrite caused run #204 to fail during source resolution before FreeCAD even
# started. Instead, make the final width pass assert that the optimized source
# gates are still present before it writes the validator back out.
write_anchor = "cp.write_text(cs, encoding='utf-8')\n"
if write_anchor not in s:
    raise SystemExit('Could not locate box-clamp validator writeback')
source_gate_assertion = r'''# The bounded-runtime clamp pass must already have installed source-BRep phase
# rejection gates. Width validation only changes the witness placement/signs.
for _source_gate in (
    "source_validation.get(\n        'axial_half_pitch_without_rotation_common_mm3'",
    "source_validation.get(\n        'wrong_phase_0_5mm_nut_common_mm3'",
):
    if _source_gate not in cs:
        raise SystemExit('Missing optimized source-BRep RH8x2 phase gate')
'''
s = s.replace(write_anchor, source_gate_assertion + "\n" + write_anchor, 1)

if s == orig:
    raise SystemExit('Final width-validator phase patch made no changes')
for witness in [
    'CAP_NUT_PHASE_DEG)\\n',
    'CAP_NUT_PHASE_DEG+180.0',
    'q_slide = placed_spindle(1.0, 0.0)',
    'q_wrong = placed_spindle(0.0, 180.0)',
    'Missing optimized source-BRep RH8x2 phase gate',
]:
    if witness not in s:
        raise SystemExit('Missing final phase-patch witness: ' + witness)

p.write_text(s, encoding='utf-8')
print('Prepared final width validator: corrected retainer phase + optimized source-BRep RH8x2 gates')
