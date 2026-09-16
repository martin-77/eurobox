import json
import math
import os

import FreeCAD as App
import Part

import apply_v60_front_final as P
import apply_v60_rack_closure as R
import build_v60_full_baseline as B

C = B.C

# Final rack-retainer thread rebuild.
#
# Do not trust a successful OpenSCAD import as proof that a functional thread
# survived the final BASE export.  Rebuild both members here as an explicit,
# deliberately pronounced matched pair, cut the female helix into the already
# final BASE, then prove the helical crest/groove exists in the final BRep.
# The top of the female cutter overruns by one pitch so the service thread is
# genuinely open at the top and the retainer can be screwed in from above.

PITCH = 2.0
MALE_CORE_R = 5.00
MALE_MAJOR_R = 6.00       # true 12.0 mm external major diameter
FEMALE_CORE_R = 5.20      # 0.20 mm radial print clearance at root
FEMALE_MAJOR_R = 6.22     # 0.22 mm radial clearance at crest
MALE_ROOT_W = 1.80
MALE_CREST_W = 0.90
FLANK_CLEAR = 0.24
FEMALE_ROOT_W = MALE_ROOT_W + 2.0*FLANK_CLEAR
FEMALE_CREST_W = MALE_CREST_W + 2.0*FLANK_CLEAR
THREAD_LEN = R.RETAINER_LEN
THREAD_Z0 = R.RETAINER_THREAD_Z0
TOP_OVERRUN = PITCH
FN = 72
SLICES_PER_PITCH = 32


def stage(msg):
    print('V60_RETAINER_THREAD_FINAL ' + msg, flush=True)


def write_thread(path, core_r, major_r, length, root_w, crest_w, top_overrun=0.0):
    span = length + top_overrun
    slices = max(24, int(math.ceil(span/PITCH*SLICES_PER_PITCH)))
    txt = f'''$fn={FN};\nmodule thread_solid(){{\n union(){{\n  translate([0,0,-0.05]) cylinder(r={core_r},h={span+0.10});\n  linear_extrude(height={span},twist=360*{span}/{PITCH},slices={slices},convexity=50)\n   polygon(points=[[{core_r-0.08},-{root_w}/2],[{major_r},-{crest_w}/2],[{major_r},{crest_w}/2],[{core_r-0.08},{root_w}/2]]);\n }}\n}}\nthread_solid();\n'''
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(txt)


stage('compile matched pronounced 12x2 service thread pair')
male_scad = os.path.join(C.OUT, 'v60_retainer_final_male_12x2.scad')
female_scad = os.path.join(C.OUT, 'v60_retainer_final_female_12x2.scad')
write_thread(male_scad, MALE_CORE_R, MALE_MAJOR_R, THREAD_LEN,
             MALE_ROOT_W, MALE_CREST_W, 0.0)
write_thread(female_scad, FEMALE_CORE_R, FEMALE_MAJOR_R, THREAD_LEN,
             FEMALE_ROOT_W, FEMALE_CREST_W, TOP_OVERRUN)

MALE_THREAD = B.import_scad_shape(male_scad).common(
    Part.makeCylinder(MALE_MAJOR_R+0.04, THREAD_LEN)
).removeSplitter()
FEMALE_CUTTER = B.import_scad_shape(female_scad).common(
    Part.makeCylinder(FEMALE_MAJOR_R+0.04, THREAD_LEN+TOP_OVERRUN)
).removeSplitter()
C.require_single(MALE_THREAD, 'final retainer male 12x2')
C.require_single(FEMALE_CUTTER, 'final base female 12x2 cutter')

# Rebuild the separate retainer from the matched male master.  Keep the same
# annular nose, through-bore and top two-pin tool interface.
retainer_nose = Part.makeCylinder(
    R.RETAINER_NOSE_OD/2.0,
    R.RETAINER_NOSE_LEN,
    App.Vector(0,0,-R.RETAINER_NOSE_LEN),
)
RACK_NUT_RETAINER = MALE_THREAD.fuse(retainer_nose).removeSplitter()
RACK_NUT_RETAINER = RACK_NUT_RETAINER.cut(
    Part.makeCylinder(
        R.RETAINER_BORE_D/2.0,
        THREAD_LEN+R.RETAINER_NOSE_LEN+0.4,
        App.Vector(0,0,-R.RETAINER_NOSE_LEN-0.2),
    )
).removeSplitter()
for sx in (-R.RETAINER_TOOL_HOLE_R, R.RETAINER_TOOL_HOLE_R):
    RACK_NUT_RETAINER = RACK_NUT_RETAINER.cut(
        Part.makeCylinder(
            R.RETAINER_TOOL_HOLE_D/2.0,
            R.RETAINER_TOOL_HOLE_DEPTH+0.2,
            App.Vector(sx,0,THREAD_LEN-R.RETAINER_TOOL_HOLE_DEPTH),
        )
    ).removeSplitter()
C.require_single(RACK_NUT_RETAINER, 'final threaded rack-nut retainer')

stage('cut explicit female helical grooves into final bases')
RIGHT = R.RIGHT
female_cut_volumes = []
for xc in C.CLAMP_X:
    cutter = FEMALE_CUTTER.copy()
    cutter.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    before = RIGHT.Volume
    RIGHT = RIGHT.cut(cutter).removeSplitter()
    removed = before - RIGHT.Volume
    female_cut_volumes.append(round(removed,6))
    if removed < 8.0:
        raise RuntimeError(
            f'Female retainer thread at X={xc} removed only {removed:.3f} mm3; '
            'helical groove did not materially reach the BASE'
        )
C.require_single(RIGHT, 'RIGHT base with final explicit female retainer threads')
LEFT = C.mirror_x(RIGHT)
C.require_single(LEFT, 'LEFT base with final explicit female retainer threads')

stage('hard geometric thread witness')
failures = []
def fail(msg): failures.append(msg)

# Male witness: material must exist well outside the 10 mm core over almost the
# whole axial length. A smooth cylinder cannot satisfy this.
outer_annulus = Part.makeCylinder(MALE_MAJOR_R+0.02, THREAD_LEN).cut(
    Part.makeCylinder(MALE_CORE_R+0.20, THREAD_LEN)
)
male_helix_volume = RACK_NUT_RETAINER.common(outer_annulus).Volume
if male_helix_volume < 12.0:
    fail(f'male retainer helix too weak/absent: {male_helix_volume:.3f} mm3')

# Female witness on the FINAL BASE: an annulus just outside the smooth root bore
# must contain BOTH retained land and removed helical groove. This rejects both
# a missing thread (100% material) and an accidentally oversized smooth bore
# (0% material).
female_witness = []
for xc in C.CLAMP_X:
    z0 = THREAD_Z0 + 1.0
    h = max(1.0, THREAD_LEN - 2.0)
    outer = Part.makeCylinder(5.90, h, App.Vector(xc,C.RACK_CLOSURE_Y,z0))
    inner = Part.makeCylinder(5.35, h, App.Vector(xc,C.RACK_CLOSURE_Y,z0))
    annulus = outer.cut(inner)
    frac = RIGHT.common(annulus).Volume / annulus.Volume
    female_witness.append({'x_mm':xc,'annular_material_fraction':round(frac,6)})
    if frac > 0.995:
        fail(f'female thread groove absent at X={xc}: annular material={frac:.6f}')
    if frac < 0.35:
        fail(f'female thread collapsed to oversized smooth bore at X={xc}: annular material={frac:.6f}')

# A correctly phased nominal retainer must fit; a half-pitch axial phase error
# without the corresponding 180 degree rotation must materially interfere.
fit_checks = []
for xc in C.CLAMP_X:
    nominal = RACK_NUT_RETAINER.copy()
    nominal.translate(App.Vector(xc,C.RACK_CLOSURE_Y,THREAD_Z0))
    nominal_common = RIGHT.common(nominal).Volume

    wrong = RACK_NUT_RETAINER.copy()
    wrong.translate(App.Vector(xc,C.RACK_CLOSURE_Y,THREAD_Z0 + PITCH/2.0))
    wrong_common = RIGHT.common(wrong).Volume
    fit_checks.append({
        'x_mm':xc,
        'nominal_common_mm3':round(nominal_common,6),
        'half_pitch_wrong_phase_common_mm3':round(wrong_common,6),
    })
    if nominal_common > 2.0:
        fail(f'nominal retainer fit collision X={xc}: {nominal_common:.3f} mm3')
    if wrong_common < nominal_common + 2.0:
        fail(f'half-pitch wrong phase does not prove helical engagement X={xc}: nominal={nominal_common:.3f}, wrong={wrong_common:.3f}')

# Keep the required through bore and top service access intact.
through = Part.makeCylinder(R.RETAINER_BORE_D/2.0-0.15, THREAD_LEN+R.RETAINER_NOSE_LEN,
                            App.Vector(0,0,-R.RETAINER_NOSE_LEN))
if RACK_NUT_RETAINER.common(through).Volume > 1e-4:
    fail('retainer M4 overrun bore is not open')

if failures:
    raise RuntimeError('V60 FINAL RETAINER THREAD CHECKS FAILED: ' + ' | '.join(failures))

stage('re-export final BASE and retainer')
R.RIGHT = RIGHT
R.LEFT = LEFT
R.RACK_NUT_RETAINER = RACK_NUT_RETAINER
C.export_shape('eurobox_v60_base_right', RIGHT)
C.export_shape('eurobox_v60_base_left', LEFT)
C.export_shape('eurobox_v60_rack_nut_retainer', RACK_NUT_RETAINER)

# Rebuild the assembly so it cannot silently retain the earlier retainer/base.
assembly_path = os.path.join(C.OUT, 'eurobox_v60_assembly.FCStd')
try:
    if App.ActiveDocument:
        App.closeDocument(App.ActiveDocument.Name)
except Exception:
    pass

doc = App.newDocument('Eurobox_v60_assembly')
def add_obj(name, shape):
    obj = doc.addObject('Part::Feature', name); obj.Shape = shape; return obj

RY = C.RACK_CTC/2.0
LY = -C.RACK_CTC/2.0
rb=RIGHT.copy(); rb.translate(App.Vector(0,RY,0)); add_obj('RIGHT_base',rb)
rp=P.PLATE.copy(); rp.translate(App.Vector(0,RY,0)); add_obj('RIGHT_plate',rp)
for xc in C.CLAMP_X:
    lo=R.LOWER.copy(); lo.translate(App.Vector(xc,RY,0)); add_obj('RIGHT_lower_'+str(int(xc)),lo)
    ret=RACK_NUT_RETAINER.copy(); ret.translate(App.Vector(xc,RY+C.RACK_CLOSURE_Y,THREAD_Z0)); add_obj('RIGHT_rack_nut_retainer_'+str(int(xc)),ret)
    knob=R.RACK_HAND_KNOB.copy(); knob.translate(App.Vector(xc,RY+C.RACK_CLOSURE_Y,R.LOWER_PAD_Z0-R.KNOB_H)); add_obj('RIGHT_rack_hand_knob_'+str(int(xc)),knob)
for sx in P.SPINDLE_X:
    sp=B.SPINDLE.copy(); sp.translate(App.Vector(sx,RY+B.PLATE_SPINDLE_Y,B.SPINDLE_Z)); add_obj('RIGHT_spindle_'+str(int(sx)),sp)

def left_transform(shape):
    q=shape.copy(); q.rotate(App.Vector(0,0,0),App.Vector(0,0,1),180); q.translate(App.Vector(0,LY,0)); return q

add_obj('LEFT_base',left_transform(LEFT))
add_obj('LEFT_plate',left_transform(P.PLATE))
for xc in C.CLAMP_X:
    lo=R.LOWER.copy(); lo.translate(App.Vector(xc,0,0)); add_obj('LEFT_lower_'+str(int(xc)),left_transform(lo))
    ret=RACK_NUT_RETAINER.copy(); ret.translate(App.Vector(xc,C.RACK_CLOSURE_Y,THREAD_Z0)); add_obj('LEFT_rack_nut_retainer_'+str(int(xc)),left_transform(ret))
    knob=R.RACK_HAND_KNOB.copy(); knob.translate(App.Vector(xc,C.RACK_CLOSURE_Y,R.LOWER_PAD_Z0-R.KNOB_H)); add_obj('LEFT_rack_hand_knob_'+str(int(xc)),left_transform(knob))
for sx in P.SPINDLE_X:
    sp=B.SPINDLE.copy(); sp.translate(App.Vector(sx,B.PLATE_SPINDLE_Y,B.SPINDLE_Z)); add_obj('LEFT_spindle_'+str(int(sx)),left_transform(sp))
add_obj('REF_right_rack_tube', C.cyl_x(C.RACK_R,400,-200,RY,0))
add_obj('REF_left_rack_tube', C.cyl_x(C.RACK_R,400,-200,LY,0))
doc.recompute(); doc.saveAs(assembly_path); App.closeDocument(doc.Name)

validation_path = os.path.join(C.OUT,'VALIDATION_v60_full.json')
with open(validation_path,'r',encoding='utf-8') as fh:
    validation=json.load(fh)
validation['stage']='full_direct_mechanism_actual_front_and_explicit_retainer_threads'
validation['rack']['m4_closure']['retainer_thread']='explicit matched printable 12x2 service thread; final BRep witnessed'
validation['rack']['m4_closure']['retainer_pitch_mm']=PITCH
validation['rack']['m4_closure']['retainer_male_major_d_mm']=2.0*MALE_MAJOR_R
validation['rack']['m4_closure']['retainer_female_major_d_mm']=2.0*FEMALE_MAJOR_R
validation['rack']['m4_closure']['retainer_male_core_d_mm']=2.0*MALE_CORE_R
validation['rack']['m4_closure']['retainer_female_core_d_mm']=2.0*FEMALE_CORE_R
validation['rack']['m4_closure']['retainer_thread_top_overrun_mm']=TOP_OVERRUN
validation['rack']['m4_closure']['male_helical_material_mm3']=round(male_helix_volume,6)
validation['rack']['m4_closure']['female_thread_removed_mm3']=female_cut_volumes
validation['rack']['m4_closure']['female_helical_witness']=female_witness
validation['rack']['m4_closure']['retainer_phase_fit_checks']=fit_checks
validation['failures']=[]
with open(validation_path,'w',encoding='utf-8') as fh:
    json.dump(validation,fh,indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFinal retainer: explicit pronounced matched 12x2 male/female thread pair; female top overrun; actual final-BRep helix/land/phase hard witnesses.\n')

stage('complete')
