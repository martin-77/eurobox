from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# ---------------------------------------------------------------------------
# Final rack-side clamp wall / holm connection
# ---------------------------------------------------------------------------
# Keep the large central wall: it is useful both as a rack-side stiffener and as
# an additional Eurobox support at the frozen BOX_SUPPORT_Z plane.
#
# Correct the two structural problems visible in the last preview:
#   1) no separate narrow DROP/top-tie step. Use ONE constant-thickness wall
#      from the rack-tube saddle all the way to BOX_SUPPORT_Z;
#   2) do not leave a slot between that wall and the two longitudinal holms.
#      Extend the wall 8 mm into each holm envelope and add one flush 3.2 mm
#      frame-side end cap to each holm. The cap closes the visible open H/I-beam
#      end and gives the wall a broad, direct load path into the holm/base.
#
# The wall still has the same-radius Ø12.42 rack-tube saddle and starts at Z=0,
# so it can bear on the rack tube without wrapping underneath it. All moving
# lower-clamp positions are hard-checked after the real final fusion.

parts_anchor = "PARTS = {\n"
if parts_anchor not in s:
    raise SystemExit('Could not locate final PARTS anchor for clamp-frame wall')

late_geometry = '''# ---------------------------------------------------------------------------
# FINAL late-fused frame-side wall between the two fixed rack clamps.
# ---------------------------------------------------------------------------
CLAMP_FRAME_WALL_HOLM_OVERLAP_X = 8.0
CLAMP_FRAME_WALL_X0 = FRONT_CLAMP_X + ARM_W/2.0 - CLAMP_FRAME_WALL_HOLM_OVERLAP_X
CLAMP_FRAME_WALL_X1 = REAR_CLAMP_X - ARM_W/2.0 + CLAMP_FRAME_WALL_HOLM_OVERLAP_X
CLAMP_FRAME_WALL_Y0 = -8.0
CLAMP_FRAME_WALL_Y1 = 8.0
CLAMP_FRAME_WALL_Z0 = 0.0
CLAMP_FRAME_WALL_Z1 = BOX_SUPPORT_Z
CLAMP_FRAME_SADDLE_R = UPPER_SADDLE_R

# One clean wall: no narrower DROP below a wider top tie, hence no ledges/steps.
_CLAMP_FRAME_WALL_RAW = box(
    CLAMP_FRAME_WALL_X0,
    CLAMP_FRAME_WALL_Y0,
    CLAMP_FRAME_WALL_Z0,
    CLAMP_FRAME_WALL_X1-CLAMP_FRAME_WALL_X0,
    CLAMP_FRAME_WALL_Y1-CLAMP_FRAME_WALL_Y0,
    CLAMP_FRAME_WALL_Z1-CLAMP_FRAME_WALL_Z0,
)
_CLAMP_FRAME_SADDLE_CUTTER = cyl_x(
    CLAMP_FRAME_SADDLE_R,
    (CLAMP_FRAME_WALL_X1-CLAMP_FRAME_WALL_X0)+2.0,
    CLAMP_FRAME_WALL_X0-1.0,
    0.0,
    0.0,
)
_CLAMP_FRAME_WALL = _CLAMP_FRAME_WALL_RAW.cut(_CLAMP_FRAME_SADDLE_CUTTER).removeSplitter()

# Close the two frame-side holm ends at the same Y=-8 front plane used by the
# reinforced root beam. These are end caps only; the long arm profile behind the
# cap is unchanged. Full 32 x 30 mm caps close the visible central void and the
# two side recesses in one printable planar face.
CLAMP_FRAME_HOLM_CAP_T = ARM_PROFILE_WEB_T
CLAMP_FRAME_HOLM_FRONT_Y = -8.0
_CLAMP_FRAME_HOLM_CAPS = [
    box(
        xc-ARM_W/2.0,
        CLAMP_FRAME_HOLM_FRONT_Y,
        ARM_BOTTOM_Z,
        ARM_W,
        CLAMP_FRAME_HOLM_CAP_T,
        ARM_H,
    )
    for xc in CLAMP_X
]

# The wall overlaps each cap/root by 8 mm in X. This removes the former visual
# and structural gap and gives a direct wall -> cap -> holm/base load path.
_CLAMP_FRAME_FINAL = _CLAMP_FRAME_WALL
for _q in _CLAMP_FRAME_HOLM_CAPS:
    _CLAMP_FRAME_FINAL = _CLAMP_FRAME_FINAL.fuse(_q).removeSplitter()
if (not _CLAMP_FRAME_FINAL.isValid() or
        len(_CLAMP_FRAME_FINAL.Solids) != 1):
    raise RuntimeError('Clamp-frame wall/cap assembly is not one valid solid')

# At this point all sensitive cage/deck/head-side BOPs are already complete.
BASE_RIGHT = BASE_RIGHT.fuse(_CLAMP_FRAME_FINAL).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(_CLAMP_FRAME_FINAL).removeSplitter()
if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Late clamp-frame wall/caps broke handed BASE topology')
if abs(BASE_RIGHT.Volume-BASE_LEFT.Volume) > 1e-4:
    raise RuntimeError('Late clamp-frame wall/caps broke LEFT/RIGHT volume symmetry')
# Canonical legacy BASE and all downstream hard checks must see the new wall.
BASE = BASE_RIGHT

'''
s = s.replace(parts_anchor, late_geometry + parts_anchor, 1)

export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate final export gate for clamp-frame wall checks')

validation = '''# Clamp-frame wall + frame-side holm-cap hard checks.
_clamp_frame_fraction_right = BASE_RIGHT.common(_CLAMP_FRAME_FINAL).Volume / _CLAMP_FRAME_FINAL.Volume
_clamp_frame_fraction_left = BASE_LEFT.common(_CLAMP_FRAME_FINAL).Volume / _CLAMP_FRAME_FINAL.Volume
_clamp_frame_cap_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _CLAMP_FRAME_HOLM_CAPS]
_clamp_frame_cap_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _CLAMP_FRAME_HOLM_CAPS]
_clamp_frame_wall_cap_overlap = [_CLAMP_FRAME_WALL.common(q).Volume for q in _CLAMP_FRAME_HOLM_CAPS]

_clamp_frame_tube = cyl_x(
    RACK_R,
    (CLAMP_FRAME_WALL_X1-CLAMP_FRAME_WALL_X0)+4.0,
    CLAMP_FRAME_WALL_X0-2.0,
    0.0,
    0.0,
)
_clamp_frame_tube_common = _CLAMP_FRAME_FINAL.common(_clamp_frame_tube).Volume
_clamp_frame_front_station = make_upper_station(FRONT_CLAMP_X)
_clamp_frame_rear_station = make_upper_station(REAR_CLAMP_X)
_clamp_frame_front_overlap = _CLAMP_FRAME_FINAL.common(_clamp_frame_front_station).Volume
_clamp_frame_rear_overlap = _CLAMP_FRAME_FINAL.common(_clamp_frame_rear_station).Volume

_clamp_frame_lower_sweep = []
for _xc in CLAMP_X:
    for _deg in (0, -15, -30, -45, -60, -75, -90):
        _lo = LOWER.copy()
        _lo.rotate(App.Vector(0, PIN_Y, PIN_Z), App.Vector(1,0,0), _deg)
        _lo.translate(App.Vector(_xc, 0, 0))
        _clamp_frame_lower_sweep.append({
            'clamp_x_mm': _xc,
            'rotation_deg': _deg,
            'wall_caps_common_mm3': round(_CLAMP_FRAME_FINAL.common(_lo).Volume, 9),
        })

V['clamp_frame_bridge'] = {
    'architecture': 'single_full_height_box_support_wall_with_rack_saddle_and_two_flush_holm_end_caps',
    'wall_x_mm': [round(CLAMP_FRAME_WALL_X0, 3), round(CLAMP_FRAME_WALL_X1, 3)],
    'wall_y_mm': [CLAMP_FRAME_WALL_Y0, CLAMP_FRAME_WALL_Y1],
    'wall_z_mm': [CLAMP_FRAME_WALL_Z0, round(CLAMP_FRAME_WALL_Z1, 3)],
    'wall_has_separate_drop': False,
    'wall_holm_overlap_x_mm': CLAMP_FRAME_WALL_HOLM_OVERLAP_X,
    'top_face_matches_box_support_plane': abs(CLAMP_FRAME_WALL_Z1-BOX_SUPPORT_Z) <= 1e-9,
    'box_support_plane_z_mm': BOX_SUPPORT_Z,
    'rack_tube_diameter_mm': RACK_D,
    'rack_tube_radius_mm': RACK_R,
    'saddle_radius_mm': CLAMP_FRAME_SADDLE_R,
    'nominal_radial_clearance_mm': round(CLAMP_FRAME_SADDLE_R-RACK_R, 3),
    'tube_common_mm3': round(_clamp_frame_tube_common, 9),
    'holm_front_y_mm': CLAMP_FRAME_HOLM_FRONT_Y,
    'holm_cap_thickness_mm': CLAMP_FRAME_HOLM_CAP_T,
    'holm_cap_count_per_base': len(_CLAMP_FRAME_HOLM_CAPS),
    'wall_to_holm_cap_overlap_mm3': [round(x, 6) for x in _clamp_frame_wall_cap_overlap],
    'holm_cap_material_fraction_right': [round(x, 6) for x in _clamp_frame_cap_fraction_right],
    'holm_cap_material_fraction_left': [round(x, 6) for x in _clamp_frame_cap_fraction_left],
    'front_station_overlap_mm3': round(_clamp_frame_front_overlap, 6),
    'rear_station_overlap_mm3': round(_clamp_frame_rear_overlap, 6),
    'material_fraction_right': round(_clamp_frame_fraction_right, 6),
    'material_fraction_left': round(_clamp_frame_fraction_left, 6),
    'lower_clamp_sweep': _clamp_frame_lower_sweep,
    'support_intent': 'Eurobox bears on flat wall top at BOX_SUPPORT_Z; wall overlaps both closed holm roots by 8 mm and may bear on Ø12.42 rack tube through same-radius saddle',
}
if _clamp_frame_fraction_right < 0.999 or _clamp_frame_fraction_left < 0.999:
    failures.append('Clamp-frame wall/cap assembly is not fully incorporated in both handed BASE parts')
if _clamp_frame_tube_common > 1e-6:
    failures.append('Clamp-frame wall/caps collide with the measured Ø12.42 mm rack tube')
if CLAMP_FRAME_SADDLE_R < RACK_R:
    failures.append('Clamp-frame saddle is tighter than the measured rack tube')
if CLAMP_FRAME_SADDLE_R-RACK_R > 0.20:
    failures.append('Clamp-frame saddle has too much radial clearance to act as a useful rack-tube support')
if len(_CLAMP_FRAME_HOLM_CAPS) != 2:
    failures.append('Clamp-frame geometry does not contain exactly two frame-side holm end caps')
for _side, _vals in (('RIGHT', _clamp_frame_cap_fraction_right), ('LEFT', _clamp_frame_cap_fraction_left)):
    for _i, _frac in enumerate(_vals):
        if _frac < 0.999:
            failures.append(f'{_side} frame-side holm end cap {_i} is not fully incorporated')
for _i, _common in enumerate(_clamp_frame_wall_cap_overlap):
    if _common < 700.0:
        failures.append(f'Clamp-frame wall has insufficient direct overlap with holm cap {_i}')
if _clamp_frame_front_overlap < 100.0 or _clamp_frame_rear_overlap < 100.0:
    failures.append('Clamp-frame wall/caps are not substantially fused into both fixed clamp/root stations')
for _state in _clamp_frame_lower_sweep:
    if _state['wall_caps_common_mm3'] > 1e-6:
        failures.append('Clamp-frame wall/caps block moving lower clamp sweep: '+repr(_state))
if CLAMP_FRAME_WALL_Z0 < -1e-9:
    failures.append('Clamp-frame wall extends below the rack-tube centreline')
if abs(CLAMP_FRAME_WALL_Z1-BOX_SUPPORT_Z) > 1e-9:
    failures.append('Clamp-frame wall top does not finish on the frozen Eurobox support plane')
if CLAMP_FRAME_WALL_Z1 > BOX_SUPPORT_Z + 1e-9:
    failures.append('Clamp-frame wall protrudes above the Eurobox support plane')
if abs(CLAMP_FRAME_HOLM_FRONT_Y-(-8.0)) > 1e-9:
    failures.append('Frame-side holm caps are not flush with the reinforced holm front plane')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Clamp-frame wall/holm-cap patch made no changes')
if 'FINAL late-fused frame-side wall' not in s:
    raise SystemExit('Late clamp-frame wall geometry was not installed')
if '_CLAMP_FRAME_HOLM_CAPS' not in s:
    raise SystemExit('Frame-side holm end caps were not installed')

p.write_text(s, encoding='utf-8')
print('Applied clean full-height clamp wall with Ø12.42 saddle, 8 mm holm overlap and two flush frame-side holm caps')
