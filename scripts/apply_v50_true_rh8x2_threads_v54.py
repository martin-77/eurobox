from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Replace the old tangential XY twist with a real radial/AXIAL trapezoid.
# OpenSCAD generates ONLY the closed helical tooth.  Do not ask CGAL to union
# that tooth with a coaxial cylinder and then reconstruct the overlap from STL:
# that was the reason builds 159..161 failed.  The tooth is imported as one
# closed solid and FreeCAD/OCC performs the core fusion natively.
pattern = re.compile(
    r"def write_thread_scad\(path, core_r, major_r, pitch, length, root_w, crest_w\):\n.*?\n\n\ndef import_scad_shape",
    re.S,
)
replacement = r'''def _write_true_helical_ridge_scad(path, core_r, major_r, pitch, length,
                                    root_w, crest_w, overrun=None):
    if overrun is None:
        overrun = pitch
    inner_r = core_r - 0.12
    root_half = root_w / 2.0
    crest_half = crest_w / 2.0
    fn = 96
    steps_per_turn = 48
    a0 = -360.0 * overrun / pitch
    a1 = 360.0 * (length + overrun) / pitch
    txt = f"""$fn={fn};
pitch={pitch};
length={length};
inner_r={inner_r};
major_r={major_r};
root_half={root_half};
crest_half={crest_half};
a0={a0};
a1={a1};
turn_span=(a1-a0)/360;
steps=ceil(turn_span*{steps_per_turn});
function ang(i)=a0+(a1-a0)*i/steps;
function zc(i)=pitch*ang(i)/360;
function pt(r,a,z)=[r*cos(a),r*sin(a),z];
pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
       each [pt(inner_r,a,z-root_half),
             pt(major_r,a,z-crest_half),
             pt(major_r,a,z+crest_half),
             pt(inner_r,a,z+root_half)]];
// Explicit outward-wound triangles.  This is one closed helical solid; the
// smooth core is deliberately NOT part of the OpenSCAD/STL object.
side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
  [4*(i+1)+((j+1)%4),4*(i+1)+j,4*i+j],
  [4*i+((j+1)%4),4*(i+1)+((j+1)%4),4*i+j]
]];
start_face=[[2,1,0],[3,2,0]];
e=4*steps;
end_face=[[e+1,e+2,e+3],[e,e+1,e+3]];
polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=100);
"""
    with open(path, 'w') as f:
        f.write(txt)


def write_thread_scad(path, core_r, major_r, pitch, length, root_w, crest_w):
    _write_true_helical_ridge_scad(
        path, core_r, major_r, pitch, length, root_w, crest_w,
        overrun=pitch)


def write_female_thread_cutter_scad(path, core_r, major_r, pitch, length,
                                    root_w, crest_w, overrun=None):
    _write_true_helical_ridge_scad(
        path, core_r, major_r, pitch, length, root_w, crest_w,
        overrun=pitch if overrun is None else overrun)


def import_scad_shape'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not install true RH8x2 helical-ridge generator')

# This helper is inserted after import_scad_shape(), so the OpenSCAD tooth is
# first reconstructed as ONE closed solid, then clipped and fused to the smooth
# core with OCC.  Male and female cutter use the exact same architecture.
export_anchor = "\n\ndef export_part(name, shape):\n"
if export_anchor not in s:
    raise SystemExit('Could not locate export_part anchor for native thread helper')
helper = r'''

def make_true_thread_solid(path, core_r, major_r, length):
    ridge = import_scad_shape(path)
    clip = Part.makeCylinder(major_r + 0.10, length)
    ridge = ridge.common(clip).removeSplitter()
    if ridge.isNull() or not ridge.isValid() or len(ridge.Solids) != 1:
        raise RuntimeError('RH8x2 helical ridge did not clip to one valid solid: '+path)
    core = Part.makeCylinder(core_r, length)
    q = core.fuse(ridge).removeSplitter()
    if q.isNull() or not q.isValid() or len(q.Solids) != 1:
        raise RuntimeError('RH8x2 native core/ridge fusion failed: '+path)
    return q
'''
s = s.replace(export_anchor, helper + export_anchor, 1)

# The single-source master pass has already rewritten these four constructions.
# Replace only the object reconstruction; write_lead_thread_pair() still writes
# the matched male/female ridge SCADs and therefore keeps pitch/phase/profile in
# one source of truth.
old_main = '''MALE = import_scad_shape(MALE_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + 0.06, LEAD_THREAD_LEN)).removeSplitter()
FEMALE = import_scad_shape(FEMALE_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + LEAD_RADIAL_CLEARANCE + 0.06,
                      NUT_THREAD_LEN)).removeSplitter()'''
new_main = '''MALE = make_true_thread_solid(
    MALE_SCAD, THREAD_CORE_R, THREAD_MAJOR/2.0, LEAD_THREAD_LEN)
FEMALE = make_true_thread_solid(
    FEMALE_SCAD,
    THREAD_CORE_R + LEAD_RADIAL_CLEARANCE,
    THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE,
    NUT_THREAD_LEN)'''
if old_main not in s:
    raise SystemExit('Could not locate RH8x2 main pair reconstruction')
s = s.replace(old_main, new_main, 1)

old_stud = '''MALE_STUD = import_scad_shape(MALE_STUD_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + 0.06, OUTER_STUD_LEN)).removeSplitter()
FEMALE_STUD = import_scad_shape(FEMALE_STUD_SCAD).common(
    Part.makeCylinder(THREAD_MAJOR/2 + LEAD_RADIAL_CLEARANCE + 0.06,
                      OUTER_STUD_LEN)).removeSplitter()'''
new_stud = '''MALE_STUD = make_true_thread_solid(
    MALE_STUD_SCAD, THREAD_CORE_R, THREAD_MAJOR/2.0, OUTER_STUD_LEN)
FEMALE_STUD = make_true_thread_solid(
    FEMALE_STUD_SCAD,
    THREAD_CORE_R + LEAD_RADIAL_CLEARANCE,
    THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE,
    OUTER_STUD_LEN)'''
if old_stud not in s:
    raise SystemExit('Could not locate RH8x2 retainer-stud pair reconstruction')
s = s.replace(old_stud, new_stud, 1)

anchor = "LEAD_PROFILE_CREST_W = 0.30\n"
if anchor not in s:
    raise SystemExit('Could not locate RH8x2 profile constants')
s = s.replace(
    anchor,
    anchor + "LEAD_THREAD_PROFILE_GENERATOR = 'true_radial_axial_OCC_fused_v55'\n",
    1,
)

if s == orig:
    raise SystemExit('v55 true RH8x2 pass made no source changes')
for witness in ['_write_true_helical_ridge_scad', 'make_true_thread_solid',
                "LEAD_THREAD_PROFILE_GENERATOR = 'true_radial_axial_OCC_fused_v55'"]:
    if witness not in s:
        raise SystemExit('Missing v55 RH8x2 witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Applied v55 RH8x2: true axial ridge imported alone and OCC-fused to smooth core')
