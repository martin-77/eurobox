from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final knob-retainer correction.
#
# The large LEAD_NUT cutter is a valid RH8x2 master, but OCC repeatedly fails
# when that complex fused cutter is subtracted from the compact AF13 retainer.
# The rack M4 nut already proves a more robust construction in this same build:
# a simple smooth through-bore plus one radial/axial helical groove generated as
# a true polyhedron, then subtracted from a native OCC hex body.  Reuse THAT
# architecture here, scaled to the established RH8x2 profile and clearances.
old = '''CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid open-threaded solid')'''
new = r'''# M4-style true female RH8x2 cutter: smooth bore + a radial/AXIAL helical
# groove.  It deliberately runs one full pitch beyond both nut faces, so there
# are no coplanar cutter/body end faces and no hidden smooth terminal wall.
CAP_RH8_SCAD = os.path.join(OUT, 'thread_RH_8x2_knob_retainer_true_female.scad')
cap_bore_r = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
cap_groove_inner_r = cap_bore_r - 0.08
cap_groove_outer_r = THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE
cap_inner_half_z = (LEAD_PROFILE_ROOT_W + 2.0*LEAD_FLANK_CLEARANCE) / 2.0
cap_outer_half_z = (LEAD_PROFILE_CREST_W + 2.0*LEAD_FLANK_CLEARANCE) / 2.0
cap_turns = CAP_NUT_H / THREAD_PITCH
cap_scad = f"""$fn=96;
pitch={THREAD_PITCH};
length={CAP_NUT_H};
bore_r={cap_bore_r};
groove_inner_r={cap_groove_inner_r};
groove_outer_r={cap_groove_outer_r};
inner_half_z={cap_inner_half_z};
outer_half_z={cap_outer_half_z};
turns=length/pitch;
steps=ceil((turns+2)*48);
a0=-360;
a1=360*(turns+1);
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
module true_helical_groove(){{
  polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=80);
}}
union(){{
  translate([0,0,-pitch]) cylinder(r=bore_r,h=length+2*pitch,$fn=96);
  true_helical_groove();
}}
"""
with open(CAP_RH8_SCAD, 'w') as f:
    f.write(cap_scad)
CAP_FEMALE = import_scad_shape(CAP_RH8_SCAD)
if CAP_FEMALE.isNull() or not CAP_FEMALE.isValid() or len(CAP_FEMALE.Solids) != 1:
    raise RuntimeError('M4-style RH8x2 retainer cutter is not one valid solid')
CAP_NUT_BODY = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT_BODY.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if CAP_NUT.isNull() or not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer M4-style RH8x2 cut is not one valid solid')

# Hard shape gate: compact AF13 x 5.8 mm retainer only.
_cap_bb = CAP_NUT.BoundBox
if not (12.95 <= _cap_bb.XLength <= 13.05):
    raise RuntimeError('Knob retainer outer X size is not the 13 mm AF hex body')
if not (5.79 <= _cap_bb.YLength <= 5.81):
    raise RuntimeError('Knob retainer axial length is not 5.8 mm')
if not (14.95 <= _cap_bb.ZLength <= 15.08):
    raise RuntimeError('Knob retainer outer Z size is not the 13 mm AF hex body')
if CAP_NUT.Volume >= CAP_NUT_BODY.Volume - 20.0:
    raise RuntimeError('Knob retainer has no substantial RH8x2 bore/thread removal')'''
if s.count(old) != 1:
    raise SystemExit('Could not locate final short RH8x2 retainer construction')
s = s.replace(old, new, 1)

profile_old = "    'profile_source': 'matched RH8x2 master profile with one-pitch cutter overrun',\n"
profile_new = "    'profile_source': 'M4-style radial/axial RH8x2 female polyhedron with full-pitch end overrun',\n"
if s.count(profile_old) != 1:
    raise SystemExit('Could not locate knob-retainer profile metadata')
s = s.replace(profile_old, profile_new, 1)

meta_anchor = "    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
meta = ("    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
        "    'construction': 'native_OCC_AF13_minus_M4_style_true_RH8x2_female_cutter',\n"
        "    'outer_across_flats_mm': 13.0,\n"
        "    'body_axial_length_mm': CAP_NUT_H,\n"
        "    'female_bore_radius_mm': cap_bore_r,\n"
        "    'female_groove_inner_radius_mm': cap_groove_inner_r,\n"
        "    'female_groove_outer_radius_mm': cap_groove_outer_r,\n"
        "    'female_root_axial_width_mm': 2.0*cap_inner_half_z,\n"
        "    'female_crest_axial_width_mm': 2.0*cap_outer_half_z,\n"
        "    'cutter_overrun_each_end_mm': THREAD_PITCH,\n")
if s.count(meta_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer metadata anchor')
s = s.replace(meta_anchor, meta, 1)

anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')
witness = '''V['knob_retainer_shape'] = {
    'construction': 'native_OCC_AF13_minus_M4_style_true_RH8x2_female_cutter',
    'bbox_x_mm': round(CAP_NUT.BoundBox.XLength, 6),
    'bbox_y_axial_mm': round(CAP_NUT.BoundBox.YLength, 6),
    'bbox_z_mm': round(CAP_NUT.BoundBox.ZLength, 6),
    'body_volume_mm3': round(CAP_NUT_BODY.Volume, 6),
    'threaded_nut_volume_mm3': round(CAP_NUT.Volume, 6),
    'removed_volume_mm3': round(CAP_NUT_BODY.Volume-CAP_NUT.Volume, 6),
    'bore_radius_mm': cap_bore_r,
    'groove_outer_radius_mm': cap_groove_outer_r,
    'cutter_overrun_each_end_mm': THREAD_PITCH,
    'is_compact_5_8mm_retainer': CAP_NUT.BoundBox.YLength <= 5.81,
}
if not V['knob_retainer_shape']['is_compact_5_8mm_retainer']:
    failures.append('Knob retainer regressed to a non-compact cartridge-like part')
if V['knob_retainer_shape']['removed_volume_mm3'] < 20.0:
    failures.append('Knob retainer lacks substantial through-bore/thread removal')

'''
s = s.replace(anchor, witness + anchor, 1)

if s == orig:
    raise SystemExit('Final knob-retainer M4-style rebuild made no changes')
for required in [
    "CAP_RH8_SCAD = os.path.join(OUT, 'thread_RH_8x2_knob_retainer_true_female.scad')",
    'cap_groove_inner_r = cap_bore_r - 0.08',
    'a0=-360;',
    'a1=360*(turns+1);',
    'CAP_NUT = CAP_NUT_BODY.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()',
    "'construction': 'native_OCC_AF13_minus_M4_style_true_RH8x2_female_cutter'",
]:
    if required not in s:
        raise SystemExit('Missing final knob-retainer witness: '+required)

p.write_text(s, encoding='utf-8')
print('Rebuilt RH8x2 knob retainer with the proven M4-style radial/axial female-thread architecture')
