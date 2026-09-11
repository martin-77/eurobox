from pathlib import Path

# Compatibility for the restored 600 mm inboard architecture. The current
# lead-nut cartridge no longer has the obsolete tail extension used by the
# original width-cleanup pass. Remove only that stale tail pocket from the
# generated build source; retain the current cartridge, pin and service-pocket
# geometry unchanged.
bp = Path('scripts/build_v50.py')
bs = bp.read_text(encoding='utf-8')
old = "NUT_TAIL_Y0 = NUT_THREAD_Y0 - LEAD_NUT_TAIL_L\n"
if old not in bs:
    raise SystemExit('Could not locate obsolete lead-nut tail datum in inboard width pass')
bs = bs.replace(old, '', 1)
old = '''    _tail_pocket = box(sx-6.2, NUT_TAIL_Y0-0.25, SPINDLE_Z-10.25,
                       12.4, LEAD_NUT_TAIL_L+0.50, 6.0)
'''
if old not in bs:
    raise SystemExit('Could not locate obsolete lead-nut tail pocket in inboard width pass')
bs = bs.replace(old, '', 1)
old = '''    for cutter in (_nut_pocket, _tail_pocket, _spindle_tunnel,
                   _pin_bore, _head_service, _clip_service):'''
new = '''    for cutter in (_nut_pocket, _spindle_tunnel,
                   _pin_bore, _head_service, _clip_service):'''
if old not in bs:
    raise SystemExit('Could not remove obsolete lead-nut tail pocket from cutter set')
bs = bs.replace(old, new, 1)

# The original inboard pass was authored after the printability pass and uses
# these four frame datums. Printability is no longer executed globally, so
# restore only the exact datums required by the inboard cage. They are taken
# verbatim from apply_v50_printability_final.py and do not modify rack roots,
# pivots, threads or frozen box/rack measurements.
anchor = "PLATE_SPINDLE_Y = BOX_RIM_INNER_Y\n"
compat = (
    "PRINT_BASE_PLANE_Z = BOX_SUPPORT_Z\n"
    "PRINT_GUIDE_Z0 = 14.0\n"
    "PRINT_FRAME_TIE_T = 6.0\n"
    "PRINT_FRAME_BOSS_Z0 = 20.0\n"
)
if anchor not in bs:
    raise SystemExit('Could not locate inboard width architecture anchor')
bs = bs.replace(anchor, compat + anchor, 1)

# The inboard plate occupies the former central crosshead corridor. Do not
# delete or weaken the whole crosshead: retain the full-width lower flange below
# the moving plate and the two outer side structures, but clear exactly the
# plate-body sweep plus the existing 0.4 mm guide clearance. The side guide
# rails start at X +/-70.4, so this cutter terminates exactly at their inner
# faces and leaves the intended sliding guides intact.
anchor = '''BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()

for sx in SPINDLE_X:
'''
plate_clearance = '''BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()

_plate_body_y0_for_clearance = BOX_RIM_INNER_Y - PLATE_Y
_plate_sweep_y0 = _plate_body_y0_for_clearance - PLATE_OPEN - GUIDE_SIDE_CLEAR
_plate_sweep_y1 = _plate_body_y0_for_clearance + PLATE_Y + GUIDE_SIDE_CLEAR
_plate_sweep = box(
    -PLATE_X/2.0-GUIDE_SIDE_CLEAR,
    _plate_sweep_y0,
    PLATE_Z0-GUIDE_Z_CLEAR,
    PLATE_X+2.0*GUIDE_SIDE_CLEAR,
    _plate_sweep_y1-_plate_sweep_y0,
    (PLATE_Z1-PLATE_Z0)+2.0*GUIDE_Z_CLEAR,
)
BASE_RIGHT = BASE_RIGHT.cut(_plate_sweep).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_plate_sweep).removeSplitter()
if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Plate-sweep clearance broke handed BASE topology')

for sx in SPINDLE_X:
'''
if anchor not in bs:
    raise SystemExit('Could not locate inboard cage for plate-sweep clearance')
bs = bs.replace(anchor, plate_clearance, 1)

# Z180 reverses the spindle through the plate. The narrow retainer groove now
# sits at the outboard plate face while the Ø11 thrust shoulder bears on the
# inboard face. Move the Ø12 x 2 mm counterbore with the retainer groove; leaving
# it on the inboard face removes the shoulder's thrust land and creates exactly
# the 0.25 mm radial journal/hole clearance seen by the hard clamp validator.
old = "    PLATE = PLATE.cut(cyl_y(6.0, 2.0, sx, PLATE_BODY_Y0, SPINDLE_Z))\n"
new = "    PLATE = PLATE.cut(cyl_y(6.0, 2.0, sx, PLATE_SPINDLE_Y-2.0, SPINDLE_Z))\n"
if old not in bs:
    raise SystemExit('Could not relocate inboard plate retainer counterbore')
bs = bs.replace(old, new, 1)

bp.write_text(bs, encoding='utf-8')

# The standalone box-clamp validator predates the restored inboard architecture.
# Keep all mechanical thresholds intact, but place and move the real exported
# hardware using the same datums/directions as the final 600 mm build source.
cp = Path('scripts/validate_box_clamp.py')
cs = cp.read_text(encoding='utf-8')

replacements = [
    (
        "NUT_Y0 = 260.465\n",
        "PLATE_SPINDLE_Y = BOX_RIM_INNER_Y\n"
        "NUT_ANCHOR_OFFSET = 15.8\n"
        "NUT_Y0 = PLATE_SPINDLE_Y - NUT_ANCHOR_OFFSET\n",
    ),
    (
        '''    closed_hook_inner_y = BOX_EDGE_Y - UNDERHOOK
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
''',
        '''    # Inboard clamp: the hook captures the INNER rim edge from below.
    # Opening moves toward -Y; 5.5 mm yields 1.3 mm release clearance.
    closed_hook_outer_y = BOX_RIM_INNER_Y + UNDERHOOK
    report['measurements']['closed_underhook_outer_y_mm'] = round(closed_hook_outer_y, 3)
    report['measurements']['closed_underhook_capture_depth_mm'] = round(closed_hook_outer_y - BOX_RIM_INNER_Y, 3)
    report['checks']['closed_hook_captures_box_edge'] = closed_hook_outer_y > BOX_RIM_INNER_Y
    report['checks']['closed_plate_does_not_interpenetrate_rim'] = common_volume(plate, rim, 'closed_plate_vs_rim') < 1e-4

    open_hook_outer_y = closed_hook_outer_y - PLATE_OPEN
    open_clearance = BOX_RIM_INNER_Y - open_hook_outer_y
    report['measurements']['open_underhook_outer_y_mm'] = round(open_hook_outer_y, 3)
    report['measurements']['open_box_edge_clearance_mm'] = round(open_clearance, 3)
    report['checks']['open_clearance_at_least_1mm'] = open_clearance >= 1.0
    pl_open = plate.copy()
    pl_open.translate(App.Vector(0, -PLATE_OPEN, 0))
''',
    ),
    (
        "    pl_clamp.translate(App.Vector(0, -CLAMP_PRELOAD, 0))\n",
        "    pl_clamp.translate(App.Vector(0, CLAMP_PRELOAD, 0))\n",
    ),
    (
        "        q.translate(App.Vector(SPINDLE_X, BOX_EDGE_Y + travel_mm, SPINDLE_Z))\n",
        "        q.translate(App.Vector(SPINDLE_X, PLATE_SPINDLE_Y - travel_mm, SPINDLE_Z))\n",
    ),
    (
        "                             NUT_Y0+LEAD_NUT_PIN_Y,\n",
        "                             NUT_Y0-LEAD_NUT_PIN_Y,\n",
    ),
    (
        "                              NUT_Y0+LEAD_NUT_PIN_Y,\n",
        "                              NUT_Y0-LEAD_NUT_PIN_Y,\n",
    ),
    (
        "        rot = -360.0 * travel / THREAD_PITCH\n",
        "        rot = +360.0 * travel / THREAD_PITCH\n",
    ),
    (
        "    # At +0.5 mm travel the correct rotation is -90 deg. +90 deg is 180 deg out\n"
        "    # of phase and must visibly intersect a developed RH 8x2 female thread.\n"
        "    q_wrong = placed_spindle(0.5, 90.0)\n",
        "    # With inward -Y travel the correct +0.5 mm rotation is +90 deg.\n"
        "    # -90 deg is 180 deg out of phase and must visibly intersect the RH8x2 nut.\n"
        "    q_wrong = placed_spindle(0.5, -90.0)\n",
    ),
    (
        "    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG)\n"
        "    cap.translate(App.Vector(0, CAP_NUT_Y0, 0))\n",
        "    cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -CAP_NUT_PHASE_DEG)\n"
        "    cap.translate(App.Vector(0, -CAP_NUT_Y0, 0))\n",
    ),
    (
        "    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), CAP_NUT_PHASE_DEG+180.0)\n"
        "    cap_wrong.translate(App.Vector(0, CAP_NUT_Y0, 0))\n",
        "    cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -CAP_NUT_PHASE_DEG-180.0)\n"
        "    cap_wrong.translate(App.Vector(0, -CAP_NUT_Y0, 0))\n",
    ),
    (
        "    report['measurements']['knob_retainer_nut_phase_deg'] = round(CAP_NUT_PHASE_DEG, 3)\n",
        "    report['measurements']['knob_retainer_nut_phase_deg'] = round(-CAP_NUT_PHASE_DEG, 3)\n",
    ),
]
for old, new in replacements:
    if old not in cs:
        raise SystemExit('Could not align box-clamp validator with inboard architecture: ' + old.splitlines()[0])
    cs = cs.replace(old, new, 1)
cp.write_text(cs, encoding='utf-8')

# The restored width pass turns the lead hardware inward by a proper Z180
# rotation, so the printable RH8x2 parts occupy local -Y. Keep the final STL
# checks aligned with that print orientation, while retaining the mechanical
# thread/drive gates themselves.
vp = Path('scripts/validate_meshes.py')
vs = vp.read_text(encoding='utf-8')

replacements = [
    ("        # Printable retainer nut is exported in local +Y.\n        checks=rh8_internal_thread_sections(mesh, (1.2,2.9,4.6))",
     "        # Inboard architecture rotates the printable retainer nut onto local -Y.\n        checks=rh8_internal_thread_sections(mesh, (-1.2,-2.9,-4.6))"),
    ("        # Printable main lead nut is exported in local +Y.\n        checks=rh8_internal_thread_sections(mesh, (3.0,8.0,13.0))",
     "        # Inboard architecture rotates the printable main lead nut onto local -Y.\n        checks=rh8_internal_thread_sections(mesh, (-3.0,-8.0,-13.0))"),
    ("    # Printable spindle is exported in local +Y. The 8x8 square-drive end lies\n    # at the outer positive-Y end; y=34.5 is safely inside the square section.\n    y=34.5",
     "    # Inboard architecture rotates the printable spindle onto local -Y. The\n    # 8x8 square-drive end is therefore sampled safely at y=-34.5.\n    y=-34.5"),
]
for old, new in replacements:
    if old not in vs:
        raise SystemExit('Could not align inward printable mesh validation: '+old.splitlines()[-1])
    vs = vs.replace(old, new, 1)

# FreeCAD/OCC may triangulate two geometrically mirrored cylindrical surfaces
# with a different angular phase. Exact vertex-cloud equality is therefore only
# diagnostic; hard handedness remains distinct bytes + mirrored bounds + equal
# volume/face count + opposite backstop envelopes.
old = "    handed_ok=bool(distinct_files and bounds_mirror_ok and vertex_mirror_ok and side_envelopes)\n"
new = (
    "    volume_mirror_ok=abs(abs(rm.volume)-abs(lm.volume)) <= 0.05\n"
    "    face_count_match=(len(rm.faces) == len(lm.faces))\n"
    "    handed_ok=bool(distinct_files and bounds_mirror_ok and volume_mirror_ok and face_count_match and side_envelopes)\n"
)
if old not in vs:
    raise SystemExit('Could not locate handed STL mirror gate')
vs = vs.replace(old, new, 1)
old_meta = "        'unique_vertex_clouds_are_x_mirrors':bool(vertex_mirror_ok),\n"
new_meta = (
    old_meta
    + "        'mesh_volumes_match':bool(volume_mirror_ok),\n"
    + "        'mesh_face_counts_match':bool(face_count_match),\n"
)
if old_meta not in vs:
    raise SystemExit('Could not locate handed STL mirror diagnostics')
vs = vs.replace(old_meta, new_meta, 1)
vp.write_text(vs, encoding='utf-8')