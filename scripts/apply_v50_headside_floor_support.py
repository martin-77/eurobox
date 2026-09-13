from pathlib import Path

p=Path('scripts/build_v50.py')
s=p.read_text(encoding='utf-8')
orig=s

anchor='BASE = fuse_all(base_parts)\n'
if anchor not in s:
    raise SystemExit('Could not locate BASE fusion point')

# Keep the proven/validated base_parts fusion untouched. Adding the local deck
# and wall extensions to that large multi-fuse made OCC return a null shape.
# Build the known-good BASE first, then fuse the three local support features
# sequentially with small internal overlaps. The overlaps are entirely inside
# existing material and only avoid coincident-face BOP failures.
replacement='''BASE = fuse_all(base_parts)

HEADSIDE_GUIDE_Z0 = 14.0
HEADSIDE_FRAME_BOSS_Z0 = 20.0
HEADSIDE_BASE_PLANE_Z = BOX_SUPPORT_Z
HEADSIDE_BOP_OVERLAP = 0.20

# Freeze the Y datums at the exact point where the head-side geometry is built.
# Later fixups intentionally reuse/rewrite CAGE_Y1 for other geometry. Validation
# must therefore compare against these immutable construction datums, not the
# later value of CAGE_Y1.
HEADSIDE_CAGE_Y0_REF = CAGE_Y0
HEADSIDE_CAGE_Y1_REF = CAGE_Y1
HEADSIDE_GUIDE_REAR_Y_REF = BOX_EDGE_Y + 14.0

# Continue the two existing side-guide/head walls straight to the head face.
# Start 0.20 mm inside the existing 14 mm wall so the fuse has real volume.
HEADSIDE_WALL_Y0 = HEADSIDE_GUIDE_REAR_Y_REF - HEADSIDE_BOP_OVERLAP
HEADSIDE_WALL_Y1 = HEADSIDE_CAGE_Y1_REF
HEADSIDE_WALL_DEPTH = HEADSIDE_WALL_Y1 - HEADSIDE_WALL_Y0
for x0 in (-78.0, 70.4):
    _head_wall = box(x0, HEADSIDE_WALL_Y0, HEADSIDE_GUIDE_Z0,
                     7.6, HEADSIDE_WALL_DEPTH,
                     HEADSIDE_BASE_PLANE_Z-HEADSIDE_GUIDE_Z0)
    BASE = BASE.fuse(_head_wall).removeSplitter()

# Low plane stays at the existing front/lower level and ends at the screw-block
# rear face. It does not raise the areas beside the local screw supports.
HEADSIDE_DECK_X0=-70.4
HEADSIDE_DECK_X1=70.4
HEADSIDE_DECK_Y0=BOX_EDGE_Y-HEADSIDE_BOP_OVERLAP
HEADSIDE_DECK_Y1=HEADSIDE_CAGE_Y1_REF
HEADSIDE_DECK_Z0=ARM_BOTTOM_Z
HEADSIDE_DECK_Z1=HEADSIDE_GUIDE_Z0
_head_deck = box(HEADSIDE_DECK_X0, HEADSIDE_DECK_Y0, HEADSIDE_DECK_Z0,
                 HEADSIDE_DECK_X1-HEADSIDE_DECK_X0,
                 HEADSIDE_DECK_Y1-HEADSIDE_DECK_Y0,
                 HEADSIDE_DECK_Z1-HEADSIDE_DECK_Z0)
BASE = BASE.fuse(_head_deck).removeSplitter()

# Fully underbuild each complete 22 mm screw block. Extend 0.20 mm into the
# existing block at Z=20 so this is a robust volumetric fuse, not a face touch.
HEADSIDE_BOSS_SUPPORT_Z0=HEADSIDE_DECK_Z1-HEADSIDE_BOP_OVERLAP
HEADSIDE_BOSS_SUPPORT_Z1=HEADSIDE_FRAME_BOSS_Z0+HEADSIDE_BOP_OVERLAP
for sx in SPINDLE_X:
    _boss_support = box(sx-11.0, HEADSIDE_CAGE_Y0_REF, HEADSIDE_BOSS_SUPPORT_Z0,
                        22.0, HEADSIDE_CAGE_Y1_REF-HEADSIDE_CAGE_Y0_REF,
                        HEADSIDE_BOSS_SUPPORT_Z1-HEADSIDE_BOSS_SUPPORT_Z0)
    BASE = BASE.fuse(_boss_support).removeSplitter()

if BASE.isNull() or not BASE.isValid() or len(BASE.Solids) != 1:
    raise RuntimeError('Head-side support fusion broke BASE topology')
'''
s=s.replace(anchor,replacement,1)

export_anchor='for name, sh in PARTS.items():\n'
if export_anchor not in s:
    raise SystemExit('Could not locate export gate')
validation='''# Validate against the immutable construction datums captured when the
# head-side geometry was generated. Do not read CAGE_Y1 here: later fixups are
# allowed to rewrite it for unrelated inboard geometry.
_head_wall_end_error = HEADSIDE_WALL_Y1 - HEADSIDE_CAGE_Y1_REF
_head_deck_end_error = HEADSIDE_DECK_Y1 - HEADSIDE_CAGE_Y1_REF
V['headside_floor_support']={
    'construction_cage_y0_ref_mm':HEADSIDE_CAGE_Y0_REF,
    'construction_cage_y1_ref_mm':HEADSIDE_CAGE_Y1_REF,
    'wall_y':[HEADSIDE_WALL_Y0,HEADSIDE_WALL_Y1],
    'deck_y':[HEADSIDE_DECK_Y0,HEADSIDE_DECK_Y1],
    'deck_z':[HEADSIDE_DECK_Z0,HEADSIDE_DECK_Z1],
    'boss_support_z':[HEADSIDE_BOSS_SUPPORT_Z0,HEADSIDE_BOSS_SUPPORT_Z1],
    'wall_end_error_mm':round(_head_wall_end_error,6),
    'deck_end_error_mm':round(_head_deck_end_error,6),
    'bop_overlap_mm':HEADSIDE_BOP_OVERLAP,
    'policy':'straight head walls and low deck terminate at frozen construction head face; full local screw-block underbuild',
}
_tol=1e-6
if abs(_head_wall_end_error) > _tol:
    failures.append('Head-side wall does not terminate at frozen construction head face')
if abs(_head_deck_end_error) > _tol:
    failures.append('Low deck does not terminate at frozen screw-block rear face')
if abs(HEADSIDE_DECK_Z1-14.0)>1e-9:
    failures.append('Head-side low deck is not on the intended front/lower level')
if HEADSIDE_BOSS_SUPPORT_Z1 < 20.0:
    failures.append('Screw blocks are not fully underbuilt')

'''
s=s.replace(export_anchor,validation+export_anchor,1)

if s==orig:
    raise SystemExit('No head-side changes applied')
p.write_text(s,encoding='utf-8')
print('Applied head-side support geometry after proven BASE fusion')
