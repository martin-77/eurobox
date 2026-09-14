from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# ---------------------------------------------------------------------------
# Final rack-side clamp bridge
# ---------------------------------------------------------------------------
# Connect the two fixed rack-clamp stations on the bicycle/frame side without
# touching the moving lower jaws. The bridge runs only between the inner faces
# of the two 34 mm upper clamp bodies (with 0.30 mm buried overlap per side).
#
# IMPORTANT: fuse this bridge only after ALL existing inboard/floor/head-side
# BASE geometry has finished. Adding it to BASE_CORE earlier made a later large
# OCC fusion numerically unstable even though the bridge itself was valid and
# mechanically collision-free. The late fusion keeps the proven BASE sequence
# untouched, then updates BASE_RIGHT/BASE_LEFT/BASE immediately before PARTS.
#
# A straight top tie carries a central DROP down to the rack tube. The DROP is
# cut with the SAME saddle radius as the fixed upper clamps, so it can bear on
# the real Ø12.42 mm rack tube without becoming a tighter third clamp. Nothing
# extends below the tube centreline.

parts_anchor = "PARTS = {\n"
if parts_anchor not in s:
    raise SystemExit('Could not locate final PARTS anchor for late clamp-frame bridge')

late_geometry = '''# ---------------------------------------------------------------------------
# FINAL late-fused frame-side bridge between the two fixed rack clamps.
# ---------------------------------------------------------------------------
CLAMP_FRAME_BRIDGE_OVERLAP_X = 0.30
CLAMP_FRAME_BRIDGE_X0 = FRONT_CLAMP_X + 17.0 - CLAMP_FRAME_BRIDGE_OVERLAP_X
CLAMP_FRAME_BRIDGE_X1 = REAR_CLAMP_X - 17.0 + CLAMP_FRAME_BRIDGE_OVERLAP_X
CLAMP_FRAME_BRIDGE_Y0 = -8.0
CLAMP_FRAME_BRIDGE_Y1 = 8.0
CLAMP_FRAME_BRIDGE_TOP_Z0 = 10.0
CLAMP_FRAME_BRIDGE_TOP_Z1 = 16.0
CLAMP_FRAME_DROP_Y0 = -7.0
CLAMP_FRAME_DROP_Y1 = 7.0
CLAMP_FRAME_DROP_Z0 = 0.0
CLAMP_FRAME_SADDLE_R = UPPER_SADDLE_R

_CLAMP_FRAME_TOP = box(
    CLAMP_FRAME_BRIDGE_X0,
    CLAMP_FRAME_BRIDGE_Y0,
    CLAMP_FRAME_BRIDGE_TOP_Z0,
    CLAMP_FRAME_BRIDGE_X1-CLAMP_FRAME_BRIDGE_X0,
    CLAMP_FRAME_BRIDGE_Y1-CLAMP_FRAME_BRIDGE_Y0,
    CLAMP_FRAME_BRIDGE_TOP_Z1-CLAMP_FRAME_BRIDGE_TOP_Z0,
)
_CLAMP_FRAME_DROP_RAW = box(
    CLAMP_FRAME_BRIDGE_X0,
    CLAMP_FRAME_DROP_Y0,
    CLAMP_FRAME_DROP_Z0,
    CLAMP_FRAME_BRIDGE_X1-CLAMP_FRAME_BRIDGE_X0,
    CLAMP_FRAME_DROP_Y1-CLAMP_FRAME_DROP_Y0,
    CLAMP_FRAME_BRIDGE_TOP_Z0-CLAMP_FRAME_DROP_Z0,
)
_CLAMP_FRAME_SADDLE_CUTTER = cyl_x(
    CLAMP_FRAME_SADDLE_R,
    (CLAMP_FRAME_BRIDGE_X1-CLAMP_FRAME_BRIDGE_X0)+2.0,
    CLAMP_FRAME_BRIDGE_X0-1.0,
    0.0,
    0.0,
)
_CLAMP_FRAME_DROP = _CLAMP_FRAME_DROP_RAW.cut(_CLAMP_FRAME_SADDLE_CUTTER).removeSplitter()
_CLAMP_FRAME_BRIDGE = fuse_all([_CLAMP_FRAME_TOP, _CLAMP_FRAME_DROP]).removeSplitter()
if (not _CLAMP_FRAME_BRIDGE.isValid() or
        len(_CLAMP_FRAME_BRIDGE.Solids) != 1):
    raise RuntimeError('Clamp-frame saddle bridge is not one valid solid')

# At this point all sensitive cage/deck/head-side BOPs are already complete.
BASE_RIGHT = BASE_RIGHT.fuse(_CLAMP_FRAME_BRIDGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(_CLAMP_FRAME_BRIDGE).removeSplitter()
if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Late clamp-frame saddle bridge broke handed BASE topology')
if abs(BASE_RIGHT.Volume-BASE_LEFT.Volume) > 1e-4:
    raise RuntimeError('Late clamp-frame saddle bridge broke LEFT/RIGHT volume symmetry')
# Canonical legacy BASE and all downstream hard checks must see the new bridge.
BASE = BASE_RIGHT

'''
s = s.replace(parts_anchor, late_geometry + parts_anchor, 1)

export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate final export gate for clamp-frame bridge checks')

validation = '''# Clamp-frame saddle bridge hard checks.
_clamp_frame_fraction_right = BASE_RIGHT.common(_CLAMP_FRAME_BRIDGE).Volume / _CLAMP_FRAME_BRIDGE.Volume
_clamp_frame_fraction_left = BASE_LEFT.common(_CLAMP_FRAME_BRIDGE).Volume / _CLAMP_FRAME_BRIDGE.Volume
_clamp_frame_tube = cyl_x(
    RACK_R,
    (CLAMP_FRAME_BRIDGE_X1-CLAMP_FRAME_BRIDGE_X0)+4.0,
    CLAMP_FRAME_BRIDGE_X0-2.0,
    0.0,
    0.0,
)
_clamp_frame_tube_common = _CLAMP_FRAME_BRIDGE.common(_clamp_frame_tube).Volume
_clamp_frame_front_station = make_upper_station(FRONT_CLAMP_X)
_clamp_frame_rear_station = make_upper_station(REAR_CLAMP_X)
_clamp_frame_front_overlap = _CLAMP_FRAME_BRIDGE.common(_clamp_frame_front_station).Volume
_clamp_frame_rear_overlap = _CLAMP_FRAME_BRIDGE.common(_clamp_frame_rear_station).Volume
_clamp_frame_lower_sweep = []
for _xc in CLAMP_X:
    for _deg in (0, -15, -30, -45, -60, -75, -90):
        _lo = LOWER.copy()
        _lo.rotate(App.Vector(0, PIN_Y, PIN_Z), App.Vector(1,0,0), _deg)
        _lo.translate(App.Vector(_xc, 0, 0))
        _clamp_frame_lower_sweep.append({
            'clamp_x_mm': _xc,
            'rotation_deg': _deg,
            'bridge_common_mm3': round(_CLAMP_FRAME_BRIDGE.common(_lo).Volume, 9),
        })

V['clamp_frame_bridge'] = {
    'architecture': 'late_fused_straight_top_tie_with_central_drop_and_rack_tube_saddle',
    'x_mm': [round(CLAMP_FRAME_BRIDGE_X0, 3), round(CLAMP_FRAME_BRIDGE_X1, 3)],
    'top_y_mm': [CLAMP_FRAME_BRIDGE_Y0, CLAMP_FRAME_BRIDGE_Y1],
    'top_z_mm': [CLAMP_FRAME_BRIDGE_TOP_Z0, CLAMP_FRAME_BRIDGE_TOP_Z1],
    'drop_y_mm': [CLAMP_FRAME_DROP_Y0, CLAMP_FRAME_DROP_Y1],
    'drop_z_mm': [CLAMP_FRAME_DROP_Z0, CLAMP_FRAME_BRIDGE_TOP_Z0],
    'station_overlap_x_mm': CLAMP_FRAME_BRIDGE_OVERLAP_X,
    'rack_tube_diameter_mm': RACK_D,
    'rack_tube_radius_mm': RACK_R,
    'saddle_radius_mm': CLAMP_FRAME_SADDLE_R,
    'nominal_radial_clearance_mm': round(CLAMP_FRAME_SADDLE_R-RACK_R, 3),
    'tube_common_mm3': round(_clamp_frame_tube_common, 9),
    'front_station_overlap_mm3': round(_clamp_frame_front_overlap, 6),
    'rear_station_overlap_mm3': round(_clamp_frame_rear_overlap, 6),
    'material_fraction_right': round(_clamp_frame_fraction_right, 6),
    'material_fraction_left': round(_clamp_frame_fraction_left, 6),
    'lower_clamp_sweep': _clamp_frame_lower_sweep,
    'support_intent': 'bridge may bear on rack tube through same-radius upper saddle; no material below tube centreline',
}
if _clamp_frame_fraction_right < 0.999 or _clamp_frame_fraction_left < 0.999:
    failures.append('Clamp-frame saddle bridge is not fully incorporated in both handed BASE parts')
if _clamp_frame_tube_common > 1e-6:
    failures.append('Clamp-frame saddle bridge collides with the measured Ø12.42 mm rack tube')
if CLAMP_FRAME_SADDLE_R < RACK_R:
    failures.append('Clamp-frame saddle is tighter than the measured rack tube')
if CLAMP_FRAME_SADDLE_R-RACK_R > 0.20:
    failures.append('Clamp-frame saddle has too much radial clearance to act as a useful rack-tube support')
if _clamp_frame_front_overlap < 1.0 or _clamp_frame_rear_overlap < 1.0:
    failures.append('Clamp-frame saddle bridge is not structurally fused into both fixed clamp stations')
for _state in _clamp_frame_lower_sweep:
    if _state['bridge_common_mm3'] > 1e-6:
        failures.append('Clamp-frame saddle bridge blocks moving lower clamp sweep: '+repr(_state))
if CLAMP_FRAME_DROP_Z0 < -1e-9:
    failures.append('Clamp-frame DROP extends below the rack-tube centreline')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Clamp-frame saddle bridge patch made no changes')
if 'FINAL late-fused frame-side bridge' not in s:
    raise SystemExit('Late clamp-frame saddle bridge geometry was not installed')

p.write_text(s, encoding='utf-8')
print('Applied late-fused frame-side saddle bridge between rack clamps with DROP to Ø12.42 rack tube')
