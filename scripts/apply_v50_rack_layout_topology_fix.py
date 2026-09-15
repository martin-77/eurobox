from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Root cause from the repeated OCC topology failure:
# the compatibility pass extended the obsolete rear-holm retirement cutter from
# y=215.7 all the way through ARM_PROFILE_HEAD_FACE_Y (~228 mm). That cutter is
# 32 mm wide in X, so at y=216..228 it also slices straight through the common
# crosshead. On RIGHT this leaves the old crosshead wing x=96..106 detached;
# LEFT mirrors the same problem at x=-106..-96. The resulting tiny detached wing
# is why BASE_RIGHT/BASE_LEFT fail the exact-one-solid gate even when the moved
# rear support itself is a valid connected solid.
#
# Retire the old long holm only up to the start of the common crosshead. The
# remaining ~4.3 mm terminal root is intentionally structural: it keeps the
# crosshead continuous, while the long obsolete rear-clamp-aligned holm is gone.
old_retire = '_RETIRED_HOLM_Y1 = ARM_PROFILE_HEAD_FACE_Y + 0.20'
new_retire = '_RETIRED_HOLM_Y1 = 215.7'
if old_retire not in s:
    raise SystemExit('Could not locate overlong rear-holm retirement cut')
s = s.replace(old_retire, new_retire, 1)

# Do not shave the old front crosshead overhang after the measured refit. The
# actual untrimmed X envelope seen in CI is 286 mm, already below both the hard
# 298 mm INDX limit and the 296 mm project target. Avoiding this extra boolean
# keeps the proven crosshead/holm load path intact.
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
# it into the handed BASE. This avoids repeated OCC solves on marginal piecewise
# interfaces and preserves the intended rear support at the backstop end.
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

# Replace the destructive front trim with a non-destructive material witness.
# Probe real upper/lower flange material at the retained front holm/crosshead
# junction; this remains a hard structural check.
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
meta_extra = meta_anchor + "    'front_holm_crosshead_overlap_right_mm3': round(_front_overlap_right, 6),\n    'front_holm_crosshead_overlap_left_mm3': round(_front_overlap_left, 6),\n    'front_crosshead_trimmed': False,\n    'retired_old_holm_y1_mm': _RETIRED_HOLM_Y1,\n"
if meta_anchor not in s:
    raise SystemExit('Could not locate measured-layout validation metadata')
s = s.replace(meta_anchor, meta_extra, 1)

if s == orig:
    raise SystemExit('Measured rack-layout topology fix made no changes')
p.write_text(s, encoding='utf-8')
print('Stabilized measured rack layout: retirement cut stops before common crosshead; rear support unified; front crosshead preserved')
