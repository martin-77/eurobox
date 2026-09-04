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

# 2) The upper guide bar had a deliberate 0.4 mm guide clearance in X but
# that also disconnected the bar from both side towers. Extend the bar over
# the towers; Z clearance above the moving plate remains unchanged.
old = "box(-70.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 140.0, 14.0, 3.4),"
new = "box(-78.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 156.0, 14.0, 3.4),"
assert old in s, 'upper guide bar source not found'
s = s.replace(old, new, 1)

# 3) The Ø11 spindle thrust shoulder travels with the plate. The original
# Ø8.9 passage only cleared the threaded shank and clipped the shoulder at
# 4.0/4.5 mm opening. Give the shoulder its own short clearance tunnel up to
# just before the fixed lead-nut cartridge, then keep the smaller shank bore.
old = "    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(BOX_EDGE_Y+8.0)+1.0, sx, BOX_EDGE_Y+8.0, SPINDLE_Z))"
new = """    BASE = BASE.cut(cyl_y(SHOULDER_D/2 + 0.30, (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50), sx, BOX_EDGE_Y+7.50, SPINDLE_Z))
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(NUT_Y0-0.50)+1.0, sx, NUT_Y0-0.50, SPINDLE_Z))"""
assert old in s, 'spindle passage source not found'
s = s.replace(old, new, 1)

# 4) A stop referenced only to the same circular tube cannot be proven as an
# anti-rotation stop: rotation about that tube preserves all radial distances.
# Keep the integrated inboard drop geometry requested for the real rack edge,
# but report only the measured tube clearance until a non-coaxial rack-edge
# datum is measured. Do not manufacture a fake hard pass from a photo.
pattern = re.compile(r"# Anti-rotation contact: nominally free;.*?\n\nRIM =", re.S)
replacement = '''# Integrated inboard drop-stop.  It is intentionally NOT validated against
# the same round tube as an anti-rotation contact: that would be a meaningless
# rotationally symmetric test.  Exact contact with the non-coaxial rack edge
# remains a physical-fit datum; all geometry relative to the measured tube is
# still checked here.
V['anti_rotation'] = {
    'mode': 'integrated_inboard_drop_stop',
    'tube_inner_tangent_y_mm': round(-RACK_R, 3),
    'stop_face_y_mm': STOP_FACE_Y,
    'nominal_clearance_from_round_tube_mm': round((-RACK_R) - STOP_FACE_Y, 3),
    'stop_z_min_mm': STOP_Z0,
    'stop_z_max_mm': STOP_Z1,
    'stop_x_width_mm': STOP_X_W,
    'rack_edge_contact_validation': 'pending non-coaxial rack-edge datum / physical fit; not inferred from photo'
}

RIM ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'anti-rotation validation block not found'

s = s.replace("if V['anti_rotation'][0]['tube_common_mm3'] > 1e-4:\n    failures.append('Anti-rotation stop collides at nominal position')\nif max(x['tube_common_mm3'] for x in V['anti_rotation'][1:]) < 0.1:\n    failures.append('Anti-rotation stop does not contact rack tube within 5 degrees')\n", "")

# 5) Do not build the final printable spindle by fusing an OCC primitive to a
# mesh-derived helical BRep.  The BRep itself validates, but re-tessellation at
# the polygonal/analytic interfaces can produce a non-manifold STL.  Build the
# COMPLETE prototype spindle as one OpenSCAD CSG solid, then bring that one
# resolved solid back into FreeCAD.  The thread ridge starts at the exact same
# Y datum and phase as before; only the core cylinders overlap neighbours by
# 0.10 mm to make the CSG union unambiguous.
pattern = re.compile(r"SPINDLE = fuse_all\(\[.*?\n\]\)\.removeSplitter\(\)\n\nKNOB =", re.S)
replacement = '''SPINDLE_SCAD = os.path.join(OUT, 'eurobox_v50_lead_screw_print_source.scad')
spindle_scad = f'''$fn=48;
module ridge(core_r, major_r, pitch, length, root_w, crest_w){{
  linear_extrude(height=length,twist=360*length/pitch,slices=ceil(length/pitch*18),convexity=40)
    polygon(points=[[core_r-0.08,-root_w/2],[major_r,-crest_w/2],[major_r,crest_w/2],[core_r-0.08,root_w/2]]);
}}
module male_thread(length){{
  union(){{
    translate([0,0,-0.10]) cylinder(r={THREAD_CORE_R},h=length+0.20);
    ridge({THREAD_CORE_R},{THREAD_MAJOR/2},{THREAD_PITCH},length,0.58,0.24);
  }}
}}
union(){{
  cylinder(r=3.0,h=0.5);
  translate([0,0,0.35]) cylinder(r=2.5,h=1.55);
  translate([0,0,1.75]) cylinder(r=3.0,h={SPINDLE_LOCAL_JOURNAL-1.65});
  translate([0,0,{SPINDLE_LOCAL_JOURNAL-0.10}]) cylinder(r={SHOULDER_D/2},h={SPINDLE_LOCAL_SHOULDER+0.20});
  translate([0,0,{SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER}]) male_thread({LEAD_THREAD_LEN});
  translate([0,0,{SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN-0.10}])
    rotate([0,0,30]) cylinder(r={10.0/math.sqrt(3.0)},h={HEX_LEN+0.20},$fn=6);
  translate([0,0,{SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN+HEX_LEN}]) male_thread({OUTER_STUD_LEN});
}}
'''
with open(SPINDLE_SCAD, 'w') as f:
    f.write(spindle_scad)
SPINDLE = z_to_y(import_scad_shape(SPINDLE_SCAD), 0, 0, 0).removeSplitter()

KNOB ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'spindle construction block not found'

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied deterministic v50 fixups to scripts/build_v50.py')
