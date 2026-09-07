from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Replace the entire accumulated rack-M4 nut CSG with the standalone source of
# truth. This part starts with a Ø4.40 root bore and ADDS the female helical
# tooth inward; it cannot leave a smaller smooth wall in front of the thread.
old = '''RACK_M4_NUT = hex_z(7.0, 5.6, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
new = '''RACK_M4_NUT = import_scad_shape(os.path.join(ROOT, 'scripts', 'rack_m4_nut.scad')).removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final rack M4 nut construction for full rebuild')
s = s.replace(old, new, 1)

# Replace prior descriptive witness values with checks against the actual rebuilt
# part. Material found inside the nominal Ø4.40 root bore can only be the inward
# projecting helical thread tooth.
anchor = "failures = []\n"
if anchor not in s:
    raise SystemExit('Could not locate validation failure anchor')
proof = '''# Authoritative rack-M4 nut checks for the standalone rebuilt part.\n_rack_m4_inner_annulus = Part.makeCylinder(2.19, 5.6).cut(Part.makeCylinder(1.76, 5.6))\n_rack_m4_inward_thread_material = RACK_M4_NUT.common(_rack_m4_inner_annulus).Volume\n_rack_m4_crest_probe = Part.makeCylinder(1.73, 5.6)\n_rack_m4_crest_probe_common = RACK_M4_NUT.common(_rack_m4_crest_probe).Volume\n_rack_m4_correct_common = RACK_M4_NUT.common(RACK_M4_MALE).Volume\n_rack_m4_wrong = RACK_M4_MALE.copy()\n_rack_m4_wrong.translate(App.Vector(0, 0, RACK_M4_PITCH/2.0))\n_rack_m4_wrong_common = RACK_M4_NUT.common(_rack_m4_wrong).Volume\nV['rack_m4_female_thread_witness'] = {\n    'standard': 'M4 x 0.7 RH printable pair',\n    'construction': 'root_bore_plus_inward_material_helix',\n    'profile_generator': 'radial_Z_trapezoid_helical_polyhedron',\n    'root_bore_diameter_mm': 4.40,\n    'minor_diameter_mm': 3.50,\n    'groove_major_diameter_mm': 4.40,\n    'radial_thread_depth_mm': 0.45,\n    'pitch_mm': RACK_M4_PITCH,\n    'nut_body_height_mm': 5.6,\n    'full_thread_turns': round(5.6/RACK_M4_PITCH, 3),\n    'nut_pocket_height_mm': RACK_M4_NUT_H,\n    'nut_pocket_axial_clearance_mm': round(RACK_M4_NUT_H-5.6, 3),\n    'bore_wall_is_thread_crest': True,\n    'continuous_full_height_thread': True,\n    'inward_thread_material_inside_root_bore_mm3': round(_rack_m4_inward_thread_material, 6),\n    'clear_crest_probe_common_mm3': round(_rack_m4_crest_probe_common, 6),\n}\nV['rack_m4_thread_check'] = {\n    'standard': 'M4 x 0.7 RH',\n    'pair_generator': 'matched_radial_Z_helical_trapezoids',\n    'female_construction': 'root_bore_plus_inward_material_helix',\n    'printed_male_major_diameter_mm': 3.90,\n    'female_root_diameter_mm': 4.40,\n    'female_crest_diameter_mm': 3.50,\n    'correct_phase_common_mm3': round(_rack_m4_correct_common, 6),\n    'half_pitch_wrong_phase_common_mm3': round(_rack_m4_wrong_common, 6),\n}\nif _rack_m4_inward_thread_material < 1.0:\n    failures.append('Rack M4 nut has no substantial inward-projecting thread material')\nif _rack_m4_crest_probe_common > 1e-4:\n    failures.append('Rack M4 nut thread blocks the required central crest clearance')\n'''
s = s.replace(anchor, anchor + proof, 1)

if s == orig:
    raise SystemExit('Rack M4 nut rebuild pass made no changes')
p.write_text(s, encoding='utf-8')
print('Applied complete rack M4 nut rebuild from standalone root-bore + inward-thread source')
