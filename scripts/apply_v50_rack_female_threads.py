from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Rack M4 female-thread correction.
#
# Build #64 proved that the helix was present and phase-sensitive, but the first
# witness gate used an absolute 1.0 mm3 removed-volume threshold for every part.
# That is invalid for a 3.2 mm nut versus an 8 mm knob.  Keep the geometric gate,
# deepen the printable female profile slightly, and validate helical removal per
# millimetre of actual threaded length.
#
# Male screw stays unchanged because its exported geometry is already correct.
old = """write_thread_scad(RACK_M4_FEMALE_SCAD, 1.72, 2.18, RACK_M4_PITCH, RACK_KNOB_H+0.8, 0.38, 0.18)
RACK_M4_MALE = import_scad_shape(RACK_M4_MALE_SCAD).common(Part.makeCylinder(2.00, RACK_M4_SCREW_LENGTH)).removeSplitter()
RACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(Part.makeCylinder(2.22, RACK_KNOB_H+0.8)).removeSplitter()"""
new = """# Explicit printable M4 x 0.7 female cutter.  Minor diameter 3.30 mm,
# groove major diameter 4.40 mm.  The 0.55 mm radial groove is deliberately
# pronounced for a 0.4 mm-nozzle PETG print while retaining clearance to the
# Ø3.90 printed screw and later nominal Ø4.00 metal M4.
RACK_M4_FEMALE_LEN = RACK_KNOB_H + 2.0*RACK_M4_PITCH
write_thread_scad(RACK_M4_FEMALE_SCAD, 1.65, 2.20, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.62, 0.10)
RACK_M4_MALE = import_scad_shape(RACK_M4_MALE_SCAD).common(Part.makeCylinder(2.00, RACK_M4_SCREW_LENGTH)).removeSplitter()
RACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(
    Part.makeCylinder(2.24, RACK_M4_FEMALE_LEN)).removeSplitter()
# Start one pitch below the part so the helical groove is fully developed at
# the lower entrance and continues beyond the upper face.
RACK_M4_FEMALE.translate(App.Vector(0,0,-RACK_M4_PITCH))"""
if old not in s:
    raise SystemExit('Could not locate v3 rack M4 female-thread generator')
s = s.replace(old, new, 1)

# Keep the v4 thread metadata truthful for the corrected profile.
s = s.replace("'female_cutter_major_diameter_mm': 4.36,", "'female_cutter_major_diameter_mm': 4.40,")
s = s.replace("'printed_pair_radial_major_clearance_mm': round((4.36-3.90)/2.0, 3),", "'printed_pair_radial_major_clearance_mm': round((4.40-3.90)/2.0, 3),")
s = s.replace("'nominal_metal_M4_radial_major_clearance_mm': round((4.36-4.00)/2.0, 3),", "'nominal_metal_M4_radial_major_clearance_mm': round((4.40-4.00)/2.0, 3),")

anchor = "V['rack_knob_checks'] = {\n"
if anchor not in s:
    raise SystemExit('Could not locate rack knob validation block')
proof = '''# Direct female-thread witness checks. Compare each actual threaded part to
# the same body with only a smooth Ø3.30 mm bore. The difference is the material
# removed specifically by the helical groove. Normalise by threaded length so a
# short M4 nut is not judged by the same absolute volume as an 8 mm hand knob.
rack_m4_smooth_nut = hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.65, 3.2))
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
    return k.cut(Part.makeCylinder(1.65, RACK_KNOB_H)).removeSplitter()

rack_m4_smooth_large_knob = _smooth_knob_for_thread_witness(RACK_KNOB_LARGE_D)
rack_m4_smooth_compact_knob = _smooth_knob_for_thread_witness(RACK_KNOB_COMPACT_D)
rack_m4_large_thread_extra_removed = rack_m4_smooth_large_knob.Volume - RACK_KNOB_LARGE.Volume
rack_m4_compact_thread_extra_removed = rack_m4_smooth_compact_knob.Volume - RACK_KNOB_COMPACT.Volume
rack_m4_nut_removed_per_mm = rack_m4_nut_thread_extra_removed / 3.2
rack_m4_large_removed_per_mm = rack_m4_large_thread_extra_removed / RACK_KNOB_H
rack_m4_compact_removed_per_mm = rack_m4_compact_thread_extra_removed / RACK_KNOB_H
V['rack_m4_female_thread_witness'] = {
    'minor_diameter_mm': 3.30,
    'groove_major_diameter_mm': 4.40,
    'radial_thread_depth_mm': 0.55,
    'nut_extra_helical_volume_removed_mm3': round(rack_m4_nut_thread_extra_removed, 6),
    'large_knob_extra_helical_volume_removed_mm3': round(rack_m4_large_thread_extra_removed, 6),
    'compact_knob_extra_helical_volume_removed_mm3': round(rack_m4_compact_thread_extra_removed, 6),
    'nut_helical_volume_removed_per_mm': round(rack_m4_nut_removed_per_mm, 6),
    'large_knob_helical_volume_removed_per_mm': round(rack_m4_large_removed_per_mm, 6),
    'compact_knob_helical_volume_removed_per_mm': round(rack_m4_compact_removed_per_mm, 6),
    'minimum_required_helical_volume_removed_per_mm': 0.10,
}

'''
s = s.replace(anchor, proof + anchor, 1)

fail_anchor = "if V['rack_m4_thread_check']['correct_phase_common_mm3'] > 0.02:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack M4 thread hard gates')
fail = '''min_removed_per_mm = V['rack_m4_female_thread_witness']['minimum_required_helical_volume_removed_per_mm']
for part_name, removed_per_mm in [
    ('rack M4 nut', V['rack_m4_female_thread_witness']['nut_helical_volume_removed_per_mm']),
    ('large rack hand knob', V['rack_m4_female_thread_witness']['large_knob_helical_volume_removed_per_mm']),
    ('compact rack hand knob', V['rack_m4_female_thread_witness']['compact_knob_helical_volume_removed_per_mm']),
]:
    if removed_per_mm < min_removed_per_mm:
        failures.append(part_name+' has no meaningful internal M4 helical groove')
'''
s = s.replace(fail_anchor, fail + fail_anchor, 1)

if s == orig:
    raise SystemExit('Rack female-thread correction made no changes')
p.write_text(s, encoding='utf-8')
print('Applied v50 rack M4 female-thread correction: deeper M4 x 0.7 grooves + length-normalised hard checks')
