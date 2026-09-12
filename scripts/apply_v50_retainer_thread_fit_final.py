from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final fit hardening for the short RH8x2 knob-retainer interface.
# The long lead-nut pair is already phase-sensitive with the global printable
# clearances. The short retainer engagement gets its own tighter, still
# printable clearance. The actual exported spindle is audited as well.
old = '''cap_female_core = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
cap_female_major = THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE
cap_root_w = LEAD_PROFILE_ROOT_W + 2.0*LEAD_FLANK_CLEARANCE
cap_crest_w = LEAD_PROFILE_CREST_W + 2.0*LEAD_FLANK_CLEARANCE'''
new = '''CAP_RH8_RADIAL_CLEARANCE = 0.14
CAP_RH8_FLANK_CLEARANCE = 0.06
cap_female_core = THREAD_CORE_R + CAP_RH8_RADIAL_CLEARANCE
cap_female_major = THREAD_MAJOR/2.0 + CAP_RH8_RADIAL_CLEARANCE
cap_root_w = LEAD_PROFILE_ROOT_W + 2.0*CAP_RH8_FLANK_CLEARANCE
cap_crest_w = LEAD_PROFILE_CREST_W + 2.0*CAP_RH8_FLANK_CLEARANCE'''
if s.count(old) != 1:
    raise SystemExit('Expected exactly one final knob-retainer clearance block')
s = s.replace(old, new, 1)

# Re-fuse the same true MALE_STUD into the actual printable SPINDLE. This is
# idempotent if the preceding spindle construction already contains it, but it
# makes the exported part—not merely the standalone helper—the authoritative
# threaded geometry.
anchor = '''cap_y = hex_y + 7.0
cap_thread_start_y = lead_drive_y0 + LEAD_DRIVE_LEN'''
replacement = '''cap_y = hex_y + 7.0
cap_thread_start_y = lead_drive_y0 + LEAD_DRIVE_LEN
_retainer_stud_actual = z_to_y(MALE_STUD, 0, cap_thread_start_y, 0)
SPINDLE = SPINDLE.fuse(_retainer_stud_actual).removeSplitter()
if not SPINDLE.isValid() or len(SPINDLE.Solids) != 1:
    raise RuntimeError('Re-fusing the true RH8x2 retainer stud invalidated SPINDLE')'''
if s.count(anchor) != 1:
    raise SystemExit('Could not locate final retainer-stud placement anchor')
s = s.replace(anchor, replacement, 1)

meta_anchor = "    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
meta = ("    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
        "    'retainer_radial_clearance_mm': CAP_RH8_RADIAL_CLEARANCE,\n"
        "    'retainer_flank_clearance_each_side_mm': CAP_RH8_FLANK_CLEARANCE,\n")
if s.count(meta_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer metadata anchor')
s = s.replace(meta_anchor, meta, 1)

# Probe only the annulus outside the smooth Ø6.5 stud core. Non-zero volume is
# therefore direct proof that the real SPINDLE has an external helical ridge.
audit_anchor = "V['knob_retainer_thread'] = {\n"
audit = '''_retainer_stud_shell = cyl_y(
    THREAD_MAJOR/2.0 + 0.03,
    OUTER_STUD_LEN,
    0, cap_thread_start_y, 0).cut(
        cyl_y(THREAD_CORE_R + 0.06,
              OUTER_STUD_LEN,
              0, cap_thread_start_y, 0)).removeSplitter()
_retainer_actual_ridge_mm3 = SPINDLE.common(_retainer_stud_shell).Volume

'''
if s.count(audit_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer validation dictionary')
s = s.replace(audit_anchor, audit + audit_anchor, 1)
metric_anchor = "    'correct_phase_common_mm3': round(SPINDLE.common(cn).Volume, 6),\n"
if s.count(metric_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer correct-phase metric')
s = s.replace(
    metric_anchor,
    "    'actual_spindle_stud_ridge_mm3': round(_retainer_actual_ridge_mm3, 6),\n" + metric_anchor,
    1,
)

# Keep the existing correct-phase and deliberately wrong-phase gates intact;
# add a separate hard gate proving that the actual screw—not only MALE_STUD—
# carries the external thread.
fail_anchor = "if V['knob_retainer_thread']['correct_phase_common_mm3'] > 0.02:\n    failures.append('Knob retainer nut collides with matched RH8x2 outer stud')\n"
if s.count(fail_anchor) != 1:
    raise SystemExit('Could not locate retainer correct-phase hard gate')
s = s.replace(
    fail_anchor,
    "if _retainer_actual_ridge_mm3 < 0.05:\n"
    "    failures.append('Actual exported lead spindle has no developed RH8x2 retainer-stud ridge')\n"
    + fail_anchor,
    1,
)

if s == orig:
    raise SystemExit('Retainer-thread final fit pass made no changes')
for witness in [
    'CAP_RH8_RADIAL_CLEARANCE = 0.14',
    'CAP_RH8_FLANK_CLEARANCE = 0.06',
    '_retainer_stud_actual = z_to_y(MALE_STUD',
    'actual_spindle_stud_ridge_mm3',
]:
    if witness not in s:
        raise SystemExit('Missing final retainer-thread witness: '+witness)

p.write_text(s, encoding='utf-8')
print('Applied final RH8x2 retainer fit: tighter cap clearance + actual SPINDLE stud audit')
