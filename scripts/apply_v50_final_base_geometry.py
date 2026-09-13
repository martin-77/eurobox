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
# IMPORTANT: this is applied AFTER the width-cleanup architecture has moved the
# screw cage inboard. Earlier head-side geometry at the old outboard Y datums is
# intentionally trimmed by width cleanup and therefore must not be used as the
# final printable geometry.
FINAL_BASE_DECK_X0 = -70.4
FINAL_BASE_DECK_X1 = 70.4
FINAL_BASE_DECK_Y0 = CAGE_Y0
FINAL_BASE_DECK_Y1 = PRINT_GUIDE_Y1
FINAL_BASE_DECK_Z0 = ARM_BOTTOM_Z
FINAL_BASE_DECK_Z1 = PRINT_GUIDE_Z0
FINAL_BASE_BOP_OVERLAP = 0.20

# Pull the existing front/lower plane straight back only as far as the complete
# screw-block depth. This gives the requested same-level surface left/right of
# the blocks without continuing farther behind them.
_inboard_parts.append(box(
    FINAL_BASE_DECK_X0,
    FINAL_BASE_DECK_Y0,
    FINAL_BASE_DECK_Z0,
    FINAL_BASE_DECK_X1-FINAL_BASE_DECK_X0,
    FINAL_BASE_DECK_Y1-FINAL_BASE_DECK_Y0,
    FINAL_BASE_DECK_Z1-FINAL_BASE_DECK_Z0,
))

# Fully underbuild the complete footprint of both 22 mm screw blocks, not only
# the spindle bores. The tiny overlap into Z=20 is purely for robust OCC fusion.
FINAL_BOSS_SUPPORT_Z0 = FINAL_BASE_DECK_Z1 - FINAL_BASE_BOP_OVERLAP
FINAL_BOSS_SUPPORT_Z1 = PRINT_FRAME_BOSS_Z0 + FINAL_BASE_BOP_OVERLAP
for sx in SPINDLE_X:
    _inboard_parts.append(box(
        sx-11.0,
        CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z0,
        22.0,
        CAGE_Y1-CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z1-FINAL_BOSS_SUPPORT_Z0,
    ))

INBOARD_CAGE = fuse_all(_inboard_parts)
BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()
'''
s = s.replace(anchor, replacement, 1)

# Add validation against the actual final handed solids, after width cleanup.
validation_anchor = '''for sx in SPINDLE_X:
    _nut_pocket = box(sx-8.35, NUT_THREAD_Y0-0.35, 23.65,
'''
if validation_anchor not in s:
    raise SystemExit('Could not locate final inboard cutter loop')

validation_prefix = '''# Geometry witnesses for the final requested BASE changes. These probe the
# actual post-width-cleanup construction, not stale pre-cleanup datums.
_FINAL_DECK_PROBE = box(
    FINAL_BASE_DECK_X0,
    FINAL_BASE_DECK_Y0,
    FINAL_BASE_DECK_Z0,
    FINAL_BASE_DECK_X1-FINAL_BASE_DECK_X0,
    FINAL_BASE_DECK_Y1-FINAL_BASE_DECK_Y0,
    FINAL_BASE_DECK_Z1-FINAL_BASE_DECK_Z0,
)
_FINAL_BOSS_PROBES = [
    box(sx-11.0, CAGE_Y0, FINAL_BOSS_SUPPORT_Z0,
        22.0, CAGE_Y1-CAGE_Y0,
        FINAL_BOSS_SUPPORT_Z1-FINAL_BOSS_SUPPORT_Z0)
    for sx in SPINDLE_X
]

'''
s = s.replace(validation_anchor, validation_prefix + validation_anchor, 1)

export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate export gate for final BASE validation')

validation = '''# Final BASE geometry checks: verify material exists over the complete requested
# floor and both full boss footprints on BOTH handed bases.
_final_deck_v = _FINAL_DECK_PROBE.Volume
_final_deck_right = BASE_RIGHT.common(_FINAL_DECK_PROBE).Volume
_final_deck_left = BASE_LEFT.common(_FINAL_DECK_PROBE).Volume
_final_boss_right = [BASE_RIGHT.common(q).Volume for q in _FINAL_BOSS_PROBES]
_final_boss_left = [BASE_LEFT.common(q).Volume for q in _FINAL_BOSS_PROBES]
V['final_requested_base_geometry'] = {
    'deck_x_mm': [FINAL_BASE_DECK_X0, FINAL_BASE_DECK_X1],
    'deck_y_mm': [FINAL_BASE_DECK_Y0, FINAL_BASE_DECK_Y1],
    'deck_z_mm': [FINAL_BASE_DECK_Z0, FINAL_BASE_DECK_Z1],
    'boss_support_z_mm': [FINAL_BOSS_SUPPORT_Z0, FINAL_BOSS_SUPPORT_Z1],
    'deck_probe_volume_mm3': round(_final_deck_v, 3),
    'deck_right_common_mm3': round(_final_deck_right, 3),
    'deck_left_common_mm3': round(_final_deck_left, 3),
    'boss_right_common_mm3': [round(x, 3) for x in _final_boss_right],
    'boss_left_common_mm3': [round(x, 3) for x in _final_boss_left],
    'policy': 'straight head walls; lower plane pulled back only through full screw-block depth; both complete 22mm bosses fully underbuilt',
}
if _final_deck_right < _final_deck_v*0.995 or _final_deck_left < _final_deck_v*0.995:
    failures.append('Final lower BASE plane is not fully present through the screw-block depth')
for side, vals in [('RIGHT', _final_boss_right), ('LEFT', _final_boss_left)]:
    for i, val in enumerate(vals):
        if val < _FINAL_BOSS_PROBES[i].Volume*0.995:
            failures.append(f'{side} screw block {i} is not fully underbuilt')
if abs(FINAL_BASE_DECK_Y0-CAGE_Y0) > 1e-9:
    failures.append('Final lower BASE plane extends behind the screw-block rear edge')
if abs(FINAL_BASE_DECK_Z1-PRINT_GUIDE_Z0) > 1e-9:
    failures.append('Final lower BASE plane is not on the front lower level')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Final BASE geometry patch made no changes')

p.write_text(s, encoding='utf-8')
print('Applied final post-width-cleanup BASE geometry: full boss underbuild + lower plane through block depth')
