from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Absolute final rebuild for the separate RH8x2 knob-retainer nut.
#
# The generic matched cutter is geometrically threaded, but because its helix
# starts and ends exactly on the nut faces it can leave a weak/visually closed
# thread entrance in the final mesh. Use the same proven strategy as the rack
# M4 nut: run the helical groove one complete pitch beyond BOTH faces and add
# short entry chamfers. The profile, pitch and clearance remain derived from the
# exact same RH8x2 master values as the male outer stud.
old = '''CAP_NUT_H = 5.8
CAP_FEMALE = FEMALE_STUD.common(Part.makeCylinder(
    THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE + 0.06, CAP_NUT_H)).removeSplitter()
CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid threaded solid')'''

new = r'''CAP_NUT_H = 5.8
CAP_NUT_LEAD = 0.40
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
cap_txt = f'''$fn=72;\nmodule thread_solid(){{\n  union(){{\n    translate([0,0,-0.05]) cylinder(r={cap_female_core},h={CAP_NUT_H+0.10});\n    translate([0,0,-{CAP_THREAD_OVERRUN}])\n      linear_extrude(height={cap_span},twist=360*{cap_span}/{THREAD_PITCH},slices=ceil({cap_span}/{THREAD_PITCH}*28),convexity=40)\n        polygon(points=[[{cap_female_core-0.08},-{cap_root_w}/2],[{cap_female_major},-{cap_crest_w}/2],[{cap_female_major},{cap_crest_w}/2],[{cap_female_core-0.08},{cap_root_w}/2]]);\n  }}\n}}\nthread_solid();\n'''
with open(CAP_FEMALE_EXT_SCAD, 'w') as f:
    f.write(cap_txt)
CAP_FEMALE = import_scad_shape(CAP_FEMALE_EXT_SCAD)

CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()

# Short entry chamfers improve printed screw pickup while retaining at least
# 4.0 mm of full-depth engagement on the existing 7 mm outer stud.
cap_entry_0 = Part.makeCone(4.55, cap_female_core, CAP_NUT_LEAD,
                            App.Vector(0,0,0), App.Vector(0,1,0))
cap_entry_1 = Part.makeCone(cap_female_core, 4.55, CAP_NUT_LEAD,
                            App.Vector(0,CAP_NUT_H-CAP_NUT_LEAD,0),
                            App.Vector(0,1,0))
CAP_NUT = CAP_NUT.cut(cap_entry_0).cut(cap_entry_1).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid open-threaded solid')'''

if old not in s:
    raise SystemExit('Could not locate final matched knob-retainer nut block')
s = s.replace(old, new, 1)

# Keep the existing phase-sensitive fit proof, but make the report state the
# actual final cutter architecture and effective full-depth thread engagement.
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

if s == orig:
    raise SystemExit('Final knob-retainer thread rebuild made no changes')
if 'CAP_THREAD_OVERRUN = THREAD_PITCH' not in s:
    raise SystemExit('Extended RH8x2 retainer cutter was not installed')

p.write_text(s, encoding='utf-8')
print('Applied final RH8x2 knob-retainer rebuild: open-ended extended cutter + entry chamfers')
