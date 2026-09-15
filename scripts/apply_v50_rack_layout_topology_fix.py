from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The previous topology patch tried to shave the old front crosshead overhang
# after the measured rack-layout refit. CI showed that the cut itself can split
# the already-fused handed BASE even though the untrimmed geometry remains one
# valid solid. The diagnostic bbox at the failure was X=-106..180 => 286 mm,
# already safely below the hard 298 mm INDX X limit and below the 296 mm target.
# Therefore do not perform a gratuitous destructive boolean here. Keep the
# structural crosshead intact and let the existing hard print-envelope gate
# verify the actual finished BASE dimensions.
old_right_trim = '''_CROSSHEAD_FRONT_TRIM_RIGHT = box(
    -106.2, 215.8, ARM_BOTTOM_Z-0.2,
    10.2, 42.8, ARM_H+0.4)
'''
new_right_trim = '''_CROSSHEAD_FRONT_TRIM_RIGHT = None
'''
old_left_trim = '''_CROSSHEAD_FRONT_TRIM_LEFT = box(
    96.0, 215.8, ARM_BOTTOM_Z-0.2,
    10.2, 42.8, ARM_H+0.4)
'''
new_left_trim = '''_CROSSHEAD_FRONT_TRIM_LEFT = None
'''
if old_right_trim not in s or old_left_trim not in s:
    raise SystemExit('Could not locate measured-layout front crosshead trims')
s = s.replace(old_right_trim, new_right_trim, 1)
s = s.replace(old_left_trim, new_left_trim, 1)

# Build each moved rear support as one connected structural solid before fusing
# it into the handed BASE. The former per-piece fuse/removeSplitter loop made
# OCC repeatedly solve marginal interfaces. The block below has deliberate
# volumetric overlaps throughout.
old_fuse = '''for _q in ([_REAR_SUPPORT_RIGHT, _REAR_SUPPORT_FRAME_CAP_RIGHT,
            _CROSSHEAD_EXT_RIGHT, _REAR_SUPPORT_HEAD_CAP_RIGHT]
           + _REAR_SUPPORT_HEAD_DROPS_RIGHT):
    BASE_RIGHT = BASE_RIGHT.fuse(_q).removeSplitter()
for _q in ([_REAR_SUPPORT_LEFT, _REAR_SUPPORT_FRAME_CAP_LEFT,
            _CROSSHEAD_EXT_LEFT, _REAR_SUPPORT_HEAD_CAP_LEFT]
           + _REAR_SUPPORT_HEAD_DROPS_LEFT):
    BASE_LEFT = BASE_LEFT.fuse(_q).removeSplitter()
'''
new_fuse = '''_REAR_STRUCTURE_RIGHT = fuse_all(
    [_REAR_SUPPORT_RIGHT, _REAR_SUPPORT_FRAME_CAP_RIGHT,
     _CROSSHEAD_EXT_RIGHT, _REAR_SUPPORT_HEAD_CAP_RIGHT]
    + _REAR_SUPPORT_HEAD_DROPS_RIGHT
).removeSplitter()
_REAR_STRUCTURE_LEFT = fuse_all(
    [_REAR_SUPPORT_LEFT, _REAR_SUPPORT_FRAME_CAP_LEFT,
     _CROSSHEAD_EXT_LEFT, _REAR_SUPPORT_HEAD_CAP_LEFT]
    + _REAR_SUPPORT_HEAD_DROPS_LEFT
).removeSplitter()
if (not _REAR_STRUCTURE_RIGHT.isValid() or len(_REAR_STRUCTURE_RIGHT.Solids) != 1 or
        not _REAR_STRUCTURE_LEFT.isValid() or len(_REAR_STRUCTURE_LEFT.Solids) != 1):
    raise RuntimeError('Moved rear support structural block is not one valid solid per side')
BASE_RIGHT = BASE_RIGHT.fuse(_REAR_STRUCTURE_RIGHT).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(_REAR_STRUCTURE_LEFT).removeSplitter()
'''
if old_fuse not in s:
    raise SystemExit('Could not locate sequential moved rear-support fusion loop')
s = s.replace(old_fuse, new_fuse, 1)

# Replace the destructive trim with a non-destructive structural witness. The
# front holm must still share real flange volume with the retained full-width
# crosshead, but no material is cut merely to satisfy an envelope that is
# already within the printer limit.
old_cut_gate = '''BASE_RIGHT = BASE_RIGHT.cut(_CROSSHEAD_FRONT_TRIM_RIGHT).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_CROSSHEAD_FRONT_TRIM_LEFT).removeSplitter()

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
'''
new_cut_gate = '''_FRONT_HOLM_CROSSHEAD_OVERLAP_RIGHT = fuse_all([
    box(-96.0, 216.0, ARM_BOTTOM_Z,
        1.0, min(ARM_Y1, BOX_RIM_INNER_Y)-216.0, FLANGE_T),
    box(-96.0, 216.0, ARM_TOP_Z-FLANGE_T,
        1.0, min(ARM_Y1, BOX_RIM_INNER_Y)-216.0, FLANGE_T),
]).removeSplitter()
_FRONT_HOLM_CROSSHEAD_OVERLAP_LEFT = fuse_all([
    box(95.0, 216.0, ARM_BOTTOM_Z,
        1.0, min(ARM_Y1, BOX_RIM_INNER_Y)-216.0, FLANGE_T),
    box(95.0, 216.0, ARM_TOP_Z-FLANGE_T,
        1.0, min(ARM_Y1, BOX_RIM_INNER_Y)-216.0, FLANGE_T),
]).removeSplitter()
_front_overlap_right = BASE_RIGHT.common(_FRONT_HOLM_CROSSHEAD_OVERLAP_RIGHT).Volume
_front_overlap_left = BASE_LEFT.common(_FRONT_HOLM_CROSSHEAD_OVERLAP_LEFT).Volume
if _front_overlap_right < 30.0 or _front_overlap_left < 30.0:
    raise RuntimeError('Front holm has no volumetric crosshead connection in measured layout')

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
'''
if old_cut_gate not in s:
    raise SystemExit('Could not locate measured-layout destructive front trim')
s = s.replace(old_cut_gate, new_cut_gate, 1)

# Expose truthful topology witnesses in the measured-layout report.
meta_anchor = "    'rear_support_crosshead_overlap_left_mm3': round(_layout_rear_crosshead_overlap_left, 6),\n"
meta_extra = meta_anchor + "    'front_holm_crosshead_overlap_right_mm3': round(_front_overlap_right, 6),\n    'front_holm_crosshead_overlap_left_mm3': round(_front_overlap_left, 6),\n    'front_crosshead_trimmed': False,\n"
if meta_anchor not in s:
    raise SystemExit('Could not locate measured-layout validation metadata')
s = s.replace(meta_anchor, meta_extra, 1)

if s == orig:
    raise SystemExit('Measured rack-layout topology fix made no changes')
p.write_text(s, encoding='utf-8')
print('Stabilized measured rack layout: unified rear structural blocks; preserved intact front crosshead within INDX envelope')
