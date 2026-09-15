from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The measured-layout refit failed in FreeCAD before validation because the
# front crosshead trim ended exactly on the retained front holm outer face.
# That leaves a face-only contact at X=-96 (RIGHT) / +96 (LEFT). OCC can keep
# that as separate solids after the surrounding booleans. Preserve a real
# 0.50 mm volumetric overlap instead. This changes no external envelope.
old_right_trim = '''_CROSSHEAD_FRONT_TRIM_RIGHT = box(
    -106.2, 215.8, ARM_BOTTOM_Z-0.2,
    10.2, 42.8, ARM_H+0.4)
'''
new_right_trim = '''_CROSSHEAD_FRONT_TRIM_RIGHT = box(
    -106.2, 215.8, ARM_BOTTOM_Z-0.2,
    9.7, 42.8, ARM_H+0.4)
'''
old_left_trim = '''_CROSSHEAD_FRONT_TRIM_LEFT = box(
    96.0, 215.8, ARM_BOTTOM_Z-0.2,
    10.2, 42.8, ARM_H+0.4)
'''
new_left_trim = '''_CROSSHEAD_FRONT_TRIM_LEFT = box(
    96.5, 215.8, ARM_BOTTOM_Z-0.2,
    9.7, 42.8, ARM_H+0.4)
'''
if old_right_trim not in s or old_left_trim not in s:
    raise SystemExit('Could not locate measured-layout front crosshead trims')
s = s.replace(old_right_trim, new_right_trim, 1)
s = s.replace(old_left_trim, new_left_trim, 1)

# Build each moved rear support as one connected structural solid before fusing
# it into the handed BASE. The former per-piece fuse/removeSplitter loop made
# OCC repeatedly solve marginal interfaces. The block below has deliberate
# volumetric overlaps throughout:
#   support <-> crosshead: y=216..220
#   support <-> head drops: y=219.8..220
#   head drops <-> head cap: y=224.815..225.015
#   support <-> frame cap: y=0..3.2
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

# Add an explicit volumetric-overlap witness for the retained front holm after
# trimming. This is a hard topology invariant, not a relaxed validator.
anchor = '''BASE_RIGHT = BASE_RIGHT.cut(_CROSSHEAD_FRONT_TRIM_RIGHT).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_CROSSHEAD_FRONT_TRIM_LEFT).removeSplitter()

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
'''
replacement = '''BASE_RIGHT = BASE_RIGHT.cut(_CROSSHEAD_FRONT_TRIM_RIGHT).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_CROSSHEAD_FRONT_TRIM_LEFT).removeSplitter()

_FRONT_HOLM_CROSSHEAD_OVERLAP_RIGHT = box(
    -96.5, 216.0, ARM_BOTTOM_Z,
    0.5, min(ARM_Y1, BOX_RIM_INNER_Y)-216.0, ARM_H)
_FRONT_HOLM_CROSSHEAD_OVERLAP_LEFT = box(
    96.0, 216.0, ARM_BOTTOM_Z,
    0.5, min(ARM_Y1, BOX_RIM_INNER_Y)-216.0, ARM_H)
_front_overlap_right = BASE_RIGHT.common(_FRONT_HOLM_CROSSHEAD_OVERLAP_RIGHT).Volume
_front_overlap_left = BASE_LEFT.common(_FRONT_HOLM_CROSSHEAD_OVERLAP_LEFT).Volume
if _front_overlap_right < 20.0 or _front_overlap_left < 20.0:
    raise RuntimeError('Front holm lost volumetric crosshead overlap after INDX trim')

if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
'''
if anchor not in s:
    raise SystemExit('Could not locate measured-layout topology gate')
s = s.replace(anchor, replacement, 1)

# Expose the topology witnesses in the existing measured-layout report.
meta_anchor = "    'rear_support_crosshead_overlap_left_mm3': round(_layout_rear_crosshead_overlap_left, 6),\n"
meta_extra = meta_anchor + "    'front_holm_crosshead_overlap_right_mm3': round(_front_overlap_right, 6),\n    'front_holm_crosshead_overlap_left_mm3': round(_front_overlap_left, 6),\n    'front_crosshead_trim_overlap_mm': 0.5,\n"
if meta_anchor not in s:
    raise SystemExit('Could not locate measured-layout validation metadata')
s = s.replace(meta_anchor, meta_extra, 1)

if s == orig:
    raise SystemExit('Measured rack-layout topology fix made no changes')
p.write_text(s, encoding='utf-8')
print('Stabilized measured rack layout: unified rear structural blocks and 0.5 mm front-holm crosshead overlap')
