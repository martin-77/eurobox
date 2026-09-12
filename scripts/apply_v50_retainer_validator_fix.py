from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The knob retainer is now an unchanged copy of the already-proven LEAD_NUT.
# The old "extra volume removed from a 5.8 mm hex" witness is no longer a valid
# metric: a full LEAD_NUT copy is larger than that obsolete reference and makes
# the volume delta negative even though the actual bore contains a developed,
# connected RH8x2 groove. Replace only that stale gate with checks against the
# real final thread-surface audit already installed earlier in the fixup chain.
pat = re.compile(
    r"if\s+V\['knob_retainer_thread'\]\['extra_helical_volume_removed_mm3'\]\s*<\s*[^:]+:\n"
    r"\s*failures\.append\('Lead knob retainer nut has no meaningful RH 8x2 internal thread'\)\n"
)
replacement = '''if V['thread_surface_audit']['rh8x2_retainer_core_block_mm3'] > 1e-4:
    failures.append('RH8x2 knob retainer bore is blocked by a smooth inner wall')
if V['thread_surface_audit']['rh8x2_retainer_bore_connected_groove_mm3'] < 5.0:
    failures.append('RH8x2 knob retainer lacks a meaningful bore-connected internal thread groove')
'''
s, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not locate exactly one stale knob-retainer volume gate')

if s == orig:
    raise SystemExit('Retainer validator fix made no changes')
for witness in [
    "rh8x2_retainer_core_block_mm3",
    "rh8x2_retainer_bore_connected_groove_mm3",
]:
    if witness not in s:
        raise SystemExit('Missing final retainer surface-audit witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Replaced stale retainer volume gate with actual RH8x2 bore/surface audit')
