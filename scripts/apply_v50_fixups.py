from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# OpenSCAD must resolve the helical CSG before FreeCAD imports it.
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
assert n == 1

# Frozen rack interface datums. These are not design freedoms in v50.
s = s.replace('UPPER_SADDLE_R = 6.31', 'UPPER_SADDLE_R = 6.26', 1)
s = s.replace('PIN_Y = 3.0', 'PIN_Y = -12.0', 1)
s = s.replace('PIN_Z = -10.5', 'PIN_Z = -5.5', 1)

# Rebuild the upper station as a real clevis. The lower jaw is central in X;
# the two fixed pivot lugs sit outside it. This prevents the previous error
# where fixed and moving pivot bosses occupied the same volume.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
replacement = '''def make_upper_station(xc):
    bridge = box(xc-17.0, -8.0, 0.0, 34.0, 22.0, 16.0)
    transition = box(xc-16.0, 10.0, ARM_BOTTOM_Z, 32.0, 20.0, ARM_H)

    # 4 mm fixed clevis lugs outside the 25.2 mm moving lower jaw.
    lug_l = cyl_x(6.0, 4.0, xc-17.0, PIN_Y, PIN_Z)
    lug_r = cyl_x(6.0, 4.0, xc+13.0, PIN_Y, PIN_Z)
    web_l = box(xc-17.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    web_r = box(xc+13.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)
    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)

    s = fuse_all([bridge, transition, lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])
    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return s.removeSplitter()

base_parts ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1

# Central moving lower jaw. Its pivot boss ends at X +/-12.6, leaving 0.4 mm
# axial clearance to the fixed lugs beginning at +/-13.0. In closed position
# it surrounds only the lower tube half; negative rotation releases downward.
old = '''LOWER = box(-12.6, -5.8, -14.0, 25.2, 17.8, 14.0)
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
LOWER = LOWER.removeSplitter()'''
new = '''lower_shell = box(-12.6, -7.0, -14.5, 25.2, 24.0, 14.5)
lower_pivot = cyl_x(5.0, 25.2, -12.6, PIN_Y, PIN_Z)
lower_web = box(-12.6, PIN_Y, -10.5, 25.2, 7.0, 10.5)
LOWER = fuse_all([lower_shell, lower_pivot, lower_web])
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
LOWER = LOWER.removeSplitter()'''
assert old in s
s = s.replace(old, new, 1)

# Keep the moving plate guide structurally connected to both side towers.
old = "box(-70.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 140.0, 14.0, 3.4),"
new = "box(-78.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 156.0, 14.0, 3.4),"
assert old in s
s = s.replace(old, new, 1)

# Clearance tunnel for the moving spindle thrust shoulder.
old = "    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(BOX_EDGE_Y+8.0)+1.0, sx, BOX_EDGE_Y+8.0, SPINDLE_Z))"
new = """    BASE = BASE.cut(cyl_y(SHOULDER_D/2 + 0.30, (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50), sx, BOX_EDGE_Y+7.50, SPINDLE_Z))
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(NUT_Y0-0.50)+1.0, sx, NUT_Y0-0.50, SPINDLE_Z))"""
assert old in s
s = s.replace(old, new, 1)

# Separate calibration support against one diagonal rack stay. Exact form fit
# remains intentionally pending until stay diameter and angle are measured.
old = "PLATE_CLIP = make_c_clip(5.4, 2.45, 1.4, 3.8)\n\nPARTS = {"
new = '''PLATE_CLIP = make_c_clip(5.4, 2.45, 1.4, 3.8)

STAY_SUPPORT = box(-18.0, -10.0, 0.0, 36.0, 20.0, 12.0)
vpts = [App.Vector(-18.5,-8.5,12.5), App.Vector(-18.5,0.0,4.0),
        App.Vector(-18.5,8.5,12.5), App.Vector(-18.5,-8.5,12.5)]
vgroove = Part.Face(Part.makePolygon(vpts)).extrude(App.Vector(37.0,0.0,0.0))
STAY_SUPPORT = STAY_SUPPORT.cut(vgroove)
for xx in (-10.0, 10.0):
    STAY_SUPPORT = STAY_SUPPORT.cut(box(xx-2.0,-5.0,-0.2,4.0,10.0,5.2))
STAY_SUPPORT = STAY_SUPPORT.removeSplitter()

PARTS = {'''
assert old in s
s = s.replace(old, new, 1)
old = "    'eurobox_v50_plate_retainer_clip': PLATE_CLIP,\n}"
new = "    'eurobox_v50_plate_retainer_clip': PLATE_CLIP,\n    'eurobox_v50_rack_stay_support_universal': STAY_SUPPORT,\n}"
assert old in s
s = s.replace(old, new, 1)

# Replace the invalid same-round-tube anti-rotation idea with an explicit
# pending measurement state for the diagonal-stay support.
pattern = re.compile(r"# Anti-rotation contact: nominally free;.*?\n\nRIM =", re.S)
replacement = '''V['anti_rotation'] = {
    'mode': 'separate_diagonal_stay_V_support',
    'part': 'eurobox_v50_rack_stay_support_universal',
    'groove_depth_mm': 8.0,
    'stay_diameter_mm': None,
    'stay_angle_deg': None,
    'contact_validation': 'pending measured diagonal-stay diameter and angle / physical fit'
}

RIM ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1
s = s.replace("if V['anti_rotation'][0]['tube_common_mm3'] > 1e-4:\n    failures.append('Anti-rotation stop collides at nominal position')\nif max(x['tube_common_mm3'] for x in V['anti_rotation'][1:]) < 0.1:\n    failures.append('Anti-rotation stop does not contact rack tube within 5 degrees')\n", "")

# Hard articulated sweep gate. Closed preload is allowed; after opening the
# lower jaw must separate from the real Ø12.42 tube and never hit the base.
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
assert anchor in s
s = s.replace(anchor, sweep + anchor, 1)

fail_anchor = "for c in V['rack_pin_checks']:\n"
fail_insert = '''for c in V['rack_lower_sweep']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Rack lower sweep collides with base at rotation='+str(c['rotation_deg']))
if next(c for c in V['rack_lower_sweep'] if c['rotation_deg'] == -45)['tube_common_mm3'] > 0.05:
    failures.append('Rack lower has not released the Ø12.42 tube by -45 degrees')
'''
assert fail_anchor in s
s = s.replace(fail_anchor, fail_insert + fail_anchor, 1)

# Make frozen-interface violations explicit in the JSON and fail immediately.
anchor = "V = {\n"
assert anchor in s
# Datums themselves are already constants; add semantic validation after V creation.
check_anchor = "TUBE = cyl_x(RACK_R, 240.0, -120.0, 0.0, 0.0)\n"
checks = '''V['frozen_interface_assertions'] = {
    'tube_diameter_12_42': abs(RACK_D-12.42) < 1e-9,
    'pivot_y_minus12': abs(PIN_Y+12.0) < 1e-9,
    'pivot_z_minus5_5': abs(PIN_Z+5.5) < 1e-9,
    'clamp_x_plusminus90': tuple(CLAMP_X) == (-90.0, 90.0),
    'box_edge_y_244_665': abs(BOX_EDGE_Y-244.665) < 1e-9,
    'box_support_z_39_54': abs(BOX_SUPPORT_Z-39.54) < 1e-9,
    'spindle_x_plusminus42': tuple(SPINDLE_X) == (-42.0, 42.0),
    'spindle_z_31': abs(SPINDLE_Z-31.0) < 1e-9,
}
if not all(V['frozen_interface_assertions'].values()):
    raise RuntimeError('Frozen v50 interface datum changed')

'''
assert check_anchor in s
s = s.replace(check_anchor, checks + check_anchor, 1)

s = s.replace(
    "f.write('No diagonal-stay V saddle. Anti-rotation is integrated into both rack-clamp roots.\\n')",
    "f.write('Includes a separate universal V-saddle anti-flop support for the diagonal Massload stay; exact stay fit awaits measurement.\\n')"
)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied deterministic v50 fixups with frozen rack interface and clevis pivot')
