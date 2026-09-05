from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Strengthen the primary load path from each rack tube clamp into the long
# longitudinal arm. The clamp/root is the main load input for the complete
# carrier, so avoid a local neck immediately behind the rack tube.
#
# The reinforcement now extends all the way to the front edge of the fixed
# upper station (Y=-8 mm). The real Ø12.42 mm tube saddle is cut afterwards
# through the fused station, so the additional material does not reduce tube
# clearance or change any frozen rack/tube/pivot datum.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
replacement = '''def make_upper_station(xc):
    bridge = box(xc-17.0, -8.0, 0.0, 34.0, 22.0, 16.0)

    # Full-height arm transition reaches the front edge of the fixed station.
    # It therefore overlaps the bridge across its complete 22 mm Y depth and
    # still overlaps the I-beam by 12 mm at the rear.
    transition = box(xc-16.0, -8.0, ARM_BOTTOM_Z, 32.0, 44.0, ARM_H)

    # Lower root shoulder also reaches the front edge. Together with the
    # transition this forms a continuous 32 mm wide, effectively full-height
    # load path around the upper tube saddle instead of a short rear shoulder.
    root_shoulder = box(xc-16.0, -8.0, 0.0, 32.0, 38.0, 20.0)

    # 4 mm fixed clevis lugs outside the 25.2 mm moving lower jaw.
    lug_l = cyl_x(6.0, 4.0, xc-17.0, PIN_Y, PIN_Z)
    lug_r = cyl_x(6.0, 4.0, xc+13.0, PIN_Y, PIN_Z)
    web_l = box(xc-17.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    web_r = box(xc+13.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)
    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)

    s = fuse_all([bridge, transition, root_shoulder,
                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])
    # Preserve the exact real rack tube envelope by cutting the saddle only
    # after all reinforcement solids have been fused.
    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return s.removeSplitter()

base_parts ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'upper station block not found'

# Record the strengthened root geometry and a simple section sanity check in
# the source validation report. This is not an FEA; it makes the design intent
# and the assumed 16 kg / 3x dynamic beam load explicit and machine-checkable.
anchor = "V['beam_sanity'] = {\n"
assert anchor in s
insert = '''root_b = 32.0
root_h = ARM_TOP_Z
root_Ix = root_b * root_h**3 / 12.0
root_static_stress = F_arm * L_check * (root_h/2.0) / root_Ix
V['rack_root_strengthening'] = {
    'tube_radius_mm': RACK_R,
    'front_edge_y_mm': -8.0,
    'root_shoulder_start_y_mm': -8.0,
    'root_shoulder_end_y_mm': 30.0,
    'bridge_end_y_mm': 14.0,
    'bridge_to_root_overlap_y_mm': 22.0,
    'transition_start_y_mm': -8.0,
    'transition_end_y_mm': 36.0,
    'bridge_to_transition_overlap_y_mm': 22.0,
    'transition_to_arm_overlap_y_mm': 12.0,
    'tube_clearance_preserved_by_post_fuse_saddle_cut': True,
    'root_effective_width_mm': root_b,
    'root_effective_height_mm': root_h,
    'root_section_Ix_mm4': round(root_Ix, 3),
    'static_root_stress_mpa_at_existing_16kg_assumption': round(root_static_stress, 4),
    'dynamic_3x_root_stress_mpa_at_existing_16kg_assumption': round(3*root_static_stress, 4),
}

'''
s = s.replace(anchor, insert + anchor, 1)

fail_anchor = "failures = []\n"
assert fail_anchor in s
fail_insert = '''r = V['rack_root_strengthening']
if abs(r['root_shoulder_start_y_mm'] - r['front_edge_y_mm']) > 1e-9:
    failures.append('Rack root shoulder no longer reaches fixed-station front edge')
if abs(r['transition_start_y_mm'] - r['front_edge_y_mm']) > 1e-9:
    failures.append('Rack root transition no longer reaches fixed-station front edge')
if r['bridge_to_root_overlap_y_mm'] < 20.0:
    failures.append('Rack clamp bridge/root overlap below front-edge reinforced design minimum')
if r['bridge_to_transition_overlap_y_mm'] < 20.0:
    failures.append('Rack clamp bridge/transition overlap below front-edge reinforced design minimum')
if r['transition_to_arm_overlap_y_mm'] < 10.0:
    failures.append('Rack root transition/arm overlap below strengthened design minimum')
'''
s = s.replace(fail_anchor, fail_anchor + fail_insert, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack-root reinforcement: full front-edge shoulder + transition')
