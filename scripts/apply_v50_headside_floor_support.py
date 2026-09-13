from pathlib import Path

# The final 600 mm width-cleanup pass deliberately trims the old outboard clamp
# architecture and rebuilds the cage at new inboard Y datums. Therefore the
# requested BASE geometry must be applied AFTER width cleanup. Patching
# build_v50.py here would be silently removed again later in the workflow.
#
# This compatibility hook makes the subsequent width-cleanup script invoke the
# actual final-geometry patch only after it has rebuilt the handed bases.
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
'''
    wc.write_text(s + hook, encoding='utf-8')

print('Deferred requested BASE geometry until after final width cleanup')
