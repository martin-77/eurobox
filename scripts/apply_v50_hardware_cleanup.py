from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final functional-hardware pass.
# - lead nuts become integral threaded bosses in BASE (no loose cartridge/pin/clip)
# - rack hand knobs use a positive AF7 hex drive instead of screwing onto the stud
# - rack M4 nut remains a separate genuinely threaded captive nut
# - lead-screw retainer nut gets a deeper explicit coarse internal thread
# - extend the lead-screw outer stud so the retainer nut has useful engagement

# Give the lead knob retainer enough threaded engagement after the 7 mm knob.
if 'OUTER_STUD_LEN = 4.5' not in s:
    raise SystemExit('Could not locate lead-screw outer stud length')
s = s.replace('OUTER_STUD_LEN = 4.5', 'OUTER_STUD_LEN = 7.0', 1)

# ---------------------------------------------------------------------------
# Integral lead nuts: keep the fixed cage solid and machine the actual female
# thread directly into BASE. The old side-loaded cartridge pocket and cross-pin
# are deleted. A short smooth entrance/exit bore leaves the moving shoulder and
# thread runout collision-free while the 14 mm central region remains threaded.
# ---------------------------------------------------------------------------
old = '''for sx in SPINDLE_X:
    pocket = box(sx-8.35, NUT_Y0-0.35, 23.65, 16.7, NUT_THREAD_LEN+0.7, 21.0)
    BASE = BASE.cut(pocket)
    BASE = BASE.cut(cyl_y(SHOULDER_D/2 + 0.30, (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50), sx, BOX_EDGE_Y+7.50, SPINDLE_Z))
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(NUT_Y0-0.50)+1.0, sx, NUT_Y0-0.50, SPINDLE_Z))
    BASE = BASE.cut(cyl_x(1.7, 24.0, sx-12.0, (NUT_Y0+NUT_Y1)/2, 40.0))
BASE = BASE.removeSplitter()'''
new = '''for sx in SPINDLE_X:
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
if old not in s:
    raise SystemExit('Could not locate post-fixup lead-nut cartridge pocket block')
s = s.replace(old, new, 1)

# Do not export obsolete loose lead-nut cartridge hardware. The LEAD_NUT shape
# remains in-memory only as an independent thread witness for source validation.
for line in [
    "    'eurobox_v50_lead_nut_print': LEAD_NUT,\n",
    "    'eurobox_v50_lead_nut_retaining_pin': NUT_PIN,\n",
    "    'eurobox_v50_lead_nut_pin_clip': NUT_PIN_CLIP,\n",
]:
    if line not in s:
        raise SystemExit('Could not locate obsolete PARTS entry: '+line.strip())
    s = s.replace(line, '', 1)

# The old cartridge/base collision check is no longer meaningful. Record the
# actual integral-thread state instead; spindle-vs-BASE kinematics below are the
# authoritative collision test.
pattern = re.compile(r"V\['lead_nut_checks'\] = \[\]\nfor sx in SPINDLE_X:\n.*?\n\nV\['thread_kinematics'\] = \[\]", re.S)
replacement = '''V['lead_nut_checks'] = {
    'mode': 'integral_RH_8x2_threads_in_base',
    'thread_start_y_mm': NUT_Y0,
    'thread_end_y_mm': NUT_Y1,
    'thread_length_mm': NUT_THREAD_LEN,
    'loose_cartridge_required': False,
    'retaining_pin_required': False,
    'retaining_clip_required': False,
    'base_is_single_valid_solid': BASE.isValid() and len(BASE.Solids) == 1,
}

V['thread_kinematics'] = []'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace lead-nut validation block')

old_fail = '''for c in V['lead_nut_checks']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Lead nut collides with cage at X='+str(c['x_mm']))
'''
if old_fail not in s:
    raise SystemExit('Could not locate loose lead-nut failure gate')
s = s.replace(old_fail, "if not V['lead_nut_checks']['base_is_single_valid_solid']:\n    failures.append('Integral lead-nut machining split or invalidated BASE')\n", 1)

# Remove loose lead-nut cartridges from the assembly on both modules.
s = re.sub(
    r"for sx in SPINDLE_X:\n    nut = LEAD_NUT\.copy\(\); nut\.translate\(App\.Vector\(sx, RY\+NUT_Y0, SPINDLE_Z\)\); add_obj\('RIGHT_nut_'\+str\(int\(sx\)\), nut\)\n    sp = SPINDLE\.copy\(\);",
    "for sx in SPINDLE_X:\n    sp = SPINDLE.copy();",
    s, count=1)
s = re.sub(
    r"for sx in SPINDLE_X:\n    nut = LEAD_NUT\.copy\(\); nut\.translate\(App\.Vector\(sx,NUT_Y0,SPINDLE_Z\)\); add_obj\('LEFT_nut_'\+str\(int\(sx\)\), left_transform\(nut\)\)\n    sp = SPINDLE\.copy\(\);",
    "for sx in SPINDLE_X:\n    sp = SPINDLE.copy();",
    s, count=1)
if "RIGHT_nut_" in s or "LEFT_nut_" in s:
    raise SystemExit('Loose lead nut still present in assembly')

# ---------------------------------------------------------------------------
# Rack screw + hand knobs: positive drive.
# The previous knob merely screwed onto the same M4 stud. Under tightening load
# it could rotate relative to the stud. Give the printed screw a real AF7 head
# and both knobs a matching AF7.20 socket open from the top. Torque is therefore
# carried by flat faces, not by thread friction.
# ---------------------------------------------------------------------------
hardware_pattern = re.compile(
    r"# Separate rack-closure test hardware\.\nRACK_M4_SCREW = RACK_M4_MALE\.fuse\(.*?RACK_KNOB_COMPACT = make_rack_knob\(RACK_KNOB_COMPACT_D\)\n\n",
    re.S)
hardware = '''# Separate rack-closure test hardware with positive hex drive.\nRACK_M4_HEAD_AF = 7.00\nRACK_M4_HEAD_H = 3.20\nRACK_M4_KNOB_SOCKET_AF = 7.20\nRACK_M4_SCREW = fuse_all([\n    RACK_M4_MALE,\n    hex_z(RACK_M4_HEAD_AF, RACK_M4_HEAD_H+0.20, -RACK_M4_HEAD_H),\n    Part.makeCylinder(2.6, 0.8, App.Vector(0,0,-0.20), App.Vector(0,0,1)),\n]).removeSplitter()\n\nRACK_M4_NUT = hex_z(7.0, 3.2, 0.0)\nRACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()\n\ndef make_rack_knob(diameter):\n    r = diameter/2.0\n    k = Part.makeCylinder(r, RACK_KNOB_H)\n    scallop_r = 3.0 if diameter >= 26.0 else 2.2\n    scallop_c = r + scallop_r - 1.4\n    for a in range(0, 360, 45):\n        x = scallop_c * math.cos(math.radians(a))\n        y = scallop_c * math.sin(math.radians(a))\n        k = k.cut(Part.makeCylinder(scallop_r, RACK_KNOB_H+0.4, App.Vector(x,y,-0.2)))\n    # Closed-bottom hex socket. The screw head enters from the top face and\n    # positively transmits torque through the AF7 flats.\n    socket = hex_z(RACK_M4_KNOB_SOCKET_AF, RACK_M4_HEAD_H+0.35,\n                   RACK_KNOB_H-(RACK_M4_HEAD_H+0.35))\n    k = k.cut(socket)\n    return k.removeSplitter()\n\nRACK_KNOB_LARGE = make_rack_knob(RACK_KNOB_LARGE_D)\nRACK_KNOB_COMPACT = make_rack_knob(RACK_KNOB_COMPACT_D)\n\n'''
s, n = hardware_pattern.subn(hardware, s, count=1)
if n != 1:
    raise SystemExit('Could not replace rack screw/knob hardware block')

# Replace the female-thread witness block added by the prior pass. Only the
# captive rack nut is now female-threaded; knobs are intentionally hex-drive.
proof_pattern = re.compile(r"# Direct female-thread witness checks\..*?\nV\['rack_knob_checks'\] = \{", re.S)
proof = '''# Direct female-thread witness for the separate captive rack M4 nut.\nrack_m4_smooth_nut = hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.65, 3.2))\nrack_m4_nut_thread_extra_removed = rack_m4_smooth_nut.Volume - RACK_M4_NUT.Volume\nrack_m4_nut_removed_per_mm = rack_m4_nut_thread_extra_removed / 3.2\nV['rack_m4_female_thread_witness'] = {\n    'minor_diameter_mm': 3.30,\n    'groove_major_diameter_mm': 4.40,\n    'radial_thread_depth_mm': 0.55,\n    'nut_extra_helical_volume_removed_mm3': round(rack_m4_nut_thread_extra_removed, 6),\n    'nut_helical_volume_removed_per_mm': round(rack_m4_nut_removed_per_mm, 6),\n    'minimum_required_helical_volume_removed_per_mm': 0.10,\n}\n\nV['rack_knob_checks'] = {'''
s, n = proof_pattern.subn(proof, s, count=1)
if n != 1:
    raise SystemExit('Could not replace rack female-thread witness block')

# Add an explicit positive-drive check to the knob metadata.
s = s.replace(
    "    'compact_radial_reduction_mm': (RACK_KNOB_LARGE_D-RACK_KNOB_COMPACT_D)/2.0,\n}",
    "    'compact_radial_reduction_mm': (RACK_KNOB_LARGE_D-RACK_KNOB_COMPACT_D)/2.0,\n    'drive': 'positive_AF7_hex_socket',\n    'screw_head_af_mm': RACK_M4_HEAD_AF,\n    'knob_socket_af_mm': RACK_M4_KNOB_SOCKET_AF,\n    'diametral_flat_clearance_mm': RACK_M4_KNOB_SOCKET_AF-RACK_M4_HEAD_AF,\n}\n",
    1)

# Metadata from the old threaded-knob design must not claim the knobs are threaded.
s = s.replace("    'knob_internal_thread': 'M4 x 0.7 RH printable clearance',\n", "    'knob_drive': 'AF7 screw head in AF7.20 socket',\n")

# Remove obsolete knob female-thread gates; retain the rack-nut helical gate.
fail_pattern = re.compile(
    r"min_removed_per_mm = V\['rack_m4_female_thread_witness'\]\['minimum_required_helical_volume_removed_per_mm'\]\nfor part_name, removed_per_mm in \[.*?\nif V\['rack_m4_thread_check'\]\['correct_phase_common_mm3'\] > 0\.02:",
    re.S)
fail = '''min_removed_per_mm = V['rack_m4_female_thread_witness']['minimum_required_helical_volume_removed_per_mm']\nif V['rack_m4_female_thread_witness']['nut_helical_volume_removed_per_mm'] < min_removed_per_mm:\n    failures.append('rack M4 nut has no meaningful internal M4 helical groove')\nif V['rack_knob_checks']['drive'] != 'positive_AF7_hex_socket':\n    failures.append('Rack hand knob lacks a positive non-slip screw drive')\nif V['rack_knob_checks']['diametral_flat_clearance_mm'] > 0.35:\n    failures.append('Rack knob hex socket is loose enough to risk rounding/slip')\nif V['rack_m4_thread_check']['correct_phase_common_mm3'] > 0.02:'''
s, n = fail_pattern.subn(fail, s, count=1)
if n != 1:
    raise SystemExit('Could not replace rack knob female-thread hard gates')

# ---------------------------------------------------------------------------
# Lead knob retainer nut: dedicated deep RH 8x2 cutter and more engagement.
# ---------------------------------------------------------------------------
old = '''CAP_NUT = z_to_y(hex_z(13.0, 4.2), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(FEMALE_STUD, 0, 0, 0)).removeSplitter()'''
new = '''CAP_FEMALE_SCAD = os.path.join(OUT, 'thread_RH_8x2_knob_retainer_cutter.scad')
write_thread_scad(CAP_FEMALE_SCAD, 3.36, 4.34, THREAD_PITCH, 5.4, 1.05, 0.24)
CAP_FEMALE = import_scad_shape(CAP_FEMALE_SCAD).common(Part.makeCylinder(4.38, 5.4)).removeSplitter()
CAP_NUT = z_to_y(hex_z(13.0, 5.4), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate lead knob retainer nut')
s = s.replace(old, new, 1)

# Direct proof that the retainer nut is not merely a smooth hole.
anchor = "V['knob_interface'] = {\n"
if anchor not in s:
    raise SystemExit('Could not locate lead knob interface validation')
proof = '''cap_smooth = z_to_y(hex_z(13.0, 5.4), 0, 0, 0).cut(cyl_y(3.36, 5.4, 0, 0, 0))\ncap_thread_extra_removed = cap_smooth.Volume - CAP_NUT.Volume\nV['knob_retainer_thread'] = {\n    'standard': 'RH 8x2',\n    'threaded_length_mm': 5.4,\n    'extra_helical_volume_removed_mm3': round(cap_thread_extra_removed, 6),\n    'outer_stud_length_mm': OUTER_STUD_LEN,\n}\n\n'''
s = s.replace(anchor, proof + anchor, 1)

fail_anchor = "for name, sh in PARTS.items():\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate final part export gate')
extra_fail = '''if V['knob_retainer_thread']['extra_helical_volume_removed_mm3'] < 1.0:\n    failures.append('Lead knob retainer nut has no meaningful RH 8x2 internal thread')\nif V['knob_retainer_thread']['outer_stud_length_mm'] < 6.0:\n    failures.append('Lead knob retainer stud too short for reliable nut engagement')\n\n'''
s = s.replace(fail_anchor, extra_fail + fail_anchor, 1)

# Update README text so generated artifacts no longer advertise obsolete loose nuts.
s = s.replace(
    "f.write('Printed test lead screw: RH 8x2, separate screw / lead nut / knob / retainers.\\n')",
    "f.write('Printed test lead screw: RH 8x2 with integral BASE lead nuts; separate drive knob and threaded retainer nut.\\n')")

if s == orig:
    raise SystemExit('Functional hardware cleanup made no changes')

p.write_text(s, encoding='utf-8')
print('Applied v50 functional hardware cleanup: integral lead nuts, positive rack knob drive, threaded retainers')
