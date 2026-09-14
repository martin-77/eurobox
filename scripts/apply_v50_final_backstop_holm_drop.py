from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# ---------------------------------------------------------------------------
# Final visual/structural cleanup requested after the validated v50 build:
# 1) the vertical rear backstop must be tied into the BASE by the rectangular
#    bridge over the COMPLETE 50 mm panel width, not by only a 4 mm root nib;
# 2) the short 4.8 mm gap between the longitudinal holm end and its flush outer
#    head cap is closed with vertical "drop" walls at both side faces. The long
#    H/I channels remain open; only the short head gap is bridged.
#
# This pass is deliberately executed after width cleanup/final-base geometry.
# It changes no spindle, nut, cage, pin or rack-clamp datums.

# Full-width rectangular backstop connection. Existing formulas for RIGHT and
# LEFT already use MOUNT_BACKSTOP_ROOT_OVERLAP_X to find the panel-side edge of
# the bridge, so setting it to the complete panel width makes the bridge run
# from the 8 mm holm overlap all the way to the outer panel edge (98..190 RIGHT,
# -190..-98 LEFT). Z/Y remain unchanged and the existing clamp-sweep validator
# therefore checks the actual stronger geometry.
old = 'MOUNT_BACKSTOP_ROOT_OVERLAP_X = 4.0\n'
new = 'MOUNT_BACKSTOP_ROOT_OVERLAP_X = MOUNT_BACKSTOP_W_X\n'
if old not in s:
    raise SystemExit('Could not locate narrow 4 mm backstop root overlap')
s = s.replace(old, new, 1)

# Short holm-head DROP solution. The holm itself ends at ARM_Y1=220.0 while the
# single flush cap begins at ARM_PROFILE_HEAD_FACE_Y-ARM_PROFILE_HEAD_CAP_T =
# 224.815. A 0.20 mm overlap into both existing solids gives an unambiguous
# manifold union. Two 3.2 mm side drops per holm close the visible slit without
# filling either longitudinal H/I channel.
anchor = '''_ARM_HEAD_CAPS = [_arm_head_cap(xc, ARM_PROFILE_HEAD_FACE_Y) for xc in CLAMP_X]
for _q in _ARM_HEAD_CAPS:
    BASE_CORE = BASE_CORE.fuse(_q).removeSplitter()
if not BASE_CORE.isValid() or len(BASE_CORE.Solids) != 1:
    raise RuntimeError('Single-wall holm head cleanup broke BASE core topology')
'''
if anchor not in s:
    raise SystemExit('Could not locate final holm head-cap fusion')
replacement = '''_ARM_HEAD_CAPS = [_arm_head_cap(xc, ARM_PROFILE_HEAD_FACE_Y) for xc in CLAMP_X]
for _q in _ARM_HEAD_CAPS:
    BASE_CORE = BASE_CORE.fuse(_q).removeSplitter()

ARM_PROFILE_HEAD_DROP_T = ARM_PROFILE_WEB_T
ARM_PROFILE_HEAD_DROP_OVERLAP = 0.20
ARM_PROFILE_HEAD_DROP_Y0 = ARM_Y1 - ARM_PROFILE_HEAD_DROP_OVERLAP
ARM_PROFILE_HEAD_DROP_Y1 = (ARM_PROFILE_HEAD_FACE_Y - ARM_PROFILE_HEAD_CAP_T
                            + ARM_PROFILE_HEAD_DROP_OVERLAP)
_ARM_HEAD_DROPS = []
for xc in CLAMP_X:
    for _x0 in (xc-ARM_W/2.0,
                xc+ARM_W/2.0-ARM_PROFILE_HEAD_DROP_T):
        _q = box(
            _x0,
            ARM_PROFILE_HEAD_DROP_Y0,
            ARM_BOTTOM_Z,
            ARM_PROFILE_HEAD_DROP_T,
            ARM_PROFILE_HEAD_DROP_Y1-ARM_PROFILE_HEAD_DROP_Y0,
            ARM_H,
        )
        _ARM_HEAD_DROPS.append(_q)
        BASE_CORE = BASE_CORE.fuse(_q).removeSplitter()

if not BASE_CORE.isValid() or len(BASE_CORE.Solids) != 1:
    raise RuntimeError('Holm head DROP cleanup broke BASE core topology')
'''
s = s.replace(anchor, replacement, 1)

# Add final hard checks immediately before export. These verify the requested
# geometry itself; no existing mechanical or mesh gate is weakened.
export_anchor = "for name, sh in PARTS.items():\n"
if export_anchor not in s:
    raise SystemExit('Could not locate final export gate for backstop/drop checks')
validation = '''# Full-width rear-backstop / holm-head DROP hard checks.
_final_drop_fraction_right = [BASE_RIGHT.common(q).Volume/q.Volume for q in _ARM_HEAD_DROPS]
_final_drop_fraction_left = [BASE_LEFT.common(q).Volume/q.Volume for q in _ARM_HEAD_DROPS]
V['final_backstop_holm_drop'] = {
    'backstop_bridge_policy': 'rectangular_full_50mm_panel_width_no_diagonal',
    'right_bridge_x_mm': [MOUNT_BACKSTOP_REAR_ROOT_X0, MOUNT_BACKSTOP_BRIDGE_X1],
    'left_bridge_x_mm': [MOUNT_BACKSTOP_LEFT_BRIDGE_X0, MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1],
    'panel_width_mm': MOUNT_BACKSTOP_W_X,
    'panel_root_overlap_mm': MOUNT_BACKSTOP_ROOT_OVERLAP_X,
    'holm_overlap_x_mm': MOUNT_BACKSTOP_HOLM_OVERLAP_X,
    'drop_count_per_base': len(_ARM_HEAD_DROPS),
    'drop_y_mm': [round(ARM_PROFILE_HEAD_DROP_Y0, 3), round(ARM_PROFILE_HEAD_DROP_Y1, 3)],
    'drop_side_thickness_mm': ARM_PROFILE_HEAD_DROP_T,
    'drop_material_fraction_right': [round(x, 6) for x in _final_drop_fraction_right],
    'drop_material_fraction_left': [round(x, 6) for x in _final_drop_fraction_left],
    'longitudinal_channels_policy': 'open except for short head-gap side drops',
}
if abs(MOUNT_BACKSTOP_ROOT_OVERLAP_X-MOUNT_BACKSTOP_W_X) > 1e-9:
    failures.append('Rear backstop bridge is not connected over the complete panel width')
if abs(MOUNT_BACKSTOP_BRIDGE_X1-(MOUNT_BACKSTOP_X0+MOUNT_BACKSTOP_W_X)) > 1e-9:
    failures.append('RIGHT rear backstop bridge does not reach the outer edge of the 50 mm panel')
if abs(MOUNT_BACKSTOP_LEFT_BRIDGE_X0-(MOUNT_BACKSTOP_LEFT_X1-MOUNT_BACKSTOP_W_X)) > 1e-9:
    failures.append('LEFT rear backstop bridge does not reach the outer edge of the 50 mm panel')
if len(_ARM_HEAD_DROPS) != 4:
    failures.append('BASE does not contain exactly two head-gap side drops per holm')
for _side, _vals in (('RIGHT', _final_drop_fraction_right), ('LEFT', _final_drop_fraction_left)):
    for _i, _frac in enumerate(_vals):
        if _frac < 0.999:
            failures.append(f'{_side} holm head DROP {_i} is not fully incorporated in the final BASE')
if ARM_PROFILE_HEAD_DROP_Y0 >= ARM_Y1:
    failures.append('Holm head DROP does not overlap the longitudinal holm')
if ARM_PROFILE_HEAD_DROP_Y1 <= ARM_PROFILE_HEAD_FACE_Y-ARM_PROFILE_HEAD_CAP_T:
    failures.append('Holm head DROP does not overlap the flush outer head cap')

'''
s = s.replace(export_anchor, validation + export_anchor, 1)

if s == orig:
    raise SystemExit('Final full-width backstop / holm-drop patch made no changes')
if 'MOUNT_BACKSTOP_ROOT_OVERLAP_X = MOUNT_BACKSTOP_W_X' not in s:
    raise SystemExit('Full-width backstop bridge was not installed')
if '_ARM_HEAD_DROPS = []' not in s:
    raise SystemExit('Holm-head DROP geometry was not installed')

p.write_text(s, encoding='utf-8')
print('Applied full-width rectangular rear backstop bridge and short holm-head DROP closures')
