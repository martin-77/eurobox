from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# v55 changed the RH8x2 generator from the old tangential twist to a true
# radial/axial helix.  After z_to_y() that helix advances along +Y with a
# positive rotation about +Y.  The older validation/retainer placement still
# encoded the opposite sign and therefore classified the real mating phase as
# a collision while its supposed wrong phase was the actual free-running one.
old = "q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -360.0*d/THREAD_PITCH)"
new = "q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +360.0*d/THREAD_PITCH)"
if s.count(old) != 1:
    raise SystemExit('Expected exactly one obsolete RH8x2 kinematics rotation sign')
s = s.replace(old, new, 1)

old = "'rotation_deg': -360.0*d/THREAD_PITCH,"
new = "'rotation_deg': +360.0*d/THREAD_PITCH,"
if s.count(old) != 1:
    raise SystemExit('Expected exactly one obsolete RH8x2 kinematics report sign')
s = s.replace(old, new, 1)

# A +0.5 mm axial offset requires +90 degrees to remain in phase for the v55
# helix.  The deliberately wrong witness therefore uses the opposite -90 deg.
old = "wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +90.0)"
new = "wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -90.0)"
if s.count(old) != 1:
    raise SystemExit('Expected exactly one obsolete RH8x2 wrong-phase witness')
s = s.replace(old, new, 1)

# The separate knob-retainer nut is cut with the same v55 helix.  Its assembly
# phase must therefore use the same positive axial/rotational relationship.
old = "cap_phase_deg = -360.0 * (cap_y-cap_thread_start_y) / THREAD_PITCH"
new = "cap_phase_deg = +360.0 * (cap_y-cap_thread_start_y) / THREAD_PITCH"
if s.count(old) != 1:
    raise SystemExit('Expected exactly one obsolete knob-retainer phase sign')
s = s.replace(old, new, 1)

if s == orig:
    raise SystemExit('RH8x2 phase fix made no changes')
for witness in [
    "+360.0*d/THREAD_PITCH",
    "wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -90.0)",
    "cap_phase_deg = +360.0 * (cap_y-cap_thread_start_y) / THREAD_PITCH",
]:
    if witness not in s:
        raise SystemExit('Missing RH8x2 phase-fix witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Applied v55 RH8x2 phase correction: +Y travel = +rotation after z_to_y')
