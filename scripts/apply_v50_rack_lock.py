from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Positive secondary lock for the articulated rack lower jaw.
# The existing pin remains the hinge. A second transverse pin on the opposite
# side of the tube prevents the lower jaw from falling/opening under gravity or
# vibration. Both pins use the same printable pin + retaining clip geometry.
# All rack/tube/pivot datums remain unchanged.
if 'LOCK_Y = 11.0' not in s:
    s = s.replace('PIN_Z = -5.5\n', 'PIN_Z = -5.5\nLOCK_Y = 11.0\nLOCK_Z = -6.5\n', 1)

# Add fixed outer clevis lugs for the lock pin to the final upper station.
old = '''    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n\n    s = fuse_all([bridge, root_beam,\n                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])\n    # The real rack-tube envelope is cut only after all root solids are fused.\n    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))\n    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))\n    return s.removeSplitter()'''
new = '''    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)\n\n    # Second clevis opposite the hinge. The lower jaw sits between these lugs.\n    # A removable transverse pin positively locks the jaw in the closed state.\n    lock_l = cyl_x(5.0, 4.0, xc-17.0, LOCK_Y, LOCK_Z)\n    lock_r = cyl_x(5.0, 4.0, xc+13.0, LOCK_Y, LOCK_Z)\n    lock_web_l = box(xc-17.0, 6.0, -6.5, 4.0, 8.0, 7.0)\n    lock_web_r = box(xc+13.0, 6.0, -6.5, 4.0, 8.0, 7.0)\n\n    s = fuse_all([bridge, root_beam,\n                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r,\n                  lock_l, lock_r, lock_web_l, lock_web_r])\n    # The real rack-tube envelope is cut only after all root solids are fused.\n    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))\n    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))\n    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, LOCK_Y, LOCK_Z))\n    return s.removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final upper rack station for lock fixup')
s = s.replace(old, new, 1)

# Add the matching lock-pin hole through the central lower jaw. The jaw already
# has enough material at this location; no bulky extra root is necessary.
old = '''LOWER = fuse_all([lower_shell, lower_pivot, lower_web])\nLOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))\nLOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))\nLOWER = LOWER.removeSplitter()'''
new = '''LOWER = fuse_all([lower_shell, lower_pivot, lower_web])\nLOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))\nLOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))\nLOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, LOCK_Y, LOCK_Z))\nLOWER = LOWER.removeSplitter()'''
if old not in s:
    raise SystemExit('Could not locate final rack lower jaw for lock fixup')
s = s.replace(old, new, 1)

# Record and hard-check the lock. At 0 degrees the lock pin must pass freely
# through base + lower. With the pin held fixed, a small attempted opening must
# run the lower material into the pin, proving that gravity cannot simply rotate
# the jaw open while locked.
anchor = "V['rack_pin_checks'] = []\n"
if anchor not in s:
    raise SystemExit('Could not locate rack pin validation anchor')
insert = '''V['rack_lock'] = {\n    'mode': 'positive_secondary_transverse_pin',\n    'hinge_y_mm': PIN_Y,\n    'hinge_z_mm': PIN_Z,\n    'lock_y_mm': LOCK_Y,\n    'lock_z_mm': LOCK_Z,\n    'pin_diameter_mm': PIN_D,\n    'hole_diameter_mm': PIN_HOLE_D,\n    'same_printed_pin_as_hinge': True,\n    'tool_less': True,\n}\nV['rack_lock_checks'] = []\nfor xc in CLAMP_X:\n    lp = PIN.copy(); lp.translate(App.Vector(xc, LOCK_Y, LOCK_Z))\n    lo0 = LOWER.copy(); lo0.translate(App.Vector(xc, 0, 0))\n    lo5 = LOWER.copy()\n    lo5.rotate(App.Vector(0, PIN_Y, PIN_Z), App.Vector(1,0,0), -5.0)\n    lo5.translate(App.Vector(xc, 0, 0))\n    V['rack_lock_checks'].append({\n        'x_mm': xc,\n        'closed_base_common_mm3': round(BASE.common(lp).Volume, 6),\n        'closed_lower_common_mm3': round(lo0.common(lp).Volume, 6),\n        'attempted_open_minus5_lower_pin_common_mm3': round(lo5.common(lp).Volume, 6),\n    })\n\n'''
s = s.replace(anchor, insert + anchor, 1)

fail_anchor = "for c in V['rack_pin_checks']:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack-pin failure checks')
fail_insert = '''for c in V['rack_lock_checks']:\n    if c['closed_base_common_mm3'] > 1e-4:\n        failures.append('Rack lock pin collides with fixed upper at closed position')\n    if c['closed_lower_common_mm3'] > 1e-4:\n        failures.append('Rack lock pin collides with lower at closed position')\n    if c['attempted_open_minus5_lower_pin_common_mm3'] < 0.05:\n        failures.append('Rack lock pin does not positively block a -5 degree opening attempt')\n'''
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack lock: secondary transverse positive-lock pin')
