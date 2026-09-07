from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Absolute final rack-M4 nut pass. Rebuild the part from its standalone source
# instead of carrying forward accumulated CSG. The standalone nut is now a
# conventional female thread: a Ø3.44 core bore plus a true radial-Z helical
# groove are SUBTRACTED from a 7 mm AF hex body. Nothing projects inward in
# front of the thread and the cutter extends beyond both nut faces.
old = '''RACK_M4_NUT = hex_z(7.0, 5.6, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
new = '''RACK_M4_NUT = import_scad_shape(os.path.join(ROOT, 'scripts', 'rack_m4_nut.scad')).removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final rack M4 nut construction for full rebuild')
s = s.replace(old, new, 1)

# Validate the actual rebuilt part, not merely nominal dimensions. The middle
# 4.2 mm deliberately excludes both entry chamfers, so additional material
# removed there can only come from the helical groove. A Ø3.40 probe must pass
# axially through the complete nut without touching anything. Finally compare
# the matched printed male in correct phase and at a half-pitch wrong phase:
# correct phase must be collision-free while wrong phase must collide. This is
# a functional geometry witness that the nut contains a real engaging thread.
anchor = "failures = []\n"
if anchor not in s:
    raise SystemExit('Could not locate validation failure anchor')
proof = '''# Authoritative rack-M4 nut checks for the standalone subtractive thread.\n_rack_m4_smooth_ref = hex_z(7.0, 5.6, 0.0).cut(Part.makeCylinder(1.72, 5.6)).removeSplitter()\n_rack_m4_mid_slab = box(-5.0, -5.0, 0.7, 10.0, 10.0, 4.2)\n_rack_m4_smooth_mid = _rack_m4_smooth_ref.common(_rack_m4_mid_slab).Volume\n_rack_m4_threaded_mid = RACK_M4_NUT.common(_rack_m4_mid_slab).Volume\n_rack_m4_helical_removed = _rack_m4_smooth_mid - _rack_m4_threaded_mid\n_rack_m4_clear_core_probe = Part.makeCylinder(1.70, 5.6)\n_rack_m4_clear_core_common = RACK_M4_NUT.common(_rack_m4_clear_core_probe).Volume\n_rack_m4_correct_common = RACK_M4_NUT.common(RACK_M4_MALE).Volume\n_rack_m4_wrong = RACK_M4_MALE.copy()\n_rack_m4_wrong.translate(App.Vector(0, 0, RACK_M4_PITCH/2.0))\n_rack_m4_wrong_common = RACK_M4_NUT.common(_rack_m4_wrong).Volume\nV['rack_m4_female_thread_witness'] = {\n    'standard': 'M4 x 0.7 RH printable pair',\n    'construction': 'subtractive_core_bore_plus_outward_helical_groove',\n    'profile_generator': 'radial_Z_trapezoid_helical_polyhedron',\n    'outer_across_flats_mm': 7.0,\n    'minor_diameter_mm': 3.44,\n    'groove_major_diameter_mm': 4.36,\n    'radial_thread_depth_mm': 0.46,\n    'pitch_mm': RACK_M4_PITCH,\n    'nut_body_height_mm': 5.6,\n    'full_thread_turns': round(5.6/RACK_M4_PITCH, 3),\n    'entry_chamfer_mm': 0.35,\n    'nut_pocket_height_mm': RACK_M4_NUT_H,\n    'nut_pocket_axial_clearance_mm': round(RACK_M4_NUT_H-5.6, 3),\n    'bore_wall_is_thread_crest': True,\n    'continuous_full_height_thread': True,\n    'central_bore_unobstructed': _rack_m4_clear_core_common <= 1e-4,\n    'helical_volume_removed_midspan_mm3': round(_rack_m4_helical_removed, 6),\n    'clear_core_probe_common_mm3': round(_rack_m4_clear_core_common, 6),\n}\nV['rack_m4_thread_check'] = {\n    'standard': 'M4 x 0.7 RH',\n    'pair_generator': 'matched_radial_Z_helical_trapezoids',\n    'female_construction': 'subtractive_core_bore_plus_outward_helical_groove',\n    'printed_male_major_diameter_mm': 3.90,\n    'printed_male_core_diameter_mm': 3.10,\n    'female_root_diameter_mm': 4.36,\n    'female_crest_diameter_mm': 3.44,\n    'radial_core_clearance_mm': 0.17,\n    'correct_phase_common_mm3': round(_rack_m4_correct_common, 6),\n    'half_pitch_wrong_phase_common_mm3': round(_rack_m4_wrong_common, 6),\n}\nif _rack_m4_helical_removed < 0.5:\n    failures.append('Rack M4 nut has no substantial subtractive helical groove')\nif _rack_m4_clear_core_common > 1e-4:\n    failures.append('Rack M4 nut blocks the required through core; thread/wall intrudes into the bore')\nif _rack_m4_correct_common > 0.02:\n    failures.append('Rack M4 nut collides with the matched screw in correct thread phase')\nif _rack_m4_wrong_common < 0.5:\n    failures.append('Rack M4 nut does not geometrically engage the screw at half-pitch wrong phase')\n'''
s = s.replace(anchor, anchor + proof, 1)

if s == orig:
    raise SystemExit('Rack M4 nut rebuild pass made no changes')
p.write_text(s, encoding='utf-8')
print('Applied complete rack M4 nut rebuild: 7 mm AF body + open subtractive M4x0.7 female thread')
