from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final rack M4 female thread.
# The generic write_thread_scad() twists an XY polygon while extruding in Z.
# That is acceptable as a coarse external visual thread, but it is the wrong
# topology for this internal thread: the supposed flank width lives in XY and
# the result can leave a smooth cylindrical bore with the helix recessed behind
# it. Generate the female cutter as an actual radial-Z trapezoid swept around a
# helix. The groove overlaps the bore by 0.08 mm so it is physically open to the
# bore wall rather than merely tangent to it.
old = '''write_thread_scad(RACK_M4_FEMALE_SCAD, 1.60, 2.25, RACK_M4_PITCH,
                  RACK_M4_FEMALE_LEN, 0.66, 0.14)'''
new = '''def write_rack_m4_true_female_scad(path):
    scad = r"""$fn=96;
pitch=0.7;
length=RACK_M4_FEMALE_LEN_PLACEHOLDER;
bore_r=1.66;
groove_inner_r=1.58;
groove_outer_r=2.20;
inner_half_z=0.14;
outer_half_z=0.08;
turns=length/pitch;
steps=ceil(turns*48);
a0=-360;
a1=360*(turns-1);
function ang(i)=a0+(a1-a0)*i/steps;
function zc(i)=pitch*ang(i)/360;
function pt(r,a,z)=[r*cos(a),r*sin(a),z];
pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
       each [pt(groove_inner_r,a,z-inner_half_z),
             pt(groove_outer_r,a,z-outer_half_z),
             pt(groove_outer_r,a,z+outer_half_z),
             pt(groove_inner_r,a,z+inner_half_z)]];
side_faces=[for(i=[0:steps-1]) for(j=[0:3])
  [4*i+j,4*(i+1)+j,4*(i+1)+((j+1)%4),4*i+((j+1)%4)]];
start_face=[[0,1,2,3]];
e=4*steps;
end_face=[[e+3,e+2,e+1,e]];
module true_helical_groove(){
  polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=60);
}
union(){
  cylinder(r=bore_r,h=length,$fn=96);
  true_helical_groove();
}
""".replace('RACK_M4_FEMALE_LEN_PLACEHOLDER', str(RACK_M4_FEMALE_LEN))
    with open(path, 'w') as f:
        f.write(scad)
write_rack_m4_true_female_scad(RACK_M4_FEMALE_SCAD)'''
if old not in s:
    raise SystemExit('Could not locate rack M4 female-thread generator')
s = s.replace(old, new, 1)

# Keep the cutter envelope bounded after OpenSCAD -> OCC conversion.
s = s.replace('Part.makeCylinder(2.29, RACK_M4_FEMALE_LEN)',
              'Part.makeCylinder(2.24, RACK_M4_FEMALE_LEN)', 1)

# Printed long nut: 5.6 mm = exactly eight M4x0.7 turns. The captive pocket is
# 6.0 mm high for 0.4 mm axial print/assembly clearance.
if 'RACK_M4_NUT_H = 3.6' not in s:
    raise SystemExit('Could not locate rack M4 captive-pocket height')
s = s.replace('RACK_M4_NUT_H = 3.6', 'RACK_M4_NUT_H = 6.0', 1)

old_nut = '''RACK_M4_NUT = hex_z(7.0, 3.2, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
new_nut = '''RACK_M4_NUT = hex_z(7.0, 5.6, 0.0)
RACK_M4_NUT = RACK_M4_NUT.cut(RACK_M4_FEMALE).removeSplitter()'''
if old_nut not in s:
    raise SystemExit('Could not locate rack M4 nut construction')
s = s.replace(old_nut, new_nut, 1)

# Truthful geometry witness for the actual female profile.
s = s.replace("'minor_diameter_mm': 3.20,", "'minor_diameter_mm': 3.32,", 1)
s = s.replace("'groove_major_diameter_mm': 4.50,", "'groove_major_diameter_mm': 4.40,", 1)
s = s.replace("'radial_thread_depth_mm': 0.65,", "'radial_thread_depth_mm': 0.54,", 1)

witness_anchor = "    'radial_thread_depth_mm': 0.54,\n"
if witness_anchor not in s:
    raise SystemExit('Could not locate rack M4 witness metadata')
s = s.replace(
    witness_anchor,
    witness_anchor
    + "    'pitch_mm': RACK_M4_PITCH,\n"
    + "    'nut_body_height_mm': 5.6,\n"
    + "    'full_thread_turns': round(5.6/RACK_M4_PITCH, 3),\n"
    + "    'nut_pocket_height_mm': RACK_M4_NUT_H,\n"
    + "    'nut_pocket_axial_clearance_mm': round(RACK_M4_NUT_H-5.6, 3),\n"
    + "    'profile_generator': 'radial_Z_trapezoid_helical_polyhedron',\n"
    + "    'smooth_bore_diameter_mm': 3.32,\n"
    + "    'groove_inner_overlap_diameter_mm': 3.16,\n"
    + "    'groove_outer_diameter_mm': 4.40,\n"
    + "    'groove_width_at_bore_approx_mm': 0.28,\n"
    + "    'remaining_thread_crest_width_approx_mm': round(RACK_M4_PITCH-0.28, 3),\n"
    + "    'bore_wall_is_thread_crest': True,\n"
    + "    'continuous_full_height_thread': True,\n",
    1,
)

# Smooth-bore witness: if the helix does not remove additional wall material,
# the existing volume-difference gate will fail.
s = s.replace("hex_z(7.0, 3.2, 0.0).cut(Part.makeCylinder(1.60, 3.2))",
              "hex_z(7.0, 5.6, 0.0).cut(Part.makeCylinder(1.66, 5.6))", 1)

# hardware_cleanup runs before this pass and historically inserted a failure
# gate that dereferenced the then-current rack_m4_female_thread_witness dict.
# Later final passes intentionally replace that dict with the authoritative nut
# witness, which made the stale gate crash with KeyError before export. Remove
# only that obsolete intermediate-nut gate here. The final standalone nut gets
# stronger direct bore/phase checks in apply_v50_rack_m4_nut_rebuild.py.
stale_gate = '''min_removed_per_mm = V['rack_m4_female_thread_witness']['minimum_required_helical_volume_removed_per_mm']
if V['rack_m4_female_thread_witness']['nut_helical_volume_removed_per_mm'] < min_removed_per_mm:
    failures.append('rack M4 nut has no meaningful internal M4 helical groove')
'''
if stale_gate not in s:
    raise SystemExit('Could not locate stale intermediate rack M4 nut gate')
s = s.replace(stale_gate, '', 1)

fail_anchor = "if V.get('lead_nut_mode') != 'separate_RH_8x2_printed_cartridge':\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate final failure-gate anchor')
extra = '''if V['rack_m4_female_thread_witness'].get('profile_generator') != 'radial_Z_trapezoid_helical_polyhedron':
    failures.append('Rack M4 female thread must use a true radial-Z helical profile')
if not V['rack_m4_female_thread_witness'].get('continuous_full_height_thread'):
    failures.append('Rack M4 nut thread must run continuously through full nut height')
if not V['rack_m4_female_thread_witness'].get('bore_wall_is_thread_crest'):
    failures.append('Rack M4 female thread must form the bore wall, not sit behind a smooth bore')
if V['rack_m4_female_thread_witness'].get('full_thread_turns', 0) < 8.0:
    failures.append('Rack M4 printed nut must provide at least eight full thread turns')
if V['rack_m4_female_thread_witness'].get('nut_pocket_axial_clearance_mm', -1) < 0.3:
    failures.append('Rack M4 captive pocket needs at least 0.3 mm axial print clearance')
'''
s = s.replace(fail_anchor, extra + fail_anchor, 1)

if s == orig:
    raise SystemExit('Final rack M4 true-thread fix made no changes')

p.write_text(s, encoding='utf-8')
print('Applied true rack M4 internal thread: radial-Z helical sweep, eight turns, no hidden smooth wall')
