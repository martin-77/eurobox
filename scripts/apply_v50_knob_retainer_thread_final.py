from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Absolute final rebuild for the separate RH8x2 knob-retainer nut.
#
# Keep the matched RH8x2 helical cutter running one complete pitch beyond both
# nut faces so the printed thread is genuinely open. Do not add tangent entry
# cone booleans at the end faces: FreeCAD/OCC accepts that BRep, but the tangent
# intersections produced a non-watertight STL in CI. The extended cutter alone
# preserves pitch, phase, clearance and the full 4.5 mm stud engagement.
old = '''CAP_NUT_H = 5.8
CAP_FEMALE = FEMALE_STUD.common(Part.makeCylinder(
    THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE + 0.06, CAP_NUT_H)).removeSplitter()
CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid threaded solid')'''

new = r'''CAP_NUT_H = 5.8
CAP_NUT_LEAD = 0.0
CAP_THREAD_OVERRUN = THREAD_PITCH
cap_female_core = THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
cap_female_major = THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE
cap_root_w = LEAD_PROFILE_ROOT_W + 2.0*LEAD_FLANK_CLEARANCE
cap_crest_w = LEAD_PROFILE_CREST_W + 2.0*LEAD_FLANK_CLEARANCE
cap_span = CAP_NUT_H + 2.0*CAP_THREAD_OVERRUN

# Dedicated extended female cutter. Starting one complete pitch before Y=0
# preserves the exact helix phase at the nut face while guaranteeing that no
# unthreaded end wall survives the boolean/export operation.
CAP_FEMALE_EXT_SCAD = os.path.join(
    OUT, 'thread_RH_8x2_knob_retainer_extended_cutter.scad')
cap_txt = f"""$fn=72;
module thread_solid(){{
  union(){{
    translate([0,0,-0.05]) cylinder(r={cap_female_core},h={CAP_NUT_H+0.10});
    translate([0,0,-{CAP_THREAD_OVERRUN}])
      linear_extrude(height={cap_span},twist=360*{cap_span}/{THREAD_PITCH},slices=ceil({cap_span}/{THREAD_PITCH}*28),convexity=40)
        polygon(points=[[{cap_female_core-0.08},-{cap_root_w}/2],[{cap_female_major},-{cap_crest_w}/2],[{cap_female_major},{cap_crest_w}/2],[{cap_female_core-0.08},{cap_root_w}/2]]);
  }}
}}
thread_solid();
"""
with open(CAP_FEMALE_EXT_SCAD, 'w') as f:
    f.write(cap_txt)
CAP_FEMALE = import_scad_shape(CAP_FEMALE_EXT_SCAD)

CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid open-threaded solid')'''

if old not in s:
    raise SystemExit('Could not locate final matched knob-retainer nut block')
s = s.replace(old, new, 1)

# Keep the existing phase-sensitive fit proof and report the exact final cutter
# architecture. CAP_NUT_LEAD intentionally remains zero so the existing report
# and >=4 mm full-depth engagement gate stay explicit without weakening checks.
s = s.replace(
    "    'profile_source': 'FEMALE_STUD from write_lead_thread_pair',\n",
    "    'profile_source': 'matched RH8x2 master profile with one-pitch cutter overrun',\n",
    1,
)
s = s.replace(
    "    'actual_stud_engagement_mm': round(cap_engagement, 3),\n",
    "    'actual_stud_engagement_mm': round(cap_engagement, 3),\n"
    "    'entry_chamfer_each_end_mm': CAP_NUT_LEAD,\n"
    "    'cutter_overrun_each_end_mm': CAP_THREAD_OVERRUN,\n"
    "    'full_depth_stud_engagement_after_entry_chamfer_mm': round(max(0.0, cap_engagement-CAP_NUT_LEAD), 3),\n",
    1,
)

fail_anchor = "if V['knob_retainer_thread']['actual_stud_engagement_mm'] < 4.0:\n    failures.append('Knob retainer nut has less than 4 mm actual thread engagement')\n"
if fail_anchor not in s:
    raise SystemExit('Could not locate knob-retainer engagement hard gate')
s = s.replace(
    fail_anchor,
    fail_anchor
    + "if V['knob_retainer_thread']['full_depth_stud_engagement_after_entry_chamfer_mm'] < 4.0:\n"
      "    failures.append('Knob retainer nut has less than 4 mm full-depth RH8x2 engagement after entry chamfer')\n",
    1,
)

# Later printability logic intentionally adjusts this smooth shoulder tunnel for
# the -0.5 mm preload state. Earlier nut/thread passes currently leave the same
# geometry formatted over four source lines. Normalize only the formatting here
# so the following printability pass can replace the geometry deterministically.
old_tunnel = '''BASE = BASE.cut(cyl_y(
        SHOULDER_D/2 + 0.30,
        (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50),
        sx, BOX_EDGE_Y+7.50, SPINDLE_Z))'''
normalized_tunnel = '''BASE = BASE.cut(cyl_y(SHOULDER_D/2 + 0.30, (NUT_Y0-0.50)-(BOX_EDGE_Y+7.50), sx, BOX_EDGE_Y+7.50, SPINDLE_Z))'''
if old_tunnel not in s:
    raise SystemExit('Could not locate multiline spindle shoulder tunnel before printability normalization')
s = s.replace(old_tunnel, normalized_tunnel, 1)

if s == orig:
    raise SystemExit('Final knob-retainer thread rebuild made no changes')
if 'CAP_THREAD_OVERRUN = THREAD_PITCH' not in s:
    raise SystemExit('Extended RH8x2 retainer cutter was not installed')
if 'CAP_NUT_LEAD = 0.0' not in s:
    raise SystemExit('Tangent retainer entry chamfers were not disabled')
if normalized_tunnel not in s:
    raise SystemExit('Spindle shoulder tunnel normalization failed')

p.write_text(s, encoding='utf-8')
print('Applied final RH8x2 knob-retainer rebuild: open-ended extended cutter, manifold end faces')