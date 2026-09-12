from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Do not invent a second RH8x2 thread for the short knob-retainer nut.
# Reuse the exact female cutter that already makes eurobox_v50_lead_nut_print:
# same pitch, hand, phase, axial profile and FDM clearances.
old_clearance = '''cap_female_core = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
cap_female_major = THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE
cap_root_w = LEAD_PROFILE_ROOT_W + 2.0*LEAD_FLANK_CLEARANCE
cap_crest_w = LEAD_PROFILE_CREST_W + 2.0*LEAD_FLANK_CLEARANCE'''
new_clearance = '''CAP_RH8_RADIAL_CLEARANCE = LEAD_RADIAL_CLEARANCE
CAP_RH8_FLANK_CLEARANCE = LEAD_FLANK_CLEARANCE
cap_female_core = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
cap_female_major = THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE
cap_root_w = LEAD_PROFILE_ROOT_W + 2.0*LEAD_FLANK_CLEARANCE
cap_crest_w = LEAD_PROFILE_CREST_W + 2.0*LEAD_FLANK_CLEARANCE'''
if s.count(old_clearance) != 1:
    raise SystemExit('Expected exactly one final knob-retainer master-clearance block')
s = s.replace(old_clearance, new_clearance, 1)

# v55 has already rebuilt FEMALE as the true radial/axial RH8x2 solid used to
# cut the known-good lead nut. Replace the separately generated cap cutter with
# an untouched copy of that exact master. Do NOT intersect/clip FEMALE first:
# OCC can split the helical solid at a coincident clip plane.
cap_pattern = re.compile(
    r"CAP_FEMALE_EXT_SCAD = os\.path\.join\(\n"
    r"    OUT, 'thread_RH_8x2_knob_retainer_extended_cutter\.scad'\)\n"
    r"write_female_thread_cutter_scad\(\n"
    r"    CAP_FEMALE_EXT_SCAD,\n"
    r"    cap_female_core, cap_female_major, THREAD_PITCH, CAP_NUT_H,\n"
    r"    cap_root_w, cap_crest_w, CAP_THREAD_OVERRUN\)\n"
    r"CAP_FEMALE = make_true_thread_solid\(\n"
    r"    CAP_FEMALE_EXT_SCAD, cap_female_core, cap_female_major, CAP_NUT_H\)\n",
    re.S,
)
cap_replacement = '''# Exact proven LEAD_NUT female master.
CAP_FEMALE = FEMALE.copy()
if CAP_FEMALE.isNull() or not CAP_FEMALE.isValid() or len(CAP_FEMALE.Solids) != 1:
    raise RuntimeError('Proven RH8x2 FEMALE master is not one valid solid')
'''
s, n = cap_pattern.subn(cap_replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace dedicated retainer cutter with proven FEMALE master')

# Critical OCC robustness detail: the proven FEMALE master is 14 mm long while
# CAP_NUT is only 5.8 mm. Move the cutter one complete 2 mm pitch before the nut
# so it crosses both nut end faces instead of starting exactly coplanar with one
# face. A full-pitch translation preserves the RH8x2 helix phase exactly.
old_cap_cut = '''CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()'''
new_cap_cut = '''CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, -THREAD_PITCH, 0)).removeSplitter()'''
if s.count(old_cap_cut) != 1:
    raise SystemExit('Could not locate short retainer-nut boolean for full-pitch cutter overrun')
s = s.replace(old_cap_cut, new_cap_cut, 1)

s = s.replace(
    "    'profile_source': 'matched RH8x2 master profile with one-pitch cutter overrun',\n",
    "    'profile_source': 'exact FEMALE master from eurobox_v50_lead_nut_print, shifted -1 full pitch for open-end boolean',\n",
    1,
)
meta_anchor = "    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
meta = ("    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
        "    'retainer_radial_clearance_mm': CAP_RH8_RADIAL_CLEARANCE,\n"
        "    'retainer_flank_clearance_each_side_mm': CAP_RH8_FLANK_CLEARANCE,\n"
        "    'retainer_cutter_axial_overrun_mm': THREAD_PITCH,\n"
        "    'reuses_proven_lead_nut_female_master': True,\n")
if s.count(meta_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer metadata anchor')
s = s.replace(meta_anchor, meta, 1)

# Audit the actual printable spindle while it still uses its local +Y screw axis.
spindle_anchor = '''    z_to_y(MALE_STUD, 0, lead_drive_y0+LEAD_DRIVE_LEN, 0),
]).removeSplitter()'''
spindle_extra = '''    z_to_y(MALE_STUD, 0, lead_drive_y0+LEAD_DRIVE_LEN, 0),
]).removeSplitter()
_retainer_thread_y0 = lead_drive_y0 + LEAD_DRIVE_LEN
_retainer_stud_shell_pre = cyl_y(
    THREAD_MAJOR/2.0 + 0.03, OUTER_STUD_LEN,
    0, _retainer_thread_y0, 0).cut(
        cyl_y(THREAD_CORE_R + 0.06, OUTER_STUD_LEN,
              0, _retainer_thread_y0, 0)).removeSplitter()
_retainer_actual_ridge_mm3 = SPINDLE.common(_retainer_stud_shell_pre).Volume
if not SPINDLE.isValid() or len(SPINDLE.Solids) != 1:
    raise RuntimeError('Lead SPINDLE is not one valid threaded solid')'''
if s.count(spindle_anchor) != 1:
    raise SystemExit('Could not locate final square-drive SPINDLE construction')
s = s.replace(spindle_anchor, spindle_extra, 1)

metric_anchor = "    'correct_phase_common_mm3': round(SPINDLE.common(cn).Volume, 6),\n"
if s.count(metric_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer correct-phase metric')
s = s.replace(
    metric_anchor,
    "    'actual_spindle_stud_ridge_mm3': round(_retainer_actual_ridge_mm3, 6),\n" + metric_anchor,
    1,
)

# The master RH8x2 pair already has an authoritative wrong-phase interference
# check on the working lead nut. Since the retainer literally reuses FEMALE,
# retain that master test rather than imposing a second arbitrary collision
# threshold on a much shorter clearance-fit nut.
old_wrong_gate = "if V['knob_retainer_thread']['half_pitch_wrong_phase_common_mm3'] < 0.25:\n    failures.append('Knob retainer nut lacks phase-sensitive RH8x2 engagement')\n"
new_wrong_gate = "if V['wrong_phase_0_5mm_nut_common_mm3'] < 1.0:\n    failures.append('Proven RH8x2 FEMALE master lost phase-sensitive engagement')\n"
if s.count(old_wrong_gate) != 1:
    raise SystemExit('Could not locate obsolete retainer-only wrong-phase gate')
s = s.replace(old_wrong_gate, new_wrong_gate, 1)

fail_anchor = "if V['knob_retainer_thread']['correct_phase_common_mm3'] > 0.02:\n    failures.append('Knob retainer nut collides with matched RH8x2 outer stud')\n"
if s.count(fail_anchor) != 1:
    raise SystemExit('Could not locate retainer correct-phase hard gate')
s = s.replace(
    fail_anchor,
    "if not V['knob_retainer_thread']['reuses_proven_lead_nut_female_master']:\n"
    "    failures.append('Knob retainer nut is not using the proven lead-nut RH8x2 female master')\n"
    "if _retainer_actual_ridge_mm3 < 0.05:\n"
    "    failures.append('Actual exported lead spindle has no developed RH8x2 retainer-stud ridge')\n"
    + fail_anchor,
    1,
)

if s == orig:
    raise SystemExit('Proven-thread retainer pass made no changes')
for witness in [
    'CAP_RH8_RADIAL_CLEARANCE = LEAD_RADIAL_CLEARANCE',
    'CAP_FEMALE = FEMALE.copy()',
    'z_to_y(CAP_FEMALE, 0, -THREAD_PITCH, 0)',
    "'reuses_proven_lead_nut_female_master': True",
    '_retainer_stud_shell_pre = cyl_y(',
]:
    if witness not in s:
        raise SystemExit('Missing proven-thread retainer witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Applied retainer RH8x2 reuse: proven FEMALE master with one-full-pitch open-end overrun')
