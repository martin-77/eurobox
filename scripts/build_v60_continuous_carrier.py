import json
import os

import FreeCAD as App
import Part

import build_v60 as C

# ---------------------------------------------------------------------------
# Canonical v60 load path
# ---------------------------------------------------------------------------
# The base is one continuous rack-side carrier.  The two rack clamps and the
# rear stop hang below / from this carrier; they are not separate structural
# towers.  The two long box-support holms fuse into the same carrier.
#
# The carrier is a closed box section on both Y faces.  The former open side
# windows were not useful here: this part is still the primary rack carrier and
# therefore keeps continuous outer walls, while the central saddle web remains
# as an internal load path around the rack tube.

CARRIER_X0 = C.FRONT_CLAMP_X - C.ARM_W / 2.0       # -96
CARRIER_X1 = C.REAR_SUPPORT_X + C.ARM_W / 2.0      # +196
CARRIER_Y0 = -8.0
CARRIER_Y1 = C.ARM_Y0 + 2.00                         # deliberate structural overlap into front long holm
CARRIER_TOP_T = C.FLANGE_T
CARRIER_BOTTOM_T = C.FLANGE_T
CARRIER_WEB_Y0 = -7.0
CARRIER_WEB_Y1 = 7.0
CARRIER_WEB_Z0 = 0.0
CARRIER_TOP_Z1 = C.BOX_SUPPORT_Z
CARRIER_TOP_Z0 = CARRIER_TOP_Z1 - CARRIER_TOP_T
CARRIER_BOTTOM_Z0 = C.ARM_BOTTOM_Z
CARRIER_BOTTOM_Z1 = CARRIER_BOTTOM_Z0 + CARRIER_BOTTOM_T
CARRIER_SADDLE_R = C.UPPER_SADDLE_R
CARRIER_SIDE_T = C.WEB_T
CARRIER_SIDE_Z0 = CARRIER_BOTTOM_Z1
CARRIER_SIDE_Z1 = CARRIER_TOP_Z0

# Close both X ends of the hollow carrier. The former "closed box" only had
# Y-side walls; its X end faces were still open and exposed the green-shelf
# DROP in the slicer. Keep the cap inside the existing X envelope and overlap
# top/bottom flanges by 0.20 mm for a robust fused printable wall.
CARRIER_END_T = C.WEB_T
CARRIER_END_OVERLAP_Z = 0.20
CARRIER_END_Z0 = CARRIER_BOTTOM_Z1 - CARRIER_END_OVERLAP_Z
CARRIER_END_Z1 = CARRIER_TOP_Z0 + CARRIER_END_OVERLAP_Z

# Support the ACTUAL green shelf in the closed carrier.
#
# In Y/Z cross-section the visible unsupported shelf is the lower flange from
# the internal saddle web (+Y face at Y=7) to the outer +Y side wall inner face
# at Y=22.8.  The BASE is printed upside-down, so installed high-Z material is
# printed first.  The DROP must therefore start HIGH on the saddle web and grow
# outward/down toward the green shelf/outer wall.  The previous experiment had
# this ramp reversed and therefore put the useful mass on the wrong side.
CARRIER_GREEN_SHELF_Y0 = CARRIER_WEB_Y1
CARRIER_GREEN_SHELF_Y1 = CARRIER_Y1 - CARRIER_SIDE_T
CARRIER_GREEN_SHELF_SPAN = CARRIER_GREEN_SHELF_Y1 - CARRIER_GREEN_SHELF_Y0
CARRIER_GREEN_SHELF_Z = CARRIER_BOTTOM_Z1
CARRIER_GREEN_DROP_ROOT_Z = CARRIER_GREEN_SHELF_Z + CARRIER_GREEN_SHELF_SPAN


def make_green_shelf_drop():
    # Same smooth self-supporting principle as the proven long-holm haunches,
    # but rotated into the carrier cavity.  Root = internal saddle web;
    # free/tip side = outer +Y wall.  The complete 15.8 mm shelf is supported.
    y_root = CARRIER_GREEN_SHELF_Y0
    y_tip = CARRIER_GREEN_SHELF_Y1
    z_floor = CARRIER_GREEN_SHELF_Z
    z_root = CARRIER_GREEN_DROP_ROOT_Z
    span = y_tip - y_root

    curve = []
    for i in range(19):
        t = i / 18.0
        y = y_root + span * C._smoothstep(t)
        z = z_root + (z_floor - z_root) * t
        curve.append(App.Vector(0.0, y, z))

    yz = [
        App.Vector(0.0, y_root, z_floor),
        App.Vector(0.0, y_root, z_root),
    ] + curve[1:] + [App.Vector(0.0, y_root, z_floor)]

    face = Part.Face(Part.makePolygon(yz))
    q = face.extrude(App.Vector(CARRIER_X1 - CARRIER_X0, 0, 0))
    q.translate(App.Vector(CARRIER_X0, 0, 0))
    C.require_single(q, 'green-shelf-drop')
    return q


def make_continuous_carrier():
    dx = CARRIER_X1 - CARRIER_X0
    top = C.box(
        CARRIER_X0, CARRIER_Y0, CARRIER_TOP_Z0,
        dx, CARRIER_Y1 - CARRIER_Y0, CARRIER_TOP_T,
    )
    bottom = C.box(
        CARRIER_X0, CARRIER_Y0, CARRIER_BOTTOM_Z0,
        dx, CARRIER_Y1 - CARRIER_Y0, CARRIER_BOTTOM_T,
    )
    web_raw = C.box(
        CARRIER_X0, CARRIER_WEB_Y0, CARRIER_WEB_Z0,
        dx, CARRIER_WEB_Y1 - CARRIER_WEB_Y0,
        CARRIER_TOP_Z0 - CARRIER_WEB_Z0,
    )
    saddle = C.cyl_x(
        CARRIER_SADDLE_R,
        dx + 2.0,
        CARRIER_X0 - 1.0,
        0.0,
        0.0,
    )
    web = web_raw.cut(saddle).removeSplitter()

    # Close the visible carrier section on both sides.  Keep the original outer
    # envelope: the walls grow inward from Y0/Y1 and bridge only between the
    # lower and upper flanges, so there is no additional tyre/box-side growth.
    side_y0 = C.box(
        CARRIER_X0, CARRIER_Y0, CARRIER_SIDE_Z0,
        dx, CARRIER_SIDE_T, CARRIER_SIDE_Z1 - CARRIER_SIDE_Z0,
    )
    side_y1 = C.box(
        CARRIER_X0, CARRIER_Y1 - CARRIER_SIDE_T, CARRIER_SIDE_Z0,
        dx, CARRIER_SIDE_T, CARRIER_SIDE_Z1 - CARRIER_SIDE_Z0,
    )
    end_x0 = C.box(
        CARRIER_X0, CARRIER_Y0, CARRIER_END_Z0,
        CARRIER_END_T, CARRIER_Y1-CARRIER_Y0, CARRIER_END_Z1-CARRIER_END_Z0,
    )
    end_x1 = C.box(
        CARRIER_X1-CARRIER_END_T, CARRIER_Y0, CARRIER_END_Z0,
        CARRIER_END_T, CARRIER_Y1-CARRIER_Y0, CARRIER_END_Z1-CARRIER_END_Z0,
    )
    green_drop = make_green_shelf_drop()
    q = C.fuse_seq(
        [top, bottom, web, side_y0, side_y1, end_x0, end_x1, green_drop],
        'continuous-rack-carrier-fully-closed-box-with-green-shelf-drop',
    )
    C.require_single(q, 'continuous-rack-carrier-closed-box')
    return q


def make_hanging_upper_station(xc):
    # v50 clamp mechanics without a separate I-beam root tower.  The station
    # is fused directly into the continuous carrier above it.
    bridge = C.box(
        xc - C.FIXED_STATION_HALF_X,
        C.UPPER_BRIDGE_Y0,
        0.0,
        2.0 * C.FIXED_STATION_HALF_X,
        C.UPPER_BRIDGE_Y1 - C.UPPER_BRIDGE_Y0,
        C.UPPER_BRIDGE_Z1,
    )
    upper_pivot = C.cyl_x(
        C.UPPER_PIVOT_R,
        C.UPPER_PIVOT_W,
        xc - C.UPPER_PIVOT_W / 2.0,
        C.PIN_Y,
        C.PIN_Z,
    )
    gusset_pts = [
        App.Vector(xc-C.UPPER_PIVOT_W/2.0, C.UPPER_GUSSET_LOWER_Y0, C.UPPER_GUSSET_LOWER_Z),
        App.Vector(xc-C.UPPER_PIVOT_W/2.0, C.UPPER_GUSSET_LOWER_Y1, C.UPPER_GUSSET_LOWER_Z),
        App.Vector(xc-C.UPPER_PIVOT_W/2.0, C.UPPER_GUSSET_TOP_Y1, C.UPPER_GUSSET_TOP_Z),
        App.Vector(xc-C.UPPER_PIVOT_W/2.0, C.UPPER_GUSSET_TOP_Y0, C.UPPER_GUSSET_TOP_Z),
    ]
    upper_gusset = Part.Face(
        Part.makePolygon(gusset_pts + [gusset_pts[0]])
    ).extrude(App.Vector(C.UPPER_PIVOT_W, 0, 0))
    pivot_web = C.box(
        xc-C.UPPER_PIVOT_W/2.0, -10.5, -5.5,
        C.UPPER_PIVOT_W, 5.0, 7.5,
    )
    saddle_back = C.box(
        xc-C.UPPER_PIVOT_W/2.0, -8.0, -4.5,
        C.UPPER_PIVOT_W, 2.5, 6.5,
    )
    q = C.fuse_seq(
        [bridge, upper_pivot, upper_gusset, pivot_web, saddle_back],
        f'hanging-upper-station@{xc}',
    )
    q = q.cut(C.cyl_x(C.UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0)).removeSplitter()
    q = q.cut(C.cyl_x(C.PIN_HOLE_D/2.0, 40.0, xc-20.0, C.PIN_Y, C.PIN_Z)).removeSplitter()
    q = q.cut(
        Part.makeCylinder(
            C.RACK_M4_BASE_CLEAR_D/2.0,
            12.0,
            App.Vector(xc, C.RACK_CLOSURE_Y, -1.0),
            App.Vector(0,0,1),
        )
    ).removeSplitter()
    nut = C.hex_z(C.RACK_M4_NUT_AF, C.RACK_M4_NUT_H, C.RACK_M4_NUT_Z0)
    nut.translate(App.Vector(xc, C.RACK_CLOSURE_Y, 0.0))
    q = q.cut(nut).removeSplitter()
    # No lateral nut-loading slot here. The production rack closure is rebuilt
    # later with a top-loaded metal nut/retainer, so a side breakout is both
    # obsolete and visually/structurally harmful.
    C.require_single(q, f'hanging-upper-station@{xc}')
    return q


def make_hanging_backstop():
    # The 50 mm stop is the third hanging function on the same carrier.
    # Its top/root deliberately overlaps the carrier and the moved rear holm.
    panel = C.box(C.BACKSTOP_X0, 8.0, -42.0, C.BACKSTOP_W, 4.0, 50.0)
    root = C.box(C.BACKSTOP_X0, 0.0, 7.0, C.BACKSTOP_W, CARRIER_Y1, 15.0)
    bridge = C.box(
        C.BACKSTOP_X0,
        0.0,
        18.0,
        C.BACKSTOP_W,
        CARRIER_Y1,
        C.BOX_SUPPORT_Z - 18.0,
    )
    q = C.fuse_seq([panel, root, bridge], 'hanging-backstop')
    C.require_single(q, 'hanging-backstop')
    return q


def build_clean_right():
    carrier = make_continuous_carrier()
    front_long = C.make_long_support(C.FRONT_CLAMP_X, C.ARM_Y0)
    rear_long = C.make_long_support(C.REAR_SUPPORT_X, 0.0)
    front_clamp = make_hanging_upper_station(C.FRONT_CLAMP_X)
    rear_clamp = make_hanging_upper_station(C.REAR_CLAMP_X)
    backstop = make_hanging_backstop()
    crosshead = C.make_crosshead()

    q = C.fuse_seq(
        [carrier, front_long, rear_long, front_clamp, rear_clamp, backstop, crosshead],
        'v60 continuous-carrier RIGHT',
    )
    q = q.cut(C.make_plate_sweep_clearance()).removeSplitter()

    # Re-open all functional clamp bores after fusing into the carrier.
    for xc in C.CLAMP_X:
        q = q.cut(C.cyl_x(C.UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0)).removeSplitter()
        q = q.cut(C.cyl_x(C.PIN_HOLE_D/2.0, 40.0, xc-20.0, C.PIN_Y, C.PIN_Z)).removeSplitter()
        q = q.cut(
            Part.makeCylinder(
                C.RACK_M4_BASE_CLEAR_D/2.0,
                12.0,
                App.Vector(xc, C.RACK_CLOSURE_Y, -1.0),
                App.Vector(0,0,1),
            )
        ).removeSplitter()

    C.require_single(q, 'v60 continuous-carrier RIGHT final')
    return q, carrier, front_long, rear_long, front_clamp, rear_clamp, backstop


RIGHT, CARRIER, FRONT_LONG, REAR_LONG, FRONT_CLAMP, REAR_CLAMP, BACKSTOP = build_clean_right()
GREEN_SHELF_DROP = make_green_shelf_drop()
LEFT = C.mirror_x(RIGHT)

# Make the clean architecture canonical for the full builder and all downstream
# validators / exports.
C.RIGHT = RIGHT
C.LEFT = LEFT
C.make_upper_station = make_hanging_upper_station
C.make_backstop = make_hanging_backstop

failures = []

# Hard-check the exact requested geometry, not a similarly named flange.
# Away from the two rack-closure stations the entire DROP must survive in the
# final continuous-carrier core.  A centre witness is used because the later
# rack-closure service machining is intentionally local at X=-80/+80.
green_drop_center_probe = C.box(
    40.0,
    CARRIER_GREEN_SHELF_Y0,
    CARRIER_GREEN_SHELF_Z,
    20.0,
    CARRIER_GREEN_SHELF_SPAN,
    CARRIER_GREEN_SHELF_SPAN + 0.10,
).common(GREEN_SHELF_DROP)
green_drop_center_volume = green_drop_center_probe.Volume
green_drop_center_common = RIGHT.common(green_drop_center_probe).Volume
green_drop_center_fraction = (
    green_drop_center_common / green_drop_center_volume
    if green_drop_center_volume > 1e-9 else 0.0
)
if green_drop_center_fraction < 0.999:
    failures.append(
        f'green carrier shelf DROP missing at centre witness: '
        f'{green_drop_center_fraction:.6f}'
    )

# At the actual rack hand-screw Y=11 the DROP is intentionally allowed to be
# locally re-machined later by the closure/nut-retainer stack; it must not move
# the rack screw axis or any hole datum.
if abs(C.RACK_CLOSURE_Y - 11.0) > 1e-9:
    failures.append('rack closure Y datum moved while adding green shelf DROP')

# Main carrier must be fully incorporated and continuously tie all three hanging
# functions plus both long box-support holms.
carrier_fraction = RIGHT.common(CARRIER).Volume / CARRIER.Volume
if carrier_fraction < 0.995:
    failures.append(f'continuous carrier not fully incorporated: {carrier_fraction:.6f}')

# The two outside faces are structural walls, not visual openings.  Probe the
# exact wall solids so any future regression back to an open section hard-fails.
side_wall_probes = {
    'y0': C.box(
        CARRIER_X0, CARRIER_Y0, CARRIER_SIDE_Z0,
        CARRIER_X1-CARRIER_X0, CARRIER_SIDE_T,
        CARRIER_SIDE_Z1-CARRIER_SIDE_Z0,
    ),
    'y1': C.box(
        CARRIER_X0, CARRIER_Y1-CARRIER_SIDE_T, CARRIER_SIDE_Z0,
        CARRIER_X1-CARRIER_X0, CARRIER_SIDE_T,
        CARRIER_SIDE_Z1-CARRIER_SIDE_Z0,
    ),
}
side_wall_fractions = {}
for label, probe in side_wall_probes.items():
    frac = RIGHT.common(probe).Volume / probe.Volume
    side_wall_fractions[label] = round(frac, 6)
    if frac < 0.999:
        failures.append(f'continuous carrier {label} side wall is not closed: {frac:.6f}')

# The two X end faces must also be real walls. This is the regression gate for
# the exact openings visible in the slicer screenshot.
end_wall_probes = {
    'x0': C.box(
        CARRIER_X0, CARRIER_Y0, CARRIER_END_Z0,
        CARRIER_END_T, CARRIER_Y1-CARRIER_Y0, CARRIER_END_Z1-CARRIER_END_Z0,
    ),
    'x1': C.box(
        CARRIER_X1-CARRIER_END_T, CARRIER_Y0, CARRIER_END_Z0,
        CARRIER_END_T, CARRIER_Y1-CARRIER_Y0, CARRIER_END_Z1-CARRIER_END_Z0,
    ),
}
end_wall_fractions = {}
for label, probe in end_wall_probes.items():
    frac = RIGHT.common(probe).Volume / probe.Volume
    end_wall_fractions[label] = round(frac, 6)
    if frac < 0.999:
        failures.append(f'continuous carrier {label} end wall is not closed: {frac:.6f}')

station_overlaps = []
for label, station in [('front', FRONT_CLAMP), ('rear', REAR_CLAMP)]:
    ov = CARRIER.common(station).Volume
    station_overlaps.append({'station': label, 'carrier_common_mm3': round(ov, 3)})
    if ov < 100.0:
        failures.append(f'{label} clamp is not substantially hanging from continuous carrier: {ov:.3f}')

backstop_overlap = CARRIER.common(BACKSTOP).Volume
if backstop_overlap < 100.0:
    failures.append(f'backstop is not substantially hanging from continuous carrier: {backstop_overlap:.3f}')

front_holm_overlap = CARRIER.common(FRONT_LONG).Volume
rear_holm_overlap = CARRIER.common(REAR_LONG).Volume
if front_holm_overlap < 100.0:
    failures.append(f'front long holm not fused into continuous carrier: {front_holm_overlap:.3f}')
if rear_holm_overlap < 100.0:
    failures.append(f'rear long holm not fused into continuous carrier: {rear_holm_overlap:.3f}')

# The measured rack tube must remain free; the carrier uses the same v50 saddle.
tube = C.cyl_x(C.RACK_R, 400.0, -200.0, 0.0, 0.0)
tube_common = RIGHT.common(tube).Volume
if tube_common > 1e-4:
    failures.append(f'continuous carrier collides with rack tube: {tube_common:.6f} mm3')

# Print and motion constraints remain hard.
plate_common = RIGHT.common(C.make_plate_sweep_clearance()).Volume
if plate_common > 1e-4:
    failures.append(f'continuous carrier blocks box-clamp plate corridor: {plate_common:.6f} mm3')
if RIGHT.BoundBox.XLength > C.V60_X_TARGET_MAX + 1e-6:
    failures.append(f'continuous carrier exceeds 296 mm X target: {RIGHT.BoundBox.XLength:.3f}')
if RIGHT.BoundBox.YLength > C.INDX_Y_MAX + 1e-6:
    failures.append(f'continuous carrier exceeds 275 mm Y target: {RIGHT.BoundBox.YLength:.3f}')

report_path = os.path.join(C.OUT, 'VALIDATION_v60.json')
with open(report_path, 'r', encoding='utf-8') as f:
    report = json.load(f)
report['stage'] = 'clean_structural_core_continuous_carrier'
report['architecture'] = 'one fully closed-box continuous rack-side carrier with Y side walls and X end caps; two rack clamps and 50 mm backstop hang from it; long box holms fuse into same carrier'
report['geometry']['right_bbox_mm'] = [round(RIGHT.BoundBox.XLength,3), round(RIGHT.BoundBox.YLength,3), round(RIGHT.BoundBox.ZLength,3)]
report['geometry']['left_bbox_mm'] = [round(LEFT.BoundBox.XLength,3), round(LEFT.BoundBox.YLength,3), round(LEFT.BoundBox.ZLength,3)]
report['geometry']['right_volume_mm3'] = round(RIGHT.Volume,3)
report['geometry']['left_volume_mm3'] = round(LEFT.Volume,3)
report['geometry']['continuous_carrier'] = {
    'section': 'fully_closed_box_with_internal_saddle_web',
    'x_mm': [CARRIER_X0, CARRIER_X1],
    'y_mm': [CARRIER_Y0, CARRIER_Y1],
    'top_z_mm': [CARRIER_TOP_Z0, CARRIER_TOP_Z1],
    'bottom_z_mm': [CARRIER_BOTTOM_Z0, CARRIER_BOTTOM_Z1],
    'side_wall_thickness_mm': CARRIER_SIDE_T,
    'side_wall_z_mm': [CARRIER_SIDE_Z0, CARRIER_SIDE_Z1],
    'side_wall_material_fractions': side_wall_fractions,
    'end_wall_thickness_mm': CARRIER_END_T,
    'end_wall_z_mm': [CARRIER_END_Z0, CARRIER_END_Z1],
    'end_wall_material_fractions': end_wall_fractions,
    'green_shelf_drop': {
        'target': 'green lower carrier shelf between saddle web +Y face and outer +Y wall',
        'print_orientation': 'BASE upside-down; high installed Z prints first',
        'root_side': 'internal saddle web at Y=7',
        'tip_side': 'outer +Y side wall inner face at Y=22.8',
        'y_mm': [round(CARRIER_GREEN_SHELF_Y0,3), round(CARRIER_GREEN_SHELF_Y1,3)],
        'shelf_z_mm': round(CARRIER_GREEN_SHELF_Z,3),
        'root_z_mm': round(CARRIER_GREEN_DROP_ROOT_Z,3),
        'span_mm': round(CARRIER_GREEN_SHELF_SPAN,3),
        'centre_witness_material_fraction': round(green_drop_center_fraction,6),
        'rack_closure_y_mm': C.RACK_CLOSURE_Y,
        'rack_closure_strategy': 'later closure machining re-opens only the local screw/nut/retainer service volume',
    },
    'saddle_radius_mm': CARRIER_SADDLE_R,
    'material_fraction': round(carrier_fraction,6),
    'rack_tube_common_mm3': round(tube_common,9),
    'front_holm_common_mm3': round(front_holm_overlap,3),
    'rear_holm_common_mm3': round(rear_holm_overlap,3),
    'clamp_overlaps': station_overlaps,
    'backstop_common_mm3': round(backstop_overlap,3),
}
report['geometry']['plate_sweep_common_mm3'] = round(plate_common,9)
report['failures'] = list(dict.fromkeys(report.get('failures', []) + failures))
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

if failures:
    raise RuntimeError('Continuous-carrier v60 checks failed: ' + ' | '.join(failures))
