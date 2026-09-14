from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

anchor = '''INBOARD_CAGE = fuse_all(_inboard_parts)
BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()
'''
if anchor not in s:
    raise SystemExit('Could not locate final inboard cage fusion point')

replacement = '''# ---------------------------------------------------------------------------
# Final requested head-side / lower-floor / closed-front geometry
# ---------------------------------------------------------------------------
# Width cleanup has now moved the screw cage to its FINAL inboard datums. Build
# the known-good cage first; then fuse the requested floor/supports sequentially
# so OCC does not have to solve them inside the large multi-fuse.
FINAL_BASE_DECK_X0 = -70.4
FINAL_BASE_DECK_X1 = 70.4
FINAL_BASE_DECK_Y0 = CAGE_Y0
FINAL_BASE_DECK_Y1 = PRINT_GUIDE_Y1
FINAL_BASE_DECK_Z0 = ARM_BOTTOM_Z
FINAL_BASE_DECK_Z1 = PRINT_GUIDE_Z0
FINAL_BASE_BOP_OVERLAP = 0.35
FINAL_GUIDE_STITCH_OVERLAP = 0.20
FINAL_BOSS_SIDE_OVERLAP = 0.35
FINAL_BOSS_SUPPORT_Z0 = FINAL_BASE_DECK_Z1 - FINAL_BASE_BOP_OVERLAP
FINAL_BOSS_SUPPORT_Z1 = PRINT_FRAME_BOSS_Z0 + FINAL_BASE_BOP_OVERLAP

# CORRECT head-side interpretation from the user's marked reference image:
# the two marked faces are the OUTER SIDE WALLS of the screw/plate cage at
# X=-78..-70.4 and X=70.4..78, not the rack-clamp stations at X=+/-90.
#
# The original guide walls begin only at PRINT_GUIDE_Y0 (~214.2 mm), while the
# upper transverse tie already begins at CAGE_Y0-0.1 (~190.6 mm). That leaves
# the tie overhanging at both outer cage heads in the upside-down print
# orientation. Extend those existing guide walls forward in Y to the tie's
# front edge and overlap the old guide by 0.35 mm, producing one continuous,
# planar support wall under each outer end of the tie.
FINAL_HEADSIDE_Y0 = CAGE_Y0 - 0.10
FINAL_HEADSIDE_Y1 = PRINT_GUIDE_Y0 + 0.35
FINAL_HEADSIDE_Z0 = PRINT_GUIDE_Z0
FINAL_HEADSIDE_Z1 = PRINT_BASE_PLANE_Z
FINAL_HEADSIDE_X_RANGES = [(-78.0, -70.4), (70.4, 78.0)]

# Close the previously open front face of the central screw cage. The wall is
# deliberately shallow in Y: it starts at the same front datum as the outer
# transverse frame and ends exactly at the front face of the removable lead-nut
# pockets, so cartridge access remains unchanged. It spans the full cage width
# and closes the frame from the lower deck into the existing upper transverse
# tie. Only the two functional spindle passages remain open.
FINAL_FRONT_X0 = -78.0
FINAL_FRONT_X1 = 78.0
FINAL_FRONT_Y0 = CAGE_Y0 - 0.10
FINAL_FRONT_Y1 = NUT_Y0 - 0.35
FINAL_FRONT_Z0 = FINAL_BASE_DECK_Z0
FINAL_FRONT_Z1 = 42.0
FINAL_FRONT_SPINDLE_CLEAR_R = 4.45

if FINAL_FRONT_Y1 <= FINAL_FRONT_Y0:
    raise RuntimeError('Closed screw-cage front has non-positive wall depth')

INBOARD_CAGE = fuse_all(_inboard_parts)
BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()

# Pull the front/lower plane straight back over the full inner width, but stop
# exactly at the rear edge of the screw blocks: no floor extension behind them.
_FINAL_BASE_DECK = box(
    FINAL_BASE_DECK_X0,
    FINAL_BASE_DECK_Y0,
    FINAL_BASE_DECK_Z0,
    FINAL_BASE_DECK_X1-FINAL_BASE_DECK_X0,
    FINAL_BASE_DECK_Y1-FINAL_BASE_DECK_Y0,
    FINAL_BASE_DECK_Z1-FINAL_BASE_DECK_Z0,
)
for _name in ('RIGHT', 'LEFT'):
    if _name == 'RIGHT':
        BASE_RIGHT = BASE_RIGHT.fuse(_FINAL_BASE_DECK).removeSplitter()
    else:
        BASE_LEFT = BASE_LEFT.fuse(_FINAL_BASE_DECK).removeSplitter()

# The deck top and the outer cage side walls meet at x=+/-70.4 and z=14.0.
# A pure edge-on-edge contact is legal enough for OCC to report one valid solid,
# but it tessellates to a non-manifold STL edge (four triangles on one edge).
# Add tiny buried stitch volumes around those two interfaces over the complete
# deck depth, including the forward head-side extension. They remain below the
# moving plate (PLATE_Z0=16) and do not change the requested 14.0 mm deck plane.
_FINAL_GUIDE_STITCHES = []
for _xc in (FINAL_BASE_DECK_X0, FINAL_BASE_DECK_X1):
    _q = box(
        _xc-FINAL_GUIDE_STITCH_OVERLAP,
        FINAL_BASE_DECK_Y0,
        FINAL_BASE_DECK_Z1-FINAL_GUIDE_STITCH_OVERLAP,
        2.0*FINAL_GUIDE_STITCH_OVERLAP,
        PRINT_GUIDE_Y1-FINAL_BASE_DECK_Y0,
        2.0*FINAL_GUIDE_STITCH_OVERLAP,
    )
    _FINAL_GUIDE_STITCHES.append(_q)
    BASE_RIGHT = BASE_RIGHT.fuse(_q).removeSplitter()
    BASE_LEFT = BASE_LEFT.fuse(_q).removeSplitter()

# Underbuild the COMPLETE screw-block footprint and deliberately overlap its
# side edges by 0.35 mm. The former exact 22.0 mm match could leave visually
# narrow slits at the two side interfaces after BOP/tessellation; the overlap
# makes the underbuild one unambiguous structural volume with the boss above.
_FINAL_BOSS_SUPPORTS = []
for sx in SPINDLE_X:
    _q = box(
        sx-11.0-FINAL_BOSS_SIDE_OVERLAP,
        CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z0,
        22.0+2.0*FINAL_BOSS_SIDE_OVERLAP,
        CAGE_Y1-CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z1-FINAL_BOSS_SUPPORT_Z0,
    )
    _FINAL_BOSS_SUPPORTS.append(_q)
    BASE_RIGHT = BASE_RIGHT.fuse(_q).removeSplitter()
    BASE_LEFT = BASE_LEFT.fuse(_q).removeSplitter()

# Extend the TWO EXISTING OUTER CAGE GUIDE WALLS forward to the front edge of
# the top tie. These are exactly the head-side faces marked with the user's thin
# black lines. Do NOT add material at the rack clamps.
_FINAL_HEADSIDE_EXTENSIONS = []
for _x0, _x1 in FINAL_HEADSIDE_X_RANGES:
    _q = box(
        _x0,
        FINAL_HEADSIDE_Y0,
        FINAL_HEADSIDE_Z0,
        _x1-_x0,
        FINAL_HEADSIDE_Y1-FINAL_HEADSIDE_Y0,
        FINAL_HEADSIDE_Z1-FINAL_HEADSIDE_Z0,
    )
    _FINAL_HEADSIDE_EXTENSIONS.append(_q)
    BASE_RIGHT = BASE_RIGHT.fuse(_q).removeSplitter()
    BASE_LEFT = BASE_LEFT.fuse(_q).removeSplitter()

# Close the central front face as one real structural wall rather than a visual
# shell. Build the wall with the spindle clearances already removed, fuse it to
# both handed BASE variants, then re-cut the same short clearance cylinders so
# no later BOP healing can accidentally skin over either functional passage.
_FINAL_FRONT_WALL = box(
    FINAL_FRONT_X0,
    FINAL_FRONT_Y0,
    FINAL_FRONT_Z0,
    FINAL_FRONT_X1-FINAL_FRONT_X0,
    FINAL_FRONT_Y1-FINAL_FRONT_Y0,
    FINAL_FRONT_Z1-FINAL_FRONT_Z0,
)
_FINAL_FRONT_SPINDLE_CUTTERS = []
for sx in SPINDLE_X:
    _c = cyl_y(
        FINAL_FRONT_SPINDLE_CLEAR_R,
        FINAL_FRONT_Y1-FINAL_FRONT_Y0+1.0,
        sx,
        FINAL_FRONT_Y0-0.5,
        SPINDLE_Z,
    )
    _FINAL_FRONT_SPINDLE_CUTTERS.append(_c)
    _FINAL_FRONT_WALL = _FINAL_FRONT_WALL.cut(_c)
_FINAL_FRONT_WALL = _FINAL_FRONT_WALL.removeSplitter()
if not _FINAL_FRONT_WALL.isValid() or len(_FINAL_FRONT_WALL.Solids) != 1:
    raise RuntimeError('Closed screw-cage front wall is not one valid solid')

BASE_RIGHT = BASE_RIGHT.fuse(_FINAL_FRONT_WALL).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(_FINAL_FRONT_WALL).removeSplitter()
for _c in _FINAL_FRONT_SPINDLE_CUTTERS:
    BASE_RIGHT = BASE_RIGHT.cut(_c).removeSplitter()
    BASE_LEFT = BASE_LEFT.cut(_c).removeSplitter()

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Requested final BASE floor/support/head-side/closed-front geometry broke handed topology')
'''
s = s.replace(anchor, replacement, 1)

export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate export gate for final BASE validation')

validation = '''# Validate the ACTUAL final handed geometry after all width-cleanup cutters.
# Functional spindle/pin/service bores are allowed to remove material locally;
# the checks below verify the floor plane, full-footprint underbuild, the two
# planar outer screw-cage head-side walls and the closed cage front are present.
_final_deck_common_right = BASE_RIGHT.common(_FINAL_BASE_DECK).Volume
_final_deck_common_left = BASE_LEFT.common(_FINAL_BASE_DECK).Volume
_final_deck_fraction_right = _final_deck_common_right / _FINAL_BASE_DECK.Volume
_final_deck_fraction_left = _final_deck_common_left / _FINAL_BASE_DECK.Volume
_final_boss_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _FINAL_BOSS_SUPPORTS]
_final_boss_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _FINAL_BOSS_SUPPORTS]
_final_guide_stitch_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _FINAL_GUIDE_STITCHES]
_final_guide_stitch_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _FINAL_GUIDE_STITCHES]
_final_guide_stitch_plate_common = [PLATE.common(q).Volume for q in _FINAL_GUIDE_STITCHES]
_final_headside_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _FINAL_HEADSIDE_EXTENSIONS]
_final_headside_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _FINAL_HEADSIDE_EXTENSIONS]
_final_headside_plate_common = [PLATE.common(q).Volume for q in _FINAL_HEADSIDE_EXTENSIONS]
_final_front_fraction_right = BASE_RIGHT.common(_FINAL_FRONT_WALL).Volume/_FINAL_FRONT_WALL.Volume
_final_front_fraction_left = BASE_LEFT.common(_FINAL_FRONT_WALL).Volume/_FINAL_FRONT_WALL.Volume
_final_front_plate_common = PLATE.common(_FINAL_FRONT_WALL).Volume
_final_front_spindle_common_right = [BASE_RIGHT.common(c).Volume for c in _FINAL_FRONT_SPINDLE_CUTTERS]
_final_front_spindle_common_left = [BASE_LEFT.common(c).Volume for c in _FINAL_FRONT_SPINDLE_CUTTERS]
V['final_requested_base_geometry'] = {
    'applied_after_width_cleanup': True,
    'deck_x_mm': [FINAL_BASE_DECK_X0, FINAL_BASE_DECK_X1],
    'deck_y_mm': [FINAL_BASE_DECK_Y0, FINAL_BASE_DECK_Y1],
    'deck_z_mm': [FINAL_BASE_DECK_Z0, FINAL_BASE_DECK_Z1],
    'boss_support_z_mm': [FINAL_BOSS_SUPPORT_Z0, FINAL_BOSS_SUPPORT_Z1],
    'boss_side_overlap_mm': FINAL_BOSS_SIDE_OVERLAP,
    'guide_stitch_overlap_mm': FINAL_GUIDE_STITCH_OVERLAP,
    'headside_target': 'outer_screw_cage_guide_walls_not_rack_clamps',
    'headside_x_ranges_mm': [list(x) for x in FINAL_HEADSIDE_X_RANGES],
    'headside_y_mm': [FINAL_HEADSIDE_Y0, FINAL_HEADSIDE_Y1],
    'headside_z_mm': [FINAL_HEADSIDE_Z0, FINAL_HEADSIDE_Z1],
    'headside_front_matches_tie_front': abs(FINAL_HEADSIDE_Y0-(CAGE_Y0-0.10)) <= 1e-9,
    'closed_front_x_mm': [FINAL_FRONT_X0, FINAL_FRONT_X1],
    'closed_front_y_mm': [FINAL_FRONT_Y0, FINAL_FRONT_Y1],
    'closed_front_z_mm': [FINAL_FRONT_Z0, FINAL_FRONT_Z1],
    'closed_front_spindle_clearance_d_mm': 2.0*FINAL_FRONT_SPINDLE_CLEAR_R,
    'closed_front_material_fraction_right': round(_final_front_fraction_right, 6),
    'closed_front_material_fraction_left': round(_final_front_fraction_left, 6),
    'closed_front_plate_common_mm3': round(_final_front_plate_common, 9),
    'closed_front_spindle_common_right_mm3': [round(x, 9) for x in _final_front_spindle_common_right],
    'closed_front_spindle_common_left_mm3': [round(x, 9) for x in _final_front_spindle_common_left],
    'closed_front_stops_at_nut_pocket_front': abs(FINAL_FRONT_Y1-(NUT_Y0-0.35)) <= 1e-9,
    'deck_material_fraction_right': round(_final_deck_fraction_right, 6),
    'deck_material_fraction_left': round(_final_deck_fraction_left, 6),
    'boss_material_fraction_right': [round(x, 6) for x in _final_boss_fraction_right],
    'boss_material_fraction_left': [round(x, 6) for x in _final_boss_fraction_left],
    'guide_stitch_material_fraction_right': [round(x, 6) for x in _final_guide_stitch_fraction_right],
    'guide_stitch_material_fraction_left': [round(x, 6) for x in _final_guide_stitch_fraction_left],
    'guide_stitch_plate_common_mm3': [round(x, 9) for x in _final_guide_stitch_plate_common],
    'headside_material_fraction_right': [round(x, 6) for x in _final_headside_fraction_right],
    'headside_material_fraction_left': [round(x, 6) for x in _final_headside_fraction_left],
    'headside_plate_common_mm3': [round(x, 9) for x in _final_headside_plate_common],
    'rear_stop_matches_block_rear_face': abs(FINAL_BASE_DECK_Y0-CAGE_Y0) <= 1e-9,
    'same_level_as_front': abs(FINAL_BASE_DECK_Z1-PRINT_GUIDE_Z0) <= 1e-9,
    'policy': 'lower plane through screw cage; screw underbuild side-overlapped; outer screw-cage guide walls extended forward under transverse tie; central screw-cage front closed with only spindle passages; no rack-clamp head-wall addition; guide/deck seam stitched',
}
if _final_deck_fraction_right < 0.98 or _final_deck_fraction_left < 0.98:
    failures.append('Final lower BASE plane is not substantially present through the screw-block depth')
for side, vals in [('RIGHT', _final_boss_fraction_right), ('LEFT', _final_boss_fraction_left)]:
    for i, frac in enumerate(vals):
        if frac < 0.90:
            failures.append(f'{side} screw block {i} lacks the requested broad connected underbuild')
for side, vals in [('RIGHT', _final_guide_stitch_fraction_right), ('LEFT', _final_guide_stitch_fraction_left)]:
    for i, frac in enumerate(vals):
        if frac < 0.999:
            failures.append(f'{side} guide/deck stitch {i} is not fully incorporated in the BASE')
for side, vals in [('RIGHT', _final_headside_fraction_right), ('LEFT', _final_headside_fraction_left)]:
    for i, frac in enumerate(vals):
        if frac < 0.999:
            failures.append(f'{side} outer screw-cage head-side extension {i} is not fully incorporated in the BASE')
for side, frac in [('RIGHT', _final_front_fraction_right), ('LEFT', _final_front_fraction_left)]:
    if frac < 0.999:
        failures.append(f'{side} central screw-cage front is not fully closed around the functional openings')
if _final_front_plate_common > 1e-6:
    failures.append('Closed screw-cage front intrudes into the moving clamp plate')
for side, vals in [('RIGHT', _final_front_spindle_common_right), ('LEFT', _final_front_spindle_common_left)]:
    for i, vol in enumerate(vals):
        if vol > 1e-5:
            failures.append(f'{side} closed-front spindle passage {i} is obstructed')
if abs(FINAL_FRONT_Y1-(NUT_Y0-0.35)) > 1e-9:
    failures.append('Closed screw-cage front intrudes beyond the lead-nut pocket front datum')
if any(v > 1e-6 for v in _final_headside_plate_common):
    failures.append('Planar screw-cage head-side extension intrudes into the moving clamp plate')
if any(v > 1e-6 for v in _final_guide_stitch_plate_common):
    failures.append('Guide/deck manifold stitch intrudes into the moving plate envelope')
if abs(FINAL_HEADSIDE_Y0-(CAGE_Y0-0.10)) > 1e-9:
    failures.append('Outer screw-cage head-side walls do not reach the front edge of the transverse tie')
if abs(FINAL_BASE_DECK_Y0-CAGE_Y0) > 1e-9:
    failures.append('Final lower BASE plane extends behind the screw-block rear edge')
if abs(FINAL_BASE_DECK_Z1-PRINT_GUIDE_Z0) > 1e-9:
    failures.append('Final lower BASE plane is not on the front lower level')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Final BASE geometry patch made no changes')

p.write_text(s, encoding='utf-8')
print('Applied final support-free BASE geometry: connected screw underbuild, head-side walls and closed screw-cage front')
