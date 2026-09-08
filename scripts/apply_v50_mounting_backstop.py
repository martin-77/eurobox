from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Integrated mounting backstop for each side module.
#
# Assembly aid only: the 100 mm lower panel rests against the upper section of
# the THRON² EQP diagonal rack stays while the two real rack clamps are closed.
# It is deliberately not a third clamp and not part of the primary load path.
#
# The old 140 mm panel left only ~3 mm to the clamp stations and hung from a
# narrow rail. This version leaves ~23 mm per side at clamp level, then widens
# only above the moving lower-clamp sweep into a broad structural schott tied
# directly into both longitudinal I-beam roots.
anchor = '''BASE = BASE.removeSplitter()\n\n# -----------------------------\n# Rack lower clamp\n# -----------------------------'''
if anchor not in s:
    raise SystemExit('Could not locate final BASE before rack lower clamp')

replacement = '''BASE = BASE.removeSplitter()\n\n# -----------------------------\n# Integrated mounting backstop between the two rack clamps\n# -----------------------------\nMOUNT_BACKSTOP_W = 100.0\nMOUNT_BACKSTOP_H = 50.0\nMOUNT_BACKSTOP_T = 4.0\nMOUNT_BACKSTOP_X0 = -MOUNT_BACKSTOP_W/2.0\nMOUNT_BACKSTOP_Y0 = -16.0\nMOUNT_BACKSTOP_Z0 = -42.0\nMOUNT_BACKSTOP_Z1 = MOUNT_BACKSTOP_Z0 + MOUNT_BACKSTOP_H\n\n# Main bicycle-bag-like stop face. At clamp/pin height it occupies only\n# x=-50..+50, leaving about 23 mm to each fixed clamp station inner face.\nMOUNT_BACKSTOP_PANEL = box(MOUNT_BACKSTOP_X0, MOUNT_BACKSTOP_Y0,\n                           MOUNT_BACKSTOP_Z0, MOUNT_BACKSTOP_W,\n                           MOUNT_BACKSTOP_T, MOUNT_BACKSTOP_H)\n\n# Deep central root block: real overlap instead of the former narrow 1-2 mm\n# connector. It overlaps the panel by 2 mm vertically and carries the load into\n# the tapered upper schott.\nMOUNT_BACKSTOP_ROOT_Y0 = -16.0\nMOUNT_BACKSTOP_ROOT_Y1 = -4.0\nMOUNT_BACKSTOP_ROOT_Z0 = 6.0\nMOUNT_BACKSTOP_ROOT_Z1 = 14.0\nMOUNT_BACKSTOP_ROOT = box(-50.0, MOUNT_BACKSTOP_ROOT_Y0,\n                          MOUNT_BACKSTOP_ROOT_Z0, 100.0,\n                          MOUNT_BACKSTOP_ROOT_Y1-MOUNT_BACKSTOP_ROOT_Y0,\n                          MOUNT_BACKSTOP_ROOT_Z1-MOUNT_BACKSTOP_ROOT_Z0)\n\n# Tapered upper schott. It stays only 100 mm wide until Z=12, then widens to\n# the complete two-beam envelope (x=-106..+106) at Z=20. The lower-clamp sweep\n# therefore remains open. Above Z=20 the schott is full width and ties into\n# both 32 mm I-beam roots. Its top stays 0.79 mm below the box support datum so\n# the Eurobox still rests on the intended arm flanges, not on this assembly aid.\nMOUNT_BACKSTOP_SCHOTT_Y0 = -10.0\nMOUNT_BACKSTOP_SCHOTT_Y1 = -4.0\nMOUNT_BACKSTOP_TAPER_Z0 = 12.0\nMOUNT_BACKSTOP_FULL_WIDTH_Z0 = 20.0\nMOUNT_BACKSTOP_SCHOTT_TOP_Z = 38.75\nMOUNT_BACKSTOP_SCHOTT_HALF_W = 106.0\n\n_mount_backstop_profile = [\n    App.Vector(-50.0, MOUNT_BACKSTOP_SCHOTT_Y0, MOUNT_BACKSTOP_TAPER_Z0),\n    App.Vector( 50.0, MOUNT_BACKSTOP_SCHOTT_Y0, MOUNT_BACKSTOP_TAPER_Z0),\n    App.Vector( MOUNT_BACKSTOP_SCHOTT_HALF_W, MOUNT_BACKSTOP_SCHOTT_Y0,\n               MOUNT_BACKSTOP_FULL_WIDTH_Z0),\n    App.Vector( MOUNT_BACKSTOP_SCHOTT_HALF_W, MOUNT_BACKSTOP_SCHOTT_Y0,\n               MOUNT_BACKSTOP_SCHOTT_TOP_Z),\n    App.Vector(-MOUNT_BACKSTOP_SCHOTT_HALF_W, MOUNT_BACKSTOP_SCHOTT_Y0,\n               MOUNT_BACKSTOP_SCHOTT_TOP_Z),\n    App.Vector(-MOUNT_BACKSTOP_SCHOTT_HALF_W, MOUNT_BACKSTOP_SCHOTT_Y0,\n               MOUNT_BACKSTOP_FULL_WIDTH_Z0),\n]\n_mount_backstop_wire = Part.makePolygon(\n    _mount_backstop_profile + [_mount_backstop_profile[0]])\nMOUNT_BACKSTOP_SCHOTT = Part.Face(_mount_backstop_wire).extrude(\n    App.Vector(0, MOUNT_BACKSTOP_SCHOTT_Y1-MOUNT_BACKSTOP_SCHOTT_Y0, 0))\n\n# Prove that the widened schott has substantial overlap into BOTH final I-beam\n# roots, not merely face contact. The reinforced roots run from Y=-8 onward;\n# the schott reaches Y=-4, giving 4 mm physical insertion depth.\nMOUNT_BACKSTOP_ROOT_OVERLAP_MM3 = []\nfor xc in CLAMP_X:\n    _root_ref = make_i_beam_y(xc, -8.0, 36.0)\n    MOUNT_BACKSTOP_ROOT_OVERLAP_MM3.append(\n        MOUNT_BACKSTOP_SCHOTT.common(_root_ref).Volume)\n\nMOUNT_BACKSTOP = fuse_all([\n    MOUNT_BACKSTOP_PANEL,\n    MOUNT_BACKSTOP_ROOT,\n    MOUNT_BACKSTOP_SCHOTT,\n])\nBASE = BASE.fuse(MOUNT_BACKSTOP).removeSplitter()\n\n# Preserve the frozen rack-pin bores after every final BASE fusion. The new\n# 100 mm lower panel is already far from the pin heads, so no ad-hoc pin-head\n# pocket is necessary anymore.\nfor xc in CLAMP_X:\n    BASE = BASE.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))\nBASE = BASE.removeSplitter()\n\nif not BASE.isValid() or len(BASE.Solids) != 1:\n    raise RuntimeError('Integrated 100 mm mounting backstop did not fuse into one valid BASE solid')\n\n# -----------------------------\n# Rack lower clamp\n# -----------------------------'''
s = s.replace(anchor, replacement, 1)

# Record the architecture and hard-gate the features that make the new
# connection materially stronger while retaining clamp service clearance.
validation_anchor = "for name, sh in PARTS.items():\n"
if validation_anchor not in s:
    raise SystemExit('Could not locate v50 export/validation gate')
validation = '''V['mounting_backstop'] = {\n    'purpose': 'assembly_aid_only_non_load_bearing',\n    'architecture': '100mm_lower_panel_tapered_to_full_two_beam_schott',\n    'panel_width_mm': MOUNT_BACKSTOP_W,\n    'panel_height_mm': MOUNT_BACKSTOP_H,\n    'panel_thickness_mm': MOUNT_BACKSTOP_T,\n    'panel_x_clearance_to_each_upper_clamp_mm': round((146.0-MOUNT_BACKSTOP_W)/2.0, 3),\n    'panel_y_range_mm': [MOUNT_BACKSTOP_Y0, MOUNT_BACKSTOP_Y0+MOUNT_BACKSTOP_T],\n    'panel_z_range_mm': [MOUNT_BACKSTOP_Z0, MOUNT_BACKSTOP_Z1],\n    'root_block_y_depth_mm': MOUNT_BACKSTOP_ROOT_Y1-MOUNT_BACKSTOP_ROOT_Y0,\n    'root_block_z_height_mm': MOUNT_BACKSTOP_ROOT_Z1-MOUNT_BACKSTOP_ROOT_Z0,\n    'taper_start_z_mm': MOUNT_BACKSTOP_TAPER_Z0,\n    'full_width_start_z_mm': MOUNT_BACKSTOP_FULL_WIDTH_Z0,\n    'upper_schott_width_mm': 2.0*MOUNT_BACKSTOP_SCHOTT_HALF_W,\n    'upper_schott_thickness_y_mm': MOUNT_BACKSTOP_SCHOTT_Y1-MOUNT_BACKSTOP_SCHOTT_Y0,\n    'upper_schott_root_insertion_y_mm': MOUNT_BACKSTOP_SCHOTT_Y1-(-8.0),\n    'upper_schott_top_z_mm': MOUNT_BACKSTOP_SCHOTT_TOP_Z,\n    'gap_below_box_support_mm': round(BOX_SUPPORT_Z-MOUNT_BACKSTOP_SCHOTT_TOP_Z, 3),\n    'i_beam_root_overlap_each_mm3': [round(v, 3) for v in MOUNT_BACKSTOP_ROOT_OVERLAP_MM3],\n    'rack_pin_bores_recut_after_fusion': True,\n    'primary_load_path': 'two_rack_clamps_only',\n}\nif abs(V['mounting_backstop']['panel_width_mm']-100.0) > 0.01:\n    failures.append('Mounting backstop lower panel is not the requested 100 mm width')\nif abs(V['mounting_backstop']['panel_height_mm']-50.0) > 0.01:\n    failures.append('Mounting backstop is not the requested 50 mm hanging panel')\nif V['mounting_backstop']['panel_x_clearance_to_each_upper_clamp_mm'] < 20.0:\n    failures.append('Mounting backstop leaves less than 20 mm clamp-side service clearance')\nif V['mounting_backstop']['root_block_y_depth_mm'] < 10.0:\n    failures.append('Mounting backstop root block is too shallow for a robust BASE connection')\nif V['mounting_backstop']['upper_schott_width_mm'] < 210.0:\n    failures.append('Mounting backstop upper schott does not span both I-beam roots')\nif V['mounting_backstop']['full_width_start_z_mm'] < 18.0:\n    failures.append('Mounting backstop widens into clamp sweep too low')\nif V['mounting_backstop']['upper_schott_root_insertion_y_mm'] < 3.0:\n    failures.append('Mounting backstop has insufficient physical insertion into I-beam roots')\nif not (0.5 <= V['mounting_backstop']['gap_below_box_support_mm'] <= 1.5):\n    failures.append('Mounting backstop top must stay 0.5..1.5 mm below box support')\nif any(v < 500.0 for v in V['mounting_backstop']['i_beam_root_overlap_each_mm3']):\n    failures.append('Mounting backstop does not substantially overlap both I-beam roots')\nif not V['mounting_backstop']['rack_pin_bores_recut_after_fusion']:\n    failures.append('Mounting backstop does not preserve rack-pin service bores')\n\n'''
s = s.replace(validation_anchor, validation + validation_anchor, 1)

# Keep generated notes aligned with the delivered geometry.
s = s.replace(
    "f.write('No diagonal-stay V saddle. Anti-rotation is integrated into both rack-clamp roots.\\n')",
    "f.write('Each BASE has a non-clamping 100 mm diagonal-stay mounting backstop, tapered upward into both I-beam roots; primary load remains on the two rack clamps.\\n')",
    1,
)
s = s.replace(
    "f.write('No diagonal-stay clamp: each BASE has a 50 mm integral flat mounting backstop between its two rack clamps; primary load remains on the rack clamps.\\n')",
    "f.write('Each BASE has a non-clamping 100 mm diagonal-stay mounting backstop, tapered upward into both I-beam roots; primary load remains on the two rack clamps.\\n')",
    1,
)

if s == orig:
    raise SystemExit('Mounting-backstop fixup made no changes')

p.write_text(s, encoding='utf-8')
print('Applied v50 mounting backstop: 100 x 50 x 4 mm stop with tapered full-width beam-root schott')
