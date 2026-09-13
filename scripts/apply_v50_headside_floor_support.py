from pathlib import Path

p=Path('scripts/build_v50.py')
s=p.read_text(encoding='utf-8')
orig=s

anchor='BASE = fuse_all(base_parts)\n'
if anchor not in s:
    raise SystemExit('Could not locate BASE fusion point')

addition='''HEADSIDE_WALL_Y0 = BOX_EDGE_Y + 14.0
HEADSIDE_WALL_Y1 = CAGE_Y1
HEADSIDE_WALL_DEPTH = HEADSIDE_WALL_Y1 - HEADSIDE_WALL_Y0
base_parts += [
    box(-78.0, HEADSIDE_WALL_Y0, PRINT_GUIDE_Z0, 7.6, HEADSIDE_WALL_DEPTH,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    box(70.4, HEADSIDE_WALL_Y0, PRINT_GUIDE_Z0, 7.6, HEADSIDE_WALL_DEPTH,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
]
HEADSIDE_DECK_X0=-70.4
HEADSIDE_DECK_X1=70.4
HEADSIDE_DECK_Y0=BOX_EDGE_Y
HEADSIDE_DECK_Y1=CAGE_Y1
HEADSIDE_DECK_Z0=ARM_BOTTOM_Z
HEADSIDE_DECK_Z1=PRINT_GUIDE_Z0
base_parts.append(box(HEADSIDE_DECK_X0,HEADSIDE_DECK_Y0,HEADSIDE_DECK_Z0,
                      HEADSIDE_DECK_X1-HEADSIDE_DECK_X0,
                      HEADSIDE_DECK_Y1-HEADSIDE_DECK_Y0,
                      HEADSIDE_DECK_Z1-HEADSIDE_DECK_Z0))
HEADSIDE_BOSS_SUPPORT_Z0=HEADSIDE_DECK_Z1
HEADSIDE_BOSS_SUPPORT_Z1=PRINT_FRAME_BOSS_Z0
for sx in SPINDLE_X:
    base_parts.append(box(sx-11.0,CAGE_Y0,HEADSIDE_BOSS_SUPPORT_Z0,22.0,
                          CAGE_Y1-CAGE_Y0,
                          HEADSIDE_BOSS_SUPPORT_Z1-HEADSIDE_BOSS_SUPPORT_Z0))

'''
s=s.replace(anchor,addition+anchor,1)

export_anchor='for name, sh in PARTS.items():\n'
if export_anchor not in s:
    raise SystemExit('Could not locate export gate')
validation='''V['headside_floor_support']={
    'wall_y':[HEADSIDE_WALL_Y0,HEADSIDE_WALL_Y1],
    'deck_y':[HEADSIDE_DECK_Y0,HEADSIDE_DECK_Y1],
    'deck_z':[HEADSIDE_DECK_Z0,HEADSIDE_DECK_Z1],
    'boss_support_z':[HEADSIDE_BOSS_SUPPORT_Z0,HEADSIDE_BOSS_SUPPORT_Z1],
}
if abs(HEADSIDE_WALL_Y1-CAGE_Y1)>1e-9:
    failures.append('Head-side wall does not reach head face')
if abs(HEADSIDE_DECK_Y1-CAGE_Y1)>1e-9:
    failures.append('Low deck extends beyond screw-block rear face')
if abs(HEADSIDE_BOSS_SUPPORT_Z1-PRINT_FRAME_BOSS_Z0)>1e-9:
    failures.append('Screw blocks are not fully underbuilt')

'''
s=s.replace(export_anchor,validation+export_anchor,1)

if s==orig:
    raise SystemExit('No head-side changes applied')
p.write_text(s,encoding='utf-8')
print('Applied head-side support geometry')
