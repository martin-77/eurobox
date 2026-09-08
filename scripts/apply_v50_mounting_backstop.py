from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Integrated mounting backstop for each side module.
#
# Purpose: assembly aid only. It hangs approximately 50 mm below the rack-clamp
# station and rests against the upper section of the THRON² EQP diagonal rack
# stays while the two actual rack clamps are being closed. It is deliberately
# not a third clamp and not part of the primary load path.
#
# The two rack-clamp centres are x=±90 mm and each upper station is 34 mm wide,
# leaving 146 mm between their inner faces. Keep 3 mm free at each end of the
# hanging panel (140 mm panel width) so the clamp pin / closure hardware remains
# unobstructed. A short high-level rail overlaps only the upper station bodies
# to make the panel an integral part of BASE.
anchor = '''BASE = BASE.removeSplitter()\n\n# -----------------------------\n# Rack lower clamp\n# -----------------------------'''
if anchor not in s:
    raise SystemExit('Could not locate final BASE before rack lower clamp')

replacement = '''BASE = BASE.removeSplitter()\n\n# -----------------------------\n# Integrated mounting backstop between the two rack clamps\n# -----------------------------\nMOUNT_BACKSTOP_W = 140.0\nMOUNT_BACKSTOP_H = 50.0\nMOUNT_BACKSTOP_T = 4.0\nMOUNT_BACKSTOP_X0 = -MOUNT_BACKSTOP_W/2.0\nMOUNT_BACKSTOP_Y0 = -16.0\nMOUNT_BACKSTOP_Z0 = -42.0\nMOUNT_BACKSTOP_Z1 = MOUNT_BACKSTOP_Z0 + MOUNT_BACKSTOP_H\n\n# Main flat panel: the bicycle-bag-like mounting stop requested for test fit.\n# It is intentionally plain: no V saddle, clip or load-bearing stay interface.\nMOUNT_BACKSTOP_PANEL = box(MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_Y0,\n                           MOUNT_BACKSTOP_Z0, MOUNT_BACKSTOP_W,\n                           MOUNT_BACKSTOP_T, MOUNT_BACKSTOP_H)\n\n# High connector rail. The final rack-root pass starts the fixed upper station\n# at Y=-8 mm, so this rail reaches to Y=-6 mm and overlaps that final station by\n# 2 mm. It stays at Z=6..12 mm, above the moving lower-clamp body.\n# The hanging panel overlaps this rail by 2 mm vertically.\nMOUNT_BACKSTOP_RAIL = box(-74.0, -16.0, 6.0, 148.0, 10.0, 6.0)\nBASE = BASE.fuse(MOUNT_BACKSTOP_PANEL).fuse(MOUNT_BACKSTOP_RAIL).removeSplitter()\n\n# The backstop is fused after the upper clamp stations were originally bored.\n# Re-cut the exact frozen rack-pin bores through the final fused BASE so the\n# added panel cannot refill either Ø4.6 mm shaft path.\nfor xc in CLAMP_X:\n    BASE = BASE.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))\n\n# The rack pin is intentionally asymmetric: its Ø7.5 mm head sits on the -X\n# side of each pin. At the +90 mm clamp that head is inboard and its local\n# x=-20.8..-18.4 envelope reaches 0.8 mm into the 140 mm panel. Provide a\n# local Ø8.3 mm service pocket only across that head envelope. The pocket stops\n# before the fixed clevis lug (which starts at x=+73 mm), so the clamp root and\n# pivot bearing remain untouched.\nRACK_PIN_HEAD_CLEAR_R = 4.15\nRACK_PIN_HEAD_CLEAR_X0 = CLAMP_X[1] - 21.2\nRACK_PIN_HEAD_CLEAR_LEN = 3.2\nBASE = BASE.cut(cyl_x(RACK_PIN_HEAD_CLEAR_R, RACK_PIN_HEAD_CLEAR_LEN,\n                      RACK_PIN_HEAD_CLEAR_X0, PIN_Y, PIN_Z))\nBASE = BASE.removeSplitter()\n\nif not BASE.isValid() or len(BASE.Solids) != 1:\n    raise RuntimeError('Integrated mounting backstop did not fuse into one valid BASE solid')\n\n# -----------------------------\n# Rack lower clamp\n# -----------------------------'''
s = s.replace(anchor, replacement, 1)

# Record the intended non-load-bearing architecture in the source validation.
validation_anchor = "for name, sh in PARTS.items():\n"
if validation_anchor not in s:
    raise SystemExit('Could not locate v50 export/validation gate')
validation = '''V['mounting_backstop'] = {\n    'purpose': 'assembly_aid_only_non_load_bearing',\n    'architecture': 'integral_flat_panel_between_two_clamps',\n    'panel_width_mm': MOUNT_BACKSTOP_W,\n    'panel_height_mm': MOUNT_BACKSTOP_H,\n    'panel_thickness_mm': MOUNT_BACKSTOP_T,\n    'panel_x_clearance_to_each_upper_clamp_mm': round((146.0-MOUNT_BACKSTOP_W)/2.0, 3),\n    'panel_y_range_mm': [MOUNT_BACKSTOP_Y0, MOUNT_BACKSTOP_Y0+MOUNT_BACKSTOP_T],\n    'panel_z_range_mm': [MOUNT_BACKSTOP_Z0, MOUNT_BACKSTOP_Z1],\n    'rack_pin_bores_recut_after_fusion': True,\n    'right_pin_head_service_pocket_diameter_mm': round(2.0*RACK_PIN_HEAD_CLEAR_R, 3),\n    'right_pin_head_service_pocket_x_range_mm': [\n        round(RACK_PIN_HEAD_CLEAR_X0, 3),\n        round(RACK_PIN_HEAD_CLEAR_X0+RACK_PIN_HEAD_CLEAR_LEN, 3)],\n    'primary_load_path': 'two_rack_clamps_only',\n}\nif V['mounting_backstop']['panel_width_mm'] < 135.0:\n    failures.append('Mounting backstop does not span enough of the space between rack clamps')\nif abs(V['mounting_backstop']['panel_height_mm']-50.0) > 0.01:\n    failures.append('Mounting backstop is not the requested 50 mm hanging panel')\nif V['mounting_backstop']['panel_x_clearance_to_each_upper_clamp_mm'] < 2.0:\n    failures.append('Mounting backstop leaves insufficient clamp-side service clearance')\nif not V['mounting_backstop']['rack_pin_bores_recut_after_fusion']:\n    failures.append('Mounting backstop does not preserve rack-pin service bores')\nif V['mounting_backstop']['right_pin_head_service_pocket_diameter_mm'] < 8.0:\n    failures.append('Mounting backstop lacks practical clearance around inboard rack-pin head')\n\n'''
s = s.replace(validation_anchor, validation + validation_anchor, 1)

# Keep the generated build note aligned with the new architecture.
s = s.replace(
    "f.write('No diagonal-stay V saddle. Anti-rotation is integrated into both rack-clamp roots.\\n')",
    "f.write('No diagonal-stay clamp: each BASE has a 50 mm integral flat mounting backstop between its two rack clamps; primary load remains on the rack clamps.\\n')",
    1,
)

if s == orig:
    raise SystemExit('Mounting-backstop fixup made no changes')

p.write_text(s, encoding='utf-8')
print('Applied v50 mounting backstop: 140 x 50 x 4 mm integral panel between rack clamps')
