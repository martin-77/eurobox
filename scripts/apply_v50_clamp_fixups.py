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

# The first v50 fixup already creates the Ø11.6 shoulder tunnel needed for the
# inward clamp motion. The remaining preload collision is at the OUTER end:
# with LEAD_THREAD_LEN=22.2 the 10 mm hex begins exactly at CAGE_Y1 in the
# nominal position. At -0.5 mm preload it therefore enters the fixed cage by
# 0.5 mm. Extend the threaded shank by 0.8 mm before the hex. The thread itself
# fits the existing Ø8.9 tunnel; at maximum preload the hex now remains 0.3 mm
# outside the cage. Nut position, pitch and all frozen box/rack datums stay put.
if 'LEAD_THREAD_LEN = 22.2' not in s:
    raise SystemExit('Could not locate v50 lead-thread length')
s = s.replace('LEAD_THREAD_LEN = 22.2', 'LEAD_THREAD_LEN = 23.0', 1)

# Extend plate-motion and thread-kinematics hard checks to the new end position.
s = s.replace('for d in [0, 1, 2, 3, 4, 4.5]:',
              'for d in [0, 1, 2, 3, 4, 4.5, 5.0, 5.5]:', 1)

# Validate the real -0.5 mm clamping preload as part of the source CAD gate,
# not only in the separate post-build clamp validator.
s = s.replace('for d in [0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5]:',
              'for d in [-0.5, 0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 5.5]:', 1)

# Keep the width diagnostic truthful; LEAD_THREAD_LEN is already part of the
# spindle outer-position formula, so the extra 0.8 mm is included automatically.
s = s.replace("'open_4_5mm': round(BOX_W + 2*((spindle_outer_local_y+4.5)-BOX_EDGE_Y), 3),",
              "'open_5_5mm': round(BOX_W + 2*((spindle_outer_local_y+5.5)-BOX_EDGE_Y), 3),", 1)

if s == orig:
    raise SystemExit('Clamp travel/preload fixup did not modify build_v50.py')
if 'PLATE_OPEN = 5.5' not in s:
    raise SystemExit('Clamp travel fixup failed')
if 'LEAD_THREAD_LEN = 23.0' not in s:
    raise SystemExit('Spindle preload travel fixup failed')
if 'for d in [-0.5, 0, 0.5' not in s:
    raise SystemExit('Preload kinematics validation fixup failed')

p.write_text(s, encoding='utf-8')
print('Applied v50 clamp fixups: 5.5 mm opening + 0.5 mm preload spindle clearance')
