from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final all-thread source audit.  v54 supplies the true radial/AXIAL RH8x2
# generator.  This pass makes every female cutter overrun both faces, preserves
# the already-correct radial/axial M4 pair, and records geometry witnesses.

# RH8x2 removable lead nut: use the true female helper with one-pitch overrun.
old_female = '''FEMALE = import_scad_shape(FEMALE_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + LEAD_RADIAL_CLEARANCE + 0.06,
                      NUT_THREAD_LEN)).removeSplitter()'''
new_female = '''LEAD_FEMALE_OVERRUN = THREAD_PITCH
lead_female_core = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
lead_female_major = THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE
lead_female_root_w = LEAD_PROFILE_ROOT_W + 2.0*LEAD_FLANK_CLEARANCE
lead_female_crest_w = LEAD_PROFILE_CREST_W + 2.0*LEAD_FLANK_CLEARANCE
lead_female_span = NUT_THREAD_LEN + 2.0*LEAD_FEMALE_OVERRUN
LEAD_FEMALE_OPEN_SCAD = os.path.join(
    OUT, 'thread_RH_8x2_female_open_overrun.scad')
write_female_thread_cutter_scad(
    LEAD_FEMALE_OPEN_SCAD,
    lead_female_core, lead_female_major, THREAD_PITCH, NUT_THREAD_LEN,
    lead_female_root_w, lead_female_crest_w, LEAD_FEMALE_OVERRUN)
FEMALE = import_scad_shape(LEAD_FEMALE_OPEN_SCAD).common(
    Part.makeCylinder(
        lead_female_major + 0.06,
        lead_female_span,
        App.Vector(0,0,-LEAD_FEMALE_OVERRUN))).removeSplitter()'''
if old_female not in s:
    raise SystemExit('Could not locate final RH8x2 removable-nut female cutter')
s = s.replace(old_female, new_female, 1)

# RH8x2 knob-retainer: replace the previous twisted-ribbon extended cutter with
# the same true radial/axial female helper used by the lead nut.
cap_pattern = re.compile(
    r"CAP_FEMALE_EXT_SCAD = os\.path\.join\(\n"
    r"    OUT, 'thread_RH_8x2_knob_retainer_extended_cutter\.scad'\)\n"
    r"cap_txt = f\"\"\".*?\n"
    r"CAP_FEMALE = import_scad_shape\(CAP_FEMALE_EXT_SCAD\)\n",
    re.S,
)
cap_replacement = '''CAP_FEMALE_EXT_SCAD = os.path.join(
    OUT, 'thread_RH_8x2_knob_retainer_extended_cutter.scad')
write_female_thread_cutter_scad(
    CAP_FEMALE_EXT_SCAD,
    cap_female_core, cap_female_major, THREAD_PITCH, CAP_NUT_H,
    cap_root_w, cap_crest_w, CAP_THREAD_OVERRUN)
CAP_FEMALE = import_scad_shape(CAP_FEMALE_EXT_SCAD).common(
    Part.makeCylinder(
        cap_female_major + 0.06,
        cap_span,
        App.Vector(0,0,-CAP_THREAD_OVERRUN))).removeSplitter()
'''
s, n = cap_pattern.subn(cap_replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace obsolete knob-retainer twisted-ribbon cutter')

# M4 true radial/axial pair: ensure its ridge/groove overruns both ends.
m4_end_hits = s.count('a1=360*(turns-1);')
if m4_end_hits != 2:
    raise SystemExit('Expected exactly two final radial-Z M4 generators, found '+str(m4_end_hits))
s = s.replace('a1=360*(turns-1);', 'a1=360*(turns+1);')

old_m4_core = '''  cylinder(r=bore_r,h=length,$fn=96);'''
new_m4_core = '''  translate([0,0,-pitch]) cylinder(r=bore_r,h=length+2*pitch,$fn=96);'''
if old_m4_core not in s:
    raise SystemExit('Could not locate true M4 female smooth core')
s = s.replace(old_m4_core, new_m4_core, 1)

old_m4_import = '''RACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(
    Part.makeCylinder(2.24, RACK_M4_FEMALE_LEN)).removeSplitter()
# Start one pitch below the part so the helical groove is fully developed at
# the lower entrance and continues beyond the upper face.
RACK_M4_FEMALE.translate(App.Vector(0,0,-RACK_M4_PITCH))'''
new_m4_import = '''RACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(
    Part.makeCylinder(
        2.24,
        RACK_M4_FEMALE_LEN + 2.0*RACK_M4_PITCH,
        App.Vector(0,0,-RACK_M4_PITCH))).removeSplitter()'''
if old_m4_import not in s:
    raise SystemExit('Could not locate final M4 female import/shift block')
s = s.replace(old_m4_import, new_m4_import, 1)

anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')

audit = r'''# Authoritative source geometry audit for every printable thread.
def _z_annulus(r0, r1, z0, h):
    return Part.makeCylinder(r1, h, App.Vector(0,0,z0)).cut(
        Part.makeCylinder(r0, h, App.Vector(0,0,z0))).removeSplitter()

def _y_annulus(r0, r1, y0, h):
    return cyl_y(r1, h, 0, y0, 0).cut(
        cyl_y(r0, h, 0, y0, 0)).removeSplitter()

def _male_end_ridge_volume(shape, core_r, major_r, pitch, length, at_end):
    seg_h = min(0.70*pitch, length/3.0)
    z0 = max(0.0, length-seg_h) if at_end else 0.0
    shell = _z_annulus(core_r+0.06, major_r+0.03, z0, seg_h)
    return shape.common(shell).Volume

_lead_bore_r = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
_lead_probe = cyl_y(_lead_bore_r-0.03, NUT_THREAD_LEN+2.0, 0, -1.0, 0)
_lead_core_block = LEAD_NUT.common(_lead_probe).Volume
_lead_body = box(-8.0, 0.0, -7.0, 16.0, NUT_THREAD_LEN, 14.0)
_lead_body = _lead_body.fuse(
    box(-6.0, 3.0, 7.0, 12.0, 8.0, LEAD_NUT_TAB_H)).removeSplitter()
_lead_body = _lead_body.cut(cyl_x(
    LEAD_NUT_PIN_HOLE_D/2.0, 20.0, -10.0,
    LEAD_NUT_PIN_Y, LEAD_NUT_PIN_Z)).removeSplitter()
_lead_smooth = _lead_body.cut(
    cyl_y(_lead_bore_r, NUT_THREAD_LEN+2.0, 0, -1.0, 0)).removeSplitter()
_lead_shell = _y_annulus(
    _lead_bore_r-0.02, _lead_bore_r+0.16, 0.5, NUT_THREAD_LEN-1.0)
_lead_groove_open = (
    _lead_smooth.common(_lead_shell).Volume
    - LEAD_NUT.common(_lead_shell).Volume)

_cap_bore_r = cap_female_core
_cap_probe = cyl_y(_cap_bore_r-0.03, CAP_NUT_H+2.0, 0, -1.0, 0)
_cap_core_block = CAP_NUT.common(_cap_probe).Volume
_cap_body = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
_cap_smooth = _cap_body.cut(
    cyl_y(_cap_bore_r, CAP_NUT_H+2.0, 0, -1.0, 0)).removeSplitter()
_cap_shell = _y_annulus(
    _cap_bore_r-0.02, _cap_bore_r+0.16, 0.35, CAP_NUT_H-0.70)
_cap_groove_open = (
    _cap_smooth.common(_cap_shell).Volume
    - CAP_NUT.common(_cap_shell).Volume)

_m4_bore_r = 1.66
_m4_probe = Part.makeCylinder(1.63, 6.6, App.Vector(0,0,-0.5))
_m4_core_block = RACK_M4_NUT.common(_m4_probe).Volume
_m4_smooth = hex_z(7.0, 5.6, 0.0).cut(
    Part.makeCylinder(_m4_bore_r, 5.6)).removeSplitter()
_m4_shell = _z_annulus(_m4_bore_r-0.02, _m4_bore_r+0.12, 0.30, 5.0)
_m4_groove_open = (
    _m4_smooth.common(_m4_shell).Volume
    - RACK_M4_NUT.common(_m4_shell).Volume)

_lead_main_start = _male_end_ridge_volume(
    MALE, THREAD_CORE_R, THREAD_MAJOR/2.0, THREAD_PITCH, LEAD_THREAD_LEN, False)
_lead_main_end = _male_end_ridge_volume(
    MALE, THREAD_CORE_R, THREAD_MAJOR/2.0, THREAD_PITCH, LEAD_THREAD_LEN, True)
_lead_stud_start = _male_end_ridge_volume(
    MALE_STUD, THREAD_CORE_R, THREAD_MAJOR/2.0, THREAD_PITCH, OUTER_STUD_LEN, False)
_lead_stud_end = _male_end_ridge_volume(
    MALE_STUD, THREAD_CORE_R, THREAD_MAJOR/2.0, THREAD_PITCH, OUTER_STUD_LEN, True)
_m4_male_start = _male_end_ridge_volume(
    RACK_M4_MALE, 1.55, 1.95, RACK_M4_PITCH, RACK_M4_SCREW_LENGTH, False)
_m4_male_end = _male_end_ridge_volume(
    RACK_M4_MALE, 1.55, 1.95, RACK_M4_PITCH, RACK_M4_SCREW_LENGTH, True)

V['thread_surface_audit'] = {
    'rh8x2_profile_generator': LEAD_THREAD_PROFILE_GENERATOR,
    'rh8x2_male_root_axial_width_mm': LEAD_PROFILE_ROOT_W,
    'rh8x2_male_crest_axial_width_mm': LEAD_PROFILE_CREST_W,
    'rh8x2_female_root_axial_width_mm': lead_female_root_w,
    'rh8x2_female_crest_axial_width_mm': lead_female_crest_w,
    'rh8x2_lead_nut_core_block_mm3': round(_lead_core_block, 6),
    'rh8x2_lead_nut_bore_connected_groove_mm3': round(_lead_groove_open, 6),
    'rh8x2_retainer_core_block_mm3': round(_cap_core_block, 6),
    'rh8x2_retainer_bore_connected_groove_mm3': round(_cap_groove_open, 6),
    'm4_nut_core_block_mm3': round(_m4_core_block, 6),
    'm4_nut_bore_connected_groove_mm3': round(_m4_groove_open, 6),
    'rh8x2_main_male_start_ridge_mm3': round(_lead_main_start, 6),
    'rh8x2_main_male_end_ridge_mm3': round(_lead_main_end, 6),
    'rh8x2_stud_start_ridge_mm3': round(_lead_stud_start, 6),
    'rh8x2_stud_end_ridge_mm3': round(_lead_stud_end, 6),
    'm4_male_start_ridge_mm3': round(_m4_male_start, 6),
    'm4_male_end_ridge_mm3': round(_m4_male_end, 6),
    'female_cutter_overrun': 'one full pitch beyond both faces',
}

if LEAD_THREAD_PROFILE_GENERATOR != 'true_radial_axial_trapezoid_polyhedron_v54':
    failures.append('RH8x2 source still uses obsolete tangential/twisted-ribbon thread generator')
if _lead_core_block > 1e-4:
    failures.append('RH8x2 lead nut has a wall blocking its through bore')
if _lead_groove_open < 0.05:
    failures.append('RH8x2 lead-nut helix is hidden behind a smooth bore wall')
if _cap_core_block > 1e-4:
    failures.append('RH8x2 knob-retainer nut has a wall blocking its through bore')
if _cap_groove_open < 0.05:
    failures.append('RH8x2 knob-retainer helix is hidden behind a smooth bore wall')
if _m4_core_block > 1e-4:
    failures.append('Rack M4 captive nut has a wall blocking its through bore')
if _m4_groove_open < 0.01:
    failures.append('Rack M4 captive-nut helix is hidden behind a smooth bore wall')
for _label, _v in [
    ('RH8x2 main screw start', _lead_main_start),
    ('RH8x2 main screw end', _lead_main_end),
    ('RH8x2 retainer stud start', _lead_stud_start),
    ('RH8x2 retainer stud end', _lead_stud_end),
    ('M4 rack screw start', _m4_male_start),
    ('M4 rack screw end', _m4_male_end),
]:
    if _v < 0.01:
        failures.append(_label+' has no developed external thread ridge')

'''
s = s.replace(anchor, audit + anchor, 1)

if s == orig:
    raise SystemExit('Final all-thread audit pass made no changes')
if 'thread_surface_audit' not in s:
    raise SystemExit('Final thread-surface audit was not installed')

p.write_text(s, encoding='utf-8')
print('Applied final thread audit: true RH8x2 axial profiles + open female cutters + M4 end overrun')
