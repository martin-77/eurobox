from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The mounting backstop is a stop against the rack/stay, so its vertical contact
# wall must be on the BOX/OUTBOARD side of the rack tube. The previous Y=-16..-12
# placement put the wall inboard, i.e. behind the tube from the box side.
# Keep all X/rear/handed logic unchanged. The 4 mm contact wall starts at Y=8.0,
# 1.79 mm beyond the measured 12.42 mm rack-tube crown (Y=6.21).
#
# Keep the structural root/gusset at the original 20 mm depth instead of the
# accidental 16 mm introduced by the first contact-side move. They live at Z>=7,
# above the 6.21 mm tube crown, so they can span Y=0..20 without hitting the tube.
repls = {
    'MOUNT_BACKSTOP_Y0 = -16.0': 'MOUNT_BACKSTOP_Y0 = 8.0',
    'MOUNT_BACKSTOP_ROOT_Y0 = -16.0': 'MOUNT_BACKSTOP_ROOT_Y0 = 0.0',
    'MOUNT_BACKSTOP_ROOT_Y1 = 4.0': 'MOUNT_BACKSTOP_ROOT_Y1 = 20.0',
    'MOUNT_BACKSTOP_GUSSET_Y0 = -16.0': 'MOUNT_BACKSTOP_GUSSET_Y0 = 0.0',
    'MOUNT_BACKSTOP_GUSSET_Y1 = 4.0': 'MOUNT_BACKSTOP_GUSSET_Y1 = 20.0',
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit('Could not locate backstop datum: ' + old)
    s = s.replace(old, new, 1)

# Make the intended side explicit in the validation report and hard-gate it.
# The canonical measured rack tube diameter in build_v50.py is RACK_D.
meta_anchor = "    'panel_y_range_mm': [MOUNT_BACKSTOP_Y0, MOUNT_BACKSTOP_Y0+MOUNT_BACKSTOP_T_Y],\n"
if meta_anchor not in s:
    raise SystemExit('Could not locate backstop panel metadata')
s = s.replace(
    meta_anchor,
    meta_anchor +
    "    'contact_side': 'outboard_box_side_in_front_of_rack_tube',\n" +
    "    'tube_outboard_crown_y_mm': round(RACK_D/2.0, 3),\n" +
    "    'panel_clearance_from_tube_outboard_crown_mm': round(MOUNT_BACKSTOP_Y0-RACK_D/2.0, 3),\n" +
    "    'structural_root_y_range_mm': [MOUNT_BACKSTOP_ROOT_Y0, MOUNT_BACKSTOP_ROOT_Y1],\n",
    1,
)

gate_anchor = "if abs(V['mounting_backstop']['panel_height_mm']-50.0) > 0.01:\n    failures.append('Rear mounting backstop is not the requested 50 mm hanging height')\n"
if gate_anchor not in s:
    raise SystemExit('Could not locate backstop validation gate')
s = s.replace(
    gate_anchor,
    gate_anchor +
    "if V['mounting_backstop']['contact_side'] != 'outboard_box_side_in_front_of_rack_tube':\n"
    "    failures.append('Rear mounting backstop is not on the box/outboard side of the rack tube')\n"
    "if V['mounting_backstop']['panel_clearance_from_tube_outboard_crown_mm'] < 1.5:\n"
    "    failures.append('Rear mounting backstop is too close to or behind the rack tube')\n"
    "if V['mounting_backstop']['root_block_y_depth_mm'] < 20.0:\n"
    "    failures.append('Rear mounting backstop structural root lost its 20 mm design depth')\n",
    1,
)

if s == orig:
    raise SystemExit('Backstop contact-side fix made no changes')
p.write_text(s, encoding='utf-8')
print('Moved rear backstop contact wall outboard while preserving a 20 mm structural root/gusset')
