from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# CORE One L+ INDX / FDM printability refinement.
# Keep the proven two-web arm architecture and leave BOTH longitudinal side
# channels open over the full holm length. The requested closure is only at the
# HEAD: each BASE has two holms, and each holm gets one short 3.2 mm end cap at
# ARM_Y1. No long -X/+X skin is allowed. Spindle, screw cage, nut pockets and
# clamp kinematics remain untouched.
#
# The side flange overhangs are carried by symmetric cubic Hermite haunches.
# The curve is deliberately slope-limited: with the final 6.4 mm lateral reach
# and 10.0 mm vertical rise, max |dx/dz| = 1.5*6.4/10 = 0.96, i.e. < 1.0
# (45 deg limit).
#
# This is intentionally NOT a free cosmetic spline and not a literal R20 arc.
# It is an R20-like soft contour whose tangent envelope is constrained for
# support-free printing in the frozen upside-down BASE orientation.

# Replace whichever make_i_beam_y implementation preceding fixups left behind.
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


def _arm_smoothstep(t):
    return 3.0*t*t - 2.0*t*t*t


def _arm_side_haunch(xc, y0, length, side, top):
    # side: -1 left, +1 right. top=False is the print-critical lower physical
    # haunch (upper in the upside-down print); top=True is its exact mirror.
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
        # t=0 at the web tip; t=1 at the flange outer edge.
        z = z_tip + (z_flange-z_tip)*t
        x = web_outer + side*span*_arm_smoothstep(t)
        curve.append(App.Vector(x, y0, z))

    # Close back along the web outer face. This produces only the material
    # under the flange; BOTH longitudinal side recesses remain open to air.
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


def _arm_head_cap(xc, y_head):
    # Short end closure only: 3.2 mm in Y immediately before the holm head.
    # It spans the 32 x 30 mm holm cross-section and stays inside the existing
    # envelope. This closes the two open H/I ends without skinning either side.
    return box(xc-ARM_W/2.0,
               y_head-ARM_PROFILE_HEAD_CAP_T,
               ARM_BOTTOM_Z,
               ARM_W,
               ARM_PROFILE_HEAD_CAP_T,
               ARM_H)
'''
s = pat.sub(rep.rstrip(), s, count=1)

# Apply exactly TWO short head caps to the shared BASE core, one at the head of
# each longitudinal holm. The caps are X-symmetric, so the established handed
# LEFT/RIGHT mirror relationship remains intact.
handed_anchor = 'BASE_CORE = BASE.copy()\n'
if handed_anchor not in s:
    raise SystemExit('Could not locate handed BASE core anchor for head caps')
handed_insert = '''BASE_CORE = BASE.copy()

_ARM_HEAD_CAPS = [_arm_head_cap(xc, ARM_Y1) for xc in CLAMP_X]
for _q in _ARM_HEAD_CAPS:
    BASE_CORE = BASE_CORE.fuse(_q).removeSplitter()
if not BASE_CORE.isValid() or len(BASE_CORE.Solids) != 1:
    raise RuntimeError('Two short holm head caps broke BASE core topology')
'''
s = s.replace(handed_anchor, handed_insert, 1)

# Final requested rear mounting-stop geometry: keep the rear edge at X=+190 mm
# but widen the panel by 10 mm toward the rear clamp. With REAR_CLAMP_X=+90 mm,
# the contact window therefore changes from +150..+190 to +140..+190 mm.
if 'MOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 60.0' not in s:
    raise SystemExit('Could not locate mounting-backstop start offset')
s = s.replace('MOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 60.0',
              'MOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 50.0', 1)
if 'MOUNT_BACKSTOP_W_X = 40.0' not in s:
    raise SystemExit('Could not locate 40 mm mounting-backstop width')
s = s.replace('MOUNT_BACKSTOP_W_X = 40.0', 'MOUNT_BACKSTOP_W_X = 50.0', 1)
s = s.replace('handed_single_rear_40mm_panel_with_deep_root_and_rear_i_beam_gusset',
              'handed_single_rear_50mm_panel_with_deep_root_and_rear_i_beam_gusset')
s = s.replace("if V['mounting_backstop']['clearance_from_rear_clamp_body_mm'] < 35.0:",
              "if V['mounting_backstop']['clearance_from_rear_clamp_body_mm'] < 32.5:")
s = s.replace("if V['mounting_backstop']['contact_window_behind_rear_clamp_center_mm'][0] < 55.0:",
              "if V['mounting_backstop']['contact_window_behind_rear_clamp_center_mm'][0] < 49.9:")

# Add hard source-level checks immediately before the existing export loop.
anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')
validation = '''# Support-safe symmetric arm-profile / SHORT HEAD-CAP checks.
# Cubic smoothstep derivative max is 1.5; lateral reach is 6.4 mm.
_arm_web_outer = 8.0 + ARM_PROFILE_WEB_T/2.0
_arm_side_reach = ARM_W/2.0 - _arm_web_outer
_arm_max_dx_dz = 1.5*_arm_side_reach/ARM_PROFILE_SPLINE_RISE
_arm_probe = make_i_beam_y(0.0, 0.0, 20.0)

# Prove that the long side channels remain open. These probes sit at mid-height
# in the outer recesses where a mistaken full-length -X/+X skin would appear,
# but the intended I/H profile contains no material.
_arm_open_probe_z0 = ARM_BOTTOM_Z + ARM_H/2.0 - 0.20
_arm_open_probe_left = box(-ARM_W/2.0+0.20, 5.0, _arm_open_probe_z0,
                           3.0, 10.0, 0.40)
_arm_open_probe_right = box(ARM_W/2.0-3.20, 5.0, _arm_open_probe_z0,
                            3.0, 10.0, 0.40)
_arm_open_left_common = _arm_probe.common(_arm_open_probe_left).Volume
_arm_open_right_common = _arm_probe.common(_arm_open_probe_right).Volume

_head_cap_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _ARM_HEAD_CAPS]
_head_cap_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _ARM_HEAD_CAPS]
V['supportfree_arm_profile'] = {
    'architecture': 'symmetric_two_web_open_profile_with_two_short_head_end_caps',
    'outer_width_mm': round(_arm_probe.BoundBox.XLength, 3),
    'outer_height_mm': round(_arm_probe.BoundBox.ZLength, 3),
    'flange_thickness_mm': ARM_PROFILE_FLANGE_T,
    'web_thickness_mm': ARM_PROFILE_WEB_T,
    'web_centers_mm': list(ARM_PROFILE_WEB_CENTERS),
    'side_reach_mm': round(_arm_side_reach, 3),
    'spline_rise_mm': ARM_PROFILE_SPLINE_RISE,
    'visual_radius_intent_mm': ARM_PROFILE_VISUAL_RADIUS,
    'max_dx_dz': round(_arm_max_dx_dz, 6),
    'max_overhang_deg_from_vertical': round(math.degrees(math.atan(_arm_max_dx_dz)), 3),
    'symmetric_top_bottom': True,
    'symmetric_left_right': True,
    'longitudinal_side_channels_open': True,
    'left_side_open_probe_common_mm3': round(_arm_open_left_common, 9),
    'right_side_open_probe_common_mm3': round(_arm_open_right_common, 9),
    'head_cap_count_per_base': len(_ARM_HEAD_CAPS),
    'head_cap_y_mm': [ARM_Y1-ARM_PROFILE_HEAD_CAP_T, ARM_Y1],
    'head_cap_thickness_mm': ARM_PROFILE_HEAD_CAP_T,
    'head_cap_material_fraction_right': [round(x, 6) for x in _head_cap_fraction_right],
    'head_cap_material_fraction_left': [round(x, 6) for x in _head_cap_fraction_left],
    'print_orientation': 'BASE rotated 180deg about X; BOX_SUPPORT_Z on bed',
    'support_policy': 'side channels remain open; only two short vertical head end caps are added; no generated support required',
}
if abs(V['supportfree_arm_profile']['outer_width_mm']-ARM_W) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 32 mm outer width')
if abs(V['supportfree_arm_profile']['outer_height_mm']-ARM_H) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 30 mm outer height')
if _arm_max_dx_dz > 1.0 + 1e-9:
    failures.append('Support-free spline exceeds the 45 degree lateral-growth envelope')
if abs(ARM_PROFILE_WEB_CENTERS[0] + ARM_PROFILE_WEB_CENTERS[1]) > 1e-9:
    failures.append('Support-free arm webs are not symmetric about the arm center')
if _arm_open_left_common > 1e-6 or _arm_open_right_common > 1e-6:
    failures.append('A longitudinal holm side channel was closed; only the two short head ends may be capped')
if len(_ARM_HEAD_CAPS) != 2:
    failures.append('BASE does not have exactly two short holm head caps')
for side, vals in [('RIGHT', _head_cap_fraction_right), ('LEFT', _head_cap_fraction_left)]:
    for i, frac in enumerate(vals):
        if frac < 0.999:
            failures.append(f'{side} short holm head cap {i} is not fully incorporated in the BASE')
if abs(MOUNT_BACKSTOP_X0-140.0) > 0.02:
    failures.append('Rear mounting backstop does not start at local X=140 mm')
if abs(MOUNT_BACKSTOP_W_X-50.0) > 1e-9:
    failures.append('Rear mounting backstop is not the requested 50 mm width')
if abs((MOUNT_BACKSTOP_X0+MOUNT_BACKSTOP_W_X)-190.0) > 0.02:
    failures.append('Rear mounting backstop does not retain its local X=190 mm rear edge')

'''
s = s.replace(anchor, validation + anchor, 1)

if s == orig:
    raise SystemExit('INDX support-free arm patch made no changes')
if 'ARM_PROFILE_MAX_DX_DZ = 0.96' not in s:
    raise SystemExit('Support-free spline constants were not installed')
if '_ARM_HEAD_CAPS = [_arm_head_cap(xc, ARM_Y1) for xc in CLAMP_X]' not in s:
    raise SystemExit('Two short holm head caps were not installed')
if 'MOUNT_BACKSTOP_W_X = 50.0' not in s:
    raise SystemExit('Requested 50 mm backstop was not installed')

p.write_text(s, encoding='utf-8')
print('Applied open longitudinal holms with only two short 3.2 mm head end caps per BASE')
