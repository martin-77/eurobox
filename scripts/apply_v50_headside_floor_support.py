from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Local printability/rigidity cleanup agreed from the actual v50 head-side view:
# 1) no extra spline at the knob/head side; simply continue the two existing
#    side-guide walls all the way out to the head face;
# 2) continue the existing low/front plane rearward only as far as the screw
#    block depth and fully support both complete screw blocks from that plane.
# Frozen clamp, spindle, hole, rim and rack datums are unchanged.

old = '''base_parts += [
    box(-78.0, BOX_EDGE_Y, PRINT_GUIDE_Z0, 7.6, 14.0,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    box(70.4, BOX_EDGE_Y, PRINT_GUIDE_Z0, 7.6, 14.0,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
]
'''
new = '''HEADSIDE_WALL_Y0 = BOX_EDGE_Y
HEADSIDE_WALL_Y1 = CAGE_Y1
HEADSIDE_WALL_DEPTH = HEADSIDE_WALL_Y1 - HEADSIDE_WALL_Y0
base_parts += [
    box(-78.0, HEADSIDE_WALL_Y0, PRINT_GUIDE_Z0, 7.6, HEADSIDE_WALL_DEPTH,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    box(70.4, HEADSIDE_WALL_Y0, PRINT_GUIDE_Z0, 7.6, HEADSIDE_WALL_DEPTH,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
]
'''
if old not in s:
    raise SystemExit('Could not locate final side-guide wall geometry')
s = s.replace(old, new, 1)

anchor = '''for sx in SPINDLE_X:
    base_parts.append(box(sx-11.0, CAGE_Y0, PRINT_FRAME_BOSS_Z0, 22.0,
                          CAGE_Y1-CAGE_Y0,
                          PRINT_BASE_PLANE_Z-PRINT_FRAME_BOSS_Z0))
'''
if anchor not in s:
    raise SystemExit('Could not locate final screw-block geometry')
addition = anchor + '''
# Head-side low deck: same level as the existing front/lower region, and only
# as deep as the screw blocks.
HEADSIDE_DECK_X0 = -70.4
HEADSIDE_DECK_X1 = 70.4
HEADSIDE_DECK_Y0 = BOX_EDGE_Y
HEADSIDE_DECK_Y1 = CAGE_Y1
HEADSIDE_DECK_Z0 = ARM_BOTTOM_Z
HEADSIDE_DECK_Z1 = PRINT_GUIDE_Z0
base_parts.append(box(HEADSIDE_DECK_X0, HEADSIDE_DECK_Y0, HEADSIDE_DECK_Z0,
                      HEADSIDE_DECK_X1-HEADSIDE_DECK_X0,
                      HEADSIDE_DECK_Y1-HEADSIDE_DECK_Y0,
                      HEADSIDE_DECK_Z1-HEADSIDE_DECK_Z0))

# Fully underbuild each whole screw block, not merely the material below the
# spindle hole. Nothing beside the block is raised above the low deck.
HEADSIDE_BOSS_SUPPORT_Z0 = HEADSIDE_DECK_Z1
HEADSIDE_BOSS_SUPPORT_Z1 = PRINT_FRAME_BOSS_Z0
for sx in SPINDLE_X:
    base_parts.append(box(sx-11.0, CAGE_Y0, HEADSIDE_BOSS_SUPPORT_Z0, 22.0,
                          CAGE_Y1-CAGE_Y0,
                          HEADSIDE_BOSS_SUPPORT_Z1-HEADSIDE_BOSS_SUPPORT_Z0))
'''
s = s.replace(anchor, addition, 1)

export_anchor = 'for name, sh in PARTS.items():\n'
if export_anchor not in s:
    raise SystemExit('Could not locate export validation gate')
validation = '''# Head-side wall / local floor-support checks.
V['headside_floor_support'] = {
    'wall_y0_mm': HEADSIDE_WALL_Y0,
    'wall_y1_mm': HEADSIDE_WALL_Y1,
    'wall_depth_mm': round(HEADSIDE_WALL_DEPTH, 3),
    'deck_x_range_mm': [HEADSIDE_DECK_X0, HEADSIDE_DECK_X1],
    'deck_y_range_mm': [HEADSIDE_DECK_Y0, HEADSIDE_DECK_Y1],
    'deck_z_range_mm': [HEADSIDE_DECK_Z0, HEADSIDE_DECK_Z1],
    'boss_support_x_width_mm': 22.0,
    'boss_support_y_range_mm': [CAGE_Y0, CAGE_Y1],
    'boss_support_z_range_mm': [HEADSIDE_BOSS_SUPPORT_Z0, HEADSIDE_BOSS_SUPPORT_Z1],
    'policy': 'head walls straight to head face; low deck only to block rear face; full block underbuild',
}
if abs(HEADSIDE_WALL_Y1-CAGE_Y1) > 1e-9:
    failures.append('Head-side wall no longer reaches the head face')
if abs(HEADSIDE_DECK_Y1-CAGE_Y1) > 1e-9:
    failures.append('Head-side low deck no longer ends exactly at screw-block rear face')
if abs(HEADSIDE_DECK_Z1-PRINT_GUIDE_Z0) > 1e-9:
    failures.append('Head-side low deck is not on the intended front/lower level')
if abs(HEADSIDE_BOSS_SUPPORT_Z1-PRINT_FRAME_BOSS_Z0) > 1e-9:
    failures.append('Screw blocks are no longer fully underbuilt to their existing lower face')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Head-side wall/floor support patch made no changes')
for token in ('HEADSIDE_WALL_DEPTH', 'HEADSIDE_DECK_Y1 = CAGE_Y1',
              'HEADSIDE_BOSS_SUPPORT_Z1 = PRINT_FRAME_BOSS_Z0'):
    if token not in s:
        raise SystemExit('Head-side wall/floor support patch incomplete: '+token)

p.write_text(s, encoding='utf-8')
print('Applied straight head-side walls plus low deck to screw-block depth and full block underbuild')
