from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final knob-retainer correction.
#
# The broken version replaced the short hex retainer with a copy of LEAD_NUT,
# which made the exported STL the wrong physical part.  Build this exactly like
# the known-good rack M4 nut: a native OCC hex body minus an already-proven,
# fully developed female thread cutter.  FEMALE is the validated RH8x2 cutter
# used by the working removable lead nut and is 14 mm long, so it naturally
# over-runs both faces of the 5.8 mm retainer without cropping thread faces.
old = '''CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid open-threaded solid')'''
new = '''# Use the already-proven full-length RH8x2 female cutter directly.  Do not
# crop/intersect the helical BRep before subtraction; that was the source of
# earlier invalid/fragile retainer geometry.
CAP_FEMALE = FEMALE.copy()
if CAP_FEMALE.isNull() or not CAP_FEMALE.isValid() or len(CAP_FEMALE.Solids) != 1:
    raise RuntimeError('Proven RH8x2 FEMALE cutter is not one valid solid')
CAP_NUT_BODY = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT_BODY.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if CAP_NUT.isNull() or not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut OCC hex-minus-RH8x2 cut is not one valid solid')

# Hard shape gate: this part must remain the compact retainer nut, never a copy
# of the large lead-nut cartridge again.  z_to_y() maps the 5.8 mm nut height to Y.
_cap_bb = CAP_NUT.BoundBox
if not (12.95 <= _cap_bb.XLength <= 13.05):
    raise RuntimeError('Knob retainer outer X size is not the 13 mm AF hex body')
if not (5.79 <= _cap_bb.YLength <= 5.81):
    raise RuntimeError('Knob retainer axial length is not 5.8 mm')
if not (14.95 <= _cap_bb.ZLength <= 15.08):
    raise RuntimeError('Knob retainer outer Z size is not the 13 mm AF hex body')
if CAP_NUT.Volume >= CAP_NUT_BODY.Volume - 1.0:
    raise RuntimeError('Knob retainer has no meaningful internal RH8x2 material removal')'''
if s.count(old) != 1:
    raise SystemExit('Could not locate final short RH8x2 retainer construction')
s = s.replace(old, new, 1)

# Keep metadata truthful and make the construction directly comparable to the
# known-good rack M4 nut architecture.
profile_old = "    'profile_source': 'matched RH8x2 master profile with one-pitch cutter overrun',\n"
profile_new = "    'profile_source': 'native OCC 13mm AF hex minus proven full-length RH8x2 FEMALE cutter',\n"
if s.count(profile_old) != 1:
    raise SystemExit('Could not locate knob-retainer profile metadata')
s = s.replace(profile_old, profile_new, 1)

meta_anchor = "    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
meta = ("    'outer_stud_length_mm': OUTER_STUD_LEN,\n"
        "    'construction': 'native_OCC_hex_minus_proven_full_length_RH8x2_female_cutter',\n"
        "    'outer_across_flats_mm': 13.0,\n"
        "    'body_axial_length_mm': CAP_NUT_H,\n"
        "    'female_cutter_source': 'FEMALE used by eurobox_v50_lead_nut_print',\n")
if s.count(meta_anchor) != 1:
    raise SystemExit('Could not locate knob-retainer metadata anchor')
s = s.replace(meta_anchor, meta, 1)

# Add a source-shape witness to the final validation object.  The existing
# thread_surface_audit independently checks open core and bore-connected helix.
anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')
witness = '''V['knob_retainer_shape'] = {
    'construction': 'native_OCC_hex_minus_proven_RH8x2_female_cutter',
    'bbox_x_mm': round(CAP_NUT.BoundBox.XLength, 6),
    'bbox_y_axial_mm': round(CAP_NUT.BoundBox.YLength, 6),
    'bbox_z_mm': round(CAP_NUT.BoundBox.ZLength, 6),
    'body_volume_mm3': round(CAP_NUT_BODY.Volume, 6),
    'threaded_nut_volume_mm3': round(CAP_NUT.Volume, 6),
    'removed_volume_mm3': round(CAP_NUT_BODY.Volume-CAP_NUT.Volume, 6),
    'is_compact_5_8mm_retainer': CAP_NUT.BoundBox.YLength <= 5.81,
}
if not V['knob_retainer_shape']['is_compact_5_8mm_retainer']:
    failures.append('Knob retainer regressed to a non-compact cartridge-like part')
if V['knob_retainer_shape']['removed_volume_mm3'] < 20.0:
    failures.append('Knob retainer lacks substantial through-bore/thread removal')

'''
s = s.replace(anchor, witness + anchor, 1)

if s == orig:
    raise SystemExit('Final knob-retainer OCC rebuild made no changes')
for required in [
    'CAP_FEMALE = FEMALE.copy()',
    'CAP_NUT_BODY = z_to_y(hex_z(13.0, CAP_NUT_H)',
    "'construction': 'native_OCC_hex_minus_proven_full_length_RH8x2_female_cutter'",
    "V['knob_retainer_shape']",
]:
    if required not in s:
        raise SystemExit('Missing final knob-retainer witness: '+required)

p.write_text(s, encoding='utf-8')
print('Rebuilt RH8x2 knob retainer as compact native OCC hex-minus-proven-thread nut')
