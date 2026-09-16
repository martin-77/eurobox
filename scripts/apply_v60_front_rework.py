import json
import math
import os

import FreeCAD as App
import Part

import build_v60_full_baseline as F

C = F.C

# ---------------------------------------------------------------------------
# v60 box-clamp front rework
# ---------------------------------------------------------------------------
# The screw blocks remain rectangular. Only the FREE FIELDS beside and between
# them get support-free DROPs. The DROPs are thin rear ribs in the X/Z plane,
# not full-depth walls: this preserves the complete moving-plate corridor while
# still supporting the upper front tie during printing.
# ---------------------------------------------------------------------------

PLATE_X = 160.0
SPINDLE_X = (-65.0, 65.0)
SPINDLE_SPACING = SPINDLE_X[1] - SPINDLE_X[0]
PLATE_EDGE_MARGIN = PLATE_X / 2.0 - abs(SPINDLE_X[1])
PLATE_SWEEP_HALF_X = PLATE_X / 2.0 + 0.40
GUIDE_W = 7.60
FRAME_X0 = -PLATE_SWEEP_HALF_X - GUIDE_W
FRAME_X1 = PLATE_SWEEP_HALF_X + GUIDE_W
FRAME_W = FRAME_X1 - FRAME_X0
DECK_X0 = -PLATE_SWEEP_HALF_X
DECK_X1 = PLATE_SWEEP_HALF_X

BOSS_HALF_X = 11.0
BOSS_LOWER_HALF_X = 11.35
DROP_Z0 = F.FINAL_DECK_Z1
DROP_Z1 = F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_TIE_T
DROP_RISE = DROP_Z1 - DROP_Z0
DROP_Y0 = F.CAGE_Y0
DROP_T = C.WEB_T

# At X=-65 the widened lead screw sits immediately beside the structural holm
# centred at X=-80.  The complete screw is ~43.5 mm long and moves another
# 5.5 mm inward while opening.  The old thread-bore started only at CAGE_Y0,
# which left the rear screw/stud section running into that holm.  Cut the real
# swept shank/hex envelope all the way to the minimum Y reached at full travel.
SPINDLE_TOTAL_LEN = (
    F.SPINDLE_LOCAL_JOURNAL
    + F.SPINDLE_LOCAL_SHOULDER
    + F.LEAD_THREAD_LEN
    + F.HEX_LEN
    + F.OUTER_STUD_LEN
)
LEAD_CLEARANCE_MARGIN = 0.80
LEAD_CLEAR_Y0 = (
    F.PLATE_SPINDLE_Y
    - F.PLATE_OPEN
    - SPINDLE_TOTAL_LEN
    - LEAD_CLEARANCE_MARGIN
)
LEAD_CLEAR_R = 5.90


def stage(msg):
    print('V60_FRONT_REWORK ' + msg, flush=True)


def triangle_drop(x0, x1, apex_x=None):
    if apex_x is None:
        apex_x = (x0 + x1) / 2.0
    pts = [
        App.Vector(x0, DROP_Y0, DROP_Z1),
        App.Vector(x1, DROP_Y0, DROP_Z1),
        App.Vector(apex_x, DROP_Y0, DROP_Z0),
        App.Vector(x0, DROP_Y0, DROP_Z1),
    ]
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, DROP_T, 0)).removeSplitter()


def wider_plate_sweep():
    return C.box(
        -PLATE_SWEEP_HALF_X,
        C.PLATE_SWEEP_Y0,
        C.PLATE_SWEEP_Z0,
        2.0 * PLATE_SWEEP_HALF_X,
        C.PLATE_SWEEP_Y1 - C.PLATE_SWEEP_Y0,
        C.PLATE_SWEEP_Z1 - C.PLATE_SWEEP_Z0,
    )


stage('build wider cage with rear support-free drops')
parts = [
    C.box(FRAME_X0, F.PRINT_GUIDE_Y0, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y1-F.PRINT_GUIDE_Y0,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    C.box(PLATE_SWEEP_HALF_X, F.PRINT_GUIDE_Y0, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y1-F.PRINT_GUIDE_Y0,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    C.box(FRAME_X0, F.CAGE_Y0-0.10,
          F.PRINT_BASE_PLANE_Z-F.PRINT_FRAME_TIE_T,
          FRAME_W, F.CAGE_Y1-F.CAGE_Y0+0.20, F.PRINT_FRAME_TIE_T),
    C.box(DECK_X0, F.CAGE_Y0, F.FINAL_DECK_Z0,
          DECK_X1-DECK_X0, F.PRINT_GUIDE_Y1-F.CAGE_Y0,
          F.FINAL_DECK_Z1-F.FINAL_DECK_Z0),
    C.box(FRAME_X0, F.CAGE_Y0-0.10, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y0-(F.CAGE_Y0-0.10)+0.35,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    C.box(PLATE_SWEEP_HALF_X, F.CAGE_Y0-0.10, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y0-(F.CAGE_Y0-0.10)+0.35,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    C.box(-PLATE_SWEEP_HALF_X-F.GUIDE_STITCH_OVERLAP,
          F.CAGE_Y0, F.FINAL_DECK_Z1-F.GUIDE_STITCH_OVERLAP,
          2*F.GUIDE_STITCH_OVERLAP, F.PRINT_GUIDE_Y1-F.CAGE_Y0,
          2*F.GUIDE_STITCH_OVERLAP),
    C.box(PLATE_SWEEP_HALF_X-F.GUIDE_STITCH_OVERLAP,
          F.CAGE_Y0, F.FINAL_DECK_Z1-F.GUIDE_STITCH_OVERLAP,
          2*F.GUIDE_STITCH_OVERLAP, F.PRINT_GUIDE_Y1-F.CAGE_Y0,
          2*F.GUIDE_STITCH_OVERLAP),
]

for sx in SPINDLE_X:
    parts.append(C.box(sx-BOSS_HALF_X, F.CAGE_Y0, F.PRINT_FRAME_BOSS_Z0,
                       2*BOSS_HALF_X, F.CAGE_Y1-F.CAGE_Y0,
                       F.PRINT_BASE_PLANE_Z-F.PRINT_FRAME_BOSS_Z0))
    parts.append(C.box(sx-BOSS_LOWER_HALF_X, F.CAGE_Y0,
                       F.FINAL_DECK_Z1-0.35,
                       2*BOSS_LOWER_HALF_X, F.CAGE_Y1-F.CAGE_Y0,
                       F.PRINT_FRAME_BOSS_Z0-(F.FINAL_DECK_Z1-0.35)+0.35))

left_block_x0 = SPINDLE_X[0] - BOSS_LOWER_HALF_X
left_block_x1 = SPINDLE_X[0] + BOSS_LOWER_HALF_X
right_block_x0 = SPINDLE_X[1] - BOSS_LOWER_HALF_X
right_block_x1 = SPINDLE_X[1] + BOSS_LOWER_HALF_X
center_x0 = left_block_x1
center_x1 = right_block_x0
center_step = (center_x1-center_x0)/3.0
DROP_SPECS = [
    (FRAME_X0, left_block_x0, DECK_X0),
    (center_x0, center_x0+center_step, None),
    (center_x0+center_step, center_x0+2.0*center_step, None),
    (center_x0+2.0*center_step, center_x1, None),
    (right_block_x1, FRAME_X1, DECK_X1),
]
DROPS = []
for x0, x1, apex in DROP_SPECS:
    d = triangle_drop(x0, x1, apex)
    DROPS.append(d)
    parts.append(d)

CAGE = C.fuse_seq(parts, 'v60-wider-support-free-box-clamp-cage')
C.require_single(CAGE, 'v60 wider front cage')

stage('fuse wider front into widened structural corridor')
CORE = C.RIGHT.cut(wider_plate_sweep()).removeSplitter()
C.require_single(CORE, 'RIGHT core with 160mm plate corridor')
RIGHT_FULL = CORE.fuse(CAGE).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT wider front before machining')

for xc in C.CLAMP_X:
    RIGHT_FULL = RIGHT_FULL.cut(
        Part.makeCylinder(
            C.RACK_M4_BASE_CLEAR_D/2.0,
            F.RACK_M4_BASE_BORE_Z1-F.RACK_M4_BASE_BORE_Z0,
            App.Vector(xc, C.RACK_CLOSURE_Y, F.RACK_M4_BASE_BORE_Z0),
            App.Vector(0,0,1),
        )
    ).removeSplitter()

stage('machine lead screw blocks at +/-65 mm')
for sx in SPINDLE_X:
    RIGHT_FULL = RIGHT_FULL.cut(
        F.cyl_y(
            LEAD_CLEAR_R,
            F.NUT_THREAD_Y0-LEAD_CLEAR_Y0+0.20,
            sx,
            LEAD_CLEAR_Y0,
            F.SPINDLE_Z,
        )
    ).removeSplitter()
    cutter = F.FEMALE_NEGY.copy()
    cutter.translate(App.Vector(sx, F.NUT_Y0, F.SPINDLE_Z))
    RIGHT_FULL = RIGHT_FULL.cut(cutter).removeSplitter()
    RIGHT_FULL = RIGHT_FULL.cut(
        F.cyl_y(F.SHOULDER_D/2.0+0.35,
                F.PLATE_SPINDLE_Y-F.NUT_Y0+0.70,
                sx, F.NUT_Y0, F.SPINDLE_Z)
    ).removeSplitter()

C.require_single(RIGHT_FULL, 'RIGHT wider front final')
LEFT_FULL = C.mirror_x(RIGHT_FULL)
C.require_single(LEFT_FULL, 'LEFT wider front final')

stage('build 160 mm clamp plate')
PLATE_BODY_Y0 = C.BOX_RIM_INNER_Y - F.PLATE_Y
PLATE_HOOK_Y0 = C.BOX_RIM_INNER_Y - F.WIDTH_RIM_CLEAR
PLATE_HOOK_Y1 = C.BOX_RIM_INNER_Y + F.UNDERHOOK
PLATE = C.box(-PLATE_X/2.0, PLATE_BODY_Y0, F.PLATE_Z0,
              PLATE_X, F.PLATE_Y, F.PLATE_Z1-F.PLATE_Z0)
PLATE = PLATE.fuse(C.box(-PLATE_X/2.0, PLATE_HOOK_Y0,
                         F.RIM_BOTTOM_Z-F.UNDERHOOK_T,
                         PLATE_X, PLATE_HOOK_Y1-PLATE_HOOK_Y0, F.UNDERHOOK_T))
for sx in SPINDLE_X:
    PLATE = PLATE.cut(F.cyl_y(F.PLATE_HOLE_D/2.0, F.PLATE_Y+1.0,
                              sx, PLATE_BODY_Y0-0.5, F.SPINDLE_Z))
    PLATE = PLATE.cut(F.cyl_y(6.0, 2.0, sx,
                              F.PLATE_SPINDLE_Y-2.0, F.SPINDLE_Z))
PLATE = PLATE.removeSplitter()
C.require_single(PLATE, '160mm box clamp plate')

stage('hard validation')
failures = []
def fail(msg): failures.append(msg)

if SPINDLE_X != (-65.0, 65.0): fail('lead screws are not at +/-65 mm')
if abs(SPINDLE_SPACING-130.0) > 1e-9: fail('lead screw spacing is not 130 mm')
if abs(PLATE_X-160.0) > 1e-9: fail('clamp plate is not 160 mm')
if abs(PLATE_EDGE_MARGIN-15.0) > 1e-9: fail('plate screw edge margin is not 15 mm')

for sx in SPINDLE_X:
    block = C.box(sx-BOSS_LOWER_HALF_X+0.02, F.CAGE_Y0,
                  F.FINAL_DECK_Z1-0.33,
                  2*BOSS_LOWER_HALF_X-0.04, F.CAGE_Y1-F.CAGE_Y0,
                  F.PRINT_BASE_PLANE_Z-(F.FINAL_DECK_Z1-0.33))
    for i,d in enumerate(DROPS):
        cv=d.common(block).Volume
        if cv>1e-4: fail(f'DROP {i} intrudes into rectangular screw block at X={sx}: {cv:.6f}')

drop_checks=[]
for i,((x0,x1,apex),d) in enumerate(zip(DROP_SPECS,DROPS)):
    ax=(x0+x1)/2.0 if apex is None else apex
    max_run=max(abs(ax-x0),abs(x1-ax))
    angle=math.degrees(math.atan2(DROP_RISE,max_run)) if max_run>0 else 90.0
    incorporated=RIGHT_FULL.common(d).Volume/d.Volume
    drop_checks.append({'index':i,'x_mm':[round(x0,3),round(x1,3)],
                        'apex_x_mm':round(ax,3),'y_mm':[round(DROP_Y0,3),round(DROP_Y0+DROP_T,3)],
                        'rise_mm':round(DROP_RISE,3),'max_horizontal_run_mm':round(max_run,3),
                        'flank_angle_from_horizontal_deg':round(angle,3),
                        'material_fraction':round(incorporated,6)})
    if angle<45.0-1e-6: fail(f'DROP {i} is not support-free: {angle:.3f} deg')
    if incorporated<0.999: fail(f'DROP {i} not fully incorporated: {incorporated:.6f}')

for side,sh in (('RIGHT',RIGHT_FULL),('LEFT',LEFT_FULL)):
    if sh.BoundBox.XLength>C.V60_X_TARGET_MAX+1e-6: fail(f'{side} exceeds 296 mm X target: {sh.BoundBox.XLength:.3f}')
    if sh.BoundBox.YLength>C.INDX_Y_MAX+1e-6: fail(f'{side} exceeds 275 mm Y target: {sh.BoundBox.YLength:.3f}')

rim=C.box(-220,C.BOX_RIM_INNER_Y,F.RIM_BOTTOM_Z,440,C.RIM_Y,C.RIM_H)
plate_motion=[]
for travel in (0,1,2,3,4,4.5,5.0,5.5):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-travel,0))
    bc=RIGHT_FULL.common(pl).Volume; rc=rim.common(pl).Volume
    plate_motion.append({'open_mm':travel,'base_common_mm3':round(bc,6),'rim_common_mm3':round(rc,6)})
    if bc>1e-4: fail(f'160mm plate/base collision at open={travel}: {bc:.6f}')
    if rc>1e-4: fail(f'160mm plate/rim collision at open={travel}: {rc:.6f}')

thread_motion=[]
for sx in SPINDLE_X:
    for travel in (0,0.5,1.0,2.0,3.0,4.0,5.5):
        q=F.SPINDLE.copy()
        q.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*travel/F.THREAD_PITCH)
        q.translate(App.Vector(sx,F.PLATE_SPINDLE_Y-travel,F.SPINDLE_Z))
        bc=RIGHT_FULL.common(q).Volume
        thread_motion.append({'x_mm':sx,'open_mm':travel,'base_common_mm3':round(bc,6)})
        if bc>1.0: fail(f'lead screw grossly collides X={sx} open={travel}: {bc:.6f}')

left_back=C.mirror_x(LEFT_FULL)
mirror_delta=abs(RIGHT_FULL.Volume-left_back.Volume)
if mirror_delta>1e-4: fail(f'wider front handed bases not exact mirrors: {mirror_delta:.6f}')
if failures: raise RuntimeError('V60 FRONT REWORK HARD CHECKS FAILED: '+' | '.join(failures))

stage('publish canonical front variables and exports')
F.RIGHT_FULL=RIGHT_FULL
F.LEFT_FULL=LEFT_FULL
F.PLATE=PLATE
F.SPINDLE_X=SPINDLE_X
C.export_shape('eurobox_v60_clamp_plate',PLATE)

validation_path=os.path.join(C.OUT,'VALIDATION_v60_full.json')
with open(validation_path,'r',encoding='utf-8') as fh: validation=json.load(fh)
validation['stage']='full_direct_mechanism_wider_support_free_front'
validation['base']['right_bbox_mm']=[round(RIGHT_FULL.BoundBox.XLength,3),round(RIGHT_FULL.BoundBox.YLength,3),round(RIGHT_FULL.BoundBox.ZLength,3)]
validation['base']['left_bbox_mm']=[round(LEFT_FULL.BoundBox.XLength,3),round(LEFT_FULL.BoundBox.YLength,3),round(LEFT_FULL.BoundBox.ZLength,3)]
validation['base']['mirror_delta_mm3']=round(mirror_delta,9)
validation['box_clamp']['plate_width_mm']=PLATE_X
validation['box_clamp']['spindle_x_mm']=list(SPINDLE_X)
validation['box_clamp']['spindle_spacing_mm']=SPINDLE_SPACING
validation['box_clamp']['plate_screw_edge_margin_mm']=PLATE_EDGE_MARGIN
validation['box_clamp']['frame_x_mm']=[FRAME_X0,FRAME_X1]
validation['box_clamp']['plate_corridor_half_x_mm']=PLATE_SWEEP_HALF_X
validation['box_clamp']['rectangular_screw_blocks']=True
validation['box_clamp']['drops_only_beside_blocks']=True
validation['box_clamp']['drop_rib_thickness_y_mm']=DROP_T
validation['box_clamp']['support_free_drop_checks']=drop_checks
validation['box_clamp']['lead_screw_clearance_y0_mm']=round(LEAD_CLEAR_Y0,3)
validation['box_clamp']['lead_screw_clearance_radius_mm']=LEAD_CLEAR_R
validation['box_clamp']['plate_motion']=plate_motion
validation['box_clamp']['thread_motion']=thread_motion
validation['failures']=[]
with open(validation_path,'w',encoding='utf-8') as fh: json.dump(validation,fh,indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFront rework: 160 mm clamp plate, lead screws +/-65 mm (130 mm spacing), rectangular screw blocks; rear support-free DROPs only beside/between blocks; widened 160.8 mm plate corridor retained; full 5.5 mm lead-screw sweep clearance machined beside front holm.\n')
stage('complete')
