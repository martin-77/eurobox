from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final arm/profile cleanup. Keep both longitudinal side channels open. At the
# head each BASE has two holms; each holm gets exactly ONE flush 3.2 mm end wall
# at BOX_RIM_INNER_Y-0.20 (=228.015 mm).
#
# The redundant inner wall is not a holm feature at all: it comes from the old
# full-width crosshead middle web at Y=216..220.5. Keep that middle web only
# between the two holms (X=-74..+74), leaving both 32 mm holm windows open.
# This applies symmetrically to BASE_LEFT/BASE_RIGHT (4 head positions total).
# Spindle/cage/nut/box-clamp geometry is untouched.

# Remove the redundant crosshead middle wall from BOTH holm windows at source.
_old_crosshead_middle = (
    "    box(-106.0, 216.0, ARM_BOTTOM_Z+FLANGE_T, "
    "212.0, 4.5, ARM_H-2*FLANGE_T),\n"
)
_new_crosshead_middle = (
    "    box(-74.0, 216.0, ARM_BOTTOM_Z+FLANGE_T, "
    "148.0, 4.5, ARM_H-2*FLANGE_T),\n"
)
if _old_crosshead_middle not in s:
    raise SystemExit('Could not locate full-width crosshead middle web')
s = s.replace(_old_crosshead_middle, _new_crosshead_middle, 1)

pat = re.compile(r"def make_i_beam_y\(xc, y0, y1\):\n.*?(?=\n\ndef |\n# -----------------------------|\nbase_parts =)", re.S)
if not pat.search(s):
    raise SystemExit('Could not locate final make_i_beam_y implementation')

rep = '''ARM_PROFILE_FLANGE_T = 4.5
ARM_PROFILE_WEB_T = 3.2
ARM_PROFILE_WEB_CENTERS = (-8.0, 8.0)
ARM_PROFILE_SPLINE_RISE = 10.0
ARM_PROFILE_VISUAL_RADIUS = 20.0
ARM_PROFILE_SPLINE_SAMPLES = 18
ARM_PROFILE_MAX_DX_DZ = 0.96
ARM_PROFILE_HEAD_CAP_T = ARM_PROFILE_WEB_T
ARM_PROFILE_HEAD_FACE_Y = BOX_RIM_INNER_Y - 0.20


def _arm_smoothstep(t):
    return 3.0*t*t - 2.0*t*t*t


def _arm_side_haunch(xc, y0, length, side, top):
    web_center = xc + side*8.0
    web_outer = web_center + side*(ARM_PROFILE_WEB_T/2.0)
    outer = xc + side*(ARM_W/2.0)
    span = abs(outer-web_outer)
    z_flange = ((ARM_TOP_Z-ARM_PROFILE_FLANGE_T) if top
                else (ARM_BOTTOM_Z+ARM_PROFILE_FLANGE_T))
    z_tip = z_flange + ((-1.0 if top else 1.0)*ARM_PROFILE_SPLINE_RISE)
    curve = []
    for i in range(ARM_PROFILE_SPLINE_SAMPLES+1):
        t = i/float(ARM_PROFILE_SPLINE_SAMPLES)
        z = z_tip + (z_flange-z_tip)*t
        x = web_outer + side*span*_arm_smoothstep(t)
        curve.append(App.Vector(x, y0, z))
    pts = [App.Vector(web_outer, y0, z_flange),
           App.Vector(web_outer, y0, z_tip)] + curve[1:] + [
           App.Vector(web_outer, y0, z_flange)]
    wire = Part.makePolygon(pts)
    return Part.Face(wire).extrude(App.Vector(0, length, 0)).removeSplitter()


def make_i_beam_y(xc, y0, y1):
    L = y1-y0
    top = box(xc-ARM_W/2.0, y0, ARM_TOP_Z-ARM_PROFILE_FLANGE_T,
              ARM_W, L, ARM_PROFILE_FLANGE_T)
    bot = box(xc-ARM_W/2.0, y0, ARM_BOTTOM_Z,
              ARM_W, L, ARM_PROFILE_FLANGE_T)
    web_h = ARM_H - 2.0*ARM_PROFILE_FLANGE_T
    web_z = ARM_BOTTOM_Z + ARM_PROFILE_FLANGE_T
    webs = [box(xc+c-ARM_PROFILE_WEB_T/2.0, y0, web_z,
                ARM_PROFILE_WEB_T, L, web_h)
            for c in ARM_PROFILE_WEB_CENTERS]
    haunches = [_arm_side_haunch(xc, y0, L, side, top_side)
                for side in (-1, 1) for top_side in (False, True)]
    return fuse_all([top, bot] + webs + haunches).removeSplitter()


def _arm_head_cap(xc, y_face):
    return box(xc-ARM_W/2.0,
               y_face-ARM_PROFILE_HEAD_CAP_T,
               ARM_BOTTOM_Z,
               ARM_W,
               ARM_PROFILE_HEAD_CAP_T,
               ARM_H)
'''
s = pat.sub(rep.rstrip(), s, count=1)

# Add exactly one outer head cap per holm to the common handed core. There is no
# post-boolean "inner wall cutter": the offending wall has already been removed
# correctly at its source above.
handed_anchor = 'BASE_CORE = BASE.copy()\n'
if handed_anchor not in s:
    raise SystemExit('Could not locate handed BASE core anchor')
handed_insert = '''BASE_CORE = BASE.copy()

_ARM_HEAD_CAPS = [_arm_head_cap(xc, ARM_PROFILE_HEAD_FACE_Y) for xc in CLAMP_X]
for _q in _ARM_HEAD_CAPS:
    BASE_CORE = BASE_CORE.fuse(_q).removeSplitter()
if not BASE_CORE.isValid() or len(BASE_CORE.Solids) != 1:
    raise RuntimeError('Single-wall holm head cleanup broke BASE core topology')
'''
s = s.replace(handed_anchor, handed_insert, 1)

# Keep rear panel edge at +190, widen it to 50 mm toward the rear clamp.
if 'MOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 60.0' not in s:
    raise SystemExit('Could not locate mounting-backstop start offset')
s = s.replace('MOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 60.0',
              'MOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 50.0', 1)
if 'MOUNT_BACKSTOP_W_X = 40.0' not in s:
    raise SystemExit('Could not locate 40 mm mounting-backstop width')
s = s.replace('MOUNT_BACKSTOP_W_X = 40.0', 'MOUNT_BACKSTOP_W_X = 50.0', 1)
s = s.replace('handed_single_rear_40mm_panel_with_deep_root_and_rear_i_beam_gusset',
              'handed_single_rear_50mm_panel_with_rectangular_step_bridge')
s = s.replace("if V['mounting_backstop']['clearance_from_rear_clamp_body_mm'] < 35.0:",
              "if V['mounting_backstop']['clearance_from_rear_clamp_body_mm'] < 32.5:")
s = s.replace("if V['mounting_backstop']['contact_window_behind_rear_clamp_center_mm'][0] < 55.0:",
              "if V['mounting_backstop']['contact_window_behind_rear_clamp_center_mm'][0] < 49.9:")

# Replace the long diagonal gusset by a short rectangular step bridge. It starts
# only 8 mm inside the rear holm's outer edge, reaches 4 mm into the 20 mm-deep
# panel root, and starts at Z=18 mm so the moving lower rack clamp remains below
# it throughout its opening sweep. No diagonal face remains.
right_pat = re.compile(
    r"MOUNT_BACKSTOP_GUSSET_Y0 = 0\.0\n"
    r"MOUNT_BACKSTOP_GUSSET_Y1 = 20\.0\n"
    r"MOUNT_BACKSTOP_GUSSET_TOP_Z = 38\.75\n"
    r"MOUNT_BACKSTOP_REAR_ROOT_X0 = REAR_CLAMP_X - ARM_W/2\.0\n"
    r"_mount_backstop_profile = \[.*?"
    r"MOUNT_BACKSTOP_GUSSET = Part\.Face\(_mount_backstop_wire\)\.extrude\(\n"
    r"    App\.Vector\(0, MOUNT_BACKSTOP_GUSSET_Y1-MOUNT_BACKSTOP_GUSSET_Y0, 0\)\)\n",
    re.S,
)
right_rep = '''MOUNT_BACKSTOP_GUSSET_Y0 = 0.0
MOUNT_BACKSTOP_GUSSET_Y1 = 20.0
MOUNT_BACKSTOP_GUSSET_TOP_Z = 38.75
MOUNT_BACKSTOP_BRIDGE_Z0 = 18.0
MOUNT_BACKSTOP_HOLM_OVERLAP_X = 8.0
MOUNT_BACKSTOP_ROOT_OVERLAP_X = 4.0
MOUNT_BACKSTOP_REAR_ROOT_X0 = REAR_CLAMP_X + ARM_W/2.0 - MOUNT_BACKSTOP_HOLM_OVERLAP_X
MOUNT_BACKSTOP_BRIDGE_X1 = MOUNT_BACKSTOP_X0 + MOUNT_BACKSTOP_ROOT_OVERLAP_X
MOUNT_BACKSTOP_GUSSET = box(
    MOUNT_BACKSTOP_REAR_ROOT_X0,
    MOUNT_BACKSTOP_GUSSET_Y0,
    MOUNT_BACKSTOP_BRIDGE_Z0,
    MOUNT_BACKSTOP_BRIDGE_X1-MOUNT_BACKSTOP_REAR_ROOT_X0,
    MOUNT_BACKSTOP_GUSSET_Y1-MOUNT_BACKSTOP_GUSSET_Y0,
    MOUNT_BACKSTOP_GUSSET_TOP_Z-MOUNT_BACKSTOP_BRIDGE_Z0,
)
'''
s, n = right_pat.subn(right_rep, s, count=1)
if n != 1:
    raise SystemExit('Could not replace RIGHT sloping backstop gusset')

left_pat = re.compile(
    r"MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1 = FRONT_CLAMP_X \+ ARM_W/2\.0\n"
    r"_mount_backstop_left_profile = \[.*?"
    r"MOUNT_BACKSTOP_GUSSET_LEFT = Part\.Face\(_mount_backstop_left_wire\)\.extrude\(\n"
    r"    App\.Vector\(0, MOUNT_BACKSTOP_GUSSET_Y1-MOUNT_BACKSTOP_GUSSET_Y0, 0\)\)\n",
    re.S,
)
left_rep = '''MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1 = FRONT_CLAMP_X - ARM_W/2.0 + MOUNT_BACKSTOP_HOLM_OVERLAP_X
MOUNT_BACKSTOP_LEFT_BRIDGE_X0 = MOUNT_BACKSTOP_LEFT_X1 - MOUNT_BACKSTOP_ROOT_OVERLAP_X
MOUNT_BACKSTOP_GUSSET_LEFT = box(
    MOUNT_BACKSTOP_LEFT_BRIDGE_X0,
    MOUNT_BACKSTOP_GUSSET_Y0,
    MOUNT_BACKSTOP_BRIDGE_Z0,
    MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1-MOUNT_BACKSTOP_LEFT_BRIDGE_X0,
    MOUNT_BACKSTOP_GUSSET_Y1-MOUNT_BACKSTOP_GUSSET_Y0,
    MOUNT_BACKSTOP_GUSSET_TOP_Z-MOUNT_BACKSTOP_BRIDGE_Z0,
)
'''
s, n = left_pat.subn(left_rep, s, count=1)
if n != 1:
    raise SystemExit('Could not replace LEFT sloping backstop gusset')

# Keep generated notes aligned with the rectangular load path.
s = s.replace('deeply gusseted into its rear I-beam root',
              'connected by a short rectangular step bridge into its rear holm')

anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')
validation = '''# Final single-wall + rectangular-backstop hard checks.
_arm_web_outer = 8.0 + ARM_PROFILE_WEB_T/2.0
_arm_side_reach = ARM_W/2.0 - _arm_web_outer
_arm_max_dx_dz = 1.5*_arm_side_reach/ARM_PROFILE_SPLINE_RISE
_arm_probe = make_i_beam_y(0.0, 0.0, 20.0)
_arm_open_probe_z0 = ARM_BOTTOM_Z + ARM_H/2.0 - 0.20
_arm_open_probe_left = box(-ARM_W/2.0+0.20, 5.0, _arm_open_probe_z0,
                           3.0, 10.0, 0.40)
_arm_open_probe_right = box(ARM_W/2.0-3.20, 5.0, _arm_open_probe_z0,
                            3.0, 10.0, 0.40)
_arm_open_left_common = _arm_probe.common(_arm_open_probe_left).Volume
_arm_open_right_common = _arm_probe.common(_arm_open_probe_right).Volume

_head_cap_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _ARM_HEAD_CAPS]
_head_cap_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _ARM_HEAD_CAPS]

# Probe the centre channel behind each outer cap. This is the exact material
# volume that the old full-width Y=216..220.5 crosshead middle wall used to
# occupy, but it deliberately avoids the two legitimate longitudinal I/H webs.
# If the redundant wall ever returns, these probes become solid immediately.
_ARM_INNER_WALL_PROBES = [
    box(xc-4.0, 216.25, 18.0, 8.0, 3.50, 13.0)
    for xc in CLAMP_X
]
_inner_wall_probe_common_right = [BASE_RIGHT.common(q).Volume for q in _ARM_INNER_WALL_PROBES]
_inner_wall_probe_common_left = [BASE_LEFT.common(q).Volume for q in _ARM_INNER_WALL_PROBES]

_backstop_sweep = []
for _side, _xc, _stop in (
    ('RIGHT', REAR_CLAMP_X, MOUNT_BACKSTOP_RIGHT),
    ('LEFT', FRONT_CLAMP_X, MOUNT_BACKSTOP_LEFT),
):
    for _deg in (0, -15, -30, -45, -60, -75):
        _lo = LOWER.copy()
        _lo.rotate(App.Vector(0, PIN_Y, PIN_Z), App.Vector(1,0,0), _deg)
        _lo.translate(App.Vector(_xc, 0, 0))
        _backstop_sweep.append({
            'side': _side,
            'rotation_deg': _deg,
            'backstop_common_mm3': round(_stop.common(_lo).Volume, 9),
        })

V['supportfree_arm_profile'] = {
    'architecture': 'symmetric_two_web_open_profile_one_flush_head_wall_per_holm',
    'outer_width_mm': round(_arm_probe.BoundBox.XLength, 3),
    'outer_height_mm': round(_arm_probe.BoundBox.ZLength, 3),
    'flange_thickness_mm': ARM_PROFILE_FLANGE_T,
    'web_thickness_mm': ARM_PROFILE_WEB_T,
    'web_centers_mm': list(ARM_PROFILE_WEB_CENTERS),
    'side_reach_mm': round(_arm_side_reach, 3),
    'spline_rise_mm': ARM_PROFILE_SPLINE_RISE,
    'max_dx_dz': round(_arm_max_dx_dz, 6),
    'longitudinal_side_channels_open': True,
    'left_side_open_probe_common_mm3': round(_arm_open_left_common, 9),
    'right_side_open_probe_common_mm3': round(_arm_open_right_common, 9),
    'holm_positions_per_base': len(CLAMP_X),
    'problem_positions_total_left_plus_right': 2*len(CLAMP_X),
    'head_face_y_mm': round(ARM_PROFILE_HEAD_FACE_Y, 3),
    'head_cap_y_mm': [round(ARM_PROFILE_HEAD_FACE_Y-ARM_PROFILE_HEAD_CAP_T, 3),
                      round(ARM_PROFILE_HEAD_FACE_Y, 3)],
    'head_cap_material_fraction_right': [round(x, 6) for x in _head_cap_fraction_right],
    'head_cap_material_fraction_left': [round(x, 6) for x in _head_cap_fraction_left],
    'crosshead_middle_web_x_mm': [-74.0, 74.0],
    'inner_wall_probe_common_right_mm3': [round(x, 9) for x in _inner_wall_probe_common_right],
    'inner_wall_probe_common_left_mm3': [round(x, 9) for x in _inner_wall_probe_common_left],
}
V['mounting_backstop_final_cleanup'] = {
    'bridge_shape': 'rectangular_step_no_diagonal_faces',
    'bridge_z_mm': [MOUNT_BACKSTOP_BRIDGE_Z0, MOUNT_BACKSTOP_GUSSET_TOP_Z],
    'holm_overlap_x_mm': MOUNT_BACKSTOP_HOLM_OVERLAP_X,
    'root_overlap_x_mm': MOUNT_BACKSTOP_ROOT_OVERLAP_X,
    'right_bridge_x_mm': [MOUNT_BACKSTOP_REAR_ROOT_X0, MOUNT_BACKSTOP_BRIDGE_X1],
    'left_bridge_x_mm': [MOUNT_BACKSTOP_LEFT_BRIDGE_X0, MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1],
    'rack_clamp_sweep': _backstop_sweep,
}
if abs(V['supportfree_arm_profile']['outer_width_mm']-ARM_W) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 32 mm outer width')
if abs(V['supportfree_arm_profile']['outer_height_mm']-ARM_H) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 30 mm outer height')
if _arm_max_dx_dz > 1.0 + 1e-9:
    failures.append('Support-free spline exceeds the 45 degree lateral-growth envelope')
if _arm_open_left_common > 1e-6 or _arm_open_right_common > 1e-6:
    failures.append('A longitudinal holm side channel was closed')
if len(_ARM_HEAD_CAPS) != 2 or len(_ARM_INNER_WALL_PROBES) != 2:
    failures.append('BASE does not contain exactly two corrected holm-head positions')
if abs(ARM_PROFILE_HEAD_FACE_Y-(BOX_RIM_INNER_Y-0.20)) > 1e-9:
    failures.append('Single holm end walls are not flush with the 228.015 mm head edge')
for _side, _vals in (('RIGHT', _head_cap_fraction_right), ('LEFT', _head_cap_fraction_left)):
    for _i, _frac in enumerate(_vals):
        if _frac < 0.999:
            failures.append(f'{_side} holm {_i} lost its single flush outer head wall')
for _side, _vals in (('RIGHT', _inner_wall_probe_common_right), ('LEFT', _inner_wall_probe_common_left)):
    for _i, _common in enumerate(_vals):
        if _common > 1e-5:
            failures.append(f'{_side} holm {_i} still has the redundant parallel inner head wall')
for _state in _backstop_sweep:
    if _state['backstop_common_mm3'] > 1e-5:
        failures.append('Rectangular rear backstop blocks rack-clamp sweep: '+repr(_state))
if abs(MOUNT_BACKSTOP_REAR_ROOT_X0-(REAR_CLAMP_X+8.0)) > 1e-9:
    failures.append('RIGHT rectangular backstop bridge reaches too deep into rear holm')
if abs(MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1-(FRONT_CLAMP_X-8.0)) > 1e-9:
    failures.append('LEFT rectangular backstop bridge reaches too deep into rear holm')
if abs(MOUNT_BACKSTOP_X0-140.0) > 0.02:
    failures.append('Rear mounting backstop does not start at local X=140 mm')
if abs(MOUNT_BACKSTOP_W_X-50.0) > 1e-9:
    failures.append('Rear mounting backstop is not the requested 50 mm width')
if abs((MOUNT_BACKSTOP_X0+MOUNT_BACKSTOP_W_X)-190.0) > 0.02:
    failures.append('Rear mounting backstop does not retain its local X=190 mm rear edge')

'''
s = s.replace(anchor, validation + anchor, 1)

if s == orig:
    raise SystemExit('INDX final arm/backstop patch made no changes')
if 'MOUNT_BACKSTOP_BRIDGE_Z0 = 18.0' not in s:
    raise SystemExit('Rectangular backstop bridge was not installed')
if _new_crosshead_middle not in s:
    raise SystemExit('Crosshead middle web was not narrowed between the holms')

p.write_text(s, encoding='utf-8')
print('Applied one flush wall per holm and a short rectangular clamp-safe rear backstop bridge')
