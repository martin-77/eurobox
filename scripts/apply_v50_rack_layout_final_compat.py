from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The measured-layout pass was initially inserted at the very end of the BASE
# construction. That meant its retirement cutter also cut material which the
# final screw-cage/deck pass had deliberately added. Move the complete measured
# geometry block to immediately BEFORE that final-base pass. The ordinary width
# cleanup and its functional cutters still run afterwards, so this preserves
# the proven clamp/cage mechanics while letting the rack layout establish the
# final support-holm positions first.
layout_start = '# ---------------------------------------------------------------------------\n# FINAL measured longitudinal rack layout / INDX print-envelope pass.\n# ---------------------------------------------------------------------------\n'
final_base_start = '# ---------------------------------------------------------------------------\n# Final requested head-side / lower-floor geometry\n# ---------------------------------------------------------------------------\n'
parts_anchor = 'PARTS = {\n'
if layout_start not in s or final_base_start not in s:
    raise SystemExit('Could not locate measured-layout/final-base blocks for ordering repair')
start = s.index(layout_start)
end = s.index(parts_anchor, start)
layout = s[start:end]
s = s[:start] + s[end:]

# Actual INDX-Y regression root cause: the new crosshead extension accidentally
# used a 42.2 mm bottom-flange depth while its top flange correctly stopped at
# BOX_RIM_INNER_Y. That single typo pushed BASE Y to 277.2 mm and also made the
# assembled holder exceed the 600 mm box envelope. Make both flanges terminate
# at the same real box-side plane. This yields the intended ~247 mm Y envelope.
old_bottom = '        42.2, FLANGE_T),'
if layout.count(old_bottom) != 2:
    raise SystemExit('Expected exactly two overlong 42.2 mm crosshead flanges')
layout = layout.replace(old_bottom, '        BOX_RIM_INNER_Y-216.2, FLANGE_T),')

# Retire the obsolete long rear-clamp-aligned holm through its old head closure,
# not merely up to y=215.7. The replacement support at the backstop rear edge
# already receives its own single cap and short DROP closure.
if '_RETIRED_HOLM_Y1 = 215.7' not in layout:
    raise SystemExit('Could not locate obsolete rear-holm retirement limit')
layout = layout.replace('_RETIRED_HOLM_Y1 = 215.7',
                        '_RETIRED_HOLM_Y1 = ARM_PROFILE_HEAD_FACE_Y + 0.20', 1)

# The +/-80 mm front support windows start at x=+/-64 mm. The old +/-90 layout
# used a central middle web out to +/-74 mm, which would now intrude 10 mm into
# the retained holm and recreate the unwanted parallel head wall. Narrow only
# that middle web; top/bottom crosshead flanges remain full structural members.
old_web = '    box(-74.0, 216.0, ARM_BOTTOM_Z+FLANGE_T, 148.0, 4.5, ARM_H-2*FLANGE_T),\n'
new_web = '    box(-64.0, 216.0, ARM_BOTTOM_Z+FLANGE_T, 128.0, 4.5, ARM_H-2*FLANGE_T),\n'
if old_web not in s:
    raise SystemExit('Could not locate old +/-74 mm crosshead middle web')
s = s.replace(old_web, new_web, 1)

# Reinsert measured geometry before the final support-free screw-cage/deck pass.
if final_base_start not in s:
    raise SystemExit('Final-base insertion point disappeared')
s = s.replace(final_base_start, layout + final_base_start, 1)

# ---------------------------------------------------------------------------
# Retarget existing hard geometry checks to the FINAL handed support positions.
# RIGHT keeps the front holm at -80 and moves the rear support to +180.
# LEFT is its exact X mirror: -180 and +80.
# These remain hard material/void checks; only their probe positions change.
# ---------------------------------------------------------------------------
old_caps = '''_head_cap_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _ARM_HEAD_CAPS]
_head_cap_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _ARM_HEAD_CAPS]
'''
new_caps = '''_FINAL_HOLM_HEAD_CAPS_RIGHT = [_ARM_HEAD_CAPS[0], _REAR_SUPPORT_HEAD_CAP_RIGHT]
_FINAL_HOLM_HEAD_CAPS_LEFT = [_REAR_SUPPORT_HEAD_CAP_LEFT, _ARM_HEAD_CAPS[1]]
_head_cap_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _FINAL_HOLM_HEAD_CAPS_RIGHT]
_head_cap_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _FINAL_HOLM_HEAD_CAPS_LEFT]
'''
if old_caps not in s:
    raise SystemExit('Could not retarget supportfree head-cap material probes')
s = s.replace(old_caps, new_caps, 1)

old_probes = '''_ARM_INNER_WALL_PROBES = [
    box(xc-4.0, 216.25, 18.0, 8.0, 3.50, 13.0)
    for xc in CLAMP_X
]
_inner_wall_probe_common_right = [BASE_RIGHT.common(q).Volume for q in _ARM_INNER_WALL_PROBES]
_inner_wall_probe_common_left = [BASE_LEFT.common(q).Volume for q in _ARM_INNER_WALL_PROBES]
'''
new_probes = '''_ARM_INNER_WALL_PROBES_RIGHT = [
    box(xc-4.0, 216.25, 18.0, 8.0, 3.50, 13.0)
    for xc in (RACK_LAYOUT_FRONT_SUPPORT_X_RIGHT, RACK_LAYOUT_REAR_SUPPORT_X_RIGHT)
]
_ARM_INNER_WALL_PROBES_LEFT = [
    box(xc-4.0, 216.25, 18.0, 8.0, 3.50, 13.0)
    for xc in (RACK_LAYOUT_REAR_SUPPORT_X_LEFT, RACK_LAYOUT_FRONT_SUPPORT_X_LEFT)
]
_inner_wall_probe_common_right = [BASE_RIGHT.common(q).Volume for q in _ARM_INNER_WALL_PROBES_RIGHT]
_inner_wall_probe_common_left = [BASE_LEFT.common(q).Volume for q in _ARM_INNER_WALL_PROBES_LEFT]
'''
if old_probes not in s:
    raise SystemExit('Could not retarget redundant-inner-wall probes')
s = s.replace(old_probes, new_probes, 1)

old_count = "if len(_ARM_HEAD_CAPS) != 2 or len(_ARM_INNER_WALL_PROBES) != 2:\n    failures.append('BASE does not contain exactly two corrected holm-head positions')\n"
new_count = "if (len(_FINAL_HOLM_HEAD_CAPS_RIGHT) != 2 or len(_FINAL_HOLM_HEAD_CAPS_LEFT) != 2 or\n        len(_ARM_INNER_WALL_PROBES_RIGHT) != 2 or len(_ARM_INNER_WALL_PROBES_LEFT) != 2):\n    failures.append('Each handed BASE does not contain exactly two corrected final holm-head positions')\n"
if old_count not in s:
    raise SystemExit('Could not retarget final holm-head count gate')
s = s.replace(old_count, new_count, 1)
s = s.replace("    'crosshead_middle_web_x_mm': [-74.0, 74.0],",
              "    'crosshead_middle_web_x_mm': [-64.0, 64.0],", 1)

# The short head-gap DROP gate must likewise follow the handed final support
# locations instead of the retired rear-clamp holm.
old_drop = '''_final_drop_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _ARM_HEAD_DROPS]
_final_drop_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _ARM_HEAD_DROPS]
'''
new_drop = '''_FINAL_HOLM_HEAD_DROPS_RIGHT = _ARM_HEAD_DROPS[0:2] + _REAR_SUPPORT_HEAD_DROPS_RIGHT
_FINAL_HOLM_HEAD_DROPS_LEFT = _REAR_SUPPORT_HEAD_DROPS_LEFT + _ARM_HEAD_DROPS[2:4]
_final_drop_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _FINAL_HOLM_HEAD_DROPS_RIGHT]
_final_drop_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _FINAL_HOLM_HEAD_DROPS_LEFT]
'''
if old_drop not in s:
    raise SystemExit('Could not retarget final holm DROP probes')
s = s.replace(old_drop, new_drop, 1)
old_drop_count = "if len(_ARM_HEAD_DROPS) != 4:\n    failures.append('BASE does not contain exactly two head-gap side drops per holm')\n"
new_drop_count = "if len(_FINAL_HOLM_HEAD_DROPS_RIGHT) != 4 or len(_FINAL_HOLM_HEAD_DROPS_LEFT) != 4:\n    failures.append('Each handed BASE does not contain exactly two head-gap side drops per final holm')\n"
if old_drop_count not in s:
    raise SystemExit('Could not retarget final holm DROP count gate')
s = s.replace(old_drop_count, new_drop_count, 1)

# Local backstop coordinates necessarily move 10 mm when the rear clamp moves
# from +90 to +80. Keep the hard 50 mm width and verify the derived intended
# local range 130..180 instead of the obsolete 140..190 constants.
old_start_gate = "if abs(MOUNT_BACKSTOP_X0-140.0) > 0.02:\n    failures.append('Rear mounting backstop does not start at local X=140 mm')\n"
new_start_gate = "if abs(MOUNT_BACKSTOP_X0-(REAR_CLAMP_X+50.0)) > 0.02:\n    failures.append('Rear mounting backstop does not start 50 mm behind the final rear clamp centre')\n"
if old_start_gate not in s:
    raise SystemExit('Could not retarget backstop start gate')
s = s.replace(old_start_gate, new_start_gate, 1)
old_end_gate = "if abs((MOUNT_BACKSTOP_X0+MOUNT_BACKSTOP_W_X)-190.0) > 0.02:\n    failures.append('Rear mounting backstop does not retain its local X=190 mm rear edge')\n"
new_end_gate = "if abs((MOUNT_BACKSTOP_X0+MOUNT_BACKSTOP_W_X)-(REAR_CLAMP_X+100.0)) > 0.02:\n    failures.append('Rear mounting backstop rear edge is not 100 mm behind the final rear clamp centre')\n"
if old_end_gate not in s:
    raise SystemExit('Could not retarget backstop rear-edge gate')
s = s.replace(old_end_gate, new_end_gate, 1)

# The moved support's own layout validation should report the corrected actual
# post-fix envelope, and remains a hard <=298 x 275 mm gate.
if s == orig:
    raise SystemExit('Measured rack-layout final compatibility pass made no changes')

p.write_text(s, encoding='utf-8')
print('Applied final measured-layout compatibility: pre-cage ordering, corrected crosshead depth, final handed holm probes and 130..180 backstop gates')
