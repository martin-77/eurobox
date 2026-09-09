from pathlib import Path

# Final mechanical closure for the inboard plate reversal.
#
# The spindle was correctly rotated 180 degrees about Z, so its 8 mm journal
# now runs from PLATE_SPINDLE_Y inward and the Ø11 x 1.8 mm thrust shoulder
# starts exactly at the inner face of the 8 mm plate. The plate rebuild in the
# width pass, however, had left the Ø12 x 2 mm counterbore on that same inner
# face. That removed every bit of plate material under the Ø11 shoulder and
# produced a real 0.25 mm minimum gap in the independent STEP mechanism check.
#
# Put the counterbore on the opposite (outboard/tip) face. This restores a
# proper annular thrust face at the inner side without moving any frozen datum:
# spindle X/Z, PLATE_SPINDLE_Y, RH8x2 thread, 5.5 mm opening travel, 0.5 mm
# preload, box rim, rack clamp and handed backstop geometry all stay unchanged.
p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

old = "    PLATE = PLATE.cut(cyl_y(6.0, 2.0, sx, PLATE_BODY_Y0, SPINDLE_Z))\n"
new = "    PLATE = PLATE.cut(cyl_y(6.0, 2.0, sx, PLATE_SPINDLE_Y-2.0, SPINDLE_Z))\n"
if old not in s:
    raise SystemExit('Could not locate inboard plate counterbore on shoulder face')
s = s.replace(old, new, 1)

if s == orig or new not in s:
    raise SystemExit('Inboard thrust-face correction made no source change')
p.write_text(s, encoding='utf-8')
print('Moved inboard plate counterbore to tip face; restored solid spindle thrust face')
