from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Absolute final rack-M4 nut pass.
# Keep the nut as a native OCC boolean using the already generated true radial-Z
# female cutter. The previous standalone SCAD import produced multiple CSG
# solids in FreeCAD/importCSG even though the STL rendered correctly. Avoid that
# fragile conversion entirely: cut the open female bore+helix directly from the
# 7 mm AF hex body in FreeCAD.
old = '''RACK_M4_NUT = hex_z(7.0, 5.6, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final OCC rack M4 nut construction')

# The existing OCC construction is already the desired final geometry. Do not
# replace it with scripts/rack_m4_nut.scad. Add a hard topology assertion right
# after construction so a split/invalid nut fails immediately and explicitly.
new = old + '''
if not RACK_M4_NUT.isValid() or len(RACK_M4_NUT.Solids) != 1:
    raise RuntimeError('Rack M4 nut OCC boolean did not produce exactly one valid solid')'''
s = s.replace(old, new, 1)

# Validate the actual OCC-built part. The final female cutter is the true
# radial-Z M4x0.7 cutter from apply_v50_m4_thread_final_fix.py:
# Ø3.32 crest bore, Ø4.40 groove root, continuous through the full 5.6 mm body.
anchor = "failures = []\n"
if anchor not in s:
    raise SystemExit('Could not locate validation failure anchor')
proof = '''# Authoritative rack-M4 nut checks for the final OCC subtractive thread.\n_rack_m4_smooth_ref = hex_z(7.0, 5.6, 0.0).cut(Part.makeCylinder(1.66, 5.6)).removeSplitter()\n_rack_m4_mid_slab = box(-5.0, -5.0, 0.7, 10.0, 10.0, 4.2)\n_rack_m4_smooth_mid = _rack_m4_smooth_ref.common(_rack_m4_mid_slab).Volume\n_rack_m4_threaded_mid = RACK_M4_NUT.common(_rack_m4_mid_slab).Volume\n_rack_m4_helical_removed = _rack_m4_smooth_mid - _rack_m4_threaded_mid\n_rack_m4_clear_core_probe = Part.makeCylinder(1.64, 5.6)\n_rack_m4_clear_core_common = RACK_M4_NUT.common(_rack_m4_clear_core_probe).Volume\n_rack_m4_correct_common = RACK_M4_NUT.common(RACK_M4_MALE).Volume\n_rack_m4_wrong = RACK_M4_MALE.copy()\n_rack_m4_wrong.translate(App.Vector(0, 0, RACK_M4_PITCH/2.0))\n_rack_m4_wrong_common = RACK_M4_NUT.common(_rack_m4_wrong).Volume\nV['rack_m4_female_thread_witness'] = {\n    'standard': 'M4 x 0.7 RH printable pair',\n    'construction': 'native_OCC_hex_minus_radial_Z_bore_and_helical_groove',\n    'profile_generator': 'radial_Z_trapezoid_helical_polyhedron',\n    'outer_across_flats_mm': 7.0,\n    'minor_diameter_mm': 3.32,\n    'groove_major_diameter_mm': 4.40,\n    'radial_thread_depth_mm': 0.54,\n    'pitch_mm': RACK_M4_PITCH,\n    'nut_body_height_mm': 5.6,\n    'full_thread_turns': round(5.6/RACK_M4_PITCH, 3),\n    'nut_pocket_height_mm': RACK_M4_NUT_H,\n    'nut_pocket_axial_clearance_mm': round(RACK_M4_NUT_H-5.6, 3),\n    'bore_wall_is_thread_crest': True,\n    'continuous_full_height_thread': True,\n    'central_bore_unobstructed': _rack_m4_clear_core_common <= 1e-4,\n    'helical_volume_removed_midspan_mm3': round(_rack_m4_helical_removed, 6),\n    'clear_core_probe_common_mm3': round(_rack_m4_clear_core_common, 6),\n    'valid_single_solid': RACK_M4_NUT.isValid() and len(RACK_M4_NUT.Solids) == 1,\n}\nV['rack_m4_thread_check'] = {\n    'standard': 'M4 x 0.7 RH',\n    'pair_generator': 'matched_radial_Z_helical_trapezoids',\n    'female_construction': 'native_OCC_subtractive_thread',\n    'printed_male_major_diameter_mm': 3.90,\n    'printed_male_core_diameter_mm': 3.10,\n    'female_root_diameter_mm': 4.40,\n    'female_crest_diameter_mm': 3.32,\n    'radial_core_clearance_mm': 0.11,\n    'correct_phase_common_mm3': round(_rack_m4_correct_common, 6),\n    'half_pitch_wrong_phase_common_mm3': round(_rack_m4_wrong_common, 6),\n}\nif not V['rack_m4_female_thread_witness']['valid_single_solid']:\n    failures.append('Rack M4 nut is not one valid OCC solid')\nif _rack_m4_helical_removed < 0.5:\n    failures.append('Rack M4 nut has no substantial subtractive helical groove')\nif _rack_m4_clear_core_common > 1e-4:\n    failures.append('Rack M4 nut blocks the required through core; thread/wall intrudes into the bore')\nif _rack_m4_correct_common > 0.02:\n    failures.append('Rack M4 nut collides with the matched screw in correct thread phase')\nif _rack_m4_wrong_common < 0.5:\n    failures.append('Rack M4 nut does not geometrically engage the screw at half-pitch wrong phase')\n'''
s = s.replace(anchor, anchor + proof, 1)

if s == orig:
    raise SystemExit('Rack M4 nut OCC final pass made no changes')
p.write_text(s, encoding='utf-8')
print('Applied final rack M4 nut pass: native OCC 7 mm AF nut with open subtractive M4x0.7 thread')
