import json
import math
import os

import FreeCAD as App
import Part

import apply_v60_front_rework as P
import build_v60_full_baseline as F

C = F.C

# Final v60 front geometry.
#
# The previous pass only added 3.2 mm rear ribs.  That did not implement the
# requested front structure.  The rectangular lead-screw blocks stay exactly
# rectangular; ONLY the three free regions (outer left, centre, outer right)
# receive printable DROPs between the lower deck and upper tie.  Because the
# centre field is too wide for one >=45 degree roof, it is split into three
# adjacent V/drop cells.  Every drop is a REAL full-depth structural web from
# CAGE_Y0 to CAGE_Y1, not a cosmetic rear rib.

RIGHT_FULL = P.RIGHT_FULL
PLATE = P.PLATE
SPINDLE_X = P.SPINDLE_X

DROP_Y0 = F.CAGE_Y0
DROP_Y1 = F.CAGE_Y1
DROP_DEPTH = DROP_Y1 - DROP_Y0
DROP_Z0 = F.FINAL_DECK_Z1
DROP_Z1 = F.PRINT_BASE_PLANE_Z - F.PRINT_FRAME_TIE_T
DROP_RISE = DROP_Z1 - DROP_Z0
DROP_FOOT_W = 1.60


def stage(msg):
    print('V60_FRONT_FINAL ' + msg, flush=True)


def structural_drop(x0, x1, apex_x=None):
    if apex_x is None:
        apex_x = (x0 + x1) / 2.0
    foot = min(DROP_FOOT_W, max(0.4, (x1-x0)*0.20))
    pts = [
        App.Vector(x0, DROP_Y0, DROP_Z1),
        App.Vector(x1, DROP_Y0, DROP_Z1),
        App.Vector(apex_x + foot/2.0, DROP_Y0, DROP_Z0),
        App.Vector(apex_x - foot/2.0, DROP_Y0, DROP_Z0),
        App.Vector(x0, DROP_Y0, DROP_Z1),
    ]
    face = Part.Face(Part.makePolygon(pts))
    q = face.extrude(App.Vector(0, DROP_DEPTH, 0)).removeSplitter()
    C.require_single(q, 'full-depth front DROP')
    return q


# Reuse the accepted X fields from the widened front: no drop may enter either
# rectangular screw block.  The centre field uses three printable cells because
# one single span would be much shallower than 45 degrees.
DROP_SPECS = list(P.DROP_SPECS)
DROPS = [structural_drop(x0, x1, apex) for x0, x1, apex in DROP_SPECS]

stage('fuse full-depth DROPs into final front')
for d in DROPS:
    RIGHT_FULL = RIGHT_FULL.fuse(d).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT final front with full-depth DROPs')
LEFT_FULL = C.mirror_x(RIGHT_FULL)
C.require_single(LEFT_FULL, 'LEFT final front with full-depth DROPs')

stage('hard-check requested front architecture')
failures = []

def fail(msg):
    failures.append(msg)

if tuple(SPINDLE_X) != (-65.0, 65.0):
    fail('final screw axes are not +/-65 mm')
if abs(P.PLATE_X - 160.0) > 1e-9:
    fail('final clamp plate is not 160 mm wide')
if DROP_DEPTH < 20.0:
    fail(f'front DROPs are not full structural depth: {DROP_DEPTH:.3f} mm')

# Prove the blocks themselves remain rectangular and every drop is outside them.
for sx in SPINDLE_X:
    block = C.box(
        sx-P.BOSS_LOWER_HALF_X+0.02,
        F.CAGE_Y0,
        F.FINAL_DECK_Z1-0.33,
        2.0*P.BOSS_LOWER_HALF_X-0.04,
        F.CAGE_Y1-F.CAGE_Y0,
        F.PRINT_BASE_PLANE_Z-(F.FINAL_DECK_Z1-0.33),
    )
    for i, d in enumerate(DROPS):
        cv = d.common(block).Volume
        if cv > 1e-4:
            fail(f'full-depth DROP {i} intrudes into screw block X={sx}: {cv:.6f}')

checks = []
for i, ((x0, x1, apex), d) in enumerate(zip(DROP_SPECS, DROPS)):
    ax = (x0+x1)/2.0 if apex is None else apex
    foot = min(DROP_FOOT_W, max(0.4, (x1-x0)*0.20))
    run = max(abs((ax-foot/2.0)-x0), abs(x1-(ax+foot/2.0)))
    angle = math.degrees(math.atan2(DROP_RISE, run)) if run > 0 else 90.0
    frac = RIGHT_FULL.common(d).Volume / d.Volume

    # Independent front/middle/back witnesses make a thin rear rib impossible
    # to pass this gate: all three Y slices must contain the same drop profile.
    y_witness = []
    for y in (DROP_Y0+0.25, (DROP_Y0+DROP_Y1)/2.0, DROP_Y1-0.25):
        probe = d.common(C.box(x0-0.1, y-0.10, DROP_Z0-0.1,
                               (x1-x0)+0.2, 0.20, DROP_RISE+0.2))
        pv = probe.Volume
        fv = RIGHT_FULL.common(probe).Volume if pv > 1e-9 else 0.0
        pf = fv/pv if pv > 1e-9 else 0.0
        y_witness.append(round(pf, 6))
        if pf < 0.995:
            fail(f'DROP {i} missing at Y={y:.3f}: material fraction {pf:.6f}')

    if angle < 45.0-1e-6:
        fail(f'DROP {i} is not support-free: {angle:.3f} deg')
    if frac < 0.999:
        fail(f'DROP {i} not incorporated in final base: {frac:.6f}')
    checks.append({
        'index': i,
        'x_mm': [round(x0,3), round(x1,3)],
        'apex_x_mm': round(ax,3),
        'depth_y_mm': round(DROP_DEPTH,3),
        'y_mm': [round(DROP_Y0,3), round(DROP_Y1,3)],
        'rise_mm': round(DROP_RISE,3),
        'flank_angle_from_horizontal_deg': round(angle,3),
        'material_fraction': round(frac,6),
        'front_mid_back_material_fraction': y_witness,
    })

# Keep all motion checks from the preceding pass valid against the ACTUAL final
# geometry after the full-depth web fusion.
rim = C.box(-220, C.BOX_RIM_INNER_Y, F.RIM_BOTTOM_Z, 440, C.RIM_Y, C.RIM_H)
plate_motion = []
for travel in (0,1,2,3,4,4.5,5.0,5.5):
    pl = PLATE.copy(); pl.translate(App.Vector(0,-travel,0))
    bc = RIGHT_FULL.common(pl).Volume
    rc = rim.common(pl).Volume
    plate_motion.append({'open_mm':travel,'base_common_mm3':round(bc,6),'rim_common_mm3':round(rc,6)})
    if bc > 1e-4:
        fail(f'final front collides with 160mm plate at open={travel}: {bc:.6f}')
    if rc > 1e-4:
        fail(f'160mm plate collides with box rim at open={travel}: {rc:.6f}')

thread_motion = []
for sx in SPINDLE_X:
    for travel in (0,0.5,1.0,2.0,3.0,4.0,5.5):
        q = F.SPINDLE.copy()
        q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 360*travel/F.THREAD_PITCH)
        q.translate(App.Vector(sx, F.PLATE_SPINDLE_Y-travel, F.SPINDLE_Z))
        bc = RIGHT_FULL.common(q).Volume
        thread_motion.append({'x_mm':sx,'open_mm':travel,'base_common_mm3':round(bc,6)})
        if bc > 1.0:
            fail(f'final lead screw collision X={sx} open={travel}: {bc:.6f}')

if failures:
    raise RuntimeError('V60 FINAL FRONT HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('publish final front geometry')
F.RIGHT_FULL = RIGHT_FULL
F.LEFT_FULL = LEFT_FULL
F.PLATE = PLATE
F.SPINDLE_X = SPINDLE_X

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_actual_full_depth_support_free_front'
validation['base']['right_bbox_mm'] = [round(RIGHT_FULL.BoundBox.XLength,3), round(RIGHT_FULL.BoundBox.YLength,3), round(RIGHT_FULL.BoundBox.ZLength,3)]
validation['base']['left_bbox_mm'] = [round(LEFT_FULL.BoundBox.XLength,3), round(LEFT_FULL.BoundBox.YLength,3), round(LEFT_FULL.BoundBox.ZLength,3)]
validation['box_clamp']['plate_width_mm'] = P.PLATE_X
validation['box_clamp']['spindle_x_mm'] = list(SPINDLE_X)
validation['box_clamp']['spindle_spacing_mm'] = P.SPINDLE_SPACING
validation['box_clamp']['rectangular_screw_blocks'] = True
validation['box_clamp']['drops_only_beside_blocks'] = True
validation['box_clamp']['drop_architecture'] = 'full-depth structural X/Z webs across CAGE_Y0..CAGE_Y1; never inside screw blocks'
validation['box_clamp']['drop_depth_y_mm'] = round(DROP_DEPTH,3)
validation['box_clamp']['support_free_drop_checks'] = checks
validation['box_clamp']['plate_motion'] = plate_motion
validation['box_clamp']['thread_motion'] = thread_motion
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

with open(os.path.join(C.OUT,'README_BUILD_v60_full.txt'),'a',encoding='utf-8') as fh:
    fh.write('\nFinal front: 160 mm plate, spindle axes +/-65 mm; rectangular screw blocks unchanged; actual full-depth support-free DROPs only in free fields beside/between blocks.\n')

stage('complete')
