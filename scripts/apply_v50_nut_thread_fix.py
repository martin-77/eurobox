from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final nut/thread correction.
# User requirement:
# - BASE must NOT contain the 8x2 working thread.
# - Working 8x2 threads live in separate printable lead-nut cartridges.
# - All printable nuts need a clearly developed, load-carrying helical profile.

# ---------------------------------------------------------------------------
# 1) Stronger printable RH 8x2 female profile for separate lead nuts.
# Male remains Ø8 major / Ø6.50 core. Female minor Ø6.76 gives 0.13 mm radial
# root clearance to the printed male core; groove major Ø8.60 gives 0.30 mm
# radial crest clearance to the Ø8.00 male. The wider root produces a visibly
# and mechanically meaningful trapezoidal thread with a 0.4 mm nozzle.
# ---------------------------------------------------------------------------
s = s.replace('THREAD_FEMALE_CORE_R = 3.42', 'THREAD_FEMALE_CORE_R = 3.38', 1)
s = s.replace('THREAD_FEMALE_MAJOR_R = 4.22', 'THREAD_FEMALE_MAJOR_R = 4.30', 1)
s = s.replace(
    'write_thread_scad(FEMALE_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, NUT_THREAD_LEN, 0.76, 0.40)',
    'write_thread_scad(FEMALE_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, NUT_THREAD_LEN, 1.10, 0.28)',
    1)
s = s.replace(
    'write_thread_scad(FEMALE_STUD_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, OUTER_STUD_LEN, 0.76, 0.40)',
    'write_thread_scad(FEMALE_STUD_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, OUTER_STUD_LEN, 1.10, 0.28)',
    1)

# Hardware-cleanup created a dedicated retainer cutter; keep that nut on the
# same robust printable 8x2 profile.
s = s.replace(
    'write_thread_scad(CAP_FEMALE_SCAD, 3.36, 4.34, THREAD_PITCH, 5.4, 1.05, 0.24)',
    'write_thread_scad(CAP_FEMALE_SCAD, 3.38, 4.30, THREAD_PITCH, 5.4, 1.10, 0.28)',
    1)
s = s.replace('Part.makeCylinder(4.38, 5.4)', 'Part.makeCylinder(4.34, 5.4)', 1)

# ---------------------------------------------------------------------------
# 2) BASE: remove integral working thread. Restore a smooth through path and
# side-loaded lead-nut cartridge pocket. The separate nut/pin/clip are again the
# serviceable hardware. No thread cutter touches BASE.
# ---------------------------------------------------------------------------
integral = '''for sx in SPINDLE_X:
    # Moving shoulder clearance from the plate side up to the thread entrance.
    BASE = BASE.cut(cyl_y(
        SHOULDER_D/2 + 0.30,
        (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50),
        sx, BOX_EDGE_Y+7.50, SPINDLE_Z))
    # 0.5 mm smooth lead-in before the integral nut thread.
    BASE = BASE.cut(cyl_y(4.45, 0.50, sx, NUT_Y0-0.50, SPINDLE_Z))
    # Actual RH 8x2 internal thread is cut directly into the fixed cage.
    BASE = BASE.cut(z_to_y(FEMALE, sx, NUT_Y0, SPINDLE_Z))
    # Smooth thread runout to the outside of the cage.
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-NUT_Y1+1.0, sx, NUT_Y1, SPINDLE_Z))
BASE = BASE.removeSplitter()'''
separate = '''for sx in SPINDLE_X:
    # Side-loaded cartridge pocket. BASE itself remains completely unthreaded.
    pocket = box(sx-8.35, NUT_Y0-0.35, 23.65, 16.7, NUT_THREAD_LEN+0.7, 21.0)
    BASE = BASE.cut(pocket)
    # Smooth spindle path through the cage; all working thread is in LEAD_NUT.
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(BOX_EDGE_Y+8.0)+1.0,
                          sx, BOX_EDGE_Y+8.0, SPINDLE_Z))
    # Retaining-pin bore for the removable nut cartridge.
    BASE = BASE.cut(cyl_x(1.7, 24.0, sx-12.0,
                          (NUT_Y0+NUT_Y1)/2, 40.0))
BASE = BASE.removeSplitter()'''
if integral not in s:
    raise SystemExit('Could not locate integral BASE lead-thread block')
s = s.replace(integral, separate, 1)

# Restore separate lead-nut hardware exports deleted by hardware_cleanup.
parts_anchor = "    'eurobox_v50_clamp_plate': PLATE,\n"
if parts_anchor not in s:
    raise SystemExit('Could not locate PARTS clamp-plate anchor')
if "'eurobox_v50_lead_nut_print': LEAD_NUT" not in s:
    s = s.replace(parts_anchor, parts_anchor
        + "    'eurobox_v50_lead_nut_print': LEAD_NUT,\n"
        + "    'eurobox_v50_lead_nut_retaining_pin': NUT_PIN,\n"
        + "    'eurobox_v50_lead_nut_pin_clip': NUT_PIN_CLIP,\n", 1)

# Restore separate nut geometry in both sides of the assembly.
s = re.sub(
    r"for sx in SPINDLE_X:\n    sp = SPINDLE\.copy\(\); sp\.translate\(App\.Vector\(sx, RY\+BOX_EDGE_Y, SPINDLE_Z\)\);",
    "for sx in SPINDLE_X:\n    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx, RY+NUT_Y0, SPINDLE_Z)); add_obj('RIGHT_nut_'+str(int(sx)), nut)\n    sp = SPINDLE.copy(); sp.translate(App.Vector(sx, RY+BOX_EDGE_Y, SPINDLE_Z));",
    s, count=1)
s = re.sub(
    r"for sx in SPINDLE_X:\n    sp = SPINDLE\.copy\(\); sp\.translate\(App\.Vector\(sx,BOX_EDGE_Y,SPINDLE_Z\)\);",
    "for sx in SPINDLE_X:\n    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z)); add_obj('LEFT_nut_'+str(int(sx)), left_transform(nut))\n    sp = SPINDLE.copy(); sp.translate(App.Vector(sx,BOX_EDGE_Y,SPINDLE_Z));",
    s, count=1)

# Replace integral-thread metadata with checks for the actual removable nuts.
meta_pattern = re.compile(
    r"V\['lead_nut_checks'\] = \{\n    'mode': 'integral_RH_8x2_threads_in_base',.*?\n\}\n\nV\['thread_kinematics'\] = \[\]",
    re.S)
meta = '''V['lead_nut_checks'] = []
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx, NUT_Y0, SPINDLE_Z))
    V['lead_nut_checks'].append({
        'x_mm': sx,
        'base_common_mm3': round(BASE.common(nut).Volume, 6),
        'distance_to_base_mm': round(BASE.distToShape(nut)[0], 6),
    })
V['lead_nut_mode'] = 'separate_RH_8x2_printed_cartridge'

V['thread_kinematics'] = []'''
s, n = meta_pattern.subn(meta, s, count=1)
if n != 1:
    raise SystemExit('Could not restore separate lead-nut validation metadata')

# Restore failure gate for removable nut/base fit.
s = s.replace(
    "if not V['lead_nut_checks']['base_is_single_valid_solid']:\n    failures.append('Integral lead-nut machining split or invalidated BASE')\n",
    "for c in V['lead_nut_checks']:\n    if c['base_common_mm3'] > 1e-4:\n        failures.append('Lead nut collides with cage at X='+str(c['x_mm']))\n",
    1)

# ---------------------------------------------------------------------------
# 3) Explicit witness for the 8x2 nut itself. Compare the actual LEAD_NUT to
# the identical cartridge with only a smooth Ø6.76 bore. The extra removal must
# be substantial, otherwise the 'thread' is visually/functionally near-smooth.
# ---------------------------------------------------------------------------
anchor = "V['thread_kinematics'] = []\n"
if anchor not in s:
    raise SystemExit('Could not locate thread kinematics anchor')
proof = '''lead_nut_smooth = box(-8.0, 0.0, -7.0, 16.0, NUT_THREAD_LEN, 14.0)
lead_nut_smooth = lead_nut_smooth.fuse(box(-6.0, 3.0, 7.0, 12.0, 8.0, 4.0))
lead_nut_smooth = lead_nut_smooth.cut(cyl_y(THREAD_FEMALE_CORE_R, NUT_THREAD_LEN, 0, 0, 0)).removeSplitter()
lead_nut_extra_helical_removed = lead_nut_smooth.Volume - LEAD_NUT.Volume
V['lead_nut_thread_witness'] = {
    'standard': 'RH 8x2 printable',
    'female_minor_diameter_mm': round(2*THREAD_FEMALE_CORE_R, 3),
    'female_groove_major_diameter_mm': round(2*THREAD_FEMALE_MAJOR_R, 3),
    'radial_groove_depth_mm': round(THREAD_FEMALE_MAJOR_R-THREAD_FEMALE_CORE_R, 3),
    'thread_length_mm': NUT_THREAD_LEN,
    'extra_helical_volume_removed_mm3': round(lead_nut_extra_helical_removed, 6),
    'extra_helical_volume_removed_per_mm': round(lead_nut_extra_helical_removed/NUT_THREAD_LEN, 6),
}

'''
s = s.replace(anchor, proof + anchor, 1)

# Strengthen M4 female profile too: Ø3.20 minor / Ø4.50 groove major. Printed
# male core is Ø3.10, so 0.05 mm radial root clearance remains; crest clearance
# to nominal metal M4 is 0.25 mm radial. This is intentionally FDM-friendly.
s = s.replace(
    'write_thread_scad(RACK_M4_FEMALE_SCAD, 1.65, 2.20, RACK_M4_PITCH,\n                  RACK_M4_FEMALE_LEN, 0.62, 0.10)',
    'write_thread_scad(RACK_M4_FEMALE_SCAD, 1.60, 2.25, RACK_M4_PITCH,\n                  RACK_M4_FEMALE_LEN, 0.66, 0.14)',
    1)
s = s.replace('Part.makeCylinder(2.24, RACK_M4_FEMALE_LEN)',
              'Part.makeCylinder(2.29, RACK_M4_FEMALE_LEN)', 1)

# Keep witness numbers aligned with the stronger M4 cutter.
s = s.replace("'minor_diameter_mm': 3.30,", "'minor_diameter_mm': 3.20,", 1)
s = s.replace("'groove_major_diameter_mm': 4.40,", "'groove_major_diameter_mm': 4.50,", 1)
s = s.replace("'radial_thread_depth_mm': 0.55,", "'radial_thread_depth_mm': 0.65,", 1)
s = s.replace("hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.65, 3.2))",
              "hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.60, 3.2))", 1)

# Hard gates: meaningful 8x2 helix and no integral BASE-thread mode allowed.
fail_anchor = "for name, sh in PARTS.items():\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate final export failure gate')
extra_fail = '''if V.get('lead_nut_mode') != 'separate_RH_8x2_printed_cartridge':
    failures.append('BASE incorrectly owns the lead-screw working thread')
if V['lead_nut_thread_witness']['radial_groove_depth_mm'] < 0.85:
    failures.append('Lead nut 8x2 groove is too shallow for printable functional thread')
if V['lead_nut_thread_witness']['extra_helical_volume_removed_per_mm'] < 0.5:
    failures.append('Lead nut 8x2 helix is not geometrically pronounced enough')

'''
s = s.replace(fail_anchor, extra_fail + fail_anchor, 1)

# Generated documentation must describe the actual hardware.
s = s.replace(
    "f.write('Printed test lead screw: RH 8x2 with integral BASE lead nuts; separate drive knob and threaded retainer nut.\\n')",
    "f.write('Printed test lead screw: RH 8x2 with separate replaceable lead-nut cartridges; BASE has only smooth guide/pocket geometry.\\n')",
    1)

if s == orig:
    raise SystemExit('Nut/thread correction made no changes')
if "BASE = BASE.cut(z_to_y(FEMALE, sx, NUT_Y0, SPINDLE_Z))" in s:
    raise SystemExit('Integral BASE working thread still present after correction')
if "'eurobox_v50_lead_nut_print': LEAD_NUT" not in s:
    raise SystemExit('Separate lead nut was not restored to PARTS')

p.write_text(s, encoding='utf-8')
print('Applied v50 nut/thread fix: unthreaded BASE + separate deep-profile 8x2/M4 nuts')
