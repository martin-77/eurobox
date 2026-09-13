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
# Final requested head-side / lower-floor geometry
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
FINAL_BASE_BOP_OVERLAP = 0.20
FINAL_BOSS_SUPPORT_Z0 = FINAL_BASE_DECK_Z1 - FINAL_BASE_BOP_OVERLAP
FINAL_BOSS_SUPPORT_Z1 = PRINT_FRAME_BOSS_Z0 + FINAL_BASE_BOP_OVERLAP

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

# Underbuild the COMPLETE 22 mm footprint of each screw block down to that lower
# plane. This is intentionally the whole block area, not a post beneath the bore.
_FINAL_BOSS_SUPPORTS = []
for sx in SPINDLE_X:
    _q = box(
        sx-11.0,
        CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z0,
        22.0,
        CAGE_Y1-CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z1-FINAL_BOSS_SUPPORT_Z0,
    )
    _FINAL_BOSS_SUPPORTS.append(_q)
    BASE_RIGHT = BASE_RIGHT.fuse(_q).removeSplitter()
    BASE_LEFT = BASE_LEFT.fuse(_q).removeSplitter()

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Requested final BASE floor/support geometry broke handed topology')
'''
s = s.replace(anchor, replacement, 1)

export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate export gate for final BASE validation')

validation = '''# Validate the ACTUAL final handed geometry after all width-cleanup cutters.
# Functional spindle/pin/service bores are allowed to remove material locally;
# the checks below verify the floor plane and broad full-footprint underbuild are
# present rather than demanding solid material inside required holes.
_final_deck_common_right = BASE_RIGHT.common(_FINAL_BASE_DECK).Volume
_final_deck_common_left = BASE_LEFT.common(_FINAL_BASE_DECK).Volume
_final_deck_fraction_right = _final_deck_common_right / _FINAL_BASE_DECK.Volume
_final_deck_fraction_left = _final_deck_common_left / _FINAL_BASE_DECK.Volume
_final_boss_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _FINAL_BOSS_SUPPORTS]
_final_boss_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _FINAL_BOSS_SUPPORTS]
V['final_requested_base_geometry'] = {
    'applied_after_width_cleanup': True,
    'deck_x_mm': [FINAL_BASE_DECK_X0, FINAL_BASE_DECK_X1],
    'deck_y_mm': [FINAL_BASE_DECK_Y0, FINAL_BASE_DECK_Y1],
    'deck_z_mm': [FINAL_BASE_DECK_Z0, FINAL_BASE_DECK_Z1],
    'boss_support_z_mm': [FINAL_BOSS_SUPPORT_Z0, FINAL_BOSS_SUPPORT_Z1],
    'deck_material_fraction_right': round(_final_deck_fraction_right, 6),
    'deck_material_fraction_left': round(_final_deck_fraction_left, 6),
    'boss_material_fraction_right': [round(x, 6) for x in _final_boss_fraction_right],
    'boss_material_fraction_left': [round(x, 6) for x in _final_boss_fraction_left],
    'rear_stop_matches_block_rear_face': abs(FINAL_BASE_DECK_Y0-CAGE_Y0) <= 1e-9,
    'same_level_as_front': abs(FINAL_BASE_DECK_Z1-PRINT_GUIDE_Z0) <= 1e-9,
    'policy': 'straight head-side wall retained; lower front plane pulled back only to block rear edge; complete 22 mm screw-block footprints underbuilt',
}
if _final_deck_fraction_right < 0.98 or _final_deck_fraction_left < 0.98:
    failures.append('Final lower BASE plane is not substantially present through the screw-block depth')
for side, vals in [('RIGHT', _final_boss_fraction_right), ('LEFT', _final_boss_fraction_left)]:
    for i, frac in enumerate(vals):
        if frac < 0.90:
            failures.append(f'{side} screw block {i} lacks the requested broad full-footprint underbuild')
if abs(FINAL_BASE_DECK_Y0-CAGE_Y0) > 1e-9:
    failures.append('Final lower BASE plane extends behind the screw-block rear edge')
if abs(FINAL_BASE_DECK_Z1-PRINT_GUIDE_Z0) > 1e-9:
    failures.append('Final lower BASE plane is not on the front lower level')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Final BASE geometry patch made no changes')

p.write_text(s, encoding='utf-8')
print('Applied requested geometry to FINAL post-width-cleanup BASE')
