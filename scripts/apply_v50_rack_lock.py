from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Tool-less adjustable rack closure. The original hinge pin remains only as the
# lower-jaw pivot. Closure opposite the hinge is now a printed eccentric cam
# lever rather than a second removable lock pin.
#
# The real rack tube is not perfectly round: measured diameter spans 12.00 to
# 12.41 mm. Because the fixed upper and moving lower jaw must accommodate the
# full diameter change, the mechanism is designed for >=0.41 mm closure change
# at the tube, not a nominal midpoint.
if 'CAM_Y = 11.0' not in s:
    s = s.replace(
        'PIN_Z = -5.5\n',
        'PIN_Z = -5.5\n'
        'CAM_Y = 11.0\n'
        'CAM_Z = -7.0\n'
        'CAM_R = 5.0\n'
        'CAM_E = 0.85\n'
        'CAM_MIN_DEG = -30.0\n'
        'CAM_MAX_DEG = 30.0\n'
        'CAM_SHAFT_D = 4.0\n'
        'CAM_HOLE_D = 4.6\n',
        1,
    )

# Fixed cam-axis lugs opposite the hinge. They sit outside the 25.2 mm lower
# jaw exactly like the hinge clevis, so the moving jaw remains central in X.
old = '''    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n\n    s = fuse_all([bridge, root_beam,\n                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])\n    # The real rack-tube envelope is cut only after all root solids are fused.\n    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))\n    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))\n    return s.removeSplitter()'''
new = '''    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n\n    # Cam bearings opposite the hinge. The cam shaft is parallel to the rack\n    # tube and hinge pin (X axis), which keeps the whole closure a 2-D Y/Z\n    # mechanism and gives the lever a collision-safe sweep below the arm.\n    cam_l = cyl_x(6.0, 4.0, xc-17.0, CAM_Y, CAM_Z)\n    cam_r = cyl_x(6.0, 4.0, xc+13.0, CAM_Y, CAM_Z)\n    cam_web_l = box(xc-17.0, 6.0, CAM_Z, 4.0, 8.0, 7.0)\n    cam_web_r = box(xc+13.0, 6.0, CAM_Z, 4.0, 8.0, 7.0)\n\n    s = fuse_all([bridge, root_beam,\n                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r,\n                  cam_l, cam_r, cam_web_l, cam_web_r])\n    # Tube and both rotating-axis holes are cut after fusion.\n    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))\n    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))\n    s = s.cut(cyl_x(CAM_HOLE_D/2, 40.0, xc-20.0, CAM_Y, CAM_Z))\n    return s.removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final upper rack station for cam fixup')
s = s.replace(old, new, 1)

# U-shaped follower pocket in the moving lower jaw. It is open downward so the
# jaw can swing away from the fixed cam axis. The flat pocket ceiling is the
# follower surface. At CAM_MIN_DEG the eccentric drum is tangent to that ceiling;
# rotating toward CAM_MAX_DEG raises the front of the lower jaw.
cam_min_top = CAM_R + CAM_E * __import__('math').sin(__import__('math').radians(CAM_MIN_DEG)) if False else None
old = '''LOWER = fuse_all([lower_shell, lower_pivot, lower_web])\nLOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))\nLOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))\nLOWER = LOWER.removeSplitter()'''
new = '''LOWER = fuse_all([lower_shell, lower_pivot, lower_web])\nLOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))\nLOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))\n# Cam pocket: 12.5 mm Y width gives the eccentric drum side clearance through\n# its full +/-30 deg sweep; ceiling is set for tangency at CAM_MIN_DEG.\nCAM_FOLLOWER_Z = CAM_Z + CAM_R + CAM_E*math.sin(math.radians(CAM_MIN_DEG))\ncam_pocket = box(-13.6, CAM_Y-6.25, -15.2, 27.2, 12.5, CAM_FOLLOWER_Z+15.2)\nLOWER = LOWER.cut(cam_pocket)\nLOWER = LOWER.removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final rack lower jaw for cam fixup')
s = s.replace(old, new, 1)

# One-piece printed cam + shaft + lever. The shaft inserts through the fixed cam
# lugs and is retained with the same small printed C-clip geometry already used
# elsewhere; the clip retains the axle only and does not provide clamping force.
anchor = 'PARTS = {\n'
if anchor not in s:
    raise SystemExit('Could not locate PARTS anchor for cam part')
cam_geometry = '''# Printed eccentric rack cam. Local shaft axis is X through Y=Z=0.\n# The drum centre is offset +Y by CAM_E; rotating about X therefore changes\n# its upward effective radius by CAM_E*sin(angle). The lever points downward\n# in its neutral orientation so the +/-30 deg operating sweep stays below the\n# fixed bridge/root rather than sweeping into the arm.\ncam_shaft = cyl_x(CAM_SHAFT_D/2, 35.75, -17.75, 0.0, 0.0)\ncam_drum = cyl_x(CAM_R, 25.0, -12.5, CAM_E, 0.0)\ncam_hub = cyl_x(4.2, 4.4, -21.6, 0.0, 0.0)\ncam_lever = box(-21.4, -3.5, -24.0, 4.0, 7.0, 24.0)\ncam_thumb = cyl_x(5.2, 4.0, -21.4, 0.0, -24.0)\ncam_groove = cyl_x(1.55, 1.5, 17.75, 0.0, 0.0)\ncam_end = cyl_x(2.0, 1.7, 19.25, 0.0, 0.0)\nCAM = fuse_all([cam_shaft, cam_drum, cam_hub, cam_lever, cam_thumb, cam_groove, cam_end])\nCAM_CLIP = PIN_CLIP.copy()\n\n'''
s = s.replace(anchor, cam_geometry + anchor, 1)

old = "    'eurobox_v50_rack_pin_clip': PIN_CLIP,\n"
new = "    'eurobox_v50_rack_pin_clip': PIN_CLIP,\n    'eurobox_v50_rack_cam_lever': CAM,\n    'eurobox_v50_rack_cam_clip': CAM_CLIP,\n"
if old not in s:
    raise SystemExit('Could not add cam parts to PARTS')
s = s.replace(old, new, 1)

# Kinematic capacity and collision checks. The follower lever arms are measured
# from the fixed hinge in Y: 12 mm to tube centre and 23 mm to the cam axis.
# The eccentric travel over +/-30 deg must map to >=0.41 mm at the tube.
anchor = "V['rack_pin_checks'] = []\n"
if anchor not in s:
    raise SystemExit('Could not locate rack validation anchor')
insert = '''cam_arm_mm = CAM_Y - PIN_Y\ntube_arm_mm = 0.0 - PIN_Y\ncam_r_min = CAM_R + CAM_E*math.sin(math.radians(CAM_MIN_DEG))\ncam_r_max = CAM_R + CAM_E*math.sin(math.radians(CAM_MAX_DEG))\ncam_front_travel = cam_r_max - cam_r_min\ncam_tube_closure = cam_front_travel * tube_arm_mm / cam_arm_mm\ncam_lower_max_deg = math.degrees(math.asin(cam_front_travel / cam_arm_mm))\nV['rack_cam'] = {\n    'mode': 'printed_eccentric_over_center_style_clamp',\n    'tube_diameter_min_mm': 12.0,\n    'tube_diameter_max_mm': 12.41,\n    'required_full_diameter_compensation_mm': 0.41,\n    'axis_y_mm': CAM_Y,\n    'axis_z_mm': CAM_Z,\n    'drum_radius_mm': CAM_R,\n    'eccentricity_mm': CAM_E,\n    'operating_angle_min_deg': CAM_MIN_DEG,\n    'operating_angle_max_deg': CAM_MAX_DEG,\n    'cam_front_travel_mm': round(cam_front_travel, 6),\n    'mapped_tube_closure_mm': round(cam_tube_closure, 6),\n    'lower_rotation_span_deg': round(cam_lower_max_deg, 6),\n    'separate_lock_bolt': False,\n    'tool_less': True,\n    'printed_cam_axle_retained_by_clip': True,\n}\nV['rack_cam_checks'] = []\nfor phi in [CAM_MIN_DEG, -15.0, 0.0, 15.0, CAM_MAX_DEG]:\n    lift = (CAM_R + CAM_E*math.sin(math.radians(phi))) - cam_r_min\n    lower_deg = math.degrees(math.asin(max(0.0, lift) / cam_arm_mm))\n    for xc in CLAMP_X:\n        cam = CAM.copy()\n        cam.rotate(App.Vector(0,0,0), App.Vector(1,0,0), phi)\n        cam.translate(App.Vector(xc, CAM_Y, CAM_Z))\n        lo = LOWER.copy()\n        lo.rotate(App.Vector(0,PIN_Y,PIN_Z), App.Vector(1,0,0), lower_deg)\n        lo.translate(App.Vector(xc,0,0))\n        V['rack_cam_checks'].append({\n            'x_mm': xc,\n            'cam_angle_deg': phi,\n            'lower_angle_deg': round(lower_deg, 6),\n            'cam_base_common_mm3': round(cam.common(BASE).Volume, 6),\n            'cam_lower_common_mm3': round(cam.common(lo).Volume, 6),\n        })\n\n# Explicit virtual tube-endpoint checks. The lower rotation generated by the\n# cam has enough mapped travel for the complete measured 12.00..12.41 range.\nV['rack_cam_tube_range'] = {\n    'diameter_12_41_supported': cam_tube_closure >= 0.41 - 1e-6,\n    'diameter_12_00_supported': cam_tube_closure >= 0.41 - 1e-6,\n    'available_compensation_mm': round(cam_tube_closure, 6),\n    'required_compensation_mm': 0.41,\n}\n\n'''
s = s.replace(anchor, insert + anchor, 1)

# Hard gates: full 0.41 mm range, no fixed-body collision through the complete
# lever sweep, and no meaningful penetration into the moving follower beyond
# numerical/tangency noise.
fail_anchor = "for c in V['rack_pin_checks']:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack-pin failure checks')
fail_insert = '''if V['rack_cam']['mapped_tube_closure_mm'] < 0.41:\n    failures.append('Rack cam cannot compensate full measured 12.00..12.41 mm tube range')\nfor c in V['rack_cam_checks']:\n    if c['cam_base_common_mm3'] > 1e-4:\n        failures.append('Rack cam lever/shaft collides with fixed base at angle='+str(c['cam_angle_deg']))\n    if c['cam_lower_common_mm3'] > 0.75:\n        failures.append('Rack cam has excessive follower interference at angle='+str(c['cam_angle_deg']))\n'''
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

# Show the cam in the assembly at the large-tube end of its working range. The
# two module copies use identical printed parts; the existing left_transform
# handles the opposite module orientation.
right_anchor = "for xc in CLAMP_X:\n    lo = LOWER.copy(); lo.translate(App.Vector(xc, RY, 0)); add_obj('RIGHT_lower_'+str(int(xc)), lo)\n"
right_new = right_anchor + "for xc in CLAMP_X:\n    ca = CAM.copy(); ca.rotate(App.Vector(0,0,0), App.Vector(1,0,0), CAM_MIN_DEG); ca.translate(App.Vector(xc, RY+CAM_Y, CAM_Z)); add_obj('RIGHT_cam_'+str(int(xc)), ca)\n"
if right_anchor not in s:
    raise SystemExit('Could not locate right assembly lower loop')
s = s.replace(right_anchor, right_new, 1)

left_anchor = "for xc in CLAMP_X:\n    lo = LOWER.copy(); lo.translate(App.Vector(xc,0,0)); add_obj('LEFT_lower_'+str(int(xc)), left_transform(lo))\n"
left_new = left_anchor + "for xc in CLAMP_X:\n    ca = CAM.copy(); ca.rotate(App.Vector(0,0,0), App.Vector(1,0,0), CAM_MIN_DEG); ca.translate(App.Vector(xc,CAM_Y,CAM_Z)); add_obj('LEFT_cam_'+str(int(xc)), left_transform(ca))\n"
if left_anchor not in s:
    raise SystemExit('Could not locate left assembly lower loop')
s = s.replace(left_anchor, left_new, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack closure: printable eccentric cam for Ø12.00..12.41 mm')
