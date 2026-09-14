from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# CORE One L+ INDX / FDM printability refinement.
# Keep the proven two-web arm architecture and its support-safe spline haunches.
# The common arm core stays X-symmetric. Only the two open longitudinal holm
# faces are closed, and that closure is applied AFTER the handed LEFT/RIGHT
# split so both printable bases remain exact X mirrors. RIGHT closes local -X;
# LEFT closes local +X. Spindle, screw cage, nut pockets and clamp kinematics
# remain untouched.
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
ARM_PROFILE_FRONT_SKIN_T = ARM_PROFILE_WEB_T


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

    # Close back along the web outer face. Both side recesses remain open in the
    # shared core; the handed closure skin is added only after LEFT/RIGHT split.
    pts = [App.Vector(web_outer, y0, z_flange),
           App.Vector(web_outer, y0, z_tip)] + curve[1:] + [
           App.Vector(web_outer, y0, z_flange)]
    wire = Part.makePolygon(pts)
    return Part.Face(wire).extrude(App.Vector(0, length, 0)).removeSplitter()


def _arm_front_skin(xc, y0, y1, side):
    # side=-1 closes the local -X face, side=+1 the exact X-mirrored +X face.
    # Keep the skin entirely inside the frozen 32 x 30 mm arm envelope and use
    # the proven 3.2 mm web thickness. It overlaps both flanges volumetrically.
    if side not in (-1, 1):
        raise ValueError('arm front skin side must be -1 or +1')
    x0 = (xc-ARM_W/2.0 if side < 0
          else xc+ARM_W/2.0-ARM_PROFILE_FRONT_SKIN_T)
    return box(x0, y0, ARM_BOTTOM_Z,
               ARM_PROFILE_FRONT_SKIN_T, y1-y0, ARM_H)


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
'''
s = pat.sub(rep.rstrip(), s, count=1)

# Apply the small holm closure to the explicit handed BASE cores, not to the
# common arm primitive. This keeps the existing hard LEFT/RIGHT mirror gate
# meaningful instead of weakening it.
handed_anchor = 'BASE_CORE = BASE.copy()\n'
if handed_anchor not in s:
    raise SystemExit('Could not locate handed BASE core anchor for holm closure')
handed_insert = '''BASE_CORE = BASE.copy()

# Close only the two longitudinal holm faces. RIGHT uses local -X; LEFT uses
# the exact mirrored +X faces. The opposite faces stay open.
_ARM_FRONT_SKINS_RIGHT = [
    _arm_front_skin(xc, ARM_Y0, ARM_Y1, -1) for xc in CLAMP_X
]
_ARM_FRONT_SKINS_LEFT = [
    _arm_front_skin(xc, ARM_Y0, ARM_Y1, +1) for xc in CLAMP_X
]
BASE_CORE_RIGHT = BASE_CORE.copy()
BASE_CORE_LEFT = BASE_CORE.copy()
for _q in _ARM_FRONT_SKINS_RIGHT:
    BASE_CORE_RIGHT = BASE_CORE_RIGHT.fuse(_q).removeSplitter()
for _q in _ARM_FRONT_SKINS_LEFT:
    BASE_CORE_LEFT = BASE_CORE_LEFT.fuse(_q).removeSplitter()
if (not BASE_CORE_RIGHT.isValid() or len(BASE_CORE_RIGHT.Solids) != 1 or
        not BASE_CORE_LEFT.isValid() or len(BASE_CORE_LEFT.Solids) != 1):
    raise RuntimeError('Handed front-holm closure broke BASE core topology')
'''
s = s.replace(handed_anchor, handed_insert, 1)

right_core = 'BASE_RIGHT = BASE_CORE.fuse(MOUNT_BACKSTOP_RIGHT).removeSplitter()'
left_core = 'BASE_LEFT = BASE_CORE.fuse(MOUNT_BACKSTOP_LEFT).removeSplitter()'
if right_core not in s or left_core not in s:
    raise SystemExit('Could not retarget handed BASE construction to closed holm cores')
s = s.replace(right_core,
              'BASE_RIGHT = BASE_CORE_RIGHT.fuse(MOUNT_BACKSTOP_RIGHT).removeSplitter()', 1)
s = s.replace(left_core,
              'BASE_LEFT = BASE_CORE_LEFT.fuse(MOUNT_BACKSTOP_LEFT).removeSplitter()', 1)

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
validation = '''# Support-safe arm-profile / handed holm-closure checks.
# Cubic smoothstep derivative max is 1.5; lateral reach is 6.4 mm.
_arm_web_outer = 8.0 + ARM_PROFILE_WEB_T/2.0
_arm_side_reach = ARM_W/2.0 - _arm_web_outer
_arm_max_dx_dz = 1.5*_arm_side_reach/ARM_PROFILE_SPLINE_RISE
_arm_core_probe = make_i_beam_y(0.0, 0.0, 20.0)
_arm_right_skin_probe = _arm_front_skin(0.0, 0.0, 20.0, -1)
_arm_left_skin_probe = _arm_front_skin(0.0, 0.0, 20.0, +1)
_arm_right_probe = _arm_core_probe.fuse(_arm_right_skin_probe).removeSplitter()
_arm_left_probe = _arm_core_probe.fuse(_arm_left_skin_probe).removeSplitter()
_arm_right_skin_fraction = (_arm_right_probe.common(_arm_right_skin_probe).Volume /
                            _arm_right_skin_probe.Volume)
_arm_left_skin_fraction = (_arm_left_probe.common(_arm_left_skin_probe).Volume /
                           _arm_left_skin_probe.Volume)
V['supportfree_arm_profile'] = {
    'architecture': 'symmetric_two_web_core_with_handed_single_face_closure_and_slope_limited_spline_haunches',
    'outer_width_mm': round(_arm_core_probe.BoundBox.XLength, 3),
    'outer_height_mm': round(_arm_core_probe.BoundBox.ZLength, 3),
    'flange_thickness_mm': ARM_PROFILE_FLANGE_T,
    'web_thickness_mm': ARM_PROFILE_WEB_T,
    'web_centers_mm': list(ARM_PROFILE_WEB_CENTERS),
    'side_reach_mm': round(_arm_side_reach, 3),
    'spline_rise_mm': ARM_PROFILE_SPLINE_RISE,
    'visual_radius_intent_mm': ARM_PROFILE_VISUAL_RADIUS,
    'max_dx_dz': round(_arm_max_dx_dz, 6),
    'max_overhang_deg_from_vertical': round(math.degrees(math.atan(_arm_max_dx_dz)), 3),
    'symmetric_top_bottom': True,
    'common_core_x_symmetric': True,
    'handed_front_closure': True,
    'right_closed_face': '-X',
    'left_closed_face': '+X',
    'front_skin_thickness_mm': ARM_PROFILE_FRONT_SKIN_T,
    'right_skin_material_fraction': round(_arm_right_skin_fraction, 6),
    'left_skin_material_fraction': round(_arm_left_skin_fraction, 6),
    'opposite_face_open': True,
    'print_orientation': 'BASE rotated 180deg about X; BOX_SUPPORT_Z on bed',
    'support_policy': 'handed skin is vertical; spline haunches remain <=45deg; no generated support required',
}
if abs(V['supportfree_arm_profile']['outer_width_mm']-ARM_W) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 32 mm outer width')
if abs(V['supportfree_arm_profile']['outer_height_mm']-ARM_H) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 30 mm outer height')
if _arm_max_dx_dz > 1.0 + 1e-9:
    failures.append('Support-free spline exceeds the 45 degree lateral-growth envelope')
if abs(ARM_PROFILE_WEB_CENTERS[0] + ARM_PROFILE_WEB_CENTERS[1]) > 1e-9:
    failures.append('Support-free arm webs are not symmetric about the arm center')
if _arm_right_skin_fraction < 0.999 or _arm_left_skin_fraction < 0.999:
    failures.append('Handed front face of the two longitudinal holms is not fully closed')
if abs(_arm_right_probe.Volume-_arm_left_probe.Volume) > 1e-6:
    failures.append('Handed holm closure probes are not equal-volume X mirrors')
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
if 'BASE_CORE_RIGHT = BASE_CORE.copy()' not in s or 'BASE_CORE_LEFT = BASE_CORE.copy()' not in s:
    raise SystemExit('Handed front-holm closure was not installed')
if 'MOUNT_BACKSTOP_W_X = 50.0' not in s:
    raise SystemExit('Requested 50 mm backstop was not installed')

p.write_text(s, encoding='utf-8')
print('Applied support-safe symmetric arm core with mirrored front-holm closures and 50 mm rear backstop')
