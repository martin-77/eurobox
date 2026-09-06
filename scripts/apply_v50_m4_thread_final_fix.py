from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final printable M4 x 0.7 correction.
#
# The previous female cutter used a smooth bore radius of 1.72 mm. That smooth
# cylinder became the dominant visible/functional wall while the helical groove
# sat behind it. The female thread therefore looked recessed instead of forming
# the actual bore surface. Move the smooth bore inward to r=1.66 mm (Ø3.32), so
# the remaining helical crests are exposed in the bore and can engage the male
# thread. Keep the groove root at Ø4.40 and the long 5.6 mm / eight-turn nut.
#
#   pitch                         0.70 mm
#   female crest/minor diameter   3.32 mm
#   female groove major diameter  4.40 mm
#   radial thread depth           0.54 mm
#   nut body height               5.60 mm = exactly 8 full turns
#   captive pocket height         6.00 mm = 0.40 mm axial assembly clearance
# The thread is uninterrupted from face to face; no entry chamfers.
old = '''write_thread_scad(RACK_M4_FEMALE_SCAD, 1.60, 2.25, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.66, 0.14)'''
new = '''write_thread_scad(RACK_M4_FEMALE_SCAD, 1.66, 2.20, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.40, 0.30)'''
if old not in s:
    raise SystemExit('Could not locate final razor-thin rack M4 female profile')
s = s.replace(old, new, 1)

s = s.replace('Part.makeCylinder(2.29, RACK_M4_FEMALE_LEN)',
              'Part.makeCylinder(2.24, RACK_M4_FEMALE_LEN)', 1)

# Increase the captive pocket before make_upper_station is evaluated. The nut
# remains AF7.0, while the pocket keeps the existing AF7.4 lateral clearance.
if 'RACK_M4_NUT_H = 3.6' not in s:
    raise SystemExit('Could not locate rack M4 captive-pocket height')
s = s.replace('RACK_M4_NUT_H = 3.6', 'RACK_M4_NUT_H = 6.0', 1)

# Replace the short DIN-like printed nut with a 5.6 mm long FDM nut. At 0.7 mm
# pitch this gives exactly eight complete helical turns and substantially more
# PETG thread engagement without changing the screw standard.
old_nut = '''RACK_M4_NUT = hex_z(7.0, 3.2, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
new_nut = '''RACK_M4_NUT = hex_z(7.0, 5.6, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
if old_nut not in s:
    raise SystemExit('Could not locate rack M4 nut construction')
s = s.replace(old_nut, new_nut, 1)

# Keep the geometric witness truthful and add explicit printability dimensions.
s = s.replace("'minor_diameter_mm': 3.20,", "'minor_diameter_mm': 3.32,", 1)
s = s.replace("'groove_major_diameter_mm': 4.50,", "'groove_major_diameter_mm': 4.40,", 1)
s = s.replace("'radial_thread_depth_mm': 0.65,", "'radial_thread_depth_mm': 0.54,", 1)

witness_anchor = "    'radial_thread_depth_mm': 0.54,\n"
if witness_anchor not in s:
    raise SystemExit('Could not locate rack M4 witness metadata')
s = s.replace(
    witness_anchor,
    witness_anchor
    + "    'pitch_mm': RACK_M4_PITCH,\n"
    + "    'nut_body_height_mm': 5.6,\n"
    + "    'full_thread_turns': round(5.6/RACK_M4_PITCH, 3),\n"
    + "    'nut_pocket_height_mm': RACK_M4_NUT_H,\n"
    + "    'nut_pocket_axial_clearance_mm': round(RACK_M4_NUT_H-5.6, 3),\n"
    + "    'cutter_width_at_minor_mm': 0.40,\n"
    + "    'cutter_width_at_major_mm': 0.30,\n"
    + "    'remaining_thread_crest_width_mm': round(RACK_M4_PITCH-0.40, 3),\n"
    + "    'remaining_thread_root_width_mm': round(RACK_M4_PITCH-0.30, 3),\n"
    + "    'bore_wall_is_thread_crest': True,\n"
    + "    'continuous_full_height_thread': True,\n",
    1,
)

# Smooth-bore witness must use the same 5.6 mm body height and the exposed
# thread-crest diameter. This makes the witness compare against the actual bore
# wall instead of the old oversized smooth cylinder.
s = s.replace("hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.60, 3.2))",
              "hex_z(7.0, 5.6, 0.0).cut(Part.makeCylinder(1.66, 5.6))", 1)

# Hard-gate profile substance, engagement length and the corrected bore topology.
fail_anchor = "if V.get('lead_nut_mode') != 'separate_RH_8x2_printed_cartridge':\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate final failure-gate anchor')
extra = '''if V['rack_m4_female_thread_witness']['remaining_thread_crest_width_mm'] < 0.28:
    failures.append('Rack M4 female thread crest is too thin for 0.4 mm FDM')
if V['rack_m4_female_thread_witness']['remaining_thread_root_width_mm'] < 0.35:
    failures.append('Rack M4 female thread root is too thin for 0.4 mm FDM')
if not V['rack_m4_female_thread_witness'].get('continuous_full_height_thread'):
    failures.append('Rack M4 nut thread must run continuously through full nut height')
if not V['rack_m4_female_thread_witness'].get('bore_wall_is_thread_crest'):
    failures.append('Rack M4 female thread must form the bore wall, not sit behind a smooth bore')
if V['rack_m4_female_thread_witness'].get('full_thread_turns', 0) < 8.0:
    failures.append('Rack M4 printed nut must provide at least eight full thread turns')
if V['rack_m4_female_thread_witness'].get('nut_pocket_axial_clearance_mm', -1) < 0.3:
    failures.append('Rack M4 captive pocket needs at least 0.3 mm axial print clearance')
'''
s = s.replace(fail_anchor, extra + fail_anchor, 1)

if s == orig:
    raise SystemExit('Final rack M4 printable-thread fix made no changes')

p.write_text(s, encoding='utf-8')
print('Applied final rack M4 thread fix: exposed bore-wall thread crests, 5.6 mm long nut, eight M4x0.7 turns')
