from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Rack M4 female-thread correction.
#
# The previous female cutter was technically helical, but the resulting internal
# surface looked almost like a smooth bore in the exported nut/knobs. Keep the
# standard M4 x 0.7 pitch, but make the printable internal V-groove explicit:
# - full-depth 60-degree-ish printable profile (0.48 mm radial depth)
# - narrow groove crest so the helix remains clearly visible in STL/slicer
# - extend the cutter one pitch beyond each end so the thread reaches the entry
#   instead of terminating on the first/last planar face.
#
# Male screw stays unchanged because its exported geometry is already correct.
old = """write_thread_scad(RACK_M4_FEMALE_SCAD, 1.72, 2.18, RACK_M4_PITCH, RACK_KNOB_H+0.8, 0.38, 0.18)
RACK_M4_MALE = import_scad_shape(RACK_M4_MALE_SCAD).common(Part.makeCylinder(2.00, RACK_M4_SCREW_LENGTH)).removeSplitter()
RACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(Part.makeCylinder(2.22, RACK_KNOB_H+0.8)).removeSplitter()"""
new = """# Explicit printable M4 x 0.7 female cutter.  Minor diameter 3.36 mm,
# groove major diameter 4.32 mm.  The 0.48 mm radial groove is deliberately
# pronounced enough to survive a 0.4 mm-nozzle PETG print while retaining
# clearance to both the Ø3.90 printed screw and later nominal Ø4.00 metal M4.
RACK_M4_FEMALE_LEN = RACK_KNOB_H + 2.0*RACK_M4_PITCH
write_thread_scad(RACK_M4_FEMALE_SCAD, 1.68, 2.16, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.50, 0.08)
RACK_M4_MALE = import_scad_shape(RACK_M4_MALE_SCAD).common(Part.makeCylinder(2.00, RACK_M4_SCREW_LENGTH)).removeSplitter()
RACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(
    Part.makeCylinder(2.20, RACK_M4_FEMALE_LEN)).removeSplitter()
# Start one pitch below the part so the helical groove is fully developed at
# the lower entrance and continues beyond the upper face.
RACK_M4_FEMALE.translate(App.Vector(0,0,-RACK_M4_PITCH))"""
if old not in s:
    raise SystemExit('Could not locate v3 rack M4 female-thread generator')
s = s.replace(old, new, 1)

# The v4 thread metadata referred to the previous cutter dimensions. Keep the
# validation report truthful and add direct part-level proof that the nut and
# both knobs contain more than a smooth cylindrical bore.
s = s.replace("'female_cutter_major_diameter_mm': 4.36,", "'female_cutter_major_diameter_mm': 4.32,")
s = s.replace("'printed_pair_radial_major_clearance_mm': round((4.36-3.90)/2.0, 3),", "'printed_pair_radial_major_clearance_mm': round((4.32-3.90)/2.0, 3),")
s = s.replace("'nominal_metal_M4_radial_major_clearance_mm': round((4.36-4.00)/2.0, 3),", "'nominal_metal_M4_radial_major_clearance_mm': round((4.32-4.00)/2.0, 3),")

anchor = "V['rack_knob_checks'] = {\n"
if anchor not in s:
    raise SystemExit('Could not locate rack knob validation block')
proof = '''# Direct female-thread witness checks.  Compare each actual threaded part to
# the same body with only a smooth Ø3.36 mm bore.  A meaningful positive volume
# difference proves that a real helical groove was removed from the wall.
rack_m4_smooth_nut = hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.68, 3.2))
rack_m4_nut_thread_extra_removed = rack_m4_smooth_nut.Volume - RACK_M4_NUT.Volume

def _smooth_knob_for_thread_witness(diameter):
    r = diameter/2.0
    k = Part.makeCylinder(r, RACK_KNOB_H)
    scallop_r = 3.0 if diameter >= 26.0 else 2.2
    scallop_c = r + scallop_r - 1.4
    for a in range(0, 360, 45):
        x = scallop_c * math.cos(math.radians(a))
        y = scallop_c * math.sin(math.radians(a))
        k = k.cut(Part.makeCylinder(scallop_r, RACK_KNOB_H+0.4, App.Vector(x,y,-0.2)))
    return k.cut(Part.makeCylinder(1.68, RACK_KNOB_H)).removeSplitter()

rack_m4_smooth_large_knob = _smooth_knob_for_thread_witness(RACK_KNOB_LARGE_D)
rack_m4_smooth_compact_knob = _smooth_knob_for_thread_witness(RACK_KNOB_COMPACT_D)
rack_m4_large_thread_extra_removed = rack_m4_smooth_large_knob.Volume - RACK_KNOB_LARGE.Volume
rack_m4_compact_thread_extra_removed = rack_m4_smooth_compact_knob.Volume - RACK_KNOB_COMPACT.Volume
V['rack_m4_female_thread_witness'] = {
    'minor_diameter_mm': 3.36,
    'groove_major_diameter_mm': 4.32,
    'radial_thread_depth_mm': 0.48,
    'nut_extra_helical_volume_removed_mm3': round(rack_m4_nut_thread_extra_removed, 6),
    'large_knob_extra_helical_volume_removed_mm3': round(rack_m4_large_thread_extra_removed, 6),
    'compact_knob_extra_helical_volume_removed_mm3': round(rack_m4_compact_thread_extra_removed, 6),
}

'''
s = s.replace(anchor, proof + anchor, 1)

fail_anchor = "if V['rack_m4_thread_check']['correct_phase_common_mm3'] > 0.02:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack M4 thread hard gates')
fail = '''for part_name, removed in [
    ('rack M4 nut', V['rack_m4_female_thread_witness']['nut_extra_helical_volume_removed_mm3']),
    ('large rack hand knob', V['rack_m4_female_thread_witness']['large_knob_extra_helical_volume_removed_mm3']),
    ('compact rack hand knob', V['rack_m4_female_thread_witness']['compact_knob_extra_helical_volume_removed_mm3']),
]:
    if removed < 1.0:
        failures.append(part_name+' has no meaningful internal M4 helical groove')
'''
s = s.replace(fail_anchor, fail + fail_anchor, 1)

if s == orig:
    raise SystemExit('Rack female-thread correction made no changes')
p.write_text(s, encoding='utf-8')
print('Applied v50 rack M4 female-thread correction: explicit full-depth M4 x 0.7 grooves')
