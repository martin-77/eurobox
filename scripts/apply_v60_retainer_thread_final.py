import json
import math
import os

import FreeCAD as App
import Part

import apply_v60_rack_closure as R
import build_v60_full_baseline as B
from v60_timing import start_timer, stop_timer

C = B.C

# Final rack-retainer thread rebuild.
#
# This stage deliberately depends only on the already-canonical rack-closure
# output.  It must not import any box-clamp/front builder: doing so would execute
# a second, obsolete front architecture after the clean modular front has already
# passed its hard checks.
#
# Do not trust a successful OpenSCAD import as proof that a functional thread
# survived the final BASE export. Rebuild both members here as an explicit,
# deliberately pronounced matched pair, cut the female helix into the already
# final BASE, then prove both the final BASE cut and the matched thread phase.

PITCH = 2.0
MALE_CORE_R = 5.00
MALE_MAJOR_R = 6.00
FEMALE_CORE_R = 5.20
FEMALE_MAJOR_R = 6.22
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
_t = start_timer('retainer.compile_matched_12x2_thread_pair')
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
stop_timer('retainer.compile_matched_12x2_thread_pair', _t)

_t = start_timer('retainer.build_threaded_service_retainer')
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
stop_timer('retainer.build_threaded_service_retainer', _t)

stage('cut explicit female helical grooves into final bases')
RIGHT = R.RIGHT
female_cut_volumes = []
for xc in C.CLAMP_X:
    label = f'retainer.cut_final_base_female_thread_x{int(xc)}'
    _t = start_timer(label)
    cutter = FEMALE_CUTTER.copy()
    cutter.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    before = RIGHT.Volume
    RIGHT = RIGHT.cut(cutter).removeSplitter()
    removed = before - RIGHT.Volume
    stop_timer(label, _t, removed_mm3=round(removed,6))
    female_cut_volumes.append(round(removed,6))
    if removed < 8.0:
        raise RuntimeError(
            f'Female retainer thread at X={xc} removed only {removed:.3f} mm3; '
            'helical groove did not materially reach the BASE'
        )
_t = start_timer('retainer.validate_and_mirror_final_threaded_base')
C.require_single(RIGHT, 'RIGHT base with final explicit female retainer threads')
LEFT = C.mirror_x(RIGHT)
C.require_single(LEFT, 'LEFT base with final explicit female retainer threads')
stop_timer('retainer.validate_and_mirror_final_threaded_base', _t)

stage('hard geometric thread witness')
_t_witness = start_timer('retainer.hard_geometric_thread_witness')
failures = []
def fail(msg): failures.append(msg)

outer_annulus = Part.makeCylinder(MALE_MAJOR_R+0.02, THREAD_LEN).cut(
    Part.makeCylinder(MALE_CORE_R+0.20, THREAD_LEN)
)
male_helix_volume = RACK_NUT_RETAINER.common(outer_annulus).Volume
if male_helix_volume < 12.0:
    fail(f'male retainer helix too weak/absent: {male_helix_volume:.3f} mm3')

# The final BASE itself is witnessed by the actual production subtraction above.
# Land/groove and phase are checked on a compact coupon cut by the exact same
# FEMALE_CUTTER, avoiding repeated global commons against the carrier BRep.
coupon_r = FEMALE_MAJOR_R + 0.8
coupon = Part.makeCylinder(coupon_r, THREAD_LEN + TOP_OVERRUN)
threaded_coupon = coupon.cut(FEMALE_CUTTER).removeSplitter()
C.require_single(threaded_coupon, 'compact female retainer thread witness coupon')

z0 = 1.0
h = max(1.0, THREAD_LEN - 2.0)
outer = Part.makeCylinder(5.90, h, App.Vector(0,0,z0))
inner = Part.makeCylinder(5.35, h, App.Vector(0,0,z0))
annulus = outer.cut(inner)
frac = threaded_coupon.common(annulus).Volume / annulus.Volume
female_witness = [
    {'x_mm': xc, 'annular_material_fraction': round(frac,6),
     'final_base_removed_mm3': female_cut_volumes[i]}
    for i, xc in enumerate(C.CLAMP_X)
]
if frac > 0.995:
    fail(f'female thread groove absent in matched cutter witness: annular material={frac:.6f}')
if frac < 0.35:
    fail(f'female thread collapsed to oversized smooth bore in matched cutter witness: annular material={frac:.6f}')

nominal_common = threaded_coupon.common(RACK_NUT_RETAINER).Volume
wrong = RACK_NUT_RETAINER.copy()
wrong.translate(App.Vector(0,0,PITCH/2.0))
wrong_common = threaded_coupon.common(wrong).Volume
fit_checks = [
    {
        'x_mm': xc,
        'nominal_common_mm3': round(nominal_common,6),
        'half_pitch_wrong_phase_common_mm3': round(wrong_common,6),
        'witness': 'compact coupon from exact production FEMALE_CUTTER',
    }
    for xc in C.CLAMP_X
]
if nominal_common > 2.0:
    fail(f'nominal retainer fit collision: {nominal_common:.3f} mm3')
if wrong_common < nominal_common + 2.0:
    fail(f'half-pitch wrong phase does not prove helical engagement: nominal={nominal_common:.3f}, wrong={wrong_common:.3f}')

through = Part.makeCylinder(R.RETAINER_BORE_D/2.0-0.15, THREAD_LEN+R.RETAINER_NOSE_LEN,
                            App.Vector(0,0,-R.RETAINER_NOSE_LEN))
if RACK_NUT_RETAINER.common(through).Volume > 1e-4:
    fail('retainer M4 overrun bore is not open')
stop_timer('retainer.hard_geometric_thread_witness', _t_witness, failures=len(failures))

if failures:
    raise RuntimeError('V60 FINAL RETAINER THREAD CHECKS FAILED: ' + ' | '.join(failures))

stage('re-export final BASE and retainer')
R.RIGHT = RIGHT
R.LEFT = LEFT
R.RACK_NUT_RETAINER = RACK_NUT_RETAINER
for name, shape in (
    ('eurobox_v60_base_right', RIGHT),
    ('eurobox_v60_base_left', LEFT),
    ('eurobox_v60_rack_nut_retainer', RACK_NUT_RETAINER),
):
    label = 'retainer.export.' + name
    _t = start_timer(label)
    C.export_shape(name, shape)
    stop_timer(label, _t)

# apply_v60_final_assembly immediately follows this module and is the sole
# canonical assembly writer. Avoid a duplicate intermediate assembly save here.

validation_path = os.path.join(C.OUT,'VALIDATION_v60_full.json')
with open(validation_path,'r',encoding='utf-8') as fh:
    validation=json.load(fh)
validation['stage']='full_direct_mechanism_actual_front_and_explicit_retainer_threads'
validation['rack']['m4_closure']['retainer_thread']='explicit matched printable 12x2 service thread; final BASE cut + compact matched-pair witness'
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
validation['rack']['m4_closure']['witness_strategy']='final BASE removal volumes plus compact coupon from exact production FEMALE_CUTTER; avoids repeated full-carrier BRep commons'
validation['failures']=[]
with open(validation_path,'w',encoding='utf-8') as fh:
    json.dump(validation,fh,indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFinal retainer: explicit pronounced matched 12x2 male/female thread pair; female top overrun; actual final-BASE cutter removal plus compact exact-cutter helix/land/phase hard witnesses.\n')

stage('complete')
