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
# Keep the proven rectangular lead-screw blocks, but move their axes outward to
# match the wider v60 base.  The free fields BESIDE the blocks get downward
# triangular DROPs between the upper tie and lower deck.  The blocks themselves
# remain rectangular.  Every DROP is >=45 deg from horizontal in print Z, so the
# front frame can be printed without support in the canonical base orientation.
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

BOSS_HALF_X = 11.0
BOSS_LOWER_HALF_X = 11.35
DROP_Z0 = F.FINAL_DECK_Z1
DROP_Z1 = F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_TIE_T
DROP_RISE = DROP_Z1 - DROP_Z0
DROP_Y0 = F.CAGE_Y0
DROP_Y1 = F.CAGE_Y1


def stage(msg):
    print('V60_FRONT_REWORK ' + msg, flush=True)


def triangle_drop(x0, x1):
    """Downward-pointing triangular prism, full cage depth in Y."""
    xm = (x0 + x1) / 2.0
    pts = [
        App.Vector(x0, DROP_Y0, DROP_Z1),
        App.Vector(x1, DROP_Y0, DROP_Z1),
        App.Vector(xm, DROP_Y0, DROP_Z0),
        App.Vector(x0, DROP_Y0, DROP_Z1),
    ]
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(App.Vector(0, DROP_Y1 - DROP_Y0, 0)).removeSplitter()


stage('build wider cage with support-free drops')
parts = [
    # Outer print guides, shifted with the wider 160 mm plate.
    C.box(FRAME_X0, F.PRINT_GUIDE_Y0, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y1-F.PRINT_GUIDE_Y0,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    C.box(PLATE_SWEEP_HALF_X, F.PRINT_GUIDE_Y0, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y1-F.PRINT_GUIDE_Y0,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    # Upper and lower horizontal frame members run across the widened front.
    C.box(FRAME_X0, F.CAGE_Y0-0.10,
          F.PRINT_BASE_PLANE_Z-F.PRINT_FRAME_TIE_T,
          FRAME_W, F.CAGE_Y1-F.CAGE_Y0+0.20, F.PRINT_FRAME_TIE_T),
    C.box(FRAME_X0, F.CAGE_Y0, F.FINAL_DECK_Z0,
          FRAME_W, F.PRINT_GUIDE_Y1-F.CAGE_Y0,
          F.FINAL_DECK_Z1-F.FINAL_DECK_Z0),
    # Rear portions of the two outer guides.
    C.box(FRAME_X0, F.CAGE_Y0-0.10, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y0-(F.CAGE_Y0-0.10)+0.35,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    C.box(PLATE_SWEEP_HALF_X, F.CAGE_Y0-0.10, F.PRINT_GUIDE_Z0,
          GUIDE_W, F.PRINT_GUIDE_Y0-(F.CAGE_Y0-0.10)+0.35,
          F.PRINT_BASE_PLANE_Z-F.PRINT_GUIDE_Z0),
    # Structural stitches from deck into both guides.
    C.box(-PLATE_SWEEP_HALF_X-F.GUIDE_STITCH_OVERLAP,
          F.CAGE_Y0, F.FINAL_DECK_Z1-F.GUIDE_STITCH_OVERLAP,
          2*F.GUIDE_STITCH_OVERLAP, F.PRINT_GUIDE_Y1-F.CAGE_Y0,
          2*F.GUIDE_STITCH_OVERLAP),
    C.box(PLATE_SWEEP_HALF_X-F.GUIDE_STITCH_OVERLAP,
          F.CAGE_Y0, F.FINAL_DECK_Z1-F.GUIDE_STITCH_OVERLAP,
          2*F.GUIDE_STITCH_OVERLAP, F.PRINT_GUIDE_Y1-F.CAGE_Y0,
          2*F.GUIDE_STITCH_OVERLAP),
]

# Screw blocks remain pure rectangular blocks, as requested.
for sx in SPINDLE_X:
    parts.append(C.box(sx-BOSS_HALF_X, F.CAGE_Y0, F.PRINT_FRAME_BOSS_Z0,
                       2*BOSS_HALF_X, F.CAGE_Y1-F.CAGE_Y0,
                       F.PRINT_BASE_PLANE_Z-F.PRINT_FRAME_BOSS_Z0))
    parts.append(C.box(sx-BOSS_LOWER_HALF_X, F.CAGE_Y0,
                       F.FINAL_DECK_Z1-0.35,
                       2*BOSS_LOWER_HALF_X, F.CAGE_Y1-F.CAGE_Y0,
                       F.PRINT_FRAME_BOSS_Z0-(F.FINAL_DECK_Z1-0.35)+0.35))

# DROPs only in the free fields next to the blocks.  The large centre field is
# split into three <=36 mm modules so every printed flank stays steeper than 45°.
left_block_x0 = SPINDLE_X[0] - BOSS_LOWER_HALF_X
left_block_x1 = SPINDLE_X[0] + BOSS_LOWER_HALF_X
right_block_x0 = SPINDLE_X[1] - BOSS_LOWER_HALF_X
right_block_x1 = SPINDLE_X[1] + BOSS_LOWER_HALF_X
center_x0 = left_block_x1
center_x1 = right_block_x0
center_step = (center_x1-center_x0)/3.0
DROP_FIELDS = [
    (FRAME_X0, left_block_x0),
    (center_x0, center_x0+center_step),
    (center_x0+center_step, center_x0+2.0*center_step),
    (center_x0+2.0*center_step, center_x1),
    (right_block_x1, FRAME_X1),
]
DROPS = []
for x0, x1 in DROP_FIELDS:
    d = triangle_drop(x0, x1)
    DROPS.append(d)
    parts.append(d)

CAGE = C.fuse_seq(parts, 'v60-wider-support-free-box-clamp-cage')
C.require_single(CAGE, 'v60 wider front cage')

stage('fuse wider front into structural core')
RIGHT_FULL = C.RIGHT.fuse(CAGE).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT wider front before machining')

# Preserve the complete rack-closure guide path expected by the rack rework.
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
    inner_y0 = F.CAGE_Y0 - 0.50
    RIGHT_FULL = RIGHT_FULL.cut(
        F.cyl_y(5.90, F.NUT_THREAD_Y0-inner_y0+0.20,
                sx, inner_y0, F.SPINDLE_Z)
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
PLATE = PLATE.fuse(
    C.box(-PLATE_X/2.0, PLATE_HOOK_Y0,
          F.RIM_BOTTOM_Z-F.UNDERHOOK_T,
          PLATE_X, PLATE_HOOK_Y1-PLATE_HOOK_Y0, F.UNDERHOOK_T)
)
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

if SPINDLE_X != (-65.0, 65.0):
    fail('lead screws are not at +/-65 mm')
if abs(SPINDLE_SPACING-130.0) > 1e-9:
    fail(f'lead screw spacing is not 130 mm: {SPINDLE_SPACING}')
if abs(PLATE_X-160.0) > 1e-9:
    fail(f'clamp plate is not 160 mm: {PLATE_X}')
if abs(PLATE_EDGE_MARGIN-15.0) > 1e-9:
    fail(f'plate screw edge margin is not 15 mm: {PLATE_EDGE_MARGIN}')

# The rectangular screw blocks must remain blocks: DROPs may touch their sides,
# but must not intrude into either rectangular block volume.
for sx in SPINDLE_X:
    block = C.box(sx-BOSS_LOWER_HALF_X, F.CAGE_Y0,
                  F.FINAL_DECK_Z1-0.35,
                  2*BOSS_LOWER_HALF_X, F.CAGE_Y1-F.CAGE_Y0,
                  F.PRINT_BASE_PLANE_Z-(F.FINAL_DECK_Z1-0.35))
    for i, d in enumerate(DROPS):
        cv = d.common(block).Volume
        if cv > 1e-4:
            fail(f'DROP {i} intrudes into rectangular screw block at X={sx}: {cv:.6f}')

# Support-free gate.  For an inverted triangle, rise/(half span) >=1 means the
# flank is at least 45 degrees from horizontal when printed in +Z.
drop_checks = []
for i, (x0, x1) in enumerate(DROP_FIELDS):
    half_span = (x1-x0)/2.0
    slope = DROP_RISE/half_span if half_span > 0 else 999.0
    angle = math.degrees(math.atan(slope))
    incorporated = RIGHT_FULL.common(DROPS[i]).Volume / DROPS[i].Volume
    drop_checks.append({
        'index': i,
        'x_mm': [round(x0,3), round(x1,3)],
        'half_span_mm': round(half_span,3),
        'rise_mm': round(DROP_RISE,3),
        'flank_angle_from_horizontal_deg': round(angle,3),
        'material_fraction': round(incorporated,6),
    })
    if angle < 45.0-1e-6:
        fail(f'DROP {i} is not support-free: {angle:.3f} deg')
    if incorporated < 0.999:
        fail(f'DROP {i} not fully incorporated: {incorporated:.6f}')

for side, sh in (('RIGHT',RIGHT_FULL),('LEFT',LEFT_FULL)):
    if sh.BoundBox.XLength > C.V60_X_TARGET_MAX+1e-6:
        fail(f'{side} exceeds 296 mm X target: {sh.BoundBox.XLength:.3f}')
    if sh.BoundBox.YLength > C.INDX_Y_MAX+1e-6:
        fail(f'{side} exceeds 275 mm Y target: {sh.BoundBox.YLength:.3f}')

# Plate and lead-screw motion remain collision-free after widening.
rim = C.box(-220, C.BOX_RIM_INNER_Y, F.RIM_BOTTOM_Z, 440, C.RIM_Y, C.RIM_H)
plate_motion=[]
for travel in (0,1,2,3,4,4.5,5.0,5.5):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-travel,0))
    bc=RIGHT_FULL.common(pl).Volume; rc=rim.common(pl).Volume
    plate_motion.append({'open_mm':travel,'base_common_mm3':round(bc,6),'rim_common_mm3':round(rc,6)})
    if bc>1e-4: fail(f'160mm plate/base collision at open={travel}: {bc:.6f}')
    if rc>1e-4: fail(f'160mm plate/rim collision at open={travel}: {rc:.6f}')

thread_motion=[]
for travel in (0,0.5,1.0,2.0,3.0,4.0,5.5):
    q=F.SPINDLE.copy()
    q.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*travel/F.THREAD_PITCH)
    q.translate(App.Vector(SPINDLE_X[0],F.PLATE_SPINDLE_Y-travel,F.SPINDLE_Z))
    bc=RIGHT_FULL.common(q).Volume
    thread_motion.append({'open_mm':travel,'base_common_mm3':round(bc,6)})
    if bc>1.0: fail(f'lead screw grossly collides after widening at open={travel}: {bc:.6f}')

# Exact handed geometry.
left_back = C.mirror_x(LEFT_FULL)
mirror_delta = abs(RIGHT_FULL.Volume-left_back.Volume)
if mirror_delta > 1e-4:
    fail(f'wider front handed bases not exact mirrors: {mirror_delta:.6f}')

if failures:
    raise RuntimeError('V60 FRONT REWORK HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('publish canonical front variables and exports')
F.RIGHT_FULL = RIGHT_FULL
F.LEFT_FULL = LEFT_FULL
F.PLATE = PLATE
F.SPINDLE_X = SPINDLE_X
C.export_shape('eurobox_v60_clamp_plate', PLATE)

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_wider_support_free_front'
validation['base']['right_bbox_mm'] = [round(RIGHT_FULL.BoundBox.XLength,3),round(RIGHT_FULL.BoundBox.YLength,3),round(RIGHT_FULL.BoundBox.ZLength,3)]
validation['base']['left_bbox_mm'] = [round(LEFT_FULL.BoundBox.XLength,3),round(LEFT_FULL.BoundBox.YLength,3),round(LEFT_FULL.BoundBox.ZLength,3)]
validation['base']['mirror_delta_mm3'] = round(mirror_delta,9)
validation['box_clamp']['plate_width_mm'] = PLATE_X
validation['box_clamp']['spindle_x_mm'] = list(SPINDLE_X)
validation['box_clamp']['spindle_spacing_mm'] = SPINDLE_SPACING
validation['box_clamp']['plate_screw_edge_margin_mm'] = PLATE_EDGE_MARGIN
validation['box_clamp']['frame_x_mm'] = [FRAME_X0, FRAME_X1]
validation['box_clamp']['rectangular_screw_blocks'] = True
validation['box_clamp']['drops_only_beside_blocks'] = True
validation['box_clamp']['support_free_drop_checks'] = drop_checks
validation['box_clamp']['plate_motion'] = plate_motion
validation['box_clamp']['thread_motion'] = thread_motion
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFront rework: 160 mm clamp plate, lead screws at +/-65 mm (130 mm spacing), rectangular screw blocks retained, five >=45deg support-free DROPs only in the free fields beside/between the blocks.\n')

stage('complete')
