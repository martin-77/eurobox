from pathlib import Path

p = Path('scripts/apply_v50_width_cleanup.py')
s = p.read_text(encoding='utf-8')
orig = s

# v55 corrected the true RH8x2 helix before the width-cleanup pass runs.
# The width cleanup still searched for the obsolete pre-v55 signs and therefore
# aborted before CAD generation.  Update that pass itself so it consumes the
# corrected outboard source and emits the physically equivalent inboard source
# after the existing Z180 hardware rotation.
#
# Before Z180: +Y axial travel == +rotation about global +Y.
# After Z180: the screw axis points toward -Y, so +travel along the local screw
# axis is -Y globally and requires -rotation about global +Y.
repls = [
    (
        "old = '''    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -360.0*d/THREAD_PITCH)\n    q.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+d, SPINDLE_Z))'''",
        "old = '''    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +360.0*d/THREAD_PITCH)\n    q.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+d, SPINDLE_Z))'''",
    ),
    (
        "new = '''    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +360.0*d/THREAD_PITCH)\n    q.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y-d, SPINDLE_Z))'''",
        "new = '''    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -360.0*d/THREAD_PITCH)\n    q.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y-d, SPINDLE_Z))'''",
    ),
    (
        "s = s.replace(\"'rotation_deg': -360.0*d/THREAD_PITCH,\",\n              \"'rotation_deg': +360.0*d/THREAD_PITCH,\", 1)",
        "s = s.replace(\"'rotation_deg': +360.0*d/THREAD_PITCH,\",\n              \"'rotation_deg': -360.0*d/THREAD_PITCH,\", 1)",
    ),
    (
        "'''wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +90.0)\nwrong.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+0.5, SPINDLE_Z))''',\n    '''wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -90.0)\nwrong.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y-0.5, SPINDLE_Z))''', 1)",
        "'''wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -90.0)\nwrong.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+0.5, SPINDLE_Z))''',\n    '''wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +90.0)\nwrong.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y-0.5, SPINDLE_Z))''', 1)",
    ),
    (
        "    rot = +360.0*travel_mm/THREAD_PITCH\n",
        "    rot = -360.0*travel_mm/THREAD_PITCH\n",
    ),
]

for old, new in repls:
    if s.count(old) != 1:
        raise SystemExit('Width-cleanup phase compatibility anchor missing or ambiguous: '+old[:80])
    s = s.replace(old, new, 1)

if s == orig:
    raise SystemExit('Width-cleanup phase compatibility made no changes')

for witness in [
    "q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -360.0*d/THREAD_PITCH)",
    "'rotation_deg': -360.0*d/THREAD_PITCH,",
    "wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +90.0)",
    "rot = -360.0*travel_mm/THREAD_PITCH",
]:
    if witness not in s:
        raise SystemExit('Missing corrected inboard phase witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Patched width cleanup for v55 phase input and correct post-Z180 inboard screw kinematics')
