from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

parts_anchor = 'PARTS = {\n'
if parts_anchor not in s:
    raise SystemExit('Could not locate final PARTS anchor for width cleanup')

inboard = r'''# ---------------------------------------------------------------------------
# Absolute final transverse-envelope architecture
# ---------------------------------------------------------------------------
PLATE_SPINDLE_Y = BOX_RIM_INNER_Y
NUT_ANCHOR_OFFSET = 15.8
NUT_Y0 = PLATE_SPINDLE_Y - NUT_ANCHOR_OFFSET
NUT_THREAD_Y0 = NUT_Y0 - NUT_THREAD_LEN
NUT_TAIL_Y0 = NUT_THREAD_Y0 - LEAD_NUT_TAIL_L
CAGE_Y0 = PLATE_SPINDLE_Y - 37.535
CAGE_Y1 = PLATE_SPINDLE_Y - 13.600
WIDTH_RIM_CLEAR = 0.20

# Remove the obsolete outboard plate guide/nut cage and under-rim tail from the
# already validated handed bases. Keep the crosshead through the rim-inner
# clearance plane, then rebuild the screw cage inward from there.
_OUTBOARD_TRIM_Y = BOX_RIM_INNER_Y - WIDTH_RIM_CLEAR
_outboard_trim = box(-260.0, _OUTBOARD_TRIM_Y, -80.0, 520.0, 180.0, 160.0)
BASE_RIGHT = BASE_RIGHT.cut(_outboard_trim).removeSplitter()
BASE_LEFT = BASE_LEFT.cut(_outboard_trim).removeSplitter()

PRINT_GUIDE_Y0 = CAGE_Y1 - 0.40
PRINT_GUIDE_Y1 = _OUTBOARD_TRIM_Y
_inboard_parts = [
    box(-78.0, PRINT_GUIDE_Y0, PRINT_GUIDE_Z0, 7.6,
        PRINT_GUIDE_Y1-PRINT_GUIDE_Y0,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    box(70.4, PRINT_GUIDE_Y0, PRINT_GUIDE_Z0, 7.6,
        PRINT_GUIDE_Y1-PRINT_GUIDE_Y0,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    box(-78.0, CAGE_Y0-0.1, PRINT_BASE_PLANE_Z-PRINT_FRAME_TIE_T,
        156.0, CAGE_Y1-CAGE_Y0+0.2, PRINT_FRAME_TIE_T),
]
for sx in SPINDLE_X:
    _inboard_parts.append(box(sx-11.0, CAGE_Y0, PRINT_FRAME_BOSS_Z0, 22.0,
                              CAGE_Y1-CAGE_Y0,
                              PRINT_BASE_PLANE_Z-PRINT_FRAME_BOSS_Z0))
INBOARD_CAGE = fuse_all(_inboard_parts)
BASE_RIGHT = BASE_RIGHT.fuse(INBOARD_CAGE).removeSplitter()
BASE_LEFT = BASE_LEFT.fuse(INBOARD_CAGE).removeSplitter()

for sx in SPINDLE_X:
    _nut_pocket = box(sx-8.35, NUT_THREAD_Y0-0.35, 23.65,
                      16.7, NUT_THREAD_LEN+0.70, 21.0)
    _tail_pocket = box(sx-6.2, NUT_TAIL_Y0-0.25, SPINDLE_Z-10.25,
                       12.4, LEAD_NUT_TAIL_L+0.50, 6.0)
    _tunnel_y0 = CAGE_Y0 - 0.50
    _tunnel_y1 = PLATE_SPINDLE_Y - PLATE_Y + 0.50
    _spindle_tunnel = cyl_y(5.90, _tunnel_y1-_tunnel_y0,
                            sx, _tunnel_y0, SPINDLE_Z)
    _pin_y = NUT_Y0 - LEAD_NUT_PIN_Y
    _pin_z = SPINDLE_Z + LEAD_NUT_PIN_Z
    _pin_bore = cyl_x(LEAD_NUT_PIN_HOLE_D/2.0, 24.0, sx-12.0, _pin_y, _pin_z)
    _head_service = cyl_x(3.55, 3.0, sx-14.0, _pin_y, _pin_z)
    _clip_service = cyl_x(4.10, 4.0, sx+11.0, _pin_y, _pin_z)
    for cutter in (_nut_pocket, _tail_pocket, _spindle_tunnel,
                   _pin_bore, _head_service, _clip_service):
        BASE_RIGHT = BASE_RIGHT.cut(cutter)
        BASE_LEFT = BASE_LEFT.cut(cutter)

for xc in CLAMP_X:
    _pivot = cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z)
    BASE_RIGHT = BASE_RIGHT.cut(_pivot)
    BASE_LEFT = BASE_LEFT.cut(_pivot)
BASE_RIGHT = BASE_RIGHT.removeSplitter()
BASE_LEFT = BASE_LEFT.removeSplitter()
BASE = BASE_RIGHT
if (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or
        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):
    raise RuntimeError('Inboard width cleanup broke handed BASE topology')

# Closed plate body is entirely inboard of the rim. Only the lower hook reaches
# 4.2 mm outward under the inner rim edge. Positive opening travel moves -Y.
PLATE_BODY_Y0 = BOX_RIM_INNER_Y - PLATE_Y
PLATE_HOOK_Y0 = BOX_RIM_INNER_Y - WIDTH_RIM_CLEAR
PLATE_HOOK_Y1 = BOX_RIM_INNER_Y + UNDERHOOK
PLATE = box(-PLATE_X/2, PLATE_BODY_Y0, PLATE_Z0,
            PLATE_X, PLATE_Y, PLATE_Z1-PLATE_Z0)
PLATE = PLATE.fuse(box(-PLATE_X/2, PLATE_HOOK_Y0,
                       RIM_BOTTOM_Z-UNDERHOOK_T, PLATE_X,
                       PLATE_HOOK_Y1-PLATE_HOOK_Y0, UNDERHOOK_T))
for sx in SPINDLE_X:
    PLATE = PLATE.cut(cyl_y(PLATE_HOLE_D/2, PLATE_Y+1.0,
                            sx, PLATE_BODY_Y0-0.5, SPINDLE_Z))
    PLATE = PLATE.cut(cyl_y(6.0, 2.0, sx, PLATE_BODY_Y0, SPINDLE_Z))
PLATE = PLATE.removeSplitter()

# Proper Z180 rotations reverse local Y without reflecting the solids, so RH8x2
# chirality, spindle Z=31 and every frozen X datum remain unchanged.
for _shape in (LEAD_NUT, SPINDLE, KNOB, CAP_NUT):
    _shape.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180.0)
LEAD_NUT = LEAD_NUT.removeSplitter()
SPINDLE = SPINDLE.removeSplitter()
KNOB = KNOB.removeSplitter()
CAP_NUT = CAP_NUT.removeSplitter()

'''
s = s.replace(parts_anchor, inboard + parts_anchor, 1)
s = s.replace("    'eurobox_v50_rack_stay_support_universal': STAY_SUPPORT,\n", '')

old = '''V['plate_motion'] = []
for d in [0, 1, 2, 3, 4, 4.5, 5.0, 5.5]:
    pl = PLATE.copy(); pl.translate(App.Vector(0,d,0))
    V['plate_motion'].append({
        'open_mm': d,
        'base_common_mm3': round(BASE.common(pl).Volume, 6),
        'rim_common_mm3': round(RIM.common(pl).Volume, 6),
        'underhook_inner_y_mm': round(BOX_EDGE_Y-UNDERHOOK+d, 3),
    })'''
new = '''V['plate_motion'] = []
for d in [0, 1, 2, 3, 4, 4.5, 5.0, 5.5]:
    pl = PLATE.copy(); pl.translate(App.Vector(0,-d,0))
    V['plate_motion'].append({
        'open_mm': d,
        'base_common_mm3': round(BASE.common(pl).Volume, 6),
        'rim_common_mm3': round(RIM.common(pl).Volume, 6),
        'underhook_outer_y_mm': round(PLATE_HOOK_Y1-d, 3),
        'inner_rim_release_clearance_mm': round(
            BOX_RIM_INNER_Y-(PLATE_HOOK_Y1-d), 3),
    })'''
if old not in s:
    raise SystemExit('Could not replace final plate-motion validation')
s = s.replace(old, new, 1)
s = s.replace(
    'probe = cyl_y(PLATE_HOLE_D/2-0.05, PLATE_Y+1.0, sx, BOX_EDGE_Y-0.5, SPINDLE_Z)',
    'probe = cyl_y(PLATE_HOLE_D/2-0.05, PLATE_Y+1.0, sx, PLATE_BODY_Y0-0.5, SPINDLE_Z)', 1)

old = '''    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -360.0*d/THREAD_PITCH)
    q.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+d, SPINDLE_Z))'''
new = '''    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +360.0*d/THREAD_PITCH)
    q.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y-d, SPINDLE_Z))'''
if old not in s:
    raise SystemExit('Could not replace lead-screw motion direction')
s = s.replace(old, new, 1)
s = s.replace("'rotation_deg': -360.0*d/THREAD_PITCH,",
              "'rotation_deg': +360.0*d/THREAD_PITCH,", 1)
s = s.replace(
    'axial_wrong.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y + THREAD_PITCH/2.0, SPINDLE_Z))',
    'axial_wrong.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y - THREAD_PITCH/2.0, SPINDLE_Z))', 1)
s = s.replace(
    '''wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +90.0)
wrong.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+0.5, SPINDLE_Z))''',
    '''wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -90.0)
wrong.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y-0.5, SPINDLE_Z))''', 1)
s = s.replace(
    'sp0 = SPINDLE.copy(); sp0.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y, SPINDLE_Z))',
    'sp0 = SPINDLE.copy(); sp0.translate(App.Vector(SPINDLE_X[0], PLATE_SPINDLE_Y, SPINDLE_Z))', 1)

s = s.replace('kb = KNOB.copy(); kb.translate(App.Vector(0, hex_y, 0))',
              'kb = KNOB.copy(); kb.translate(App.Vector(0, -hex_y, 0))', 1)
s = s.replace(
    '''cn.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg)
cn.translate(App.Vector(0, cap_y, 0))''',
    '''cn.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -cap_phase_deg)
cn.translate(App.Vector(0, -cap_y, 0))''', 1)
s = s.replace(
    '''cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg+180.0)
cap_wrong.translate(App.Vector(0, cap_y, 0))''',
    '''cap_wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -cap_phase_deg-180.0)
cap_wrong.translate(App.Vector(0, -cap_y, 0))''', 1)
s = s.replace("'correct_phase_deg': round(cap_phase_deg, 3),",
              "'correct_phase_deg': round(-cap_phase_deg, 3),", 1)

pat = re.compile(
    r"spindle_outer_local_y = BOX_EDGE_Y \+ \(SPINDLE_LOCAL_JOURNAL \+ SPINDLE_LOCAL_SHOULDER \+ LEAD_THREAD_LEN \+ HEX_LEN \+ OUTER_STUD_LEN\)\n"
    r"V\['system_width_estimate_mm'\] = \{\n.*?\n\}\n", re.S)
width = r'''def _placed_box_hardware_outboard_y(travel_mm):
    rot = +360.0*travel_mm/THREAD_PITCH
    pl = PLATE.copy(); pl.translate(App.Vector(0,-travel_mm,0))
    sp = SPINDLE.copy(); sp.rotate(App.Vector(0,0,0), App.Vector(0,1,0), rot)
    sp.translate(App.Vector(0, PLATE_SPINDLE_Y-travel_mm, SPINDLE_Z))
    k = KNOB.copy(); k.rotate(App.Vector(0,0,0), App.Vector(0,1,0), rot)
    k.translate(App.Vector(0, PLATE_SPINDLE_Y-travel_mm-hex_y, SPINDLE_Z))
    cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -cap_phase_deg+rot)
    cap.translate(App.Vector(0, PLATE_SPINDLE_Y-travel_mm-cap_y, SPINDLE_Z))
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(0,NUT_Y0,SPINDLE_Z))
    pin = NUT_PIN.copy(); pin.translate(App.Vector(
        0,NUT_Y0-LEAD_NUT_PIN_Y,SPINDLE_Z+LEAD_NUT_PIN_Z))
    clip = NUT_PIN_CLIP.copy(); clip.rotate(
        App.Vector(0,0,0), App.Vector(0,1,0), 90.0)
    clip.translate(App.Vector(
        NUT_PIN_CLIP_X,NUT_Y0-LEAD_NUT_PIN_Y,SPINDLE_Z+LEAD_NUT_PIN_Z))
    return max(sh.BoundBox.YMax for sh in
               (BASE_RIGHT, pl, sp, k, cap, nut, pin, clip))

_width_states = {
    'preload_-0_5': _placed_box_hardware_outboard_y(-0.5),
    'closed_0': _placed_box_hardware_outboard_y(0.0),
    'open_5_5': _placed_box_hardware_outboard_y(5.5),
}
_max_holder_local_y = max(_width_states.values())
_holder_global_half_width = RACK_CTC/2.0 + _max_holder_local_y
V['system_width_estimate_mm'] = {
    'box_width_mm': BOX_W,
    'box_half_width_mm': BOX_W/2.0,
    'state_outboard_local_y_mm': {k: round(v,3) for k,v in _width_states.items()},
    'holder_global_half_width_mm': round(_holder_global_half_width,3),
    'holder_total_width_mm': round(2.0*_holder_global_half_width,3),
    'effective_system_width_mm': round(max(BOX_W,2.0*_holder_global_half_width),3),
    'hard_limit_mm': BOX_W,
    'within_600mm_box_envelope': _holder_global_half_width <= BOX_W/2.0 + 0.02,
}
'''
s, n = pat.subn(width, s, count=1)
if n != 1:
    raise SystemExit('Could not replace obsolete system-width estimate')
s = s.replace('failures = []\n',
              "failures = []\nif not V['system_width_estimate_mm']['within_600mm_box_envelope']:\n    failures.append('Holder exceeds the hard 600 mm Eurobox width envelope')\n", 1)

pat = re.compile(r"V\['anti_rotation'\] = \{\n    'mode': 'separate_diagonal_stay_V_support',.*?\n\}\n", re.S)
s, n = pat.subn("""V['anti_rotation'] = {
    'mode': 'integrated_handed_rear_mounting_backstop',
    'separate_stay_support': False,
    'primary_load_path': False,
    'purpose': 'assembly anti-flop / rear stay contact aid only',
}
""", s, count=1)
if n != 1:
    raise SystemExit('Could not replace obsolete separate stay-support metadata')

s = s.replace('RY+BOX_EDGE_Y, SPINDLE_Z', 'RY+PLATE_SPINDLE_Y, SPINDLE_Z')
s = s.replace('RY+BOX_EDGE_Y+hex_y, SPINDLE_Z', 'RY+PLATE_SPINDLE_Y-hex_y, SPINDLE_Z')
s = s.replace('RY+NUT_Y0+LEAD_NUT_PIN_Y', 'RY+NUT_Y0-LEAD_NUT_PIN_Y')
s = s.replace(
    '''cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg)
    cap.translate(App.Vector(sx, RY+BOX_EDGE_Y+cap_y, SPINDLE_Z))''',
    '''cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -cap_phase_deg)
    cap.translate(App.Vector(sx, RY+PLATE_SPINDLE_Y-cap_y, SPINDLE_Z))''', 1)
s = s.replace('sx,BOX_EDGE_Y,SPINDLE_Z', 'sx,PLATE_SPINDLE_Y,SPINDLE_Z')
s = s.replace('NUT_Y0+LEAD_NUT_PIN_Y', 'NUT_Y0-LEAD_NUT_PIN_Y')
s = s.replace(
    '''cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), cap_phase_deg)
    cap.translate(App.Vector(sx, BOX_EDGE_Y+cap_y, SPINDLE_Z))''',
    '''cap = CAP_NUT.copy(); cap.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -cap_phase_deg)
    cap.translate(App.Vector(sx, PLATE_SPINDLE_Y-cap_y, SPINDLE_Z))''', 1)
needle = "    sp = SPINDLE.copy(); sp.translate(App.Vector(sx,PLATE_SPINDLE_Y,SPINDLE_Z)); add_obj('LEFT_spindle_'+str(int(sx)), left_transform(sp))\n"
if needle in s and "add_obj('LEFT_knob_'" not in s:
    s = s.replace(needle, needle +
        "    k = KNOB.copy(); k.translate(App.Vector(sx,PLATE_SPINDLE_Y-hex_y,SPINDLE_Z)); add_obj('LEFT_knob_'+str(int(sx)), left_transform(k))\n", 1)

s = s.replace("'crosshead': 'bed-side full-width tie plus twin tapered under-rim side connectors'",
              "'crosshead': 'bed-side full-width tie plus twin tapered rim-inner side connectors'")
s = s.replace("'crosshead_low_bridge_span_mm': round(BOX_EDGE_Y-CROSSHEAD_BOTTOM_Y1, 3)",
              "'crosshead_low_bridge_span_mm': 0.0")
s = s.replace("'support_policy': 'no large structural support; only two short under-rim bridges plus optional local support at round bores'",
              "'support_policy': 'no large structural support; no fixed under-rim bridge; optional local support only at round bores'")
s = s.replace(
    "f.write('Includes a separate universal V-saddle anti-flop support for the diagonal Massload stay; exact stay fit awaits measurement.\\n')",
    "f.write('Anti-flop mounting aid is integrated as the single rear-only handed backstop; no separate stay saddle is exported.\\n')")

if s == orig:
    raise SystemExit('Width cleanup made no source changes')
p.write_text(s, encoding='utf-8')
print('Applied final v50 inboard box clamp and hard 600 mm envelope')
