from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The mounting backstop is a stop against the rack/stay, so its vertical contact
# wall must be on the BOX/OUTBOARD side of the rack tube. The previous Y=-16..-12
# placement put the wall inboard, i.e. behind the tube from the box side.
# Keep all X/rear/handed logic unchanged and move only the contact wall/root/gusset
# across the tube. Tube OD is 12.42 -> crown at local Y=+6.21 mm. Start the wall
# at +8.0 mm, leaving 1.79 mm nominal clearance to the main rack tube envelope.
repls = {
    'MOUNT_BACKSTOP_Y0 = -16.0': 'MOUNT_BACKSTOP_Y0 = 8.0',
    'MOUNT_BACKSTOP_ROOT_Y0 = -16.0': 'MOUNT_BACKSTOP_ROOT_Y0 = 4.0',
    'MOUNT_BACKSTOP_ROOT_Y1 = 4.0': 'MOUNT_BACKSTOP_ROOT_Y1 = 20.0',
    'MOUNT_BACKSTOP_GUSSET_Y0 = -16.0': 'MOUNT_BACKSTOP_GUSSET_Y0 = 4.0',
    'MOUNT_BACKSTOP_GUSSET_Y1 = 4.0': 'MOUNT_BACKSTOP_GUSSET_Y1 = 20.0',
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit('Could not locate backstop datum: ' + old)
    s = s.replace(old, new, 1)

# Make the intended side explicit in the validation report and hard-gate it.
# The canonical restored v50 source names the measured rack diameter TUBE_D.
meta_anchor = "    'panel_y_range_mm': [MOUNT_BACKSTOP_Y0, MOUNT_BACKSTOP_Y0+MOUNT_BACKSTOP_T_Y],\n"
if meta_anchor not in s:
    raise SystemExit('Could not locate backstop panel metadata')
s = s.replace(
    meta_anchor,
    meta_anchor +
    "    'contact_side': 'outboard_box_side_in_front_of_rack_tube',\n" +
    "    'tube_outboard_crown_y_mm': round(TUBE_D/2.0, 3),\n" +
    "    'panel_clearance_from_tube_outboard_crown_mm': round(MOUNT_BACKSTOP_Y0-TUBE_D/2.0, 3),\n",
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
    "    failures.append('Rear mounting backstop is too close to or behind the rack tube')\n",
    1,
)

if s == orig:
    raise SystemExit('Backstop contact-side fix made no changes')
p.write_text(s, encoding='utf-8')
print('Moved rear backstop to outboard/box side: wall now in front of rack tube')
