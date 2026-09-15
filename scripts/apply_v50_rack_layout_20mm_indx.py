from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# ---------------------------------------------------------------------------
# Real-bike longitudinal layout from the 2026-09-15 rack measurement/photo.
# ---------------------------------------------------------------------------
# Installation target (physical coordinates measured from the front end of the
# straight upper rack tube):
#   fixed front-clamp body front edge       20 mm
#   front clamp centre                     39 mm
#   rear clamp centre                     199 mm
#   rear fixed body rear edge             218 mm
#   backstop panel                        249..299 mm
#   moved rear support-holm centre        299 mm
#   rear support outer edge               315 mm
#
# Why 160 mm clamp spacing instead of the former 180 mm:
# the fixed rear clamp must remain well ahead of the downward-curving rack tube,
# while the backstop is allowed to continue into that rear region. Keeping the
# proven 31 mm clear gap from the reinforced fixed-clamp body to the 50 mm panel
# and moving the rear support holm to the panel's rear edge gives a 295 mm final
# part envelope. This leaves 3 mm total reserve inside the CORE One L + INDX
# X build volume of 298 mm. The other in-bed dimension is about 247 mm, below
# the INDX Y limit of 275 mm.

# Move the two actual rack clamps from +/-90 to +/-80 => 160 mm C-C.
if 'CLAMP_X = (-90.0, 90.0)' not in s:
    raise SystemExit('Could not locate former 180 mm rack-clamp spacing')
s = s.replace('CLAMP_X = (-90.0, 90.0)', 'CLAMP_X = (-80.0, 80.0)', 1)

# The early frozen-interface assertion was intentionally tied to the previous
# measured-layout assumption. Replace it by the now measured/print-bed-derived
# layout gate; all true mechanical datums (tube, pivot, spindle etc.) remain
# frozen exactly as before.
s = s.replace(
    "    'clamp_x_plusminus90': tuple(CLAMP_X) == (-90.0, 90.0),",
    "    'clamp_spacing_160mm_layout': tuple(CLAMP_X) == (-80.0, 80.0),",
    1,
)

parts_anchor = "PARTS = {\n"
if parts_anchor not in s:
    raise SystemExit('Could not locate PARTS anchor for final longitudinal rack layout')

layout_geometry = r'''# ---------------------------------------------------------------------------
# FINAL measured longitudinal rack layout / INDX print-envelope pass.
# ---------------------------------------------------------------------------
RACK_LAYOUT_FRONT_MARGIN_MM = 20.0
RACK_FIXED_STATION_HALF_X_MM = 19.0
RACK_LAYOUT_CLAMP_SPACING_MM = REAR_CLAMP_X - FRONT_CLAMP_X
RACK_LAYOUT_FRONT_CLAMP_PHYSICAL_X = RACK_LAYOUT_FRONT_MARGIN_MM + RACK_FIXED_STATION_HALF_X_MM
RACK_LAYOUT_REAR_CLAMP_PHYSICAL_X = RACK_LAYOUT_FRONT_CLAMP_PHYSICAL_X + RACK_LAYOUT_CLAMP_SPACING_MM
RACK_LAYOUT_REAR_FIXED_EDGE_PHYSICAL_X = RACK_LAYOUT_REAR_CLAMP_PHYSICAL_X + RACK_FIXED_STATION_HALF_X_MM
RACK_LAYOUT_BACKSTOP_GAP_FROM_FIXED_EDGE_MM = (
    MOUNT_BACKSTOP_X0 - (REAR_CLAMP_X + RACK_FIXED_STATION_HALF_X_MM)
)
RACK_LAYOUT_BACKSTOP_PHYSICAL_X0 = (
    RACK_LAYOUT_REAR_FIXED_EDGE_PHYSICAL_X + RACK_LAYOUT_BACKSTOP_GAP_FROM_FIXED_EDGE_MM
)
RACK_LAYOUT_BACKSTOP_PHYSICAL_X1 = RACK_LAYOUT_BACKSTOP_PHYSICAL_X0 + MOUNT_BACKSTOP_W_X

# The rear BOX-support holm no longer sits at the rear rack clamp. It moves to
# the rear edge of the 50 mm backstop panel. This keeps the mechanical clamp on
# the straight tube but puts the structural/box support farther back.
RACK_LAYOUT_REAR_SUPPORT_X_RIGHT = MOUNT_BACKSTOP_X0 + MOUNT_BACKSTOP_W_X
RACK_LAYOUT_REAR_SUPPORT_X_LEFT = -(MOUNT_BACKSTOP_X0 + MOUNT_BACKSTOP_W_X)
RACK_LAYOUT_FRONT_SUPPORT_X_RIGHT = FRONT_CLAMP_X
RACK_LAYOUT_FRONT_SUPPORT_X_LEFT = -FRONT_CLAMP_X
RACK_LAYOUT_REAR_SUPPORT_PHYSICAL_X = RACK_LAYOUT_BACKSTOP_PHYSICAL_X1

# Retire only the LONG portion of the former rear-clamp-aligned support holm.
# Keep y<=36.2 as a short reinforced rack-clamp root, because it is part of the
# fixed station/load path and the full-width backstop bridge already uses it.
_RETIRED_HOLM_Y0 = 36.2
_RETIRED_HOLM_Y1 = 215.7
_RETIRED_HOLM_PAD = 0.20
_retired_right = box(
    REAR_CLAMP_X-ARM_W/2.0-_RETIRED_HOLM_PAD,
    _RETIRED_HOLM_Y0,
    ARM_BOTTOM_Z-_RETIRED_HOLM_PAD,
    ARM_W+2*_RETIRED_HOLM_PAD,
    _RETIRED_HOLM_Y1-_RETIRED_HOLM_Y0,
    ARM_H+2*_RETIRED_HOLM_PAD,
)
_retired_left = box(
    FRONT_CLAMP_X-ARM_W/2.0-_RETIRED_HOLM_PAD,
    _RETIRED_HOLM_Y0,
    ARM_BOTTOM_Z-_RETIRED_HOLM_PAD,
    ARM_W+2*_RETIRED_HOLM_PAD,
    _RETIRED_HOLM_Y1-_RETIRED_HOLM_Y0,
    ARM_H+2*_RETIRED_HOLM_PAD,
)
BASE_RIGHT = BASE_RIGHT.cut(_retired_right).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_retired_left).removeSplitter()

# Move the rear support holm to the panel rear edge. Start at local Y=0 so it
# substantially overlaps the full-width rectangular backstop bridge (Y=0..20),
# but its lower flange stays 3.33 mm above the measured Ø12.42 rack-tube crown.
_REAR_SUPPORT_RIGHT = make_i_beam_y(RACK_LAYOUT_REAR_SUPPORT_X_RIGHT, 0.0, ARM_Y1)
_REAR_SUPPORT_LEFT = make_i_beam_y(RACK_LAYOUT_REAR_SUPPORT_X_LEFT, 0.0, ARM_Y1)

# Close its rack-side end with one planar 3.2 mm cap.
_REAR_SUPPORT_CAP_T = ARM_PROFILE_WEB_T
_REAR_SUPPORT_FRAME_CAP_RIGHT = box(
    RACK_LAYOUT_REAR_SUPPORT_X_RIGHT-ARM_W/2.0,
    0.0,
    ARM_BOTTOM_Z,
    ARM_W,
    _REAR_SUPPORT_CAP_T,
    ARM_H,
)
_REAR_SUPPORT_FRAME_CAP_LEFT = box(
    RACK_LAYOUT_REAR_SUPPORT_X_LEFT-ARM_W/2.0,
    0.0,
    ARM_BOTTOM_Z,
    ARM_W,
    _REAR_SUPPORT_CAP_T,
    ARM_H,
)

# Extend the box-side crosshead only toward the moved rear support. The old
# common crosshead ends at X=+/-106 mm. Keep a 0.20 mm overlap for robust OCC
# fusion; stop the middle web at the new holm's inner face so its H/I opening is
# not re-closed by a second internal wall.
_CROSSHEAD_OLD_RIGHT_EDGE = 106.0
_CROSSHEAD_OLD_LEFT_EDGE = -106.0
_CROSSHEAD_OVERLAP = 0.20
_CROSSHEAD_RIGHT_X0 = _CROSSHEAD_OLD_RIGHT_EDGE-_CROSSHEAD_OVERLAP
_CROSSHEAD_RIGHT_X1 = RACK_LAYOUT_REAR_SUPPORT_X_RIGHT + ARM_W/2.0
_CROSSHEAD_LEFT_X0 = RACK_LAYOUT_REAR_SUPPORT_X_LEFT - ARM_W/2.0
_CROSSHEAD_LEFT_X1 = _CROSSHEAD_OLD_LEFT_EDGE+_CROSSHEAD_OVERLAP
_CROSSHEAD_RIGHT_INNER_X1 = RACK_LAYOUT_REAR_SUPPORT_X_RIGHT - ARM_W/2.0
_CROSSHEAD_LEFT_INNER_X0 = RACK_LAYOUT_REAR_SUPPORT_X_LEFT + ARM_W/2.0

_CROSSHEAD_EXT_RIGHT = fuse_all([
    box(_CROSSHEAD_RIGHT_X0, 216.0, ARM_TOP_Z-FLANGE_T,
        _CROSSHEAD_RIGHT_X1-_CROSSHEAD_RIGHT_X0,
        BOX_RIM_INNER_Y-216.2, FLANGE_T),
    box(_CROSSHEAD_RIGHT_X0, 216.0, ARM_BOTTOM_Z,
        _CROSSHEAD_RIGHT_X1-_CROSSHEAD_RIGHT_X0,
        42.2, FLANGE_T),
    box(_CROSSHEAD_RIGHT_X0, 216.0, ARM_BOTTOM_Z+FLANGE_T,
        _CROSSHEAD_RIGHT_INNER_X1-_CROSSHEAD_RIGHT_X0,
        4.5, ARM_H-2*FLANGE_T),
]).removeSplitter()
_CROSSHEAD_EXT_LEFT = fuse_all([
    box(_CROSSHEAD_LEFT_X0, 216.0, ARM_TOP_Z-FLANGE_T,
        _CROSSHEAD_LEFT_X1-_CROSSHEAD_LEFT_X0,
        BOX_RIM_INNER_Y-216.2, FLANGE_T),
    box(_CROSSHEAD_LEFT_X0, 216.0, ARM_BOTTOM_Z,
        _CROSSHEAD_LEFT_X1-_CROSSHEAD_LEFT_X0,
        42.2, FLANGE_T),
    box(_CROSSHEAD_LEFT_INNER_X0, 216.0, ARM_BOTTOM_Z+FLANGE_T,
        _CROSSHEAD_LEFT_X1-_CROSSHEAD_LEFT_INNER_X0,
        4.5, ARM_H-2*FLANGE_T),
]).removeSplitter()

# Head closure for the moved rear support: same single outer cap + short side
# DROP architecture as the already accepted front holm.
_REAR_SUPPORT_HEAD_CAP_RIGHT = _arm_head_cap(
    RACK_LAYOUT_REAR_SUPPORT_X_RIGHT, ARM_PROFILE_HEAD_FACE_Y)
_REAR_SUPPORT_HEAD_CAP_LEFT = _arm_head_cap(
    RACK_LAYOUT_REAR_SUPPORT_X_LEFT, ARM_PROFILE_HEAD_FACE_Y)
_REAR_SUPPORT_HEAD_DROPS_RIGHT = []
_REAR_SUPPORT_HEAD_DROPS_LEFT = []
for _xc, _dst in (
    (RACK_LAYOUT_REAR_SUPPORT_X_RIGHT, _REAR_SUPPORT_HEAD_DROPS_RIGHT),
    (RACK_LAYOUT_REAR_SUPPORT_X_LEFT, _REAR_SUPPORT_HEAD_DROPS_LEFT),
):
    for _x0 in (_xc-ARM_W/2.0, _xc+ARM_W/2.0-ARM_PROFILE_HEAD_DROP_T):
        _dst.append(box(
            _x0,
            ARM_PROFILE_HEAD_DROP_Y0,
            ARM_BOTTOM_Z,
            ARM_PROFILE_HEAD_DROP_T,
            ARM_PROFILE_HEAD_DROP_Y1-ARM_PROFILE_HEAD_DROP_Y0,
            ARM_H,
        ))

for _q in ([_REAR_SUPPORT_RIGHT, _REAR_SUPPORT_FRAME_CAP_RIGHT,
            _CROSSHEAD_EXT_RIGHT, _REAR_SUPPORT_HEAD_CAP_RIGHT]
           + _REAR_SUPPORT_HEAD_DROPS_RIGHT):
    BASE_RIGHT = BASE_RIGHT.fuse(_q).removeSplitter()
for _q in ([_REAR_SUPPORT_LEFT, _REAR_SUPPORT_FRAME_CAP_LEFT,
            _CROSSHEAD_EXT_LEFT, _REAR_SUPPORT_HEAD_CAP_LEFT]
           + _REAR_SUPPORT_HEAD_DROPS_LEFT):
    BASE_LEFT = BASE_LEFT.fuse(_q).removeSplitter()

# The old common crosshead was still 212 mm wide from the former +/-90 layout.
# Trim only its now-superfluous FRONT overhang, preserving the front support at
# X=-80 RIGHT / +80 LEFT. This is what brings the exact printable X envelope to
# 295 mm rather than 302 mm.
_CROSSHEAD_FRONT_TRIM_RIGHT = box(
    -106.2, 215.8, ARM_BOTTOM_Z-0.2,
    10.2, 42.8, ARM_H+0.4)
_CROSSHEAD_FRONT_TRIM_LEFT = box(
    96.0, 215.8, ARM_BOTTOM_Z-0.2,
    10.2, 42.8, ARM_H+0.4)
BASE_RIGHT = BASE_RIGHT.cut(_CROSSHEAD_FRONT_TRIM_RIGHT).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_CROSSHEAD_FRONT_TRIM_LEFT).removeSplitter()

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Measured rack-layout refit broke handed BASE topology')
if abs(BASE_RIGHT.Volume-BASE_LEFT.Volume) > 1e-4:
    raise RuntimeError('Measured rack-layout refit broke LEFT/RIGHT mirror volume symmetry')
BASE = BASE_RIGHT

'''
s = s.replace(parts_anchor, layout_geometry + parts_anchor, 1)

export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate export gate for measured rack-layout checks')

layout_validation = r'''# Measured rack-layout / INDX-bed hard checks.
_INDX_X_MAX = 298.0
_INDX_Y_MAX = 275.0
_LAYOUT_TARGET_X_MAX = 296.0
_layout_tube = cyl_x(RACK_R, 420.0, -210.0, 0.0, 0.0)
_layout_rear_support_tube_common_right = _REAR_SUPPORT_RIGHT.common(_layout_tube).Volume
_layout_rear_support_tube_common_left = _REAR_SUPPORT_LEFT.common(_layout_tube).Volume
_layout_rear_bridge_overlap_right = _REAR_SUPPORT_RIGHT.common(MOUNT_BACKSTOP_RIGHT).Volume
_layout_rear_bridge_overlap_left = _REAR_SUPPORT_LEFT.common(MOUNT_BACKSTOP_LEFT).Volume
_layout_rear_crosshead_overlap_right = _REAR_SUPPORT_RIGHT.common(_CROSSHEAD_EXT_RIGHT).Volume
_layout_rear_crosshead_overlap_left = _REAR_SUPPORT_LEFT.common(_CROSSHEAD_EXT_LEFT).Volume

V['measured_rack_longitudinal_layout'] = {
    'photo_measurement_date': '2026-09-15',
    'front_install_margin_mm': RACK_LAYOUT_FRONT_MARGIN_MM,
    'fixed_station_half_length_mm': RACK_FIXED_STATION_HALF_X_MM,
    'front_clamp_physical_center_mm': round(RACK_LAYOUT_FRONT_CLAMP_PHYSICAL_X, 3),
    'rear_clamp_physical_center_mm': round(RACK_LAYOUT_REAR_CLAMP_PHYSICAL_X, 3),
    'clamp_center_distance_mm': round(RACK_LAYOUT_CLAMP_SPACING_MM, 3),
    'rear_fixed_body_edge_physical_mm': round(RACK_LAYOUT_REAR_FIXED_EDGE_PHYSICAL_X, 3),
    'backstop_gap_after_fixed_body_mm': round(RACK_LAYOUT_BACKSTOP_GAP_FROM_FIXED_EDGE_MM, 3),
    'backstop_physical_x_mm': [round(RACK_LAYOUT_BACKSTOP_PHYSICAL_X0, 3),
                               round(RACK_LAYOUT_BACKSTOP_PHYSICAL_X1, 3)],
    'rear_support_holm_physical_center_mm': round(RACK_LAYOUT_REAR_SUPPORT_PHYSICAL_X, 3),
    'rear_support_holm_right_local_x_mm': RACK_LAYOUT_REAR_SUPPORT_X_RIGHT,
    'rear_support_holm_left_local_x_mm': RACK_LAYOUT_REAR_SUPPORT_X_LEFT,
    'right_base_bbox_xy_mm': [round(BASE_RIGHT.BoundBox.XLength, 3), round(BASE_RIGHT.BoundBox.YLength, 3)],
    'left_base_bbox_xy_mm': [round(BASE_LEFT.BoundBox.XLength, 3), round(BASE_LEFT.BoundBox.YLength, 3)],
    'indx_build_volume_xy_mm': [_INDX_X_MAX, _INDX_Y_MAX],
    'target_x_envelope_mm': _LAYOUT_TARGET_X_MAX,
    'right_x_margin_to_indx_mm': round(_INDX_X_MAX-BASE_RIGHT.BoundBox.XLength, 3),
    'left_x_margin_to_indx_mm': round(_INDX_X_MAX-BASE_LEFT.BoundBox.XLength, 3),
    'rear_support_tube_common_right_mm3': round(_layout_rear_support_tube_common_right, 9),
    'rear_support_tube_common_left_mm3': round(_layout_rear_support_tube_common_left, 9),
    'rear_support_backstop_overlap_right_mm3': round(_layout_rear_bridge_overlap_right, 6),
    'rear_support_backstop_overlap_left_mm3': round(_layout_rear_bridge_overlap_left, 6),
    'rear_support_crosshead_overlap_right_mm3': round(_layout_rear_crosshead_overlap_right, 6),
    'rear_support_crosshead_overlap_left_mm3': round(_layout_rear_crosshead_overlap_left, 6),
    'layout_intent': 'front clamp starts 20 mm from rack front; rear clamp remains on straight tube; backstop follows with existing gap; rear box-support holm moves to backstop rear edge',
}
if abs(RACK_LAYOUT_CLAMP_SPACING_MM-160.0) > 1e-9:
    failures.append('Measured rack layout no longer has the calculated 160 mm clamp spacing')
if abs(RACK_LAYOUT_FRONT_CLAMP_PHYSICAL_X-39.0) > 1e-9:
    failures.append('Front clamp centre no longer gives the requested 20 mm body-front installation margin')
if abs(RACK_LAYOUT_REAR_CLAMP_PHYSICAL_X-199.0) > 1e-9:
    failures.append('Rear clamp centre moved away from the calculated 199 mm safe position')
if abs(RACK_LAYOUT_BACKSTOP_PHYSICAL_X0-249.0) > 1e-9 or abs(RACK_LAYOUT_BACKSTOP_PHYSICAL_X1-299.0) > 1e-9:
    failures.append('Backstop no longer occupies the calculated 249..299 mm physical rack range')
if abs(RACK_LAYOUT_REAR_SUPPORT_PHYSICAL_X-299.0) > 1e-9:
    failures.append('Rear support holm is not centred on the backstop rear edge')
for _side, _b in (('RIGHT', BASE_RIGHT), ('LEFT', BASE_LEFT)):
    if _b.BoundBox.XLength > _INDX_X_MAX + 1e-6:
        failures.append(f'{_side} BASE exceeds CORE One L INDX X build volume: {_b.BoundBox.XLength:.3f} > {_INDX_X_MAX:.3f} mm')
    if _b.BoundBox.YLength > _INDX_Y_MAX + 1e-6:
        failures.append(f'{_side} BASE exceeds CORE One L INDX Y build volume: {_b.BoundBox.YLength:.3f} > {_INDX_Y_MAX:.3f} mm')
    if _b.BoundBox.XLength > _LAYOUT_TARGET_X_MAX + 1e-6:
        failures.append(f'{_side} BASE lost the intended >=2 mm INDX X-axis design reserve')
if _layout_rear_support_tube_common_right > 1e-6 or _layout_rear_support_tube_common_left > 1e-6:
    failures.append('Moved rear support holm collides with the measured Ø12.42 rack tube')
if _layout_rear_bridge_overlap_right < 500.0 or _layout_rear_bridge_overlap_left < 500.0:
    failures.append('Moved rear support holm is not substantially tied into the full-width backstop bridge')
if _layout_rear_crosshead_overlap_right < 300.0 or _layout_rear_crosshead_overlap_left < 300.0:
    failures.append('Moved rear support holm is not substantially tied into the box-side crosshead extension')

'''
s = s.replace(export_anchor, layout_validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Measured rack-layout / INDX patch made no changes')
if 'RACK_LAYOUT_REAR_SUPPORT_X_RIGHT' not in s:
    raise SystemExit('Moved rear support holm was not installed')

p.write_text(s, encoding='utf-8')
print('Applied measured rack layout: 20 mm front margin, 160 mm clamp spacing, rear support at backstop end, <=296 mm target X envelope')
