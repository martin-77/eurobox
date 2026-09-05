from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The previous 4.5 mm travel cleared the measured 244.665 mm box edge by only
# 0.30 mm (underhook inner face 244.965 mm). That is too little allowance for
# a real Eurobox plus FDM tolerances. Keep the frozen box/rack datums unchanged
# and use 5.5 mm usable opening travel instead. The existing 14 mm guide depth
# with an 8 mm plate still leaves 0.5 mm guide overlap margin at full opening.
s = s.replace('PLATE_OPEN = 4.5', 'PLATE_OPEN = 5.5', 1)

# The spindle shoulder starts nominally at BOX_EDGE_Y + 8.0, exactly at the
# outside face of the 8 mm clamp plate. The intended 0.5 mm clamp preload moves
# both plate and spindle inward by 0.5 mm. The original base bore started only
# at +8.0 and therefore let the Ø11 shoulder clip the base during that preload.
# Add a shallow Ø11.6 counterbore from +7.4 to +10.0: 0.6 mm inward allowance
# plus 0.3 mm radial FDM clearance around the Ø11 shoulder. The normal Ø8.9
# spindle bore remains unchanged farther outward.
needle = "    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(BOX_EDGE_Y+8.0)+1.0, sx, BOX_EDGE_Y+8.0, SPINDLE_Z))\n"
replacement = needle + "    BASE = BASE.cut(cyl_y(5.8, 2.6, sx, BOX_EDGE_Y+7.4, SPINDLE_Z))\n"
if needle not in s:
    raise SystemExit('Could not locate spindle base bore for preload relief')
s = s.replace(needle, replacement, 1)

# Extend plate-motion and thread-kinematics hard checks to the new end position.
s = s.replace('for d in [0, 1, 2, 3, 4, 4.5]:',
              'for d in [0, 1, 2, 3, 4, 4.5, 5.0, 5.5]:', 1)
# Also validate the actual -0.5 mm clamp-preload position in the source CAD,
# not only the opening direction. This prevents this regression from hiding in
# the separate post-build validator again.
s = s.replace('for d in [0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5]:',
              'for d in [-0.5, 0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 5.5]:', 1)

# Keep the width diagnostic truthful.
s = s.replace("'open_4_5mm': round(BOX_W + 2*((spindle_outer_local_y+4.5)-BOX_EDGE_Y), 3),",
              "'open_5_5mm': round(BOX_W + 2*((spindle_outer_local_y+5.5)-BOX_EDGE_Y), 3),", 1)

if s == orig:
    raise SystemExit('Clamp travel/preload fixup did not modify build_v50.py')
if 'PLATE_OPEN = 5.5' not in s:
    raise SystemExit('Clamp travel fixup failed')
if 'BOX_EDGE_Y+7.4' not in s:
    raise SystemExit('Spindle shoulder preload relief fixup failed')
if 'for d in [-0.5, 0, 0.5' not in s:
    raise SystemExit('Preload kinematics validation fixup failed')

p.write_text(s, encoding='utf-8')
print('Applied v50 clamp fixups: 5.5 mm opening + spindle shoulder preload relief')
