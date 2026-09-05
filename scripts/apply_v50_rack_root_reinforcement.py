from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Strengthen the primary load path from each rack tube clamp into the long
# longitudinal arm. The previous clevis geometry had only ~4 mm longitudinal
# overlap between the upper clamp bridge and the raised transition block and
# only 6 mm overlap between transition and the I-beam. That creates an
# unnecessary stress concentration exactly at the main rack load input.
#
# Keep all frozen rack/tube/pivot datums unchanged. Reinforcement begins behind
# the Ø12.42 mm tube (Y > tube radius), so clamp kinematics and tube clearance
# remain untouched.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
replacement = '''def make_upper_station(xc):
    bridge = box(xc-17.0, -8.0, 0.0, 34.0, 22.0, 16.0)

    # Main arm transition: longer in Y so the solid transition overlaps the
    # I-beam by 12 mm instead of 6 mm.
    transition = box(xc-16.0, 8.0, ARM_BOTTOM_Z, 32.0, 28.0, ARM_H)

    # Low root shoulder starts safely behind the real rack tube (R=6.21 mm).
    # It ties the lower half of the clamp bridge into the full-height
    # transition and removes the abrupt Z-offset/notch in the primary load path.
    root_shoulder = box(xc-16.0, 6.5, 0.0, 32.0, 23.5, 20.0)

    # 4 mm fixed clevis lugs outside the 25.2 mm moving lower jaw.
    lug_l = cyl_x(6.0, 4.0, xc-17.0, PIN_Y, PIN_Z)
    lug_r = cyl_x(6.0, 4.0, xc+13.0, PIN_Y, PIN_Z)
    web_l = box(xc-17.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    web_r = box(xc+13.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)
    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)

    s = fuse_all([bridge, transition, root_shoulder,
                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])
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
    'root_shoulder_start_y_mm': 6.5,
    'bridge_end_y_mm': 14.0,
    'bridge_to_root_overlap_y_mm': 7.5,
    'transition_start_y_mm': 8.0,
    'transition_end_y_mm': 36.0,
    'transition_to_arm_overlap_y_mm': 12.0,
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
if r['root_shoulder_start_y_mm'] <= RACK_R:
    failures.append('Rack root reinforcement intrudes into rack tube envelope')
if r['bridge_to_root_overlap_y_mm'] < 7.0:
    failures.append('Rack clamp bridge/root overlap below strengthened design minimum')
if r['transition_to_arm_overlap_y_mm'] < 10.0:
    failures.append('Rack root transition/arm overlap below strengthened design minimum')
'''
s = s.replace(fail_anchor, fail_anchor + fail_insert, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack-root reinforcement: shoulder + extended arm transition')
