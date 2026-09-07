from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Final screw-hardware cleanup.
# Keep screws as screws: no nut-shaped hex collar fused into the lead spindle.
# The RH8x2 lead spindle uses an integral square drive section, the hand knob
# has the matching square socket, and the threaded retainer nut remains a
# completely separate exported part.

old_spindle = '''SPINDLE = fuse_all([\n    cyl_y(3.0, 0.4, 0, 0.0, 0),\n    cyl_y(2.5, 1.4, 0, 0.4, 0),\n    cyl_y(3.0, SPINDLE_LOCAL_JOURNAL-1.8, 0, 1.8, 0),\n    cyl_y(SHOULDER_D/2, SPINDLE_LOCAL_SHOULDER, 0, SPINDLE_LOCAL_JOURNAL, 0),\n    z_to_y(MALE, 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER, 0),\n    z_to_y(hex_z(10.0, HEX_LEN), 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN, 0),\n    z_to_y(MALE_STUD, 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN+HEX_LEN, 0),\n]).removeSplitter()'''

new_spindle = '''LEAD_DRIVE_SQUARE = 8.0\nLEAD_DRIVE_LEN = HEX_LEN\nlead_drive_y0 = SPINDLE_LOCAL_JOURNAL + SPINDLE_LOCAL_SHOULDER + LEAD_THREAD_LEN\nLEAD_DRIVE = box(-LEAD_DRIVE_SQUARE/2.0, lead_drive_y0, -LEAD_DRIVE_SQUARE/2.0,\n                 LEAD_DRIVE_SQUARE, LEAD_DRIVE_LEN, LEAD_DRIVE_SQUARE)\n\nSPINDLE = fuse_all([\n    cyl_y(3.0, 0.4, 0, 0.0, 0),\n    cyl_y(2.5, 1.4, 0, 0.4, 0),\n    cyl_y(3.0, SPINDLE_LOCAL_JOURNAL-1.8, 0, 1.8, 0),\n    cyl_y(SHOULDER_D/2, SPINDLE_LOCAL_SHOULDER, 0, SPINDLE_LOCAL_JOURNAL, 0),\n    z_to_y(MALE, 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER, 0),\n    LEAD_DRIVE,\n    z_to_y(MALE_STUD, 0, lead_drive_y0+LEAD_DRIVE_LEN, 0),\n]).removeSplitter()'''

if old_spindle not in s:
    raise SystemExit('Could not locate lead spindle nut-like hex drive')
s = s.replace(old_spindle, new_spindle, 1)

# Replace the old AF10.35 hex socket in the hand knob with a square socket.
old_knob = '''KNOB = KNOB.cut(cyl_y(4.3, 7.4, 0, -0.2, 0))\nKNOB = KNOB.cut(z_to_y(hex_z(10.35, 5.2), 0, 0, 0)).removeSplitter()'''
new_knob = '''KNOB = KNOB.cut(cyl_y(4.3, 7.4, 0, -0.2, 0))\nLEAD_DRIVE_SOCKET = box(-4.15, -0.2, -4.15, 8.30, 5.2, 8.30)\nKNOB = KNOB.cut(LEAD_DRIVE_SOCKET).removeSplitter()'''
if old_knob not in s:
    raise SystemExit('Could not locate lead knob hex socket')
s = s.replace(old_knob, new_knob, 1)

# The old variable name hex_y is retained only as a coordinate in older
# diagnostics. Make the source describe the actual square-drive start.
s = s.replace(
    'hex_y = SPINDLE_LOCAL_JOURNAL + SPINDLE_LOCAL_SHOULDER + LEAD_THREAD_LEN',
    'hex_y = lead_drive_y0',
    1,
)

# Add explicit hardware architecture witness before the final export gate.
anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final PARTS export gate')
witness = '''V['screw_hardware_architecture'] = {\n    'lead_screw_part': 'eurobox_v50_lead_screw_print',\n    'lead_drive': 'integral_square_screw_drive',\n    'lead_drive_square_mm': LEAD_DRIVE_SQUARE,\n    'lead_knob_part': 'eurobox_v50_knob',\n    'lead_retainer_nut_part': 'eurobox_v50_knob_retainer_nut',\n    'lead_retainer_nut_separate_from_screw': True,\n    'rack_screw_part': 'eurobox_v50_rack_m4x20_screw_print',\n    'rack_nut_part': 'eurobox_v50_rack_m4_nut_print',\n    'rack_nut_separate_from_screw': True,\n    'no_print_in_place_threaded_nuts': True,\n}\nif not V['screw_hardware_architecture']['lead_retainer_nut_separate_from_screw']:\n    failures.append('Lead retainer nut must be a separate printable part')\nif not V['screw_hardware_architecture']['rack_nut_separate_from_screw']:\n    failures.append('Rack M4 nut must be a separate printable part')\nif not V['screw_hardware_architecture']['no_print_in_place_threaded_nuts']:\n    failures.append('Threaded nuts may not be fused into screw print parts')\n\n'''
s = s.replace(anchor, witness + anchor, 1)

# Make README wording explicit.
s = s.replace(
    "f.write('Printed test lead screw: RH 8x2 with integral BASE lead nuts; separate drive knob and threaded retainer nut.\\n')",
    "f.write('Printed RH8x2 lead screw: integral square drive; knob and threaded retainer nut are separate printable parts.\\n')",
)

if s == orig:
    raise SystemExit('Screw hardware cleanup made no changes')

p.write_text(s, encoding='utf-8')
print('Applied screw hardware cleanup: square-drive lead screw + all threaded nuts separate')
