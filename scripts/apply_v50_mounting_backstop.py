from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Rear mounting backstop for each side module.
#
# Frozen riding-direction convention for v50 from this pass onward:
#   -X = bicycle front / saddle side
#   +X = bicycle rear / wheel end
# Therefore CLAMP_X max() is the rear clamp on the RIGHT local module.
#
# Because the left module is rotated 180 degrees around Z to point its +Y arm
# outboard, an X-asymmetric rear stop makes the BASE inherently handed. Build a
# mirrored LEFT printable BASE so both assembled stops still end up at global
# +X (rear). The THRON² EQP diagonal stay starts behind the rear clamp and runs
# forward as it drops. This aid remains non-load-bearing and is not a third rack
# clamp.
anchor = '''BASE = BASE.removeSplitter()\n\n# -----------------------------\n# Rack lower clamp\n# -----------------------------'''
if anchor not in s:
    raise SystemExit('Could not locate final BASE before rack lower clamp')

replacement = '''BASE = BASE.removeSplitter()\n\n# -----------------------------\n# Rear-only integrated mounting backstop\n# -----------------------------\nRIDE_FRONT_X_SIGN = -1\nRIDE_REAR_X_SIGN = 1\nFRONT_CLAMP_X = min(CLAMP_X)\nREAR_CLAMP_X = max(CLAMP_X)\n\n# Photo-derived useful stay-contact zone: roughly 60..100 mm behind the rear\n# clamp centre over the planned 50 mm hanging height. Keep this a broad contact\n# window rather than inventing an exact axis for the still-unmeasured stay.\nMOUNT_BACKSTOP_X_FROM_REAR_CLAMP = 60.0\nMOUNT_BACKSTOP_W_X = 40.0\nMOUNT_BACKSTOP_H = 50.0\nMOUNT_BACKSTOP_T_Y = 4.0\nMOUNT_BACKSTOP_X0 = REAR_CLAMP_X + MOUNT_BACKSTOP_X_FROM_REAR_CLAMP\nMOUNT_BACKSTOP_X1 = MOUNT_BACKSTOP_X0 + MOUNT_BACKSTOP_W_X\nMOUNT_BACKSTOP_Y0 = -16.0\nMOUNT_BACKSTOP_Z0 = -42.0\nMOUNT_BACKSTOP_Z1 = MOUNT_BACKSTOP_Z0 + MOUNT_BACKSTOP_H\n\n# Bicycle-bag-like flat stop face: one per BASE, behind the rear clamp only.\nMOUNT_BACKSTOP_PANEL = box(MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_Y0,\n                           MOUNT_BACKSTOP_Z0, MOUNT_BACKSTOP_W_X,\n                           MOUNT_BACKSTOP_T_Y, MOUNT_BACKSTOP_H)\n\n# Strong lower root. It overlaps the hanging panel and extends 20 mm toward the\n# BASE. Z starts at 7 mm, safely above the real 12.42 mm rack tube crown at\n# Z=6.21, so strength is added without a hidden tube collision.\nMOUNT_BACKSTOP_ROOT_Y0 = -16.0\nMOUNT_BACKSTOP_ROOT_Y1 = 4.0\nMOUNT_BACKSTOP_ROOT_Z0 = 7.0\nMOUNT_BACKSTOP_ROOT_Z1 = 22.0\nMOUNT_BACKSTOP_ROOT = box(MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_ROOT_Y0,\n                          MOUNT_BACKSTOP_ROOT_Z0, MOUNT_BACKSTOP_W_X,\n                          MOUNT_BACKSTOP_ROOT_Y1-MOUNT_BACKSTOP_ROOT_Y0,\n                          MOUNT_BACKSTOP_ROOT_Z1-MOUNT_BACKSTOP_ROOT_Z0)\n\n# Upper gusset: broad material path from the rear stop into the rear I-beam /\n# clamp root. Near the clamp it stays above the lower-clamp sweep; at the stop\n# it drops to the root block. Its top remains 0.79 mm below box support.\nMOUNT_BACKSTOP_GUSSET_Y0 = -16.0\nMOUNT_BACKSTOP_GUSSET_Y1 = 4.0\nMOUNT_BACKSTOP_GUSSET_TOP_Z = 38.75\nMOUNT_BACKSTOP_REAR_ROOT_X0 = REAR_CLAMP_X - ARM_W/2.0\n_mount_backstop_profile = [\n    App.Vector(MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_GUSSET_Y0, 7.0),\n    App.Vector(MOUNT_BACKSTOP_X1, MOUNT_BACKSTOP_GUSSET_Y0, 7.0),\n    App.Vector(MOUNT_BACKSTOP_X1, MOUNT_BACKSTOP_GUSSET_Y0, MOUNT_BACKSTOP_GUSSET_TOP_Z),\n    App.Vector(MOUNT_BACKSTOP_REAR_ROOT_X0, MOUNT_BACKSTOP_GUSSET_Y0, MOUNT_BACKSTOP_GUSSET_TOP_Z),\n    App.Vector(MOUNT_BACKSTOP_REAR_ROOT_X0, MOUNT_BACKSTOP_GUSSET_Y0, 24.0),\n    App.Vector(MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_GUSSET_Y0, 20.0),\n]\n_mount_backstop_wire = Part.makePolygon(_mount_backstop_profile + [_mount_backstop_profile[0]])\nMOUNT_BACKSTOP_GUSSET = Part.Face(_mount_backstop_wire).extrude(\n    App.Vector(0, MOUNT_BACKSTOP_GUSSET_Y1-MOUNT_BACKSTOP_GUSSET_Y0, 0))\n\n# Quantify the RIGHT local connection.\n_rear_root_ref = make_i_beam_y(REAR_CLAMP_X, -8.0, 36.0)\n_front_root_ref = make_i_beam_y(FRONT_CLAMP_X, -8.0, 36.0)\nMOUNT_BACKSTOP_REAR_ROOT_OVERLAP_MM3 = MOUNT_BACKSTOP_GUSSET.common(_rear_root_ref).Volume\nMOUNT_BACKSTOP_FRONT_ROOT_OVERLAP_MM3 = MOUNT_BACKSTOP_GUSSET.common(_front_root_ref).Volume\n\nMOUNT_BACKSTOP = fuse_all([\n    MOUNT_BACKSTOP_PANEL,\n    MOUNT_BACKSTOP_ROOT,\n    MOUNT_BACKSTOP_GUSSET,\n])\nBASE = BASE.fuse(MOUNT_BACKSTOP).removeSplitter()\n\n# Preserve both frozen rack-pin bores after every final BASE fusion.\nfor xc in CLAMP_X:\n    BASE = BASE.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))\nBASE = BASE.removeSplitter()\n\nif not BASE.isValid() or len(BASE.Solids) != 1:\n    raise RuntimeError('Rear-only mounting backstop did not fuse into one valid BASE solid')\n\n# The old universal BASE was X-symmetric and could simply be rotated 180 deg for\n# the left side. The rear-only stop breaks that symmetry. Keep BASE/BASE_RIGHT\n# as the right printable part and mirror X for a dedicated left printable BASE.\nBASE_RIGHT = BASE.copy()\nBASE_LEFT = BASE.copy()\nBASE_LEFT.mirror(App.Vector(0,0,0), App.Vector(1,0,0))\nif (not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1 or\n        abs(BASE_LEFT.Volume-BASE_RIGHT.Volume) > 1e-4):\n    raise RuntimeError('Mirrored LEFT rear-backstop BASE is not a valid handed copy')\n\n# -----------------------------\n# Rack lower clamp\n# -----------------------------'''
s = s.replace(anchor, replacement, 1)

# Export explicit handed BASE files while keeping eurobox_v50_base as the right
# legacy/canonical alias so existing validators and external links stay valid.
parts_anchor = "PARTS = {\n    'eurobox_v50_base': BASE,\n"
if parts_anchor not in s:
    raise SystemExit('Could not locate PARTS base entry for handed export')
s = s.replace(
    parts_anchor,
    "PARTS = {\n"
    "    'eurobox_v50_base': BASE_RIGHT,\n"
    "    'eurobox_v50_base_right': BASE_RIGHT,\n"
    "    'eurobox_v50_base_left': BASE_LEFT,\n",
    1,
)

# Assembly must use the handed BASE_LEFT before the existing proper 180-degree
# rotation. That maps its local -X stop back to global +X, same as RIGHT.
s = s.replace(
    "right_base = BASE.copy(); right_base.translate(App.Vector(0, RY, 0)); add_obj('RIGHT_base', right_base)",
    "right_base = BASE_RIGHT.copy(); right_base.translate(App.Vector(0, RY, 0)); add_obj('RIGHT_base', right_base)",
    1,
)
s = s.replace(
    "add_obj('LEFT_base', left_transform(BASE))",
    "add_obj('LEFT_base', left_transform(BASE_LEFT))",
    1,
)
if "left_transform(BASE_LEFT)" not in s:
    raise SystemExit('Assembly was not switched to the handed LEFT base')

validation_anchor = "for name, sh in PARTS.items():\n"
if validation_anchor not in s:
    raise SystemExit('Could not locate v50 export/validation gate')
validation = '''V['mounting_backstop'] = {\n    'purpose': 'rear_diagonal_stay_assembly_aid_only_non_load_bearing',\n    'riding_axis': 'X',\n    'front_direction': '-X',\n    'rear_direction': '+X',\n    'handed_bases_required': True,\n    'front_clamp_x_mm': FRONT_CLAMP_X,\n    'rear_clamp_x_mm': REAR_CLAMP_X,\n    'architecture': 'handed_single_rear_40mm_panel_with_deep_root_and_rear_i_beam_gusset',\n    'right_base_local_panel_x_range_mm': [MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_X1],\n    'left_base_local_panel_x_range_mm': [-MOUNT_BACKSTOP_X1, -MOUNT_BACKSTOP_X0],\n    'right_assembled_global_panel_x_range_mm': [MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_X1],\n    'left_assembled_global_panel_x_range_mm': [MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_X1],\n    'panel_x_width_mm': MOUNT_BACKSTOP_W_X,\n    'panel_height_mm': MOUNT_BACKSTOP_H,\n    'panel_thickness_y_mm': MOUNT_BACKSTOP_T_Y,\n    'panel_y_range_mm': [MOUNT_BACKSTOP_Y0, MOUNT_BACKSTOP_Y0+MOUNT_BACKSTOP_T_Y],\n    'panel_z_range_mm': [MOUNT_BACKSTOP_Z0, MOUNT_BACKSTOP_Z1],\n    'contact_window_behind_rear_clamp_center_mm': [\n        round(MOUNT_BACKSTOP_X0-REAR_CLAMP_X, 3),\n        round(MOUNT_BACKSTOP_X1-REAR_CLAMP_X, 3),\n    ],\n    'clearance_from_rear_clamp_body_mm': round(MOUNT_BACKSTOP_X0-(REAR_CLAMP_X+17.0), 3),\n    'root_block_y_depth_mm': MOUNT_BACKSTOP_ROOT_Y1-MOUNT_BACKSTOP_ROOT_Y0,\n    'root_block_z_height_mm': MOUNT_BACKSTOP_ROOT_Z1-MOUNT_BACKSTOP_ROOT_Z0,\n    'upper_gusset_top_z_mm': MOUNT_BACKSTOP_GUSSET_TOP_Z,\n    'gap_below_box_support_mm': round(BOX_SUPPORT_Z-MOUNT_BACKSTOP_GUSSET_TOP_Z, 3),\n    'rear_i_beam_root_overlap_mm3': round(MOUNT_BACKSTOP_REAR_ROOT_OVERLAP_MM3, 3),\n    'front_i_beam_root_overlap_mm3': round(MOUNT_BACKSTOP_FRONT_ROOT_OVERLAP_MM3, 6),\n    'left_right_base_volume_delta_mm3': round(abs(BASE_LEFT.Volume-BASE_RIGHT.Volume), 6),\n    'rack_pin_bores_recut_after_fusion': True,\n    'primary_load_path': 'two_rack_clamps_only',\n}\nif V['mounting_backstop']['front_direction'] != '-X' or V['mounting_backstop']['rear_direction'] != '+X':\n    failures.append('Riding-direction convention is not frozen as -X front / +X rear')\nif not V['mounting_backstop']['handed_bases_required']:\n    failures.append('Rear-only mounting backstop incorrectly claims a universal base')\nif V['mounting_backstop']['right_assembled_global_panel_x_range_mm'] != V['mounting_backstop']['left_assembled_global_panel_x_range_mm']:\n    failures.append('Left/right mounting backstops do not assemble at the same global rear X range')\nif abs(V['mounting_backstop']['panel_height_mm']-50.0) > 0.01:\n    failures.append('Rear mounting backstop is not the requested 50 mm hanging height')\nif V['mounting_backstop']['right_base_local_panel_x_range_mm'][0] <= REAR_CLAMP_X + 17.0:\n    failures.append('RIGHT mounting backstop is not fully behind the rear clamp body')\nif V['mounting_backstop']['left_base_local_panel_x_range_mm'][1] >= FRONT_CLAMP_X - 17.0:\n    failures.append('LEFT local mounting backstop is not on the mirrored rear end')\nif V['mounting_backstop']['clearance_from_rear_clamp_body_mm'] < 35.0:\n    failures.append('Rear mounting backstop leaves too little service space behind the rear clamp')\nif V['mounting_backstop']['contact_window_behind_rear_clamp_center_mm'][0] < 55.0:\n    failures.append('Rear mounting backstop starts too close to the rear clamp for the falling diagonal stay')\nif V['mounting_backstop']['contact_window_behind_rear_clamp_center_mm'][1] > 105.0:\n    failures.append('Rear mounting backstop extends beyond the intended photo-derived stay contact window')\nif V['mounting_backstop']['root_block_y_depth_mm'] < 18.0:\n    failures.append('Rear mounting backstop root block is too shallow for a robust BASE connection')\nif not (0.5 <= V['mounting_backstop']['gap_below_box_support_mm'] <= 1.5):\n    failures.append('Rear mounting backstop gusset top must stay 0.5..1.5 mm below box support')\nif V['mounting_backstop']['rear_i_beam_root_overlap_mm3'] < 1000.0:\n    failures.append('Rear mounting backstop does not substantially overlap the rear I-beam root')\nif V['mounting_backstop']['front_i_beam_root_overlap_mm3'] > 1e-4:\n    failures.append('RIGHT rear mounting backstop incorrectly reaches the front I-beam root')\nif V['mounting_backstop']['left_right_base_volume_delta_mm3'] > 1e-4:\n    failures.append('Handed LEFT/RIGHT base volumes differ after mirror')\nif not V['mounting_backstop']['rack_pin_bores_recut_after_fusion']:\n    failures.append('Rear mounting backstop does not preserve rack-pin service bores')\n\n'''
s = s.replace(validation_anchor, validation + validation_anchor, 1)

# Keep generated notes aligned with delivered geometry.
for old_note in [
    "f.write('No diagonal-stay V saddle. Anti-rotation is integrated into both rack-clamp roots.\\n')",
    "f.write('No diagonal-stay clamp: each BASE has a 50 mm integral flat mounting backstop between its two rack clamps; primary load remains on the rack clamps.\\n')",
    "f.write('Each BASE has a non-clamping 100 mm diagonal-stay mounting backstop, tapered upward into both I-beam roots; primary load remains on the two rack clamps.\\n')",
    "f.write('Each BASE has one rear-only 50 mm diagonal-stay mounting backstop behind the rear rack clamp, strongly gusseted into that rear I-beam root; primary load remains on the two rack clamps.\\n')",
]:
    s = s.replace(
        old_note,
        "f.write('Rear-only diagonal-stay aid uses handed LEFT/RIGHT BASE parts so both 50 mm stops assemble at the wheel end; each is deeply gusseted into its rear I-beam root. Primary load remains on the two rack clamps.\\n')",
    )

if s == orig:
    raise SystemExit('Handed rear mounting-backstop fixup made no changes')

p.write_text(s, encoding='utf-8')
print('Applied handed v50 rear backstops: both assembled at global +X rear, 60..100 mm behind rear clamp')
