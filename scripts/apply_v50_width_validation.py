from pathlib import Path

# Align the independent STEP mechanism validator with the final inboard clamp.
vp = Path('scripts/validate_box_clamp.py')
vs = vp.read_text(encoding='utf-8')
vorig = vs

if 'NUT_Y0 = 260.465' not in vs:
    raise SystemExit('Could not locate resolved box-clamp nut datum')
vs = vs.replace(
    'NUT_Y0 = 260.465',
    'PLATE_SPINDLE_Y = BOX_RIM_INNER_Y\nNUT_Y0 = PLATE_SPINDLE_Y - 15.8', 1)

old = '''    closed_hook_inner_y = BOX_EDGE_Y - UNDERHOOK
    report['measurements']['closed_underhook_inner_y_mm'] = round(closed_hook_inner_y, 3)
    report['measurements']['closed_underhook_capture_depth_mm'] = round(BOX_EDGE_Y - closed_hook_inner_y, 3)
    report['checks']['closed_hook_captures_box_edge'] = closed_hook_inner_y < BOX_EDGE_Y
    report['checks']['closed_plate_does_not_interpenetrate_rim'] = common_volume(plate, rim, 'closed_plate_vs_rim') < 1e-4

    open_hook_inner_y = closed_hook_inner_y + PLATE_OPEN
    open_clearance = open_hook_inner_y - BOX_EDGE_Y
    report['measurements']['open_underhook_inner_y_mm'] = round(open_hook_inner_y, 3)
    report['measurements']['open_box_edge_clearance_mm'] = round(open_clearance, 3)
    report['checks']['open_clearance_at_least_1mm'] = open_clearance >= 1.0
    pl_open = plate.copy()
    pl_open.translate(App.Vector(0, PLATE_OPEN, 0))
    report['checks']['plate_open_position_clear_of_base'] = common_volume(pl_open, base, 'open_plate_vs_base') < 1e-4
    report['checks']['plate_open_position_clear_of_rim'] = common_volume(pl_open, rim, 'open_plate_vs_rim') < 1e-4

    pl_clamp = plate.copy()
    pl_clamp.translate(App.Vector(0, -CLAMP_PRELOAD, 0))'''
new = '''    closed_hook_outer_y = BOX_RIM_INNER_Y + UNDERHOOK
    report['measurements']['closed_underhook_outer_y_mm'] = round(closed_hook_outer_y, 3)
    report['measurements']['closed_underhook_capture_depth_mm'] = round(closed_hook_outer_y-BOX_RIM_INNER_Y, 3)
    report['checks']['closed_hook_captures_inner_rim_edge'] = closed_hook_outer_y > BOX_RIM_INNER_Y
    report['checks']['closed_plate_does_not_interpenetrate_rim'] = common_volume(plate, rim, 'closed_plate_vs_rim') < 1e-4
    report['checks']['closed_plate_stays_inside_box_outer_edge'] = plate.BoundBox.YMax <= BOX_EDGE_Y + 0.02
    report['checks']['base_stays_inside_box_outer_edge'] = base.BoundBox.YMax <= BOX_EDGE_Y + 0.02

    open_hook_outer_y = closed_hook_outer_y - PLATE_OPEN
    open_clearance = BOX_RIM_INNER_Y - open_hook_outer_y
    report['measurements']['open_underhook_outer_y_mm'] = round(open_hook_outer_y, 3)
    report['measurements']['open_inner_rim_clearance_mm'] = round(open_clearance, 3)
    report['checks']['open_clearance_at_least_1mm'] = open_clearance >= 1.0
    pl_open = plate.copy()
    pl_open.translate(App.Vector(0, -PLATE_OPEN, 0))
    report['checks']['plate_open_position_clear_of_base'] = common_volume(pl_open, base, 'open_plate_vs_base') < 1e-4
    report['checks']['plate_open_position_clear_of_rim'] = common_volume(pl_open, rim, 'open_plate_vs_rim') < 1e-4

    pl_clamp = plate.copy()
    pl_clamp.translate(App.Vector(0, +CLAMP_PRELOAD, 0))'''
if old not in vs:
    raise SystemExit('Could not replace box-clamp rim semantics')
vs = vs.replace(old, new, 1)

vs = vs.replace(
    'q.translate(App.Vector(SPINDLE_X, BOX_EDGE_Y + travel_mm, SPINDLE_Z))',
    'q.translate(App.Vector(SPINDLE_X, PLATE_SPINDLE_Y - travel_mm, SPINDLE_Z))', 1)
vs = vs.replace('NUT_Y0+LEAD_NUT_PIN_Y', 'NUT_Y0-LEAD_NUT_PIN_Y')
vs = vs.replace('rot = -360.0 * travel / THREAD_PITCH',
                'rot = +360.0 * travel / THREAD_PITCH', 1)
vs = vs.replace('q_wrong = placed_spindle(0.5, 90.0)',
                'q_wrong = placed_spindle(0.5, -90.0)', 1)
vs = vs.replace(
    '''    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG)
    cap.translate(App.Vector(0, CAP_NUT_Y0, 0))''',
    '''    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -CAP_NUT_PHASE_DEG)
    cap.translate(App.Vector(0, -CAP_NUT_Y0, 0))''', 1)
vs = vs.replace(
    '''    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG+180.0)
    cap_wrong.translate(App.Vector(0, CAP_NUT_Y0, 0))''',
    '''    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -CAP_NUT_PHASE_DEG-180.0)
    cap_wrong.translate(App.Vector(0, -CAP_NUT_Y0, 0))''', 1)
vs = vs.replace(
    "report['measurements']['knob_retainer_nut_phase_deg'] = round(CAP_NUT_PHASE_DEG, 3)",
    "report['measurements']['knob_retainer_nut_phase_deg'] = round(-CAP_NUT_PHASE_DEG, 3)", 1)

if vs == vorig:
    raise SystemExit('Width validation made no box-clamp changes')
vp.write_text(vs, encoding='utf-8')
print('Updated box-clamp validator for inboard clamp')

# Add the actual source-solid width result to the independent global-layout gate.
ap = Path('scripts/validate_assembly_layout.py')
a = ap.read_text(encoding='utf-8')
aorig = a
needle = '''checks["assembled_box_width_is_600"] = abs(report["box_width_from_edges_mm"] - 600.0) < 1e-9
'''
extra = needle + '''width = source.get("system_width_estimate_mm", {})
report["holder_width_from_source_mm"] = width.get("holder_total_width_mm")
report["effective_system_width_from_source_mm"] = width.get("effective_system_width_mm")
checks["holder_source_width_gate_present"] = width.get("within_600mm_box_envelope") is True
checks["holder_itself_is_not_wider_than_box"] = (
    isinstance(width.get("holder_total_width_mm"), (int, float)) and
    width["holder_total_width_mm"] <= 600.02
)
checks["effective_system_width_is_600"] = (
    isinstance(width.get("effective_system_width_mm"), (int, float)) and
    width["effective_system_width_mm"] <= 600.02
)
'''
if needle not in a:
    raise SystemExit('Could not locate assembly width check')
a = a.replace(needle, extra, 1)
if a == aorig:
    raise SystemExit('Width validation made no assembly-layout changes')
ap.write_text(a, encoding='utf-8')
print('Updated assembly validator with 600 mm holder hard gate')
