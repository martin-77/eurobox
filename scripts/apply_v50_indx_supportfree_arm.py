from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# CORE One L+ INDX / FDM printability refinement.
# Keep the proven two-web arm architecture, but restore an open H/I-style
# section instead of the later closed tapered solid. The side flange overhangs
# are carried by symmetric cubic Hermite haunches. The curve is deliberately
# slope-limited: with the final 6.4 mm lateral reach and 10.0 mm vertical rise,
# max |dx/dz| = 1.5*6.4/10 = 0.96, i.e. < 1.0 (45 deg limit).
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
    # under the flange; the side recess remains open to air.
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
'''
s = pat.sub(rep.rstrip(), s, count=1)

# Shorten the rear mounting stop from 40 to 35 mm. This keeps its start at
# +150 mm but ends at +185 mm, giving the 298 mm CORE One L+ INDX X envelope
# materially more margin than the former ~297 mm overall BASE length.
if 'MOUNT_BACKSTOP_W_X = 40.0' not in s:
    raise SystemExit('Could not locate 40 mm mounting-backstop width')
s = s.replace('MOUNT_BACKSTOP_W_X = 40.0', 'MOUNT_BACKSTOP_W_X = 35.0', 1)

# Add hard source-level checks immediately before the existing export loop.
anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')
validation = '''# Support-safe symmetric arm-profile / INDX checks.
# Cubic smoothstep derivative max is 1.5; lateral reach is 6.4 mm.
_arm_web_outer = 8.0 + ARM_PROFILE_WEB_T/2.0
_arm_side_reach = ARM_W/2.0 - _arm_web_outer
_arm_max_dx_dz = 1.5*_arm_side_reach/ARM_PROFILE_SPLINE_RISE
_arm_probe = make_i_beam_y(0.0, 0.0, 20.0)
V['supportfree_arm_profile'] = {
    'architecture': 'symmetric_two_web_open_profile_with_slope_limited_spline_haunches',
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
    'print_orientation': 'BASE rotated 180deg about X; BOX_SUPPORT_Z on bed',
    'support_policy': 'no generated support required for side flange haunches when max_dx_dz<=1.0',
}
if abs(V['supportfree_arm_profile']['outer_width_mm']-ARM_W) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 32 mm outer width')
if abs(V['supportfree_arm_profile']['outer_height_mm']-ARM_H) > 0.02:
    failures.append('Support-free arm profile no longer has the frozen 30 mm outer height')
if _arm_max_dx_dz > 1.0 + 1e-9:
    failures.append('Support-free spline exceeds the 45 degree lateral-growth envelope')
if abs(ARM_PROFILE_WEB_CENTERS[0] + ARM_PROFILE_WEB_CENTERS[1]) > 1e-9:
    failures.append('Support-free arm webs are not symmetric about the arm center')
if abs(MOUNT_BACKSTOP_W_X-35.0) > 1e-9:
    failures.append('INDX rear mounting backstop is not the intended 35 mm width')
if abs((MOUNT_BACKSTOP_X0+MOUNT_BACKSTOP_W_X)-185.0) > 0.02:
    failures.append('INDX rear mounting backstop does not end at local X=185 mm')

'''
s = s.replace(anchor, validation + anchor, 1)

if s == orig:
    raise SystemExit('INDX support-free arm patch made no changes')
if 'ARM_PROFILE_MAX_DX_DZ = 0.96' not in s:
    raise SystemExit('Support-free spline constants were not installed')
if 'MOUNT_BACKSTOP_W_X = 35.0' not in s:
    raise SystemExit('INDX backstop shortening was not installed')

p.write_text(s, encoding='utf-8')
print('Applied symmetric support-safe spline arm profile (max dx/dz 0.96) and 35 mm INDX backstop')
