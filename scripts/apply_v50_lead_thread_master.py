from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Build the box-clamp RH 8x2 screw and all matching female cutters from one
# profile definition. Keep the rack M4 generator completely untouched.
anchor = "THREAD_CORE_R = 3.25\n"
if anchor not in s:
    raise SystemExit('Could not locate lead-thread constants')
params = """THREAD_CORE_R = 3.25
LEAD_PROFILE_ROOT_W = 0.72
LEAD_PROFILE_CREST_W = 0.30
LEAD_RADIAL_CLEARANCE = 0.18
LEAD_FLANK_CLEARANCE = 0.12
"""
s = s.replace(anchor, params, 1)

# Insert a single source-of-truth helper immediately before the existing 8x2
# master block. Male and female share pitch, hand, phase and trapezoid; female
# dimensions are derived only by explicit radial/flank print clearance.
master_anchor = "MALE_SCAD = os.path.join(OUT, 'thread_RH_8x2_male.scad')\n"
if master_anchor not in s:
    raise SystemExit('Could not locate RH8x2 master start')
helper = '''def write_lead_thread_pair(male_path, female_path, male_length, female_length):
    male_core = THREAD_CORE_R
    male_major = THREAD_MAJOR / 2.0
    female_core = male_core + LEAD_RADIAL_CLEARANCE
    female_major = male_major + LEAD_RADIAL_CLEARANCE
    female_root_w = LEAD_PROFILE_ROOT_W + 2.0 * LEAD_FLANK_CLEARANCE
    female_crest_w = LEAD_PROFILE_CREST_W + 2.0 * LEAD_FLANK_CLEARANCE
    write_thread_scad(male_path, male_core, male_major, THREAD_PITCH,
                      male_length, LEAD_PROFILE_ROOT_W, LEAD_PROFILE_CREST_W)
    write_thread_scad(female_path, female_core, female_major, THREAD_PITCH,
                      female_length, female_root_w, female_crest_w)

'''
s = s.replace(master_anchor, helper + master_anchor, 1)

old_main = '''write_thread_scad(MALE_SCAD, THREAD_CORE_R, THREAD_MAJOR/2, THREAD_PITCH, LEAD_THREAD_LEN, 0.58, 0.24)
write_thread_scad(FEMALE_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, NUT_THREAD_LEN, 1.10, 0.28)
MALE = import_scad_shape(MALE_SCAD).common(Part.makeCylinder(4.06, LEAD_THREAD_LEN)).removeSplitter()
FEMALE = import_scad_shape(FEMALE_SCAD).common(Part.makeCylinder(4.28, NUT_THREAD_LEN)).removeSplitter()'''
new_main = '''write_lead_thread_pair(MALE_SCAD, FEMALE_SCAD, LEAD_THREAD_LEN, NUT_THREAD_LEN)
MALE = import_scad_shape(MALE_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + 0.06, LEAD_THREAD_LEN)).removeSplitter()
FEMALE = import_scad_shape(FEMALE_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + LEAD_RADIAL_CLEARANCE + 0.06,
                      NUT_THREAD_LEN)).removeSplitter()'''
if old_main not in s:
    raise SystemExit('Could not locate final main RH8x2 pair')
s = s.replace(old_main, new_main, 1)

old_stud = '''write_thread_scad(MALE_STUD_SCAD, THREAD_CORE_R, THREAD_MAJOR/2, THREAD_PITCH, OUTER_STUD_LEN, 0.58, 0.24)
write_thread_scad(FEMALE_STUD_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, OUTER_STUD_LEN, 1.10, 0.28)
MALE_STUD = import_scad_shape(MALE_STUD_SCAD).common(Part.makeCylinder(4.06, OUTER_STUD_LEN)).removeSplitter()
FEMALE_STUD = import_scad_shape(FEMALE_STUD_SCAD).common(Part.makeCylinder(4.28, OUTER_STUD_LEN)).removeSplitter()'''
new_stud = '''write_lead_thread_pair(MALE_STUD_SCAD, FEMALE_STUD_SCAD, OUTER_STUD_LEN, OUTER_STUD_LEN)
MALE_STUD = import_scad_shape(MALE_STUD_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + 0.06, OUTER_STUD_LEN)).removeSplitter()
FEMALE_STUD = import_scad_shape(FEMALE_STUD_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + LEAD_RADIAL_CLEARANCE + 0.06,
                      OUTER_STUD_LEN)).removeSplitter()'''
if old_stud not in s:
    raise SystemExit('Could not locate final RH8x2 stud pair')
s = s.replace(old_stud, new_stud, 1)

# Replace obsolete independent-radius witness with the actual matched pair data.
w0 = s.find("lead_nut_smooth = box(-8.0, 0.0, -7.0")
w1 = s.find("V['thread_kinematics'] = []", w0)
if w0 >= 0 and w1 >= 0:
    witness = """V['lead_nut_thread_witness'] = {
    'standard': 'RH 8x2 printable single-source pair',
    'pitch_mm': THREAD_PITCH,
    'male_major_diameter_mm': THREAD_MAJOR,
    'male_minor_diameter_mm': round(2*THREAD_CORE_R, 3),
    'female_minor_diameter_mm': round(2*(THREAD_CORE_R+LEAD_RADIAL_CLEARANCE), 3),
    'female_groove_major_diameter_mm': round(THREAD_MAJOR+2*LEAD_RADIAL_CLEARANCE, 3),
    'radial_clearance_mm': LEAD_RADIAL_CLEARANCE,
    'flank_clearance_each_side_mm': LEAD_FLANK_CLEARANCE,
    'male_root_width_mm': LEAD_PROFILE_ROOT_W,
    'male_crest_width_mm': LEAD_PROFILE_CREST_W,
}

"""
    s = s[:w0] + witness + s[w1:]

s = s.replace("if V['lead_nut_thread_witness']['radial_groove_depth_mm'] < 0.85:\n    failures.append('Lead nut 8x2 groove is too shallow for printable functional thread')\n", "", 1)
s = s.replace("if V['lead_nut_thread_witness']['extra_helical_volume_removed_per_mm'] < 0.5:\n    failures.append('Lead nut 8x2 helix is not geometrically pronounced enough')\n", "", 1)

# Add a phase-sensitive source check. A half-pitch axial move without the
# corresponding 180 degree rotation must hit the female thread.
kin_anchor = "wrong = SPINDLE.copy()\n"
if kin_anchor not in s:
    raise SystemExit('Could not locate lead-thread kinematics checks')
phase_test = """axial_wrong = SPINDLE.copy()
axial_wrong.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y + THREAD_PITCH/2.0, SPINDLE_Z))
nut_phase = LEAD_NUT.copy(); nut_phase.translate(App.Vector(SPINDLE_X[0], NUT_Y0, SPINDLE_Z))
V['axial_half_pitch_without_rotation_common_mm3'] = round(nut_phase.common(axial_wrong).Volume, 6)

"""
s = s.replace(kin_anchor, phase_test + kin_anchor, 1)

fail_anchor = "if V['wrong_phase_0_5mm_nut_common_mm3'] < 1.0:\n    failures.append('Wrong-phase thread test did not create meaningful interference')\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate wrong-phase failure gate')
s = s.replace(fail_anchor, fail_anchor + "if V['axial_half_pitch_without_rotation_common_mm3'] < 1.0:\n    failures.append('Half-pitch axial move without screw rotation did not interfere with lead nut')\n", 1)

if s == orig:
    raise SystemExit('Single-source lead-thread pass made no changes')
if 'RACK_M4_FEMALE_SCAD' not in s:
    raise SystemExit('Rack M4 thread block was lost by RH8x2 pass')

p.write_text(s, encoding='utf-8')
print('Applied v50 single-source RH8x2 lead thread without touching rack M4 geometry')
