from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Absolute final pass for the box-clamp lead hardware.
# Goals:
# - keep the removable RH8x2 lead-nut cartridge architecture;
# - give its retaining pin a real external groove and a matched snap clip;
# - keep enough printed material around the cartridge cross-pin hole;
# - derive the knob-retainer female thread from the same RH8x2 master pair as
#   the male outer stud, instead of a second independent cutter;
# - hard-fail if any of those interfaces regress.

# ---------------------------------------------------------------------------
# Lead-nut cartridge: strengthen the top retaining lug and move the cross-pin
# up by 1 mm. The previous 4 mm lug around a Ø3.4 mm bore left only 0.3 mm of
# material above and below the hole, which is not a credible PETG load path.
# ---------------------------------------------------------------------------
old = '''LEAD_NUT = box(-8.0, 0.0, -7.0, 16.0, NUT_THREAD_LEN, 14.0)
LEAD_NUT = LEAD_NUT.fuse(box(-6.0, 3.0, 7.0, 12.0, 8.0, 4.0))
LEAD_NUT = LEAD_NUT.cut(z_to_y(FEMALE, 0, 0, 0))
LEAD_NUT = LEAD_NUT.cut(cyl_x(1.7, 20.0, -10.0, 7.0, 9.0))
LEAD_NUT = LEAD_NUT.removeSplitter()

NUT_PIN = fuse_all([
    cyl_x(1.5, 23.5, -11.75, 0, 0),
    cyl_x(3.0, 2.0, -13.75, 0, 0),
])
NUT_PIN_CLIP = make_c_clip(3.2, 1.25, 1.3, 2.4)'''
new = '''LEAD_NUT_TAB_H = 6.0
LEAD_NUT_PIN_Y = 7.0
LEAD_NUT_PIN_Z = 10.0
LEAD_NUT_PIN_HOLE_D = 3.4

LEAD_NUT = box(-8.0, 0.0, -7.0, 16.0, NUT_THREAD_LEN, 14.0)
LEAD_NUT = LEAD_NUT.fuse(box(-6.0, 3.0, 7.0, 12.0, 8.0, LEAD_NUT_TAB_H))
LEAD_NUT = LEAD_NUT.cut(z_to_y(FEMALE, 0, 0, 0))
LEAD_NUT = LEAD_NUT.cut(cyl_x(LEAD_NUT_PIN_HOLE_D/2.0, 20.0, -10.0,
                              LEAD_NUT_PIN_Y, LEAD_NUT_PIN_Z))
LEAD_NUT = LEAD_NUT.removeSplitter()

# Retaining pin: Ø3 shaft through the Ø3.4 bore, head on one side, a genuine
# Ø2.4 x 1.6 mm retaining groove just outside the +X cage face, then a short
# Ø3 end. The old pin ended flush with the cage and had no groove at all.
NUT_PIN_SHAFT_D = 3.0
NUT_PIN_GROOVE_D = 2.4
NUT_PIN_GROOVE_W = 1.6
NUT_PIN_HEAD_D = 6.5
NUT_PIN_HEAD_T = 2.0
NUT_PIN_X0 = -11.4
NUT_PIN_GROOVE_X0 = 11.4
NUT_PIN_END_X1 = 14.5
NUT_PIN = fuse_all([
    cyl_x(NUT_PIN_SHAFT_D/2.0, NUT_PIN_GROOVE_X0-NUT_PIN_X0, NUT_PIN_X0, 0, 0),
    cyl_x(NUT_PIN_GROOVE_D/2.0, NUT_PIN_GROOVE_W, NUT_PIN_GROOVE_X0, 0, 0),
    cyl_x(NUT_PIN_SHAFT_D/2.0,
          NUT_PIN_END_X1-(NUT_PIN_GROOVE_X0+NUT_PIN_GROOVE_W),
          NUT_PIN_GROOVE_X0+NUT_PIN_GROOVE_W, 0, 0),
    cyl_x(NUT_PIN_HEAD_D/2.0, NUT_PIN_HEAD_T,
          NUT_PIN_X0-NUT_PIN_HEAD_T, 0, 0),
]).removeSplitter()

# Flat printable C-clip. It is rotated 90° only in the assembly. The mouth is
# deliberately narrower than the Ø2.4 groove so the clip must elastically snap
# over it; its Ø2.6 inner circle then runs with 0.2 mm diametral clearance.
NUT_PIN_CLIP_OUTER_R = 3.8
NUT_PIN_CLIP_INNER_R = 1.30
NUT_PIN_CLIP_T = 1.4
NUT_PIN_CLIP_OPENING_W = 1.90
NUT_PIN_CLIP = make_c_clip(NUT_PIN_CLIP_OUTER_R, NUT_PIN_CLIP_INNER_R,
                           NUT_PIN_CLIP_T, NUT_PIN_CLIP_OPENING_W)'''
if old not in s:
    raise SystemExit('Could not locate lead-nut cartridge/pin/clip block')
s = s.replace(old, new, 1)

# Match the BASE retaining bore to the strengthened cartridge lug.
old = '''    BASE = BASE.cut(cyl_x(1.7, 24.0, sx-12.0,
                          (NUT_Y0+NUT_Y1)/2, 40.0))'''
new = '''    BASE = BASE.cut(cyl_x(LEAD_NUT_PIN_HOLE_D/2.0, 24.0, sx-12.0,
                          NUT_Y0+LEAD_NUT_PIN_Y,
                          SPINDLE_Z+LEAD_NUT_PIN_Z))'''
if old not in s:
    raise SystemExit('Could not locate removable lead-nut retaining bore in BASE')
s = s.replace(old, new, 1)

# ---------------------------------------------------------------------------
# Knob retainer nut: use the exact same female RH8x2 master cutter as the male
# outer stud. The previous independent CAP_FEMALE profile could look threaded
# yet still collide with the actual stud. One master pair removes that drift.
# ---------------------------------------------------------------------------
pattern = re.compile(
    r"CAP_FEMALE_SCAD = os\.path\.join\(OUT, 'thread_RH_8x2_knob_retainer_cutter\.scad'\)\n"
    r"write_thread_scad\(CAP_FEMALE_SCAD, 3\.38, 4\.30, THREAD_PITCH, 5\.4, 1\.10, 0\.28\)\n"
    r"CAP_FEMALE = import_scad_shape\(CAP_FEMALE_SCAD\)\.common\(Part\.makeCylinder\(4\.34, 5\.4\)\)\.removeSplitter\(\)\n"
    r"CAP_NUT = z_to_y\(hex_z\(13\.0, 5\.4\), 0, 0, 0\)\n"
    r"CAP_NUT = CAP_NUT\.cut\(z_to_y\(CAP_FEMALE, 0, 0, 0\)\)\.removeSplitter\(\)",
    re.S,
)
replacement = '''CAP_NUT_H = 5.8
CAP_FEMALE = FEMALE_STUD.common(Part.makeCylinder(
    THREAD_MAJOR/2.0 + LEAD_RADIAL_CLEARANCE + 0.06, CAP_NUT_H)).removeSplitter()
CAP_NUT = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(CAP_FEMALE, 0, 0, 0)).removeSplitter()
if not CAP_NUT.isValid() or len(CAP_NUT.Solids) != 1:
    raise RuntimeError('Lead knob retainer nut is not one valid threaded solid')'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace independent knob-retainer thread cutter')

# Put the retainer nut at the phase dictated by its actual axial position on the
# RH8x2 stud. This turns the existing interface diagnostic into a real fit test.
old = '''cap_y = hex_y + 7.0
cn = CAP_NUT.copy(); cn.translate(App.Vector(0, cap_y, 0))'''
new = '''cap_y = hex_y + 7.0
cap_thread_start_y = lead_drive_y0 + LEAD_DRIVE_LEN
cap_phase_deg = -360.0 * (cap_y-cap_thread_start_y) / THREAD_PITCH
cn = CAP_NUT.copy()
cn.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg)
cn.translate(App.Vector(0, cap_y, 0))'''
if old not in s:
    raise SystemExit('Could not locate knob-retainer placement diagnostic')
s = s.replace(old, new, 1)

# Replace the old smooth-hole volume witness with a matched-pair phase test.
pattern = re.compile(
    r"cap_smooth = .*?\n\nV\['knob_interface'\] = \{",
    re.S,
)
replacement = '''cap_smooth = z_to_y(hex_z(13.0, CAP_NUT_H), 0, 0, 0).cut(
    cyl_y(THREAD_CORE_R+LEAD_RADIAL_CLEARANCE, CAP_NUT_H, 0, 0, 0))
cap_thread_extra_removed = cap_smooth.Volume - CAP_NUT.Volume
cap_wrong = CAP_NUT.copy()
cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg+180.0)
cap_wrong.translate(App.Vector(0, cap_y, 0))
cap_engagement = max(0.0, min(CAP_NUT_H,
    cap_thread_start_y + OUTER_STUD_LEN - cap_y))
V['knob_retainer_thread'] = {
    'standard': 'RH 8x2 matched single-source pair',
    'profile_source': 'FEMALE_STUD from write_lead_thread_pair',
    'threaded_length_mm': CAP_NUT_H,
    'actual_stud_engagement_mm': round(cap_engagement, 3),
    'extra_helical_volume_removed_mm3': round(cap_thread_extra_removed, 6),
    'outer_stud_length_mm': OUTER_STUD_LEN,
    'correct_phase_deg': round(cap_phase_deg, 3),
    'correct_phase_common_mm3': round(SPINDLE.common(cn).Volume, 6),
    'half_pitch_wrong_phase_common_mm3': round(SPINDLE.common(cap_wrong).Volume, 6),
}

V['knob_interface'] = {'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Could not replace knob-retainer thread witness')

# ---------------------------------------------------------------------------
# Retainer hardware proof. These checks encode the actual assembly logic rather
# than merely asserting that three STL files exist.
# ---------------------------------------------------------------------------
anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final export gate')
proof = '''V['lead_nut_retainer_hardware'] = {
    'architecture': 'drop_in_cartridge_cross_pin_with_external_C_clip',
    'cartridge_tab_height_mm': LEAD_NUT_TAB_H,
    'pin_hole_diameter_mm': LEAD_NUT_PIN_HOLE_D,
    'minimum_tab_wall_around_pin_mm': round((LEAD_NUT_TAB_H-LEAD_NUT_PIN_HOLE_D)/2.0, 3),
    'pin_shaft_diameter_mm': NUT_PIN_SHAFT_D,
    'pin_hole_diametral_clearance_mm': round(LEAD_NUT_PIN_HOLE_D-NUT_PIN_SHAFT_D, 3),
    'pin_head_diameter_mm': NUT_PIN_HEAD_D,
    'pin_groove_diameter_mm': NUT_PIN_GROOVE_D,
    'pin_groove_width_mm': NUT_PIN_GROOVE_W,
    'pin_groove_start_outside_cage_mm': round(NUT_PIN_GROOVE_X0-11.0, 3),
    'clip_inner_diameter_mm': round(2.0*NUT_PIN_CLIP_INNER_R, 3),
    'clip_outer_diameter_mm': round(2.0*NUT_PIN_CLIP_OUTER_R, 3),
    'clip_thickness_mm': NUT_PIN_CLIP_T,
    'clip_opening_width_mm': NUT_PIN_CLIP_OPENING_W,
    'clip_to_groove_diametral_clearance_mm': round(2.0*NUT_PIN_CLIP_INNER_R-NUT_PIN_GROOVE_D, 3),
    'snap_retention_overlap_mm': round(NUT_PIN_GROOVE_D-NUT_PIN_CLIP_OPENING_W, 3),
}
if V['lead_nut_retainer_hardware']['minimum_tab_wall_around_pin_mm'] < 1.0:
    failures.append('Lead-nut cartridge has insufficient printed wall around retaining pin')
if not (0.25 <= V['lead_nut_retainer_hardware']['pin_hole_diametral_clearance_mm'] <= 0.60):
    failures.append('Lead-nut retaining pin/hole clearance is not FDM-credible')
if V['lead_nut_retainer_hardware']['pin_groove_start_outside_cage_mm'] < 0.25:
    failures.append('Lead-nut retaining-pin groove is buried in the BASE cage')
if V['lead_nut_retainer_hardware']['clip_to_groove_diametral_clearance_mm'] < 0.10:
    failures.append('Lead-nut C-clip is too tight on the retaining-pin groove')
if V['lead_nut_retainer_hardware']['clip_to_groove_diametral_clearance_mm'] > 0.35:
    failures.append('Lead-nut C-clip is too loose on the retaining-pin groove')
if V['lead_nut_retainer_hardware']['snap_retention_overlap_mm'] < 0.35:
    failures.append('Lead-nut C-clip mouth is too wide to retain the pin groove')
if NUT_PIN_CLIP_T > NUT_PIN_GROOVE_W-0.10:
    failures.append('Lead-nut C-clip is too thick for the retaining-pin groove')
if NUT_PIN_HEAD_D < LEAD_NUT_PIN_HOLE_D + 2.0:
    failures.append('Lead-nut retaining-pin head is too small for positive retention')
if V['knob_retainer_thread']['correct_phase_common_mm3'] > 0.02:
    failures.append('Knob retainer nut collides with matched RH8x2 outer stud')
if V['knob_retainer_thread']['half_pitch_wrong_phase_common_mm3'] < 0.25:
    failures.append('Knob retainer nut lacks phase-sensitive RH8x2 engagement')
if V['knob_retainer_thread']['actual_stud_engagement_mm'] < 4.0:
    failures.append('Knob retainer nut has less than 4 mm actual thread engagement')

'''
s = s.replace(anchor, proof + anchor, 1)

# Put the cartridge pins, clips and knob retainer nuts into the assembly so the
# saved FCStd represents the hardware that is actually meant to be built.
right_anchor = "    k = KNOB.copy(); k.translate(App.Vector(sx, RY+BOX_EDGE_Y+hex_y, SPINDLE_Z)); add_obj('RIGHT_knob_'+str(int(sx)), k)\n"
right_extra = '''    np = NUT_PIN.copy(); np.translate(App.Vector(sx, RY+NUT_Y0+LEAD_NUT_PIN_Y,
                                                     SPINDLE_Z+LEAD_NUT_PIN_Z)); add_obj('RIGHT_nut_pin_'+str(int(sx)), np)
    nc = NUT_PIN_CLIP.copy(); nc.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90.0)
    nc.translate(App.Vector(sx+NUT_PIN_GROOVE_X0, RY+NUT_Y0+LEAD_NUT_PIN_Y,
                            SPINDLE_Z+LEAD_NUT_PIN_Z)); add_obj('RIGHT_nut_pin_clip_'+str(int(sx)), nc)
    cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg)
    cap.translate(App.Vector(sx, RY+BOX_EDGE_Y+cap_y, SPINDLE_Z)); add_obj('RIGHT_knob_retainer_nut_'+str(int(sx)), cap)
'''
if right_anchor not in s:
    raise SystemExit('Could not locate right spindle/knob assembly block')
s = s.replace(right_anchor, right_anchor + right_extra, 1)

left_anchor = "    sp = SPINDLE.copy(); sp.translate(App.Vector(sx,BOX_EDGE_Y,SPINDLE_Z)); add_obj('LEFT_spindle_'+str(int(sx)), left_transform(sp))\n"
left_extra = '''    np = NUT_PIN.copy(); np.translate(App.Vector(sx, NUT_Y0+LEAD_NUT_PIN_Y,
                                                     SPINDLE_Z+LEAD_NUT_PIN_Z)); add_obj('LEFT_nut_pin_'+str(int(sx)), left_transform(np))
    nc = NUT_PIN_CLIP.copy(); nc.rotate(App.Vector(0,0,0), App.Vector(0,1,0), 90.0)
    nc.translate(App.Vector(sx+NUT_PIN_GROOVE_X0, NUT_Y0+LEAD_NUT_PIN_Y,
                            SPINDLE_Z+LEAD_NUT_PIN_Z)); add_obj('LEFT_nut_pin_clip_'+str(int(sx)), left_transform(nc))
    cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg)
    cap.translate(App.Vector(sx, BOX_EDGE_Y+cap_y, SPINDLE_Z)); add_obj('LEFT_knob_retainer_nut_'+str(int(sx)), left_transform(cap))
'''
if left_anchor not in s:
    raise SystemExit('Could not locate left spindle assembly block')
s = s.replace(left_anchor, left_anchor + left_extra, 1)

if s == orig:
    raise SystemExit('Lead-hardware final pass made no changes')
p.write_text(s, encoding='utf-8')
print('Applied final lead hardware pass: matched retainer thread + grooved pin + retained C-clip')
