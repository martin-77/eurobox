from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

pattern = re.compile(
    r"def write_thread_scad\(path, core_r, major_r, pitch, length, root_w, crest_w\):\n.*?\n\n\ndef import_scad_shape",
    re.S,
)
replacement = r'''def _write_true_helical_profile_scad(path, core_r, major_r, pitch, length,
                                     root_w, crest_w, female=False,
                                     overrun=None):
    # True radial/AXIAL trapezoid swept around a helix. The obsolete generator
    # twisted an XY radial/tangential polygon and yielded needle-like notches in
    # longitudinal sections instead of a printable thread tooth.
    if overrun is None:
        overrun = pitch
    span = length + 2.0*overrun
    inner_r = core_r - (0.12 if female else 0.10)
    root_half = root_w / 2.0
    crest_half = crest_w / 2.0
    fn = 96
    steps_per_turn = 48
    if female:
        core_line = f"translate([0,0,-{overrun}]) cylinder(r={core_r},h={span},$fn={fn});"
    else:
        core_line = f"cylinder(r={core_r},h={length},$fn={fn});"
    txt = f"""$fn={fn};
pitch={pitch};
length={length};
core_r={core_r};
major_r={major_r};
inner_r={inner_r};
root_half={root_half};
crest_half={crest_half};
overrun={overrun};
span={span};
a0=-360*overrun/pitch;
a1=360*(length+overrun)/pitch;
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
// Every side is explicitly triangulated. Non-planar quad faces were accepted
// by CGAL but reconstructed as an invalid multi-shell solid by FreeCAD/OCC.
side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
  [4*i+j,4*(i+1)+j,4*(i+1)+((j+1)%4)],
  [4*i+j,4*(i+1)+((j+1)%4),4*i+((j+1)%4)]
]];
start_face=[[0,1,2],[0,2,3]];
e=4*steps;
end_face=[[e+3,e+2,e+1],[e+3,e+1,e]];
module true_helical_tooth(){{
  polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=80);
}}
union(){{
  {core_line}
  true_helical_tooth();
}}
"""
    with open(path, 'w') as f:
        f.write(txt)


def write_thread_scad(path, core_r, major_r, pitch, length, root_w, crest_w):
    _write_true_helical_profile_scad(
        path, core_r, major_r, pitch, length, root_w, crest_w,
        female=False, overrun=pitch)


def write_female_thread_cutter_scad(path, core_r, major_r, pitch, length,
                                    root_w, crest_w, overrun=None):
    _write_true_helical_profile_scad(
        path, core_r, major_r, pitch, length, root_w, crest_w,
        female=True, overrun=pitch if overrun is None else overrun)


def import_scad_shape'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace obsolete tangential thread generator with v54 radial/axial helix')

anchor = "LEAD_PROFILE_CREST_W = 0.30\n"
if anchor not in s:
    raise SystemExit('Could not locate RH8x2 profile constants')
s = s.replace(
    anchor,
    anchor + "LEAD_THREAD_PROFILE_GENERATOR = 'true_radial_axial_trapezoid_polyhedron_v54'\n",
    1,
)

if s == orig:
    raise SystemExit('v54 true RH8x2 pass made no source changes')
if 'write_female_thread_cutter_scad' not in s:
    raise SystemExit('v54 female true-thread helper was not installed')

p.write_text(s, encoding='utf-8')
print('Applied v54 true RH8x2 profiles: triangulated radial/axial trapezoidal helices')
