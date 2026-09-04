from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# 1) OpenSCAD must resolve the CSG union. FreeCAD importCSG exposed the
# cylinder and twisted extrusion separately and effectively discarded the
# thread ridge. Compile to STL with OpenSCAD first, then convert the closed
# mesh to a BRep solid for the FreeCAD assembly/STEP export.
s = s.replace('import os, math, json, shutil', 'import os, math, json, shutil, subprocess')
s = s.replace('$fn=72;', '$fn=48;').replace('*28),convexity=30)', '*18),convexity=30)')

pattern = re.compile(r"def import_scad_shape\(path\):\n.*?\n\ndef export_part", re.S)
replacement = '''def import_scad_shape(path):
    stl = os.path.splitext(path)[0] + '_compiled.stl'
    subprocess.run(['openscad', '-o', stl, path], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = Mesh.Mesh(stl)
    sh = Part.Shape()
    sh.makeShapeFromMesh(m.Topology, 0.035)
    if sh.ShapeType == 'Shell':
        sh = Part.makeSolid(sh)
    elif sh.ShapeType == 'Compound':
        solids = []
        for shell in sh.Shells:
            try:
                q = Part.makeSolid(shell)
                if q.isValid() and q.Volume > 0:
                    solids.append(q)
            except Exception:
                pass
        if not solids:
            raise RuntimeError('No solid could be reconstructed from '+stl)
        sh = solids[0]
        for q in solids[1:]:
            sh = sh.fuse(q)
    sh = sh.removeSplitter()
    if sh.isNull() or not sh.isValid() or len(sh.Solids) != 1:
        raise RuntimeError('Compiled thread is not one valid solid: '+path)
    return sh


def export_part'''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'import_scad_shape block not found exactly once'

# 2) Hard rack fit and proven pivot datum.
# Actual tube Ø12.42, rigid saddle Ø12.52 => 0.05 mm radial clearance.
# The Y=-12/Z=-5.5 pivot is the previously verified geometry that opens away
# from the tube in negative X rotation; the temporary +3/-10.5 clean-sheet
# pivot failed the articulated sweep and is discarded.
s = s.replace('UPPER_SADDLE_R = 6.31', 'UPPER_SADDLE_R = 6.26', 1)
s = s.replace('PIN_Y = 3.0', 'PIN_Y = -12.0', 1)
s = s.replace('PIN_Z = -10.5', 'PIN_Z = -5.5', 1)

# 3) Rebuild the whole upper rack station around the correct pivot instead of
# merely moving a hole. The pivot boss is a real load path into the bridge and
# arm transition. There is no same-tube anti-rotation stop.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
replacement = '''def make_upper_station(xc):
    # Upper saddle bridge. It reaches slightly behind tube centre so the
    # separate pivot lug can merge into it without a thin diagonal neck.
    bridge = box(xc-17.0, -8.0, 0.0, 34.0, 22.0, 16.0)
    pivot_boss = cyl_x(6.2, 34.0, xc-17.0, PIN_Y, PIN_Z)
    pivot_web = box(xc-17.0, PIN_Y, PIN_Z, 34.0, 7.0, 7.5)
    transition = box(xc-16.0, 10.0, ARM_BOTTOM_Z, 32.0, 20.0, ARM_H)
    s = fuse_all([bridge, pivot_boss, pivot_web, transition])
    # Real rack-tube saddle and real through pivot hole.
    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return s.removeSplitter()

base_parts ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'upper station block not found exactly once'

# 4) Rebuild rack_lower around the same proven pivot. The compact lower shell
# occupies the lower half of the tube, and a large pivot boss plus short web
# connect it to Y=-12/Z=-5.5. Negative rotation moves the saddle away/down
# from the fixed tube; CI verifies the full 0..-75 degree sweep.
old = '''LOWER = box(-12.6, -5.8, -14.0, 25.2, 17.8, 14.0)
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
LOWER = LOWER.removeSplitter()'''
new = '''lower_shell = box(-17.0, -7.0, -14.5, 34.0, 24.0, 14.5)
lower_pivot = cyl_x(6.0, 34.0, -17.0, PIN_Y, PIN_Z)
lower_web = box(-17.0, PIN_Y, -10.5, 34.0, 7.0, 10.5)
LOWER = fuse_all([lower_shell, lower_pivot, lower_web])
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 36.0, -18.0, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 36.0, -18.0, PIN_Y, PIN_Z))
LOWER = LOWER.removeSplitter()'''
assert old in s, 'old rack lower block not found'
s = s.replace(old, new, 1)

# 5) The upper guide bar had a deliberate 0.4 mm guide clearance in X but
# that also disconnected the bar from both side towers. Extend it over the
# towers; Z clearance above the moving plate remains unchanged.
old = "box(-70.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 140.0, 14.0, 3.4),"
new = "box(-78.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 156.0, 14.0, 3.4),"
assert old in s, 'upper guide bar source not found'
s = s.replace(old, new, 1)

# 6) The Ø11 spindle thrust shoulder travels with the plate. Give it a short
# clearance tunnel up to just before the fixed lead-nut cartridge, then keep
# the smaller shank bore through the fixed outer cage.
old = "    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(BOX_EDGE_Y+8.0)+1.0, sx, BOX_EDGE_Y+8.0, SPINDLE_Z))"
new = """    BASE = BASE.cut(cyl_y(SHOULDER_D/2 + 0.30, (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50), sx, BOX_EDGE_Y+7.50, SPINDLE_Z))
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(NUT_Y0-0.50)+1.0, sx, NUT_Y0-0.50, SPINDLE_Z))"""
assert old in s, 'spindle passage source not found'
s = s.replace(old, new, 1)

# 7) Add a genuine separate anti-flop calibration part for the diagonal
# Massload 3-leg stay. Stay diameter and angle are not measured yet, so this
# is deliberately a V saddle with two zip-tie windows rather than a claimed
# form-fit clamp.
old = "PLATE_CLIP = make_c_clip(5.4, 2.45, 1.4, 3.8)\n\nPARTS = {"
new = '''PLATE_CLIP = make_c_clip(5.4, 2.45, 1.4, 3.8)

# Universal diagonal-stay anti-flop support (calibration part).
# Body X=36, Y=20, Z=12. An 8 mm-deep 90° V groove runs along X.
STAY_SUPPORT = box(-18.0, -10.0, 0.0, 36.0, 20.0, 12.0)
vpts = [
    App.Vector(-18.5, -8.5, 12.5),
    App.Vector(-18.5,  0.0,  4.0),
    App.Vector(-18.5,  8.5, 12.5),
    App.Vector(-18.5, -8.5, 12.5),
]
vgroove = Part.Face(Part.makePolygon(vpts)).extrude(App.Vector(37.0, 0.0, 0.0))
STAY_SUPPORT = STAY_SUPPORT.cut(vgroove)
for xx in (-10.0, 10.0):
    STAY_SUPPORT = STAY_SUPPORT.cut(box(xx-2.0, -5.0, -0.2, 4.0, 10.0, 5.2))
STAY_SUPPORT = STAY_SUPPORT.removeSplitter()

PARTS = {'''
assert old in s, 'plate clip / PARTS anchor not found'
s = s.replace(old, new, 1)

old = "    'eurobox_v50_plate_retainer_clip': PLATE_CLIP,\n}"
new = "    'eurobox_v50_plate_retainer_clip': PLATE_CLIP,\n    'eurobox_v50_rack_stay_support_universal': STAY_SUPPORT,\n}"
assert old in s, 'PARTS tail not found'
s = s.replace(old, new, 1)

# 8) Replace the invalid same-tube anti-rotation test with an honest state
# report for the separate diagonal-stay support.
pattern = re.compile(r"# Anti-rotation contact: nominally free;.*?\n\nRIM =", re.S)
replacement = '''# Anti-flop support is referenced to a diagonal Massload rack stay, not to
# the coaxial upper tube. Exact stay contact stays pending until stay Ø/angle
# are measured. The printable calibration support itself is fully exported.
V['anti_rotation'] = {
    'mode': 'separate_diagonal_stay_V_support',
    'part': 'eurobox_v50_rack_stay_support_universal',
    'groove_depth_mm': 8.0,
    'stay_diameter_mm': None,
    'stay_angle_deg': None,
    'contact_validation': 'pending measured diagonal-stay diameter and angle / physical fit'
}

RIM ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'anti-rotation validation block not found'
s = s.replace("if V['anti_rotation'][0]['tube_common_mm3'] > 1e-4:\n    failures.append('Anti-rotation stop collides at nominal position')\nif max(x['tube_common_mm3'] for x in V['anti_rotation'][1:]) < 0.1:\n    failures.append('Anti-rotation stop does not contact rack tube within 5 degrees')\n", "")

# 9) Add actual articulated lower-jaw sweep around the corrected pivot.
anchor = "V['rack_pin_checks'] = []\n"
sweep = '''V['rack_lower_sweep'] = []
for deg in [0, -15, -30, -45, -60, -75]:
    lo = LOWER.copy()
    lo.rotate(App.Vector(0, PIN_Y, PIN_Z), App.Vector(1,0,0), deg)
    lo.translate(App.Vector(CLAMP_X[0], 0, 0))
    V['rack_lower_sweep'].append({
        'rotation_deg': deg,
        'base_common_mm3': round(BASE.common(lo).Volume, 6),
        'tube_common_mm3': round(TUBE.common(lo).Volume, 6),
    })

'''
assert anchor in s, 'rack pin validation anchor not found'
s = s.replace(anchor, sweep + anchor, 1)

fail_anchor = "for c in V['rack_pin_checks']:\n"
fail_insert = '''for c in V['rack_lower_sweep']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Rack lower sweep collides with base at rotation='+str(c['rotation_deg']))
if next(c for c in V['rack_lower_sweep'] if c['rotation_deg'] == -45)['tube_common_mm3'] > 0.05:
    failures.append('Rack lower has not released the Ø12.42 tube by -45 degrees')
'''
assert fail_anchor in s, 'rack pin failure anchor not found'
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

# 10) Documentation emitted with the artifact must match the actual design.
s = s.replace(
    "f.write('No diagonal-stay V saddle. Anti-rotation is integrated into both rack-clamp roots.\\n')",
    "f.write('Includes a separate universal V-saddle anti-flop support for the diagonal Massload stay; exact stay fit awaits measurement.\\n')"
)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied deterministic v50 fixups to scripts/build_v50.py')
