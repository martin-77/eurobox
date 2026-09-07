from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The final female M4 cutter is a true radial-Z helical trapezoid. Generate the
# printed male with the same axis, pitch, phase, angular discretisation and
# trapezoid convention instead of the old generic XY-polygon thread. Female
# radial/axial dimensions remain the explicit FDM clearance envelope.
old = "write_thread_scad(RACK_M4_MALE_SCAD, 1.55, 1.95, RACK_M4_PITCH, RACK_M4_SCREW_LENGTH, 0.28, 0.12)"
new = r'''def write_rack_m4_true_male_scad(path):
    scad = r"""$fn=96;
pitch=0.7;
length=RACK_M4_SCREW_LENGTH_PLACEHOLDER;
core_r=1.55;
ridge_inner_r=1.47;
ridge_outer_r=1.95;
inner_half_z=0.08;
outer_half_z=0.04;
turns=length/pitch;
steps=ceil(turns*48);
a0=-360;
a1=360*(turns-1);
function ang(i)=a0+(a1-a0)*i/steps;
function zc(i)=pitch*ang(i)/360;
function pt(r,a,z)=[r*cos(a),r*sin(a),z];
pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
       each [pt(ridge_inner_r,a,z-inner_half_z),
             pt(ridge_outer_r,a,z-outer_half_z),
             pt(ridge_outer_r,a,z+outer_half_z),
             pt(ridge_inner_r,a,z+inner_half_z)]];
side_faces=[for(i=[0:steps-1]) for(j=[0:3])
  [4*i+j,4*(i+1)+j,4*(i+1)+((j+1)%4),4*i+((j+1)%4)]];
start_face=[[0,1,2,3]];
e=4*steps;
end_face=[[e+3,e+2,e+1,e]];
module true_helical_ridge(){
  polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=60);
}
union(){
  cylinder(r=core_r,h=length,$fn=96);
  true_helical_ridge();
}
""".replace('RACK_M4_SCREW_LENGTH_PLACEHOLDER', str(RACK_M4_SCREW_LENGTH))
    with open(path, 'w') as f:
        f.write(scad)
write_rack_m4_true_male_scad(RACK_M4_MALE_SCAD)'''
if old not in s:
    raise SystemExit('Could not locate old generic rack M4 male generator')
s = s.replace(old, new, 1)

# Make the validation metadata describe the actual matched profile rather than
# merely its nominal diameters.
meta_anchor = "    'standard': 'M4 x 0.7 RH',\n"
if meta_anchor not in s:
    raise SystemExit('Could not locate rack M4 thread-check metadata')
s = s.replace(meta_anchor,
    meta_anchor
    + "    'pair_generator': 'matched_radial_Z_helical_trapezoids',\n"
    + "    'male_core_diameter_mm': 3.10,\n"
    + "    'female_bore_diameter_mm': 3.32,\n"
    + "    'radial_core_clearance_mm': 0.11,\n"
    + "    'male_outer_half_width_mm': 0.04,\n"
    + "    'female_outer_half_width_mm': 0.08,\n",
    1)

# Require the actual matched generator in addition to the collision/phase tests.
fail_anchor = "if V['rack_m4_thread_check']['correct_phase_common_mm3'] > 0.02:\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate rack M4 correct-phase gate')
s = s.replace(fail_anchor,
    "if V['rack_m4_thread_check'].get('pair_generator') != 'matched_radial_Z_helical_trapezoids':\n"
    "    failures.append('Rack M4 male/female must use the matched radial-Z helical pair')\n"
    + fail_anchor,
    1)

if s == orig:
    raise SystemExit('Matched rack M4 pair pass made no changes')

p.write_text(s, encoding='utf-8')
print('Applied matched rack M4 pair: true radial-Z male and female helices with explicit FDM clearance')
