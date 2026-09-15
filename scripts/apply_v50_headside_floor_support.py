from pathlib import Path

# The final 600 mm width-cleanup pass deliberately trims the old outboard clamp
# architecture and rebuilds the cage at new inboard Y datums. Therefore the
# requested BASE geometry must be applied AFTER width cleanup. Patching
# build_v50.py here would be silently removed again later in the workflow.
#
# This compatibility hook makes the subsequent width-cleanup script invoke the
# actual final-geometry patches only after it has rebuilt the handed bases.
wc = Path('scripts/apply_v50_width_cleanup.py')
s = wc.read_text(encoding='utf-8')
marker = '# APPLY_FINAL_REQUESTED_BASE_GEOMETRY_AFTER_WIDTH_CLEANUP'

if marker not in s:
    hook = r'''

# APPLY_FINAL_REQUESTED_BASE_GEOMETRY_AFTER_WIDTH_CLEANUP
# The user-requested head-side/lower-floor changes belong to the final inboard
# BASE, not to the obsolete pre-width-cleanup cage.
_final_base_patch = Path('scripts/apply_v50_final_base_geometry.py')
if not _final_base_patch.is_file():
    raise SystemExit('Missing final requested BASE geometry patch')
exec(compile(_final_base_patch.read_text(encoding='utf-8'),
             str(_final_base_patch), 'exec'))

# Apply the final visual/structural corrections at the same stable stage: the
# rear backstop bridge spans the complete 50 mm panel width and the short gap
# from each holm to its single flush head cap is closed by side DROP walls.
_final_backstop_drop_patch = Path('scripts/apply_v50_final_backstop_holm_drop.py')
if not _final_backstop_drop_patch.is_file():
    raise SystemExit('Missing final backstop/holm DROP geometry patch')
exec(compile(_final_backstop_drop_patch.read_text(encoding='utf-8'),
             str(_final_backstop_drop_patch), 'exec'))

# Finally tie the two fixed rack-clamp stations together on the frame side. A
# straight top member plus DROP uses the same saddle radius as the upper clamps,
# so it may bear on the Ø12.42 rack tube while the moving lower clamps stay free.
_final_clamp_frame_patch = Path('scripts/apply_v50_clamp_frame_bridge.py')
if not _final_clamp_frame_patch.is_file():
    raise SystemExit('Missing final clamp-frame saddle bridge patch')
exec(compile(_final_clamp_frame_patch.read_text(encoding='utf-8'),
             str(_final_clamp_frame_patch), 'exec'))
'''
    wc.write_text(s + hook, encoding='utf-8')

# Width validation used to locate the inboard cage by assuming that the first
# nut-cutter loop followed immediately after the cage fuse. The final requested
# BASE geometry now legitimately sits between those two sections. Make that
# validator anchor on the stable nut-cutter loop itself instead of on layout
# adjacency, while keeping the exact same plate-sweep cutter logic.
wv = Path('scripts/apply_v50_width_validation.py')
vs = wv.read_text(encoding='utf-8')
old = '''anchor = \'\'\'BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()\nBASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()\n\nfor sx in SPINDLE_X:\n\'\'\'\nplate_clearance = \'\'\'BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()\nBASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()\n\n_plate_body_y0_for_clearance = BOX_RIM_INNER_Y - PLATE_Y\n'''
new = '''anchor = \'\'\'for sx in SPINDLE_X:\n    _nut_pocket = box(sx-8.35, NUT_THREAD_Y0-0.35, 23.65,\n\'\'\'\nplate_clearance = \'\'\'_plate_body_y0_for_clearance = BOX_RIM_INNER_Y - PLATE_Y\n'''
if old not in vs:
    raise SystemExit('Could not retarget width-validation plate-sweep anchor')
vs = vs.replace(old, new, 1)
old_tail = '''for sx in SPINDLE_X:\n\'\'\'\nif anchor not in bs:\n    raise SystemExit('Could not locate inboard cage for plate-sweep clearance')\nbs = bs.replace(anchor, plate_clearance, 1)\n'''
new_tail = '''for sx in SPINDLE_X:\n    _nut_pocket = box(sx-8.35, NUT_THREAD_Y0-0.35, 23.65,\n\'\'\'\nif anchor not in bs:\n    raise SystemExit('Could not locate final nut-cutter loop for plate-sweep clearance')\nbs = bs.replace(anchor, plate_clearance, 1)\n'''
if old_tail not in vs:
    raise SystemExit('Could not retarget width-validation replacement tail')
vs = vs.replace(old_tail, new_tail, 1)
wv.write_text(vs, encoding='utf-8')

print('Deferred requested BASE geometry until after final width cleanup, including backstop, holm DROP and clamp-frame saddle bridge')
