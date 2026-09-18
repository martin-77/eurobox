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
# A radial/axial helical ridge must stay narrower than one pitch at its root.
# The previous female root width was 2.28 mm on a 2.0 mm pitch, so adjacent
# turns self-overlapped and OpenSCAD produced a non-solid shell.  Keep the
# female cutter wider than the male thread, but cap its root below one pitch.
FEMALE_ROOT_W = min(PITCH - 0.10, MALE_ROOT_W + 2.0*FLANK_CLEAR)
FEMALE_CREST_W = min(PITCH - 0.40, MALE_CREST_W + 2.0*FLANK_CLEAR)
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
female_cut_volumes = []
for xc in C.CLAMP_X:
    label = f'retainer.cut_final_base_female_thread_x{int(xc)}'
    _t = start_timer(label)
    before = RIGHT.Volume

    core_cutter = FEMALE_CORE_CUTTER.copy()
    core_cutter.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    RIGHT = RIGHT.cut(core_cutter).removeSplitter()
    C.require_single(RIGHT, f'BASE after female crest-bore cut X={xc}')

    ridge_cutter = FEMALE_RIDGE_CUTTER.copy()
    ridge_cutter.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    RIGHT = RIGHT.cut(ridge_cutter).removeSplitter()
    C.require_single(RIGHT, f'BASE after true female helical groove cut X={xc}')
    # Explicit open mouth: remove the full male-major envelope through the
    # carrier top. A valid helix hidden behind a roof/ring wall must be impossible.
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

# Validate the actual final BASE against the actual final retainer. No coupon is
# allowed to stand in for the production female thread.
female_witness = []
fit_checks = []
entry_checks = []
bore_connected_groove_checks = []
for xc in C.CLAMP_X:
    # The complete outer envelope of the screw must be open at the top surface.
    mouth_probe = Part.makeCylinder(
        ENTRY_CLEAR_R - 0.05,
        ENTRY_CLEAR_DEPTH,
        App.Vector(
            xc, C.RACK_CLOSURE_Y,
            R.CARRIER_TOP_PLANE_Z - ENTRY_CLEAR_DEPTH,
        ),
        App.Vector(0,0,1),
    )
    mouth_block = RIGHT.common(mouth_probe).Volume
    female_witness.append({
        'x_mm': xc,
        'final_base_removed_mm3': female_cut_volumes[len(female_witness)],
        'mouth_block_mm3': round(mouth_block,6),
        'entry_clear_d_mm': round(2.0*ENTRY_CLEAR_R,3),
    })
    if mouth_block > 1e-4:
        fail(f'female thread mouth is hidden behind BASE material X={xc}: {mouth_block:.6f} mm3')

    # Compare the actual threaded BASE with a smooth-bore-only reference in a
    # mid-span annulus.  A real female thread must remove substantial additional
    # helical material from the bore wall; a visually smooth cylinder cannot pass.
    smooth_ref = RIGHT_PRETHREAD.copy()
    smooth_core = Part.makeCylinder(
        FEMALE_CORE_R,
        THREAD_LEN+TOP_OVERRUN,
        App.Vector(xc,C.RACK_CLOSURE_Y,THREAD_Z0),
        App.Vector(0,0,1),
    )
    smooth_ref = smooth_ref.cut(smooth_core).removeSplitter()
    smooth_ref = smooth_ref.cut(Part.makeCylinder(
        ENTRY_CLEAR_R,
        ENTRY_CLEAR_DEPTH+0.50,
        App.Vector(
            xc,C.RACK_CLOSURE_Y,
            R.CARRIER_TOP_PLANE_Z-ENTRY_CLEAR_DEPTH,
        ),
        App.Vector(0,0,1),
    )).removeSplitter()
    shell_z0 = THREAD_Z0 + 2.0*PITCH
    shell_h = max(PITCH, THREAD_LEN - 4.0*PITCH)
    shell = Part.makeCylinder(
        FEMALE_MAJOR_R+0.04, shell_h,
        App.Vector(xc,C.RACK_CLOSURE_Y,shell_z0),
        App.Vector(0,0,1),
    ).cut(Part.makeCylinder(
        FEMALE_CORE_R-0.02, shell_h,
        App.Vector(xc,C.RACK_CLOSURE_Y,shell_z0),
        App.Vector(0,0,1),
    )).removeSplitter()
    smooth_shell_material = smooth_ref.common(shell).Volume
    threaded_shell_material = RIGHT.common(shell).Volume
    helical_removed = smooth_shell_material - threaded_shell_material
    bore_connected_groove_checks.append({
        'x_mm':xc,
        'helical_removed_midspan_mm3':round(helical_removed,6),
        'smooth_shell_material_mm3':round(smooth_shell_material,6),
        'threaded_shell_material_mm3':round(threaded_shell_material,6),
    })
    if helical_removed < 20.0:
        fail(f'female retainer bore lacks substantial connected helical groove X={xc}: {helical_removed:.6f} mm3')

    nominal = RACK_NUT_RETAINER.copy()
    nominal.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    nominal_common = RIGHT.common(nominal).Volume

    wrong = RACK_NUT_RETAINER.copy()
    wrong.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180.0)
    wrong.translate(App.Vector(xc, C.RACK_CLOSURE_Y, THREAD_Z0))
    wrong_common = RIGHT.common(wrong).Volume
    fit_checks.append({
        'x_mm': xc,
        'nominal_common_mm3': round(nominal_common,6),
        'half_pitch_wrong_phase_common_mm3': round(wrong_common,6),
        'witness': 'actual final BASE against actual final retainer',
    })
    if nominal_common > 0.20:
        fail(f'nominal retainer collides with final BASE X={xc}: {nominal_common:.6f} mm3')
    if wrong_common < nominal_common + 2.0:
        fail(f'final BASE female thread lacks phase-sensitive engagement X={xc}: nominal={nominal_common:.6f} wrong={wrong_common:.6f}')

    # Prove physical entry from free space, not merely motion after the part is
    # already buried in the thread. The retainer starts with its thread body
    # above the carrier top and is screwed into the first two millimetres.
    entry_lift = R.CARRIER_TOP_PLANE_Z - THREAD_Z0 + 0.20
    for depth in (0.0,0.5,1.0,2.0):
        lift = entry_lift - depth
        q = RACK_NUT_RETAINER.copy()
        q.rotate(
            App.Vector(0,0,0), App.Vector(0,0,1),
            -360.0*lift/PITCH,
        )
        q.translate(App.Vector(
            xc, C.RACK_CLOSURE_Y, THREAD_Z0 + lift,
        ))
        common = RIGHT.common(q).Volume
        entry_checks.append({
            'x_mm': xc,
            'entry_depth_mm': depth,
            'lift_from_installed_mm': round(lift,3),
            'base_common_mm3': round(common,6),
        })
        if common > 0.20:
            fail(f'retainer cannot enter female thread from outside X={xc} depth={depth}: {common:.6f} mm3')

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
validation['rack']['m4_closure']['retainer_thread']='explicit matched printable 12x2 true radial/axial service thread; final BASE cut + compact matched-pair witness'
validation['rack']['m4_closure']['retainer_thread_profile_generator']=THREAD_PROFILE_GENERATOR
validation['rack']['m4_closure']['retainer_pitch_mm']=PITCH
validation['rack']['m4_closure']['retainer_male_major_d_mm']=2.0*MALE_MAJOR_R
validation['rack']['m4_closure']['retainer_female_major_d_mm']=2.0*FEMALE_MAJOR_R
validation['rack']['m4_closure']['retainer_male_core_d_mm']=2.0*MALE_CORE_R
validation['rack']['m4_closure']['retainer_female_core_d_mm']=2.0*FEMALE_CORE_R
validation['rack']['m4_closure']['retainer_thread_top_overrun_mm']=TOP_OVERRUN
validation['rack']['m4_closure']['male_helical_material_mm3']=round(male_helix_volume,6)
validation['rack']['m4_closure']['female_thread_removed_mm3']=female_cut_volumes
validation['rack']['m4_closure']['female_helical_witness']=female_witness
validation['rack']['m4_closure']['female_bore_connected_groove_checks']=bore_connected_groove_checks
validation['rack']['m4_closure']['retainer_phase_fit_checks']=fit_checks
validation['rack']['m4_closure']['entry_clear_d_mm']=round(2.0*ENTRY_CLEAR_R,3)
validation['rack']['m4_closure']['entry_clear_depth_mm']=ENTRY_CLEAR_DEPTH
validation['rack']['m4_closure']['female_thread_start_recess_mm']=ENTRY_CLEAR_DEPTH
validation['rack']['m4_closure']['retainer_entry_checks']=entry_checks
validation['rack']['m4_closure']['witness_strategy']='actual final BASE + actual final retainer; open-mouth envelope and entry motion from free space'
validation['failures']=[]
with open(validation_path,'w',encoding='utf-8') as fh:
    json.dump(validation,fh,indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFinal retainer: one matched 12x2 true radial/axial male/female pair; Ø13.0 mm shallow service lead-in with the female thread starting 0.45 mm below the carrier top; actual final BASE/retainer fit, bore-connected helical-groove, phase and insertion-from-free-space hard checks.\n')

stage('complete')
