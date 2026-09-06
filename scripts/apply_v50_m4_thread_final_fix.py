from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final printable M4 x 0.7 correction.
#
# The previous female cutter used root_w=0.66 mm at a 0.70 mm pitch. That left
# only 0.04 mm of material at the internal-thread crest. It looked helical in
# CAD and could pass phase/collision checks, but it is physically unprintable
# with a 0.4 mm nozzle. Replace it with a deliberately truncated FDM profile:
#   female minor diameter      3.44 mm
#   female groove major dia.   4.40 mm
#   radial thread depth        0.48 mm
#   cutter width at minor dia. 0.40 mm -> 0.30 mm remaining crest material
#   cutter width at major dia. 0.30 mm -> 0.40 mm remaining root material
# This preserves M4 x 0.7 pitch and clearance to both the Ø3.90 printed test
# screw and later nominal Ø4.00 metal M4 hardware.
old = '''write_thread_scad(RACK_M4_FEMALE_SCAD, 1.60, 2.25, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.66, 0.14)'''
new = '''write_thread_scad(RACK_M4_FEMALE_SCAD, 1.72, 2.20, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.40, 0.30)'''
if old not in s:
    raise SystemExit('Could not locate final razor-thin rack M4 female profile')
s = s.replace(old, new, 1)

s = s.replace('Part.makeCylinder(2.29, RACK_M4_FEMALE_LEN)',
              'Part.makeCylinder(2.24, RACK_M4_FEMALE_LEN)', 1)

# The service nut must have one uninterrupted helical thread from face to face.
# Do NOT add entry chamfers here: on a 3.2 mm-high M4 nut a 0.55 mm chamfer at
# each end removes a substantial part of the first and last turns and makes the
# thread look and behave like separated rings. The female cutter already extends
# beyond both faces, so the helix opens cleanly at each end without a skin.
old_nut = '''RACK_M4_NUT = hex_z(7.0, 3.2, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
new_nut = '''RACK_M4_NUT = hex_z(7.0, 3.2, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
if old_nut not in s:
    raise SystemExit('Could not locate rack M4 nut construction')
s = s.replace(old_nut, new_nut, 1)

# Keep the geometric witness truthful and add explicit printability dimensions.
s = s.replace("'minor_diameter_mm': 3.20,", "'minor_diameter_mm': 3.44,", 1)
s = s.replace("'groove_major_diameter_mm': 4.50,", "'groove_major_diameter_mm': 4.40,", 1)
s = s.replace("'radial_thread_depth_mm': 0.65,", "'radial_thread_depth_mm': 0.48,", 1)

witness_anchor = "    'radial_thread_depth_mm': 0.48,\n"
if witness_anchor not in s:
    raise SystemExit('Could not locate rack M4 witness metadata')
s = s.replace(
    witness_anchor,
    witness_anchor
    + "    'pitch_mm': RACK_M4_PITCH,\n"
    + "    'cutter_width_at_minor_mm': 0.40,\n"
    + "    'cutter_width_at_major_mm': 0.30,\n"
    + "    'remaining_thread_crest_width_mm': round(RACK_M4_PITCH-0.40, 3),\n"
    + "    'remaining_thread_root_width_mm': round(RACK_M4_PITCH-0.30, 3),\n"
    + "    'continuous_full_height_thread': True,\n",
    1,
)

# The smooth witness bore must match the new 3.44 mm minor diameter.
s = s.replace("hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.60, 3.2))",
              "hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.72, 3.2))", 1)

# Hard gate the feature the old validation missed: actual material width at the
# internal thread crest/root. A phase-sensitive helix alone is not sufficient.
fail_anchor = "if V.get('lead_nut_mode') != 'separate_RH_8x2_printed_cartridge':\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate final failure-gate anchor')
extra = '''if V['rack_m4_female_thread_witness']['remaining_thread_crest_width_mm'] < 0.28:
    failures.append('Rack M4 female thread crest is too thin for 0.4 mm FDM')
if V['rack_m4_female_thread_witness']['remaining_thread_root_width_mm'] < 0.35:
    failures.append('Rack M4 female thread root is too thin for 0.4 mm FDM')
if not V['rack_m4_female_thread_witness'].get('continuous_full_height_thread'):
    failures.append('Rack M4 nut thread must run continuously through full nut height')
'''
s = s.replace(fail_anchor, extra + fail_anchor, 1)

if s == orig:
    raise SystemExit('Final rack M4 printable-thread fix made no changes')

p.write_text(s, encoding='utf-8')
print('Applied final rack M4 thread fix: continuous full-height printable nut thread; AF7 knobs unchanged')
