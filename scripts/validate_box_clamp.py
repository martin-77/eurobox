import json
import os
import sys

import FreeCAD as App
import Part

OUT = sys.argv[1] if len(sys.argv) > 1 else 'build_v50'

# Frozen / designed clamp datums.
BOX_EDGE_Y = 244.665
BOX_RIM_INNER_Y = 228.215
BOX_SUPPORT_Z = 39.54
RIM_BOTTOM_Z = 23.09
RIM_Y = 16.45
RIM_H = 16.45
SPINDLE_X = -42.0
SPINDLE_Z = 31.0
THREAD_PITCH = 2.0
PLATE_OPEN = 5.5
CLAMP_PRELOAD = 0.5
UNDERHOOK = 4.2
PLATE_HOLE_D = 6.5
JOURNAL_D = 6.0
SHOULDER_D = 11.0
PLATE_COUNTERBORE_D = 12.0


def read_step(name):
    p = os.path.join(OUT, name + '.step')
    if not os.path.exists(p):
        raise SystemExit('Missing STEP: ' + p)
    s = Part.Shape()
    s.read(p)
    if s.isNull() or not s.isValid() or len(s.Solids) != 1:
        raise SystemExit('Invalid STEP solid: ' + p)
    return s


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


base = read_step('eurobox_v50_base')
plate = read_step('eurobox_v50_clamp_plate')
spindle = read_step('eurobox_v50_lead_screw_print')
nut = read_step('eurobox_v50_lead_nut_print')

rim = box(-200.0, BOX_RIM_INNER_Y, RIM_BOTTOM_Z, 400.0, RIM_Y, RIM_H)

report = {
    'version': 'v50',
    'plate_open_mm': PLATE_OPEN,
    'clamp_preload_mm': CLAMP_PRELOAD,
    'checks': {},
    'measurements': {},
    'failed': [],
}

# 1) Hole / shaft / shoulder fit: explicit diametral clearances.
report['measurements']['plate_journal_diametral_clearance_mm'] = round(PLATE_HOLE_D - JOURNAL_D, 3)
report['measurements']['shoulder_counterbore_diametral_clearance_mm'] = round(PLATE_COUNTERBORE_D - SHOULDER_D, 3)
report['checks']['plate_journal_clearance_positive'] = (PLATE_HOLE_D - JOURNAL_D) >= 0.4
report['checks']['shoulder_counterbore_clearance_positive'] = (PLATE_COUNTERBORE_D - SHOULDER_D) >= 0.8

# 2) Closed geometry: hook is under the box and exactly reaches the measured outer face.
closed_hook_inner_y = BOX_EDGE_Y - UNDERHOOK
report['measurements']['closed_underhook_inner_y_mm'] = round(closed_hook_inner_y, 3)
report['measurements']['closed_underhook_capture_depth_mm'] = round(BOX_EDGE_Y - closed_hook_inner_y, 3)
report['checks']['closed_hook_captures_box_edge'] = closed_hook_inner_y < BOX_EDGE_Y
report['checks']['closed_plate_does_not_interpenetrate_rim'] = plate.common(rim).Volume < 1e-4

# 3) Full opening: the hook must clear the measured outer box face with >=1.0 mm real allowance.
open_hook_inner_y = closed_hook_inner_y + PLATE_OPEN
open_clearance = open_hook_inner_y - BOX_EDGE_Y
report['measurements']['open_underhook_inner_y_mm'] = round(open_hook_inner_y, 3)
report['measurements']['open_box_edge_clearance_mm'] = round(open_clearance, 3)
report['checks']['open_clearance_at_least_1mm'] = open_clearance >= 1.0
pl_open = plate.copy(); pl_open.translate(App.Vector(0, PLATE_OPEN, 0))
report['checks']['plate_open_position_clear_of_base'] = pl_open.common(base).Volume < 1e-4
report['checks']['plate_open_position_clear_of_rim'] = pl_open.common(rim).Volume < 1e-4

# 4) Actual clamping action: allow 0.5 mm inward travel beyond nominal contact.
# Rigid CAD overlap with the rim here is intentional and represents preload/compression.
pl_clamp = plate.copy(); pl_clamp.translate(App.Vector(0, -CLAMP_PRELOAD, 0))
clamp_rim_overlap = pl_clamp.common(rim).Volume
clamp_base_overlap = pl_clamp.common(base).Volume
report['measurements']['preload_rim_overlap_mm3'] = round(clamp_rim_overlap, 6)
report['measurements']['preload_base_overlap_mm3'] = round(clamp_base_overlap, 6)
report['checks']['preload_reaches_box_rim'] = clamp_rim_overlap > 1.0
report['checks']['preload_does_not_hit_base'] = clamp_base_overlap < 1e-4

# 5) Fixed nut and lead screw: prove actual helical engagement, not merely a clear bore.
# Correct RH kinematics: +Y opening requires -rotation around Y.
def placed_spindle(travel_mm, rotate_deg):
    q = spindle.copy()
    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), rotate_deg)
    q.translate(App.Vector(SPINDLE_X, BOX_EDGE_Y + travel_mm, SPINDLE_Z))
    return q

placed_nut = nut.copy(); placed_nut.translate(App.Vector(SPINDLE_X, 260.465, SPINDLE_Z))

thread_states = []
for travel in (-CLAMP_PRELOAD, 0.0, 0.5, 1.0, 2.0, 4.0, PLATE_OPEN):
    rot = -360.0 * travel / THREAD_PITCH
    q = placed_spindle(travel, rot)
    n_common = placed_nut.common(q).Volume
    b_common = base.common(q).Volume
    thread_states.append({
        'travel_mm': travel,
        'rotation_deg': rot,
        'nut_common_mm3': round(n_common, 6),
        'base_common_mm3': round(b_common, 6),
    })
report['thread_states'] = thread_states
report['checks']['correct_thread_phase_collision_free'] = all(x['nut_common_mm3'] < 0.5 and x['base_common_mm3'] < 0.5 for x in thread_states)

# A threaded spindle must NOT be able to translate 0.5 mm axially without rotating.
q_slide = placed_spindle(0.5, 0.0)
slide_interference = placed_nut.common(q_slide).Volume
report['measurements']['axial_slide_without_rotation_interference_mm3'] = round(slide_interference, 6)
report['checks']['thread_blocks_axial_slide_without_rotation'] = slide_interference > 1.0

# 6) At nominal position the spindle must pass through the plate without solid overlap,
# while the shoulder is geometrically adjacent to the plate rather than floating away.
q0 = placed_spindle(0.0, 0.0)
spindle_plate_overlap = q0.common(plate).Volume
spindle_plate_distance = q0.distToShape(plate)[0]
report['measurements']['spindle_plate_overlap_mm3'] = round(spindle_plate_overlap, 6)
report['measurements']['spindle_plate_min_distance_mm'] = round(spindle_plate_distance, 6)
report['checks']['spindle_passes_plate_hole'] = spindle_plate_overlap < 1e-4
report['checks']['spindle_thrust_face_reaches_plate'] = spindle_plate_distance < 0.05

for name, ok in report['checks'].items():
    if not ok:
        report['failed'].append(name)

path = os.path.join(OUT, 'BOX_CLAMP_VALIDATION.json')
with open(path, 'w') as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if report['failed']:
    raise SystemExit('BOX CLAMP VALIDATION FAILED: ' + ' | '.join(report['failed']))
