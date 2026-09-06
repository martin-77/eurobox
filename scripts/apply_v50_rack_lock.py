from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Rack-lower closure v2.
#
# The eccentric-cam version forced the rotating cam drum into a pocket cut into
# the moving lower jaw. That made the closure unnecessarily sensitive to the
# exact lower-jaw pose and created a collision-prone three-body interface.
#
# Replace it with a simple positive screw clamp opposite the hinge:
#   - fixed BASE contains an M4 clearance bore and a side-loaded M4 hex-nut trap
#   - moving LOWER contains a short reinforced closure ear with a generous bore
#   - a normal M4 x 20 thumb/knob screw is inserted from below
#
# The screw is tool-less, continuously adjustable and positively retains the
# lower jaw. The full measured rack-tube spread (12.00..12.41 mm) therefore does
# not depend on an eccentric profile. The hinge and every frozen rack datum stay
# unchanged.
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
        + 'RACK_M4_SCREW_LENGTH = 20.0\n',
        1,
    )

# Add the fixed screw guide and nut trap to the final reinforced upper station.
# The nut is inserted laterally, so there is no support-trapped blind cavity and
# no need to print an M4 female thread in PETG. The slot is directed toward the
# outside of each clamp station.
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

    # Standard M4 nut: nominal 7 mm AF / ~3.2 mm thick. The pocket has FDM
    # allowance and is loaded from the OUTSIDE of the station through a short
    # lateral slot. Screw tension reacts against material above the nut.
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

# Rebuild the moving lower jaw with a compact closure ear rather than cutting a
# large cam pocket through the shell. The ear overlaps the shell at Y=5..7 and
# sits 3.5 mm below the fixed bridge in the nominal pose, so the existing
# articulated opening sweep only gains clearance as it rotates downward.
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
# Oversize lower hole gives the M4 screw angular/lateral freedom needed while
# the jaw finds the actual tube diameter before it is tightened.
lower_screw_bore = Part.makeCylinder(
    RACK_M4_LOWER_CLEAR_D/2.0, 7.0,
    App.Vector(0.0, RACK_CLOSURE_Y, RACK_CLOSURE_PAD_Z0-1.0),
    App.Vector(0,0,1))
LOWER = LOWER.cut(lower_screw_bore)
LOWER = LOWER.removeSplitter()'''
s, n = lower_pattern.subn(lower_new, s, count=1)
if n != 1:
    raise SystemExit('Could not locate final rack lower jaw for screw closure')

# Source-level mechanism validation. The threaded closure has far more linear
# adjustment than the 0.41 mm measured tube spread; map the available lower-ear
# gap back to the tube using the two hinge lever arms. Also prove that the screw
# axis is outside the maximum rack tube envelope and that the lower still clears
# the fixed BASE through the existing opening sweep.
anchor = "V['rack_pin_checks'] = []\n"
if anchor not in s:
    raise SystemExit('Could not locate rack validation anchor')
insert = '''closure_arm_mm = RACK_CLOSURE_Y - PIN_Y
tube_arm_mm = 0.0 - PIN_Y
closure_nominal_gap_mm = 0.0 - RACK_CLOSURE_PAD_Z1
closure_mapped_tube_adjustment_mm = closure_nominal_gap_mm * tube_arm_mm / closure_arm_mm
closure_tube_edge_clearance_mm = RACK_CLOSURE_Y - RACK_D/2.0 - RACK_M4_BASE_CLEAR_D/2.0
V['rack_closure'] = {
    'mode': 'positive_M4_thumb_screw_into_captive_hex_nut',
    'screw': 'M4 x 20 thumb screw or M4 x 20 screw with hand knob',
    'nut': 'standard M4 hex nut, side-loaded captive pocket',
    'tool_less': True,
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

'''
s = s.replace(anchor, insert + anchor, 1)

fail_anchor = "for c in V['rack_pin_checks']:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack-pin failure checks')
fail_insert = '''if V['rack_closure']['mapped_tube_adjustment_mm'] < 0.41:
    failures.append('Rack screw closure cannot compensate full measured 12.00..12.41 mm tube range')
if V['rack_closure']['screw_to_tube_edge_clearance_mm'] < 1.0:
    failures.append('Rack M4 closure axis too close to maximum tube envelope')
for c in V['rack_closure_checks']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Rack screw-closure lower collides with fixed base at rotation='+str(c['rotation_deg']))
'''
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

# Keep the assembly representation mechanically truthful: lower remains in the
# nominal closed pose; the standard M4 hardware is declared in validation/BOM
# metadata rather than exported as a fake printable threaded fastener.

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack closure: positive M4 thumb-screw clamp with captive nut')
