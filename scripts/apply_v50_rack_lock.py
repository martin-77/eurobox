from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Rack-lower closure v3.
#
# Keep the mechanically simple positive M4 screw closure, but make all service
# hardware modular and separately printable/testable:
#   - printed M4 x 20 screw/stud (later directly replaceable by metal M4)
#   - separate M4 nut fitting the captive BASE pocket
#   - separate female-threaded hand knob which screws onto the M4 screw
#   - two knob diameters: normal and compact/frame-side
#
# The knob is not fused to the screw. It bottoms against the screw's small end
# flange so the assembled pair behaves as a thumb screw. The nut remains a fully
# separate component and still sits in the side-loaded captive BASE pocket.
if 'RACK_CLOSURE_Y = 11.0' not in s:
    marker = 'PIN_Z = -5.5\n'
    if marker not in s:
        raise SystemExit('Could not locate frozen rack pivot constants')
    s = s.replace(
        marker,
        marker
        + 'RACK_CLOSURE_Y = 11.0\n'
        + 'RACK_CLOSURE_PAD_Z0 = -8.0\n'
        + 'RACK_CLOSURE_PAD_Z1 = -3.5\n'
        + 'RACK_CLOSURE_PAD_X = 18.0\n'
        + 'RACK_M4_SCREW_D = 4.0\n'
        + 'RACK_M4_LOWER_CLEAR_D = 5.0\n'
        + 'RACK_M4_BASE_CLEAR_D = 4.6\n'
        + 'RACK_M4_NUT_AF = 7.4\n'
        + 'RACK_M4_NUT_H = 3.6\n'
        + 'RACK_M4_NUT_Z0 = 3.0\n'
        + 'RACK_M4_SCREW_LENGTH = 20.0\n'
        + 'RACK_M4_PITCH = 0.7\n'
        + 'RACK_KNOB_LARGE_D = 28.0\n'
        + 'RACK_KNOB_COMPACT_D = 20.0\n'
        + 'RACK_KNOB_H = 8.0\n'
        + 'RACK_FRAME_SIDE_X = -90.0\n',
        1,
    )

# Dedicated printable M4 thread masters. These tolerances are intentionally
# looser than metal ISO M4 so a 0.4 mm nozzle PETG test print can assemble after
# normal elephant-foot cleanup. Metal M4 hardware remains the later drop-in.
thread_anchor = "FEMALE_STUD = import_scad_shape(FEMALE_STUD_SCAD).common(Part.makeCylinder(4.28, OUTER_STUD_LEN)).removeSplitter()\n"
if thread_anchor not in s:
    raise SystemExit('Could not locate existing thread master anchor')
thread_insert = '''\n# Rack closure M4 x 0.7 printable test thread.\nRACK_M4_MALE_SCAD = os.path.join(OUT, 'thread_RH_M4x0_7_male.scad')\nRACK_M4_FEMALE_SCAD = os.path.join(OUT, 'thread_RH_M4x0_7_female_cutter.scad')\nwrite_thread_scad(RACK_M4_MALE_SCAD, 1.55, 1.95, RACK_M4_PITCH, RACK_M4_SCREW_LENGTH, 0.28, 0.12)\nwrite_thread_scad(RACK_M4_FEMALE_SCAD, 1.72, 2.18, RACK_M4_PITCH, RACK_KNOB_H+0.8, 0.38, 0.18)\nRACK_M4_MALE = import_scad_shape(RACK_M4_MALE_SCAD).common(Part.makeCylinder(2.00, RACK_M4_SCREW_LENGTH)).removeSplitter()\nRACK_M4_FEMALE = import_scad_shape(RACK_M4_FEMALE_SCAD).common(Part.makeCylinder(2.22, RACK_KNOB_H+0.8)).removeSplitter()\n'''
s = s.replace(thread_anchor, thread_anchor + thread_insert, 1)

# Add the fixed screw guide and nut trap to the final reinforced upper station.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n    return s\.removeSplitter\(\)\n", re.S)
m = pattern.search(s)
if not m:
    raise SystemExit('Could not locate final upper rack station')
upper = m.group(0)
if 'RACK_M4_NUT_AF' not in upper:
    old = '''    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return s.removeSplitter()
'''
    new = '''    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))

    # Vertical M4 screw path, safely forward of the Ø12.42 rack tube.
    screw_bore = Part.makeCylinder(
        RACK_M4_BASE_CLEAR_D/2.0, 9.0,
        App.Vector(xc, RACK_CLOSURE_Y, -1.0), App.Vector(0,0,1))
    s = s.cut(screw_bore)

    # Captive pocket only: the nut itself remains a completely separate part.
    nut_pocket = hex_z(RACK_M4_NUT_AF, RACK_M4_NUT_H, RACK_M4_NUT_Z0)
    nut_pocket.translate(App.Vector(xc, RACK_CLOSURE_Y, 0.0))
    s = s.cut(nut_pocket)
    if xc > 0:
        nut_slot = box(xc+3.45, RACK_CLOSURE_Y-RACK_M4_NUT_AF/2.0,
                       RACK_M4_NUT_Z0, 13.75,
                       RACK_M4_NUT_AF, RACK_M4_NUT_H)
    else:
        nut_slot = box(xc-17.2, RACK_CLOSURE_Y-RACK_M4_NUT_AF/2.0,
                       RACK_M4_NUT_Z0, 13.75,
                       RACK_M4_NUT_AF, RACK_M4_NUT_H)
    s = s.cut(nut_slot)
    return s.removeSplitter()
'''
    if old not in upper:
        raise SystemExit('Could not locate upper station final cuts')
    upper_new = upper.replace(old, new, 1)
    s = s[:m.start()] + upper_new + s[m.end():]

# Moving lower jaw: compact closure ear opposite the hinge.
lower_pattern = re.compile(
    r"lower_shell = box\(-12\.6, -7\.0, -14\.5, 25\.2, 24\.0, 14\.5\)\n"
    r"lower_pivot = cyl_x\(5\.0, 25\.2, -12\.6, PIN_Y, PIN_Z\)\n"
    r"lower_web = box\(-12\.6, PIN_Y, -10\.5, 25\.2, 7\.0, 10\.5\)\n"
    r"LOWER = fuse_all\(\[lower_shell, lower_pivot, lower_web\]\)\n"
    r"LOWER = LOWER\.cut\(cyl_x\(LOWER_SADDLE_R, 27\.2, -13\.6, 0\.0, 0\.0\)\)\n"
    r"LOWER = LOWER\.cut\(cyl_x\(PIN_HOLE_D/2, 27\.2, -13\.6, PIN_Y, PIN_Z\)\)\n"
    r"LOWER = LOWER\.removeSplitter\(\)"
)
lower_new = '''lower_shell = box(-12.6, -7.0, -14.5, 25.2, 14.0, 14.5)
lower_pivot = cyl_x(5.0, 25.2, -12.6, PIN_Y, PIN_Z)
lower_web = box(-12.6, PIN_Y, -10.5, 25.2, 7.0, 10.5)
closure_ear = box(-RACK_CLOSURE_PAD_X/2.0, 5.0, RACK_CLOSURE_PAD_Z0,
                  RACK_CLOSURE_PAD_X, 10.0,
                  RACK_CLOSURE_PAD_Z1-RACK_CLOSURE_PAD_Z0)
LOWER = fuse_all([lower_shell, lower_pivot, lower_web, closure_ear])
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
lower_screw_bore = Part.makeCylinder(
    RACK_M4_LOWER_CLEAR_D/2.0, 7.0,
    App.Vector(0.0, RACK_CLOSURE_Y, RACK_CLOSURE_PAD_Z0-1.0),
    App.Vector(0,0,1))
LOWER = LOWER.cut(lower_screw_bore)
LOWER = LOWER.removeSplitter()'''
s, n = lower_pattern.subn(lower_new, s, count=1)
if n != 1:
    raise SystemExit('Could not locate final rack lower jaw for screw closure')

# Separate printable rack hardware. The screw is a threaded stud with a small
# end flange. Each hand knob has a real M4 female thread and screws onto the
# stud until it seats against that flange. Nut and knob are therefore independent.
parts_anchor = "PARTS = {\n"
if parts_anchor not in s:
    raise SystemExit('Could not locate PARTS anchor')
hardware = '''# Separate rack-closure test hardware.\nRACK_M4_SCREW = RACK_M4_MALE.fuse(\n    Part.makeCylinder(3.1, 1.8, App.Vector(0,0,-1.8), App.Vector(0,0,1))\n).removeSplitter()\n\nRACK_M4_NUT = hex_z(7.0, 3.2, 0.0)\nRACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()\n\ndef make_rack_knob(diameter):\n    r = diameter/2.0\n    k = Part.makeCylinder(r, RACK_KNOB_H)\n    # Eight shallow scallops improve grip without increasing the collision envelope.\n    scallop_r = 3.0 if diameter >= 26.0 else 2.2\n    scallop_c = r + scallop_r - 1.4\n    for a in range(0, 360, 45):\n        x = scallop_c * math.cos(math.radians(a))\n        y = scallop_c * math.sin(math.radians(a))\n        k = k.cut(Part.makeCylinder(scallop_r, RACK_KNOB_H+0.4, App.Vector(x,y,-0.2)))\n    k = k.cut(RACK_M4_FEMALE)\n    return k.removeSplitter()\n\nRACK_KNOB_LARGE = make_rack_knob(RACK_KNOB_LARGE_D)\nRACK_KNOB_COMPACT = make_rack_knob(RACK_KNOB_COMPACT_D)\n\n'''
s = s.replace(parts_anchor, hardware + parts_anchor, 1)

# Export all modular hardware as distinct files.
old = "    'eurobox_v50_rack_pin_clip': PIN_CLIP,\n"
new = "    'eurobox_v50_rack_pin_clip': PIN_CLIP,\n    'eurobox_v50_rack_m4x20_screw_print': RACK_M4_SCREW,\n    'eurobox_v50_rack_m4_nut_print': RACK_M4_NUT,\n    'eurobox_v50_rack_hand_knob_large_m4': RACK_KNOB_LARGE,\n    'eurobox_v50_rack_hand_knob_compact_m4': RACK_KNOB_COMPACT,\n"
if old not in s:
    raise SystemExit('Could not add rack hardware to PARTS')
s = s.replace(old, new, 1)

# Mechanism and knob-envelope validation.
anchor = "V['rack_pin_checks'] = []\n"
if anchor not in s:
    raise SystemExit('Could not locate rack validation anchor')
insert = '''closure_arm_mm = RACK_CLOSURE_Y - PIN_Y
tube_arm_mm = 0.0 - PIN_Y
closure_nominal_gap_mm = 0.0 - RACK_CLOSURE_PAD_Z1
closure_mapped_tube_adjustment_mm = closure_nominal_gap_mm * tube_arm_mm / closure_arm_mm
closure_tube_edge_clearance_mm = RACK_CLOSURE_Y - RACK_D/2.0 - RACK_M4_BASE_CLEAR_D/2.0
V['rack_closure'] = {
    'mode': 'positive_M4_screw_into_separate_captive_nut',
    'screw_part': 'eurobox_v50_rack_m4x20_screw_print',
    'nut_part': 'eurobox_v50_rack_m4_nut_print',
    'large_knob_part': 'eurobox_v50_rack_hand_knob_large_m4',
    'compact_frame_knob_part': 'eurobox_v50_rack_hand_knob_compact_m4',
    'metal_drop_in_later': 'standard M4 hardware',
    'tool_less_with_knob': True,
    'screw_and_nut_separate': True,
    'knob_and_screw_separate': True,
    'knob_internal_thread': 'M4 x 0.7 RH printable clearance',
    'frame_side_assumed_clamp_x_mm': RACK_FRAME_SIDE_X,
    'large_knob_diameter_mm': RACK_KNOB_LARGE_D,
    'compact_knob_diameter_mm': RACK_KNOB_COMPACT_D,
    'knob_height_mm': RACK_KNOB_H,
    'hinge_y_mm': PIN_Y,
    'hinge_z_mm': PIN_Z,
    'closure_y_mm': RACK_CLOSURE_Y,
    'lower_clearance_hole_d_mm': RACK_M4_LOWER_CLEAR_D,
    'base_clearance_hole_d_mm': RACK_M4_BASE_CLEAR_D,
    'nut_pocket_af_mm': RACK_M4_NUT_AF,
    'nut_pocket_height_mm': RACK_M4_NUT_H,
    'nominal_lower_to_base_gap_mm': round(closure_nominal_gap_mm, 6),
    'mapped_tube_adjustment_mm': round(closure_mapped_tube_adjustment_mm, 6),
    'required_measured_tube_range_mm': 0.41,
    'screw_to_tube_edge_clearance_mm': round(closure_tube_edge_clearance_mm, 6),
}
V['rack_closure_checks'] = []
for deg in [0, -15, -30, -45, -60, -75]:
    lo = LOWER.copy()
    lo.rotate(App.Vector(0,PIN_Y,PIN_Z), App.Vector(1,0,0), deg)
    lo.translate(App.Vector(CLAMP_X[0],0,0))
    V['rack_closure_checks'].append({
        'rotation_deg': deg,
        'base_common_mm3': round(BASE.common(lo).Volume, 6),
    })
V['rack_knob_checks'] = {
    'large_diameter_mm': RACK_KNOB_LARGE_D,
    'compact_diameter_mm': RACK_KNOB_COMPACT_D,
    'compact_is_smaller': RACK_KNOB_COMPACT_D < RACK_KNOB_LARGE_D,
    'diameter_reduction_mm': RACK_KNOB_LARGE_D-RACK_KNOB_COMPACT_D,
    'compact_radial_reduction_mm': (RACK_KNOB_LARGE_D-RACK_KNOB_COMPACT_D)/2.0,
}

'''
s = s.replace(anchor, insert + anchor, 1)

fail_anchor = "for c in V['rack_pin_checks']:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack-pin failure checks')
fail_insert = '''if V['rack_closure']['mapped_tube_adjustment_mm'] < 0.41:
    failures.append('Rack screw closure cannot compensate full measured 12.00..12.41 mm tube range')
if V['rack_closure']['screw_to_tube_edge_clearance_mm'] < 1.0:
    failures.append('Rack M4 closure axis too close to maximum tube envelope')
if not V['rack_knob_checks']['compact_is_smaller']:
    failures.append('Frame-side rack knob is not smaller than normal rack knob')
if V['rack_knob_checks']['compact_radial_reduction_mm'] < 3.5:
    failures.append('Frame-side rack knob does not reduce radial collision envelope enough')
for c in V['rack_closure_checks']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Rack screw-closure lower collides with fixed base at rotation='+str(c['rotation_deg']))
'''
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

# Put the modular closure hardware into the assembly so future collision checks
# can see it. Current coordinate convention treats x=-90 as frame-near/front.
right_anchor = "for xc in CLAMP_X:\n    lo = LOWER.copy(); lo.translate(App.Vector(xc, RY, 0)); add_obj('RIGHT_lower_'+str(int(xc)), lo)\n"
if right_anchor in s:
    right_extra = '''for xc in CLAMP_X:
    rs = RACK_M4_SCREW.copy(); rs.translate(App.Vector(xc, RY+RACK_CLOSURE_Y, RACK_CLOSURE_PAD_Z0-1.8)); add_obj('RIGHT_rack_screw_'+str(int(xc)), rs)
    rn = RACK_M4_NUT.copy(); rn.translate(App.Vector(xc, RY+RACK_CLOSURE_Y, RACK_M4_NUT_Z0)); add_obj('RIGHT_rack_nut_'+str(int(xc)), rn)
    rk = (RACK_KNOB_COMPACT if xc == RACK_FRAME_SIDE_X else RACK_KNOB_LARGE).copy()
    rk.translate(App.Vector(xc, RY+RACK_CLOSURE_Y, RACK_CLOSURE_PAD_Z0-RACK_KNOB_H-1.8)); add_obj('RIGHT_rack_knob_'+str(int(xc)), rk)
'''
    s = s.replace(right_anchor, right_anchor + right_extra, 1)

left_anchor = "for xc in CLAMP_X:\n    lo = LOWER.copy(); lo.translate(App.Vector(xc,0,0)); add_obj('LEFT_lower_'+str(int(xc)), left_transform(lo))\n"
if left_anchor in s:
    left_extra = '''for xc in CLAMP_X:
    rs = RACK_M4_SCREW.copy(); rs.translate(App.Vector(xc,RACK_CLOSURE_Y,RACK_CLOSURE_PAD_Z0-1.8)); add_obj('LEFT_rack_screw_'+str(int(xc)), left_transform(rs))
    rn = RACK_M4_NUT.copy(); rn.translate(App.Vector(xc,RACK_CLOSURE_Y,RACK_M4_NUT_Z0)); add_obj('LEFT_rack_nut_'+str(int(xc)), left_transform(rn))
    rk = (RACK_KNOB_COMPACT if xc == RACK_FRAME_SIDE_X else RACK_KNOB_LARGE).copy()
    rk.translate(App.Vector(xc,RACK_CLOSURE_Y,RACK_CLOSURE_PAD_Z0-RACK_KNOB_H-1.8)); add_obj('LEFT_rack_knob_'+str(int(xc)), left_transform(rk))
'''
    s = s.replace(left_anchor, left_anchor + left_extra, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack closure: separate M4 screw/nut + large/compact threaded hand knobs')
