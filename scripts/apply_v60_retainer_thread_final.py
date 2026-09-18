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
FEMALE_CORE_R = 5.25
FEMALE_MAJOR_R = 6.25

# Printable 12x2 service profile for a 0.4 mm nozzle.
# The previous 1.80 mm male root forced the female groove to ~1.90 mm on a
# 2.00 mm pitch, leaving only ~0.10 mm of female crest material between turns.
# That is not a printable/useful internal thread.  Keep a robust 0.60 mm male
# crest and leave 0.50 mm of female crest material at the bore wall.
MALE_ROOT_W = 1.20
MALE_CREST_W = 0.60
FEMALE_ROOT_W = 1.50
FEMALE_CREST_W = 0.90
AXIAL_PROFILE_CLEARANCE = 0.30
FEMALE_CREST_MATERIAL_W = PITCH - FEMALE_ROOT_W
THREAD_LEN = R.RETAINER_LEN
THREAD_Z0 = R.RETAINER_THREAD_Z0
TOP_OVERRUN = PITCH
# The service retainer is Ø12.0 mm at the thread major diameter.  The old
# Ø12.6 x 1.2 mm smooth entry throat made the first female thread sit visibly
# behind the carrier top wall.  Use a slightly larger Ø13.0 mm lead-in, but only
# for a shallow 0.45 mm print/chamfer relief so the actual 12x2 thread starts
# essentially at the top surface.
ENTRY_CLEAR_R = MALE_MAJOR_R + 0.50
ENTRY_CLEAR_DEPTH = 0.45
FN = 96
SLICES_PER_PITCH = 48
THREAD_PROFILE_GENERATOR = 'true_radial_axial_OCC_fused'


def stage(msg):
    print('V60_RETAINER_THREAD_FINAL ' + msg, flush=True)


def write_true_helical_ridge(path, core_r, major_r, length, root_w, crest_w, overrun):
    # Build one closed radial/axial trapezoid swept around a real helix.
    # Widths >= pitch make neighboring turns overlap and the polyhedron ceases
    # to be a valid solid, so reject that geometry before handing it to OpenSCAD.
    if root_w >= PITCH or crest_w >= PITCH:
        raise RuntimeError(
            f'Invalid helical profile: root={root_w:.3f} crest={crest_w:.3f} '
            f'must both be < pitch={PITCH:.3f}'
        )
    # The previous linear_extrude XY ribbon could leave a visually smooth,
    # functionally useless bore even though volume/phase checks passed.
    inner_r = core_r - 0.12
    root_half = root_w / 2.0
    crest_half = crest_w / 2.0
    a0 = -360.0 * overrun / PITCH
    a1 = 360.0 * (length + overrun) / PITCH
    turn_span = (a1-a0)/360.0
    steps = max(48, int(math.ceil(turn_span*SLICES_PER_PITCH)))
    txt = f'''$fn={FN};
pitch={PITCH};
inner_r={inner_r};
major_r={major_r};
root_half={root_half};
crest_half={crest_half};
a0={a0};
a1={a1};
steps={steps};
function ang(i)=a0+(a1-a0)*i/steps;
function zc(i)=pitch*ang(i)/360;
function pt(r,a,z)=[r*cos(a),r*sin(a),z];
pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
       each [pt(inner_r,a,z-root_half),
             pt(major_r,a,z-crest_half),
             pt(major_r,a,z+crest_half),
             pt(inner_r,a,z+root_half)]];
side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
  [4*(i+1)+((j+1)%4),4*(i+1)+j,4*i+j],
  [4*i+((j+1)%4),4*(i+1)+((j+1)%4),4*i+j]
]];
start_face=[[2,1,0],[3,2,0]];
e=4*steps;
end_face=[[e+1,e+2,e+3],[e,e+1,e+3]];
polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=100);
'''
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(txt)


def make_true_thread_solid(path, core_r, major_r, length, z0=0.0):
    ridge = B.import_scad_shape(path)
    clip = Part.makeCylinder(
        major_r + 0.10,
        length,
        App.Vector(0,0,z0),
    )
    ridge = ridge.common(clip).removeSplitter()
    C.require_single(ridge, 'true helical ridge '+os.path.basename(path))
    core = Part.makeCylinder(
        core_r,
        length,
        App.Vector(0,0,z0),
    )
    q = core.fuse(ridge).removeSplitter()
    C.require_single(q, 'true thread solid '+os.path.basename(path))
    return q


stage('compile matched pronounced 12x2 service thread pair')
_t = start_timer('retainer.compile_matched_12x2_thread_pair')
male_scad = os.path.join(C.OUT, 'v60_retainer_final_male_12x2.scad')
female_scad = os.path.join(C.OUT, 'v60_retainer_final_female_12x2.scad')
write_true_helical_ridge(
    male_scad, MALE_CORE_R, MALE_MAJOR_R, THREAD_LEN,
    MALE_ROOT_W, MALE_CREST_W, PITCH,
)
write_true_helical_ridge(
    female_scad, FEMALE_CORE_R, FEMALE_MAJOR_R, THREAD_LEN+TOP_OVERRUN,
    FEMALE_ROOT_W, FEMALE_CREST_W, PITCH,
)

MALE_THREAD = make_true_thread_solid(
    male_scad, MALE_CORE_R, MALE_MAJOR_R, THREAD_LEN, 0.0,
)
# Keep the female helical ridge and smooth crest bore as two cutters.
# Fusing the faceted helical ridge to the long coaxial core produced an invalid
# result after subtraction from the complex BASE.  Sequential subtraction is
# both more robust and more explicit: first open the crest bore, then cut the
# connected radial/axial helical groove into that bore wall.
FEMALE_RIDGE_CUTTER = B.import_scad_shape(female_scad)
C.require_single(FEMALE_RIDGE_CUTTER, 'final female true helical ridge')
FEMALE_CORE_CUTTER = Part.makeCylinder(
    FEMALE_CORE_R,
    THREAD_LEN + TOP_OVERRUN + 2.0*PITCH,
    App.Vector(0,0,-PITCH),
)
C.require_single(FEMALE_CORE_CUTTER, 'final female smooth crest-bore cutter')
C.require_single(MALE_THREAD, 'final retainer male 12x2')
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
RIGHT_PRETHREAD = R.RIGHT.copy()
RIGHT = R.RIGHT

# First machine all simple coaxial service geometry while the BASE topology is
# still simple.  Doing the second smooth bore after the first faceted helical
# subtraction made OCC return an invalid BRep even though the geometry was
# conceptually sound.
for xc in C.CLAMP_X:
    core_cutter = FEMALE_CORE_CUTTER.copy()
    core_cutter.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    RIGHT = RIGHT.cut(core_cutter).removeSplitter()

    entry = Part.makeCylinder(
        ENTRY_CLEAR_R,
        ENTRY_CLEAR_DEPTH + 0.50,
        App.Vector(
            xc, C.RACK_CLOSURE_Y,
            R.CARRIER_TOP_PLANE_Z - ENTRY_CLEAR_DEPTH,
        ),
        App.Vector(0,0,1),
    )
    RIGHT = RIGHT.cut(entry).removeSplitter()
    C.require_single(RIGHT, f'BASE after female crest-bore/service-mouth cuts X={xc}')

# Only after both smooth mouths are complete do we cut the two actual helices.
female_cut_volumes = []
for xc in C.CLAMP_X:
    label = f'retainer.cut_final_base_female_thread_x{int(xc)}'
    _t = start_timer(label)
    ridge_cutter = FEMALE_RIDGE_CUTTER.copy()
    ridge_cutter.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    before = RIGHT.Volume
    RIGHT = RIGHT.cut(ridge_cutter).removeSplitter()
    C.require_single(RIGHT, f'BASE after true female helical groove cut X={xc}')
    removed = before - RIGHT.Volume
    stop_timer(label, _t, removed_mm3=round(removed,6))
    female_cut_volumes.append(round(removed,6))
    if removed < 8.0:
        raise RuntimeError(
            f'Female retainer helix at X={xc} removed only {removed:.3f} mm3; '
            'usable helical groove did not materially reach the BASE'
        )
_t = start_timer('retainer.validate_and_mirror_final_threaded_base')
C.require_single(RIGHT, 'RIGHT base with final explicit female retainer threads')
LEFT = C.mirror_x(RIGHT)
C.require_single(LEFT, 'LEFT base with final explicit female retainer threads')
stop_timer('retainer.validate_and_mirror_final_threaded_base', _t)

stage('fast hard geometric thread witness')
_t_witness = start_timer('retainer.fast_hard_geometric_thread_witness')
failures = []
def fail(msg): failures.append(msg)

# Static printability gates.  These dimensions are part of the actual generated
# radial/axial profile, not metadata inferred from a twisted ribbon.
if MALE_CREST_W < 0.50:
    fail(f'male retainer crest too narrow for 0.4 mm FDM: {MALE_CREST_W:.3f} mm')
if FEMALE_CREST_MATERIAL_W < 0.45:
    fail(f'female retainer crest material too narrow for 0.4 mm FDM: {FEMALE_CREST_MATERIAL_W:.3f} mm')
if FEMALE_ROOT_W < MALE_ROOT_W + 0.20:
    fail('female root groove lacks axial clearance over male root')
if FEMALE_CREST_W < MALE_CREST_W + 0.20:
    fail('female crest groove lacks axial clearance over male crest')
if FEMALE_CORE_R <= MALE_CORE_R + 0.15:
    fail('female crest bore lacks radial clearance over male core')
if FEMALE_MAJOR_R <= MALE_MAJOR_R + 0.15:
    fail('female groove root lacks radial clearance over male major')

def inside(shape, x, y, z):
    return bool(shape.isInside(App.Vector(x,y,z), 1e-5, False))

# Direct point sampling of the ACTUAL final BASE.  This replaces the previous
# full-body common() phase/insertion booleans that took >45 minutes.  At a radius
# halfway through the thread depth, points on the helical centreline must be air
# and points half a pitch away must still be BASE material.  A smooth bore, a
# hidden helix, or a groove that erased the whole wall cannot pass this test.
female_thread_point_samples = []
female_sample_r = (FEMALE_CORE_R + FEMALE_MAJOR_R) / 2.0
sample_angles = (0.0, 90.0, 180.0, 270.0)
sample_turns = (3, 7)
for xc in C.CLAMP_X:
    for turn in sample_turns:
        for angle_deg in sample_angles:
            a = math.radians(angle_deg)
            x = xc + female_sample_r*math.cos(a)
            y = C.RACK_CLOSURE_Y + female_sample_r*math.sin(a)
            z_center = THREAD_Z0 + PITCH*(turn + angle_deg/360.0)
            groove_solid = inside(RIGHT, x, y, z_center)
            between_solid = inside(RIGHT, x, y, z_center + PITCH/2.0)
            rec = {
                'x_station_mm':xc,
                'turn':turn,
                'angle_deg':angle_deg,
                'radius_mm':round(female_sample_r,3),
                'groove_center_solid':groove_solid,
                'between_turns_solid':between_solid,
            }
            female_thread_point_samples.append(rec)
            if groove_solid:
                fail(f'female groove centre still solid X={xc} turn={turn} angle={angle_deg}')
            if not between_solid:
                fail(f'female crest missing between turns X={xc} turn={turn} angle={angle_deg}')

# Equivalent direct check on the actual printed retainer.  The ridge centre must
# contain material and half a pitch away, outside the smooth core, must be air.
male_thread_point_samples = []
male_sample_r = (MALE_CORE_R + MALE_MAJOR_R) / 2.0
for turn in sample_turns:
    for angle_deg in sample_angles:
        a = math.radians(angle_deg)
        x = male_sample_r*math.cos(a)
        y = male_sample_r*math.sin(a)
        z_center = PITCH*(turn + angle_deg/360.0)
        ridge_solid = inside(RACK_NUT_RETAINER, x, y, z_center)
        between_solid = inside(RACK_NUT_RETAINER, x, y, z_center + PITCH/2.0)
        rec = {
            'turn':turn,
            'angle_deg':angle_deg,
            'radius_mm':round(male_sample_r,3),
            'ridge_center_solid':ridge_solid,
            'between_turns_solid':between_solid,
        }
        male_thread_point_samples.append(rec)
        if not ridge_solid:
            fail(f'male ridge missing turn={turn} angle={angle_deg}')
        if between_solid:
            fail(f'male ridge fills space between turns turn={turn} angle={angle_deg}')

# The service mouth must be genuinely open in the actual final BASE.  Sample at
# r=6.30 mm, safely outside the 12.0 mm male major diameter and inside the
# Ø13.0 mm lead-in, 0.20 mm below the carrier top.
female_witness = []
mouth_r = 6.30
mouth_z = R.CARRIER_TOP_PLANE_Z - 0.20
for xc in C.CLAMP_X:
    blocked = 0
    for angle_deg in sample_angles:
        a = math.radians(angle_deg)
        if inside(
            RIGHT,
            xc + mouth_r*math.cos(a),
            C.RACK_CLOSURE_Y + mouth_r*math.sin(a),
            mouth_z,
        ):
            blocked += 1
    female_witness.append({
        'x_mm':xc,
        'blocked_sample_points':blocked,
        'sample_radius_mm':mouth_r,
        'sample_z_mm':round(mouth_z,3),
        'final_base_removed_mm3':female_cut_volumes[len(female_witness)],
        'entry_clear_d_mm':round(2.0*ENTRY_CLEAR_R,3),
    })
    if blocked:
        fail(f'female thread service mouth blocked at {blocked} sampled points X={xc}')

# The M4 overrun bore through the printed retainer must remain open.
if inside(RACK_NUT_RETAINER, 0.0, 0.0, THREAD_LEN/2.0):
    fail('retainer M4 overrun bore is blocked')

thread_printability = {
    'pitch_mm':PITCH,
    'male_root_width_mm':MALE_ROOT_W,
    'male_crest_width_mm':MALE_CREST_W,
    'female_groove_root_width_mm':FEMALE_ROOT_W,
    'female_groove_crest_width_mm':FEMALE_CREST_W,
    'female_crest_material_between_turns_mm':round(FEMALE_CREST_MATERIAL_W,3),
    'male_core_d_mm':round(2.0*MALE_CORE_R,3),
    'male_major_d_mm':round(2.0*MALE_MAJOR_R,3),
    'female_crest_bore_d_mm':round(2.0*FEMALE_CORE_R,3),
    'female_groove_root_d_mm':round(2.0*FEMALE_MAJOR_R,3),
    'radial_core_clearance_mm':round(FEMALE_CORE_R-MALE_CORE_R,3),
    'radial_major_clearance_mm':round(FEMALE_MAJOR_R-MALE_MAJOR_R,3),
    'axial_root_clearance_mm':round(FEMALE_ROOT_W-MALE_ROOT_W,3),
    'axial_crest_clearance_mm':round(FEMALE_CREST_W-MALE_CREST_W,3),
    'target_nozzle_mm':0.4,
}

stop_timer(
    'retainer.fast_hard_geometric_thread_witness',
    _t_witness,
    failures=len(failures),
    female_samples=len(female_thread_point_samples),
    male_samples=len(male_thread_point_samples),
)

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
validation['rack']['m4_closure']['retainer_thread']='explicit matched printable 12x2 true radial/axial service thread; final BASE cut + compact matched-pair witness'
validation['rack']['m4_closure']['retainer_thread_profile_generator']=THREAD_PROFILE_GENERATOR
validation['rack']['m4_closure']['retainer_pitch_mm']=PITCH
validation['rack']['m4_closure']['retainer_male_major_d_mm']=2.0*MALE_MAJOR_R
validation['rack']['m4_closure']['retainer_female_major_d_mm']=2.0*FEMALE_MAJOR_R
validation['rack']['m4_closure']['retainer_male_core_d_mm']=2.0*MALE_CORE_R
validation['rack']['m4_closure']['retainer_female_core_d_mm']=2.0*FEMALE_CORE_R
validation['rack']['m4_closure']['retainer_thread_top_overrun_mm']=TOP_OVERRUN
validation['rack']['m4_closure']['thread_printability']=thread_printability
validation['rack']['m4_closure']['female_thread_removed_mm3']=female_cut_volumes
validation['rack']['m4_closure']['female_helical_witness']=female_witness
validation['rack']['m4_closure']['female_thread_point_samples']=female_thread_point_samples
validation['rack']['m4_closure']['male_thread_point_samples']=male_thread_point_samples
validation['rack']['m4_closure']['entry_clear_d_mm']=round(2.0*ENTRY_CLEAR_R,3)
validation['rack']['m4_closure']['entry_clear_depth_mm']=ENTRY_CLEAR_DEPTH
validation['rack']['m4_closure']['female_thread_start_recess_mm']=ENTRY_CLEAR_DEPTH
validation['rack']['m4_closure']['witness_strategy']='actual final BASE/retainer sampled directly with isInside at helical centres and half-pitch crest positions; no full-body validation booleans'
validation['failures']=[]
with open(validation_path,'w',encoding='utf-8') as fh:
    json.dump(validation,fh,indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFinal retainer: printable matched 12x2 true radial/axial pair for 0.4 mm FDM; 0.60 mm male crest, 0.50 mm female crest material between turns, Ø13.0 mm shallow service lead-in; actual final BASE/retainer helical centres and half-pitch crests are point-sampled directly.\n')

stage('complete')
