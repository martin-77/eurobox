from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# v52 Upper pivot-root reinforcement.
#
# The v51 inverted clevis deliberately moved the broad bearing into UPPER/BASE,
# but the circular eye still enters the saddle bridge through a relatively
# narrow local root. Add a full-width tapered/teardrop buttress from the upper
# half of the eye into the fixed bridge. This is a load-path change, not an
# envelope change:
# - no movement of tube, pin, closure or clamp-station datums;
# - no growth beyond the existing tyre-side pivot envelope Y=-19 mm;
# - full 18 mm X width, matching the broad Upper bearing;
# - the Lower remains the smaller replaceable/service member;
# - the tube saddle is cut after the fuse, so real tube clearance is preserved.

const_anchor = "UPPER_BRIDGE_Z1 = 18.0\n"
if const_anchor not in s:
    raise SystemExit('Could not locate v51 Upper bridge constants')
consts = '''UPPER_GUSSET_LOWER_Y0 = PIN_Y - 5.5
UPPER_GUSSET_LOWER_Y1 = PIN_Y + 5.5
UPPER_GUSSET_LOWER_Z = PIN_Z + 3.0
UPPER_GUSSET_TOP_Y0 = UPPER_BRIDGE_Y0
UPPER_GUSSET_TOP_Y1 = 10.0
UPPER_GUSSET_TOP_Z = 13.0
'''
s = s.replace(const_anchor, const_anchor + consts, 1)

pivot_anchor = '''    upper_pivot = cyl_x(UPPER_PIVOT_R, UPPER_PIVOT_W,
                        xc-UPPER_PIVOT_W/2.0, PIN_Y, PIN_Z)

'''
if pivot_anchor not in s:
    raise SystemExit('Could not locate v51 broad Upper pivot')
pivot_gusset = pivot_anchor + '''    # Full-width teardrop-style buttress. The lower chord is buried well inside
    # the Ø14 Upper eye; the upper chord is buried broadly in the fixed bridge.
    # Its tyre-side edge slopes inward from Y=-17.5 to the bridge boundary Y=-8,
    # so it never grows beyond the already validated circular-eye Y-min=-19.
    gusset_pts = [
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_LOWER_Y0, UPPER_GUSSET_LOWER_Z),
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_LOWER_Y1, UPPER_GUSSET_LOWER_Z),
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_TOP_Y1, UPPER_GUSSET_TOP_Z),
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_TOP_Y0, UPPER_GUSSET_TOP_Z),
    ]
    gusset_wire = Part.makePolygon(gusset_pts + [gusset_pts[0]])
    upper_gusset = Part.Face(gusset_wire).extrude(App.Vector(UPPER_PIVOT_W, 0, 0))

'''
s = s.replace(pivot_anchor, pivot_gusset, 1)

old_fuse = "    q = fuse_all([bridge, root_beam, upper_pivot, pivot_web, saddle_back])\n"
new_fuse = "    q = fuse_all([bridge, root_beam, upper_pivot, upper_gusset, pivot_web, saddle_back])\n"
if old_fuse not in s:
    raise SystemExit('Could not locate v51 Upper fuse list')
s = s.replace(old_fuse, new_fuse, 1)

meta_anchor = '''    'upper_bridge_y_range_mm': [UPPER_BRIDGE_Y0, UPPER_BRIDGE_Y1],
    'upper_pivot_y_min_mm': PIN_Y-UPPER_PIVOT_R,
    'service_bias': 'BASE-side bearing deliberately stronger; replaceable Lower fork is service part',
'''
if meta_anchor not in s:
    raise SystemExit('Could not locate v51 rack-root validation metadata')
meta_replacement = '''    'upper_bridge_y_range_mm': [UPPER_BRIDGE_Y0, UPPER_BRIDGE_Y1],
    'upper_pivot_y_min_mm': PIN_Y-UPPER_PIVOT_R,
    'upper_gusset_x_width_mm': UPPER_PIVOT_W,
    'upper_gusset_lower_y_range_mm': [UPPER_GUSSET_LOWER_Y0, UPPER_GUSSET_LOWER_Y1],
    'upper_gusset_lower_z_mm': UPPER_GUSSET_LOWER_Z,
    'upper_gusset_top_y_range_mm': [UPPER_GUSSET_TOP_Y0, UPPER_GUSSET_TOP_Y1],
    'upper_gusset_top_z_mm': UPPER_GUSSET_TOP_Z,
    'service_bias': 'BASE-side bearing deliberately stronger; replaceable Lower fork is service part',
'''
s = s.replace(meta_anchor, meta_replacement, 1)

gate_anchor = '''if r['upper_pivot_y_min_mm'] < -19.0-1e-9:
    failures.append('Upper pivot grew toward the tyre beyond the previous Y=-19 envelope')
if r['upper_pivot_width_mm'] <= 2.0*r['lower_fork_ear_thickness_mm']:
'''
if gate_anchor not in s:
    raise SystemExit('Could not locate v51 rack-root hard gates')
gates = '''if r['upper_pivot_y_min_mm'] < -19.0-1e-9:
    failures.append('Upper pivot grew toward the tyre beyond the previous Y=-19 envelope')
if r['upper_gusset_lower_y_range_mm'][0] < r['upper_pivot_y_min_mm']-1e-9:
    failures.append('Upper pivot gusset grew toward the tyre beyond the existing pivot envelope')
if r['upper_gusset_top_y_range_mm'][0] < r['upper_bridge_y_range_mm'][0]-1e-9:
    failures.append('Upper pivot gusset top grows tyre-side beyond the fixed bridge')
if r['upper_gusset_top_y_range_mm'][1] > r['upper_bridge_y_range_mm'][1]+1e-9:
    failures.append('Upper pivot gusset top exceeds the fixed bridge inward envelope')
if r['upper_gusset_top_z_mm'] > UPPER_BRIDGE_Z1+1e-9:
    failures.append('Upper pivot gusset exceeds the fixed bridge height')
if not (r['upper_gusset_lower_z_mm'] < 0.0 < r['upper_gusset_top_z_mm']):
    failures.append('Upper pivot gusset does not span from the eye into the bridge')
if abs(r['upper_gusset_x_width_mm']-r['upper_pivot_width_mm']) > 1e-9:
    failures.append('Upper pivot gusset is not full bearing width')
for gy in r['upper_gusset_lower_y_range_mm']:
    if ((gy-PIN_Y)**2 + (r['upper_gusset_lower_z_mm']-PIN_Z)**2) > UPPER_PIVOT_R**2+1e-9:
        failures.append('Upper pivot gusset lower chord is not buried inside the pivot eye')
        break
if r['upper_pivot_width_mm'] <= 2.0*r['lower_fork_ear_thickness_mm']:
'''
s = s.replace(gate_anchor, gates, 1)

joint_anchor = '''    'bridge_y_max_mm': UPPER_BRIDGE_Y1,
    'upper_bearing_to_lower_ear_width_ratio': round(
'''
if joint_anchor not in s:
    raise SystemExit('Could not locate v51 rack-joint geometric witness')
joint_replacement = '''    'bridge_y_max_mm': UPPER_BRIDGE_Y1,
    'upper_gusset_x_width_mm': UPPER_PIVOT_W,
    'upper_gusset_profile_yz_mm': [
        [UPPER_GUSSET_LOWER_Y0, UPPER_GUSSET_LOWER_Z],
        [UPPER_GUSSET_LOWER_Y1, UPPER_GUSSET_LOWER_Z],
        [UPPER_GUSSET_TOP_Y1, UPPER_GUSSET_TOP_Z],
        [UPPER_GUSSET_TOP_Y0, UPPER_GUSSET_TOP_Z],
    ],
    'upper_bearing_to_lower_ear_width_ratio': round(
'''
s = s.replace(joint_anchor, joint_replacement, 1)

if s == orig:
    raise SystemExit('v52 Upper pivot gusset made no changes')

p.write_text(s, encoding='utf-8')
print('Applied v52 rack joint: full-width teardrop Upper pivot gusset into BASE, existing tyre envelope preserved')
