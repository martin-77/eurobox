from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# v51 rack-joint refinement.
#
# Design intent:
# - keep the tire-side Y envelope unchanged;
# - put the broad, hard-to-replace pivot bearing into UPPER/BASE;
# - make the replaceable rack_lower the outer fork and therefore the preferred
#   sacrificial/service part;
# - enlarge the fixed upper tube-support mass without moving the frozen tube,
#   pivot, clamp-station or box datums;
# - retain the positive M4 closure and the validated opening sweep.
#
# The former layout had two fixed outer Upper cheeks and one broad moving Lower
# pivot. Although the 6 mm cheeks themselves were adequate, each circular eye
# fed into BASE through a comparatively narrow local neck. The new layout uses
# one 18 mm-wide central Upper eye with a broad web directly into the saddle
# bridge. Lower becomes a 28 mm-wide fork with two 4.6 mm service ears.

upper_pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
upper_replacement = '''UPPER_PIVOT_W = 18.0
UPPER_PIVOT_R = 7.0
LOWER_FORK_SIDE_CLEAR = 0.40
LOWER_FORK_EAR_T = 4.60
LOWER_FORK_INNER_HALF_X = UPPER_PIVOT_W/2.0 + LOWER_FORK_SIDE_CLEAR
LOWER_FORK_OUTER_HALF_X = LOWER_FORK_INNER_HALF_X + LOWER_FORK_EAR_T
LOWER_FORK_W = 2.0 * LOWER_FORK_OUTER_HALF_X
LOWER_PIVOT_R = 5.0
UPPER_BRIDGE_Y0 = -8.0
UPPER_BRIDGE_Y1 = 18.0
UPPER_BRIDGE_Z1 = 18.0


def make_upper_station(xc):
    # No growth toward the tyre: the bridge still starts at Y=-8 and the
    # circular pivot keeps the former Y-min of PIN_Y-7 = -19 mm. Extra material
    # is placed inward/toward the arm and across X, where space already exists.
    bridge = box(xc-19.0, UPPER_BRIDGE_Y0, 0.0,
                 38.0, UPPER_BRIDGE_Y1-UPPER_BRIDGE_Y0, UPPER_BRIDGE_Z1)
    root_beam = make_i_beam_y(xc, -8.0, 36.0)

    # Broad central fixed bearing. This is the expensive BASE-side member and
    # intentionally carries much more bearing length than either Lower fork ear.
    upper_pivot = cyl_x(UPPER_PIVOT_R, UPPER_PIVOT_W,
                        xc-UPPER_PIVOT_W/2.0, PIN_Y, PIN_Z)

    # Broad load path from the eye into the fixed saddle. Both solids overlap
    # the circular eye and the bridge volumetrically; there is no point/edge-only
    # attachment. The saddle cut below removes only the real tube envelope.
    pivot_web = box(xc-UPPER_PIVOT_W/2.0, -10.5, -5.5,
                    UPPER_PIVOT_W, 5.0, 7.5)
    saddle_back = box(xc-UPPER_PIVOT_W/2.0, -8.0, -4.5,
                      UPPER_PIVOT_W, 2.5, 6.5)

    q = fuse_all([bridge, root_beam, upper_pivot, pivot_web, saddle_back])

    # Frozen real rack tube and pivot axes.
    q = q.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    q = q.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))

    # Preserve the proven positive M4 closure from the previous rack-lock pass.
    screw_bore = Part.makeCylinder(
        RACK_M4_BASE_CLEAR_D/2.0, 9.0,
        App.Vector(xc, RACK_CLOSURE_Y, -1.0), App.Vector(0,0,1))
    q = q.cut(screw_bore)

    nut_pocket = hex_z(RACK_M4_NUT_AF, RACK_M4_NUT_H, RACK_M4_NUT_Z0)
    nut_pocket.translate(App.Vector(xc, RACK_CLOSURE_Y, 0.0))
    q = q.cut(nut_pocket)
    if xc > 0:
        nut_slot = box(xc+3.45, RACK_CLOSURE_Y-RACK_M4_NUT_AF/2.0,
                       RACK_M4_NUT_Z0, 13.75,
                       RACK_M4_NUT_AF, RACK_M4_NUT_H)
    else:
        nut_slot = box(xc-17.2, RACK_CLOSURE_Y-RACK_M4_NUT_AF/2.0,
                       RACK_M4_NUT_Z0, 13.75,
                       RACK_M4_NUT_AF, RACK_M4_NUT_H)
    q = q.cut(nut_slot)
    return q.removeSplitter()

base_parts ='''
s, n = upper_pattern.subn(upper_replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace final Upper rack station with central-bearing architecture')

# Replace the complete final Lower geometry, but keep the existing M4 closure.
# The main clamp body stays continuous through the closure axis. Only the
# hinge-side centre is opened into a fork around the wide Upper eye.
lower_pattern = re.compile(
    r"# Continuous full-depth lower clamp body\..*?LOWER = LOWER\.removeSplitter\(\)",
    re.S,
)
lower_replacement = '''# Replaceable Lower fork around the broad central Upper bearing.
# The full-depth body remains continuous at the tube and M4 closure; a local
# centre slot exists only around the hinge eye.
lower_shell = box(-LOWER_FORK_OUTER_HALF_X, -7.0, -14.5,
                  LOWER_FORK_W, 22.0, 14.5)
lower_pivot_l = cyl_x(LOWER_PIVOT_R, LOWER_FORK_EAR_T,
                      -LOWER_FORK_OUTER_HALF_X, PIN_Y, PIN_Z)
lower_pivot_r = cyl_x(LOWER_PIVOT_R, LOWER_FORK_EAR_T,
                      LOWER_FORK_INNER_HALF_X, PIN_Y, PIN_Z)
lower_web_l = box(-LOWER_FORK_OUTER_HALF_X, PIN_Y, -10.5,
                  LOWER_FORK_EAR_T, 7.0, 10.5)
lower_web_r = box(LOWER_FORK_INNER_HALF_X, PIN_Y, -10.5,
                  LOWER_FORK_EAR_T, 7.0, 10.5)
LOWER = fuse_all([lower_shell, lower_pivot_l, lower_pivot_r,
                  lower_web_l, lower_web_r])

# 0.4 mm running clearance on each side of the 18 mm Upper eye. The slot also
# clears the Upper circular eye/web in Y/Z while preserving the forward clamp
# body and the M4 load path as one solid.
lower_fork_slot = box(-LOWER_FORK_INNER_HALF_X, -20.0, -13.0,
                      2.0*LOWER_FORK_INNER_HALF_X, 15.5, 15.5)
LOWER = LOWER.cut(lower_fork_slot)
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, LOWER_FORK_W+2.0,
                         -LOWER_FORK_OUTER_HALF_X-1.0, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2.0, LOWER_FORK_W+2.0,
                         -LOWER_FORK_OUTER_HALF_X-1.0, PIN_Y, PIN_Z))
lower_screw_bore = Part.makeCylinder(
    RACK_M4_LOWER_CLEAR_D/2.0, 16.5,
    App.Vector(0.0, RACK_CLOSURE_Y, -15.5),
    App.Vector(0,0,1))
LOWER = LOWER.cut(lower_screw_bore)
LOWER = LOWER.removeSplitter()'''
s, n = lower_pattern.subn(lower_replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace final rack_lower with outer-fork architecture')

# Match the service pin to the new 28 mm Lower outer fork. Head and C-clip
# clearances intentionally retain the previously validated PETG service values.
pin_pattern = re.compile(r"PIN = fuse_all\(\[\n.*?\n\]\)", re.S)
pin_replacement = '''PIN = fuse_all([
    # Main Ø4 shaft: 0.8 mm beyond left Lower ear to 1.0 mm beyond right ear.
    cyl_x(2.0, 29.8, -14.8, 0, 0),
    # C-clip groove and retaining end.
    cyl_x(1.55, 1.5, 15.0, 0, 0),
    cyl_x(2.0, 1.7, 16.5, 0, 0),
    # Head inner face at X=-14.8.
    cyl_x(3.75, 2.4, -17.2, 0, 0),
])'''
s, n = pin_pattern.subn(pin_replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not resize rack service pin for new Lower fork')

# Make the existing rack-root validation truthful for the inverted clevis.
s = s.replace(
    "'design': 'continuous_same_I_beam_as_long_arm_plus_6mm_fixed_clevis',",
    "'design': 'broad_central_upper_bearing_plus_replaceable_lower_fork',",
    1,
)
old_meta = '''    'fixed_clevis_lug_thickness_mm': RACK_FIXED_LUG_T,
    'fixed_clevis_inner_gap_mm': 2*RACK_FIXED_LUG_INNER_X,
    'moving_lower_width_mm': 25.2,
    'total_lateral_running_clearance_mm': 2*RACK_FIXED_LUG_INNER_X-25.2,
'''
new_meta = '''    'upper_pivot_width_mm': UPPER_PIVOT_W,
    'upper_pivot_outer_diameter_mm': 2.0*UPPER_PIVOT_R,
    'upper_pivot_radial_wall_mm': UPPER_PIVOT_R-PIN_HOLE_D/2.0,
    'lower_fork_ear_thickness_mm': LOWER_FORK_EAR_T,
    'lower_fork_outer_width_mm': LOWER_FORK_W,
    'lower_pivot_outer_diameter_mm': 2.0*LOWER_PIVOT_R,
    'lower_pivot_radial_wall_mm': LOWER_PIVOT_R-PIN_HOLE_D/2.0,
    'total_lateral_running_clearance_mm': 2.0*LOWER_FORK_SIDE_CLEAR,
    'upper_bridge_y_range_mm': [UPPER_BRIDGE_Y0, UPPER_BRIDGE_Y1],
    'upper_pivot_y_min_mm': PIN_Y-UPPER_PIVOT_R,
    'service_bias': 'BASE-side bearing deliberately stronger; replaceable Lower fork is service part',
'''
if old_meta not in s:
    raise SystemExit('Could not locate stale fixed-clevis validation metadata')
s = s.replace(old_meta, new_meta, 1)

old_gates = '''if r['fixed_clevis_lug_thickness_mm'] < 6.0:
    failures.append('Rack lower fixed clevis support below 6 mm PETG minimum')
if not (0.6 <= r['total_lateral_running_clearance_mm'] <= 1.2):
    failures.append('Rack lower clevis running clearance outside 0.6..1.2 mm')
'''
new_gates = '''if r['upper_pivot_width_mm'] < 16.0:
    failures.append('Upper central rack-pivot bearing is too narrow')
if r['upper_pivot_radial_wall_mm'] < 4.5:
    failures.append('Upper central rack-pivot eye has insufficient radial PETG wall')
if r['lower_fork_ear_thickness_mm'] < 4.2:
    failures.append('Replaceable Lower fork ears are too thin for service use')
if r['lower_pivot_radial_wall_mm'] < 2.5:
    failures.append('Replaceable Lower pivot eye has insufficient radial PETG wall')
if not (0.6 <= r['total_lateral_running_clearance_mm'] <= 1.2):
    failures.append('Upper/Lower fork running clearance outside 0.6..1.2 mm')
if r['upper_bridge_y_range_mm'][0] < -8.0-1e-9:
    failures.append('Upper saddle bridge grew toward the tyre beyond frozen Y=-8 envelope')
if r['upper_pivot_y_min_mm'] < -19.0-1e-9:
    failures.append('Upper pivot grew toward the tyre beyond the previous Y=-19 envelope')
if r['upper_pivot_width_mm'] <= 2.0*r['lower_fork_ear_thickness_mm']:
    failures.append('Upper bearing is not materially broader than combined Lower service ears')
'''
if old_gates not in s:
    raise SystemExit('Could not locate stale fixed-clevis hard gates')
s = s.replace(old_gates, new_gates, 1)

# Pin service-clearance metadata remains numerically identical, but its meaning
# is now relative to the outer Lower fork faces rather than fixed Upper cheeks.

# Add direct geometric witnesses for the new architecture after TUBE is defined.
anchor = "V['tube_base_common_mm3'] = round(BASE.common(TUBE).Volume, 6)\n"
if anchor not in s:
    raise SystemExit('Could not locate rack tube/base validation anchor')
extra = '''V['rack_joint_v51'] = {
    'upper_central_bearing_width_mm': UPPER_PIVOT_W,
    'lower_fork_ear_thickness_mm': LOWER_FORK_EAR_T,
    'lower_fork_outer_width_mm': LOWER_FORK_W,
    'side_clearance_each_mm': LOWER_FORK_SIDE_CLEAR,
    'upper_pivot_y_min_mm': PIN_Y-UPPER_PIVOT_R,
    'bridge_y_min_mm': UPPER_BRIDGE_Y0,
    'bridge_y_max_mm': UPPER_BRIDGE_Y1,
    'upper_bearing_to_lower_ear_width_ratio': round(
        UPPER_PIVOT_W/(2.0*LOWER_FORK_EAR_T), 4),
}
'''
s = s.replace(anchor, anchor + extra, 1)

if s == orig:
    raise SystemExit('v51 rack-joint refinement made no changes')

p.write_text(s, encoding='utf-8')
print('Applied v51 rack joint: broad central Upper bearing + replaceable Lower fork, tyre-side envelope unchanged')
