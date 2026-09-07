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

# The rack clamp/root carries the primary vertical and torsional load. Apply
# the dedicated reinforcement after the clevis and clamp-travel fixups so the
# final generated CAD contains the strengthened load path.
reinforcement = Path('scripts/apply_v50_rack_root_reinforcement.py')
if not reinforcement.is_file():
    raise SystemExit('Missing rack-root reinforcement fixup')
exec(compile(reinforcement.read_text(encoding='utf-8'), str(reinforcement), 'exec'))

# Positive tool-less screw closure for the hinged lower rack jaw. This runs
# after the root geometry so it can add the matching fixed nut pocket and
# modular M4 hardware to the final station.
rack_lock = Path('scripts/apply_v50_rack_lock.py')
if not rack_lock.is_file():
    raise SystemExit('Missing rack-lock fixup')
exec(compile(rack_lock.read_text(encoding='utf-8'), str(rack_lock), 'exec'))

# Final rack-closure geometry pass: remove the cantilevered closure ear, carry
# the lower clamp body continuously through the screw axis, and add hard checks
# for the printable M4 x 0.7 screw/nut/knob thread pair.
massive_closure = Path('scripts/apply_v50_rack_closure_massive.py')
if not massive_closure.is_file():
    raise SystemExit('Missing continuous rack-closure fixup')
exec(compile(massive_closure.read_text(encoding='utf-8'), str(massive_closure), 'exec'))

# Make the female M4 thread unmistakable in the printable nut. This correction
# runs before the final hardware pass, which deliberately changes both hand
# knobs from threaded-on-stud to positive AF7 hex-drive interfaces.
female_threads = Path('scripts/apply_v50_rack_female_threads.py')
if not female_threads.is_file():
    raise SystemExit('Missing rack female-thread correction')
exec(compile(female_threads.read_text(encoding='utf-8'), str(female_threads), 'exec'))

# Resolve the remaining real-world hardware issues found by visual inspection:
# positive rack-knob drive and a deeper threaded lead-knob retainer nut.
hardware_cleanup = Path('scripts/apply_v50_hardware_cleanup.py')
if not hardware_cleanup.is_file():
    raise SystemExit('Missing v50 functional hardware cleanup')
exec(compile(hardware_cleanup.read_text(encoding='utf-8'), str(hardware_cleanup), 'exec'))

# Final source-of-truth nut pass. The BASE must stay unthreaded; separate lead
# nuts own the RH 8x2 working thread, and all printable female threads must have
# a visibly and mechanically developed profile suitable for PETG/0.4 mm FDM.
nut_thread_fix = Path('scripts/apply_v50_nut_thread_fix.py')
if not nut_thread_fix.is_file():
    raise SystemExit('Missing v50 nut/thread correction')
exec(compile(nut_thread_fix.read_text(encoding='utf-8'), str(nut_thread_fix), 'exec'))

# Replace the independently tuned 8x2 screw/nut helices with one master profile.
# The female cutter is derived from the exact male helix plus explicit radial
# and flank clearance, so pitch/hand/phase can no longer drift independently.
lead_thread_master = Path('scripts/apply_v50_lead_thread_master.py')
if not lead_thread_master.is_file():
    raise SystemExit('Missing single-source RH8x2 lead-thread pass')
exec(compile(lead_thread_master.read_text(encoding='utf-8'), str(lead_thread_master), 'exec'))

# The previous final M4 pass still left a razor-thin 0.04 mm internal-thread
# crest at 0.70 mm pitch. Replace that mathematically valid but unprintable
# geometry with a deliberately truncated FDM profile and real lead-in chamfers.
m4_thread_final = Path('scripts/apply_v50_m4_thread_final_fix.py')
if not m4_thread_final.is_file():
    raise SystemExit('Missing final printable rack M4 thread correction')
exec(compile(m4_thread_final.read_text(encoding='utf-8'), str(m4_thread_final), 'exec'))
