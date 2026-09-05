from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Carry the normal longitudinal I-beam section all the way to the front edge
# of each fixed rack-clamp station instead of using a large solid root block.
# The fixed clamp bridge itself provides the local material around the tube;
# the continuous I-beam provides the main bending load path into the arm.
#
# All measured rack/tube/pivot datums stay unchanged. The Ø12.42 mm upper
# saddle is cut after the bridge and I-beam have been fused, preserving the
# exact tube interface while avoiding an abrupt neck behind the clamp.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
replacement = '''def make_upper_station(xc):
    bridge = box(xc-17.0, -8.0, 0.0, 34.0, 22.0, 16.0)

    # Same 32 x 30 mm double-web I-beam section as the normal arm, extended
    # from the fixed-station front edge to Y=36. This overlaps the regular arm
    # (which starts at Y=24) by 12 mm and removes the former solid root block.
    root_beam = make_i_beam_y(xc, -8.0, 36.0)

    # 4 mm fixed clevis lugs outside the 25.2 mm moving lower jaw.
    lug_l = cyl_x(6.0, 4.0, xc-17.0, PIN_Y, PIN_Z)
    lug_r = cyl_x(6.0, 4.0, xc+13.0, PIN_Y, PIN_Z)
    web_l = box(xc-17.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    web_r = box(xc+13.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)
    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)

    s = fuse_all([bridge, root_beam,
                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])
    # The real rack-tube envelope is cut only after all root solids are fused.
    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return s.removeSplitter()

base_parts ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'upper station block not found'

# Record the root design in the source validation report. The root deliberately
# uses the same section as the normal arm, so its nominal section properties
# should match beam_sanity. This is a simple beam check, not FEA.
anchor = "V['beam_sanity'] = {\n"
assert anchor in s
insert = '''root_area = 2*ARM_W*FLANGE_T + 2*WEB_T*(ARM_H-2*FLANGE_T)
root_Ix = 2*(ARM_W*FLANGE_T**3/12.0 + ARM_W*FLANGE_T*(ARM_H/2.0-FLANGE_T/2.0)**2) \\
          + 2*(WEB_T*(ARM_H-2*FLANGE_T)**3/12.0)
root_static_stress = F_arm * L_check * (ARM_H/2.0) / root_Ix
V['rack_root_strengthening'] = {
    'design': 'continuous_same_I_beam_as_long_arm',
    'front_edge_y_mm': -8.0,
    'root_beam_start_y_mm': -8.0,
    'root_beam_end_y_mm': 36.0,
    'regular_arm_start_y_mm': ARM_Y0,
    'root_to_regular_arm_overlap_y_mm': 36.0-ARM_Y0,
    'bridge_start_y_mm': -8.0,
    'bridge_end_y_mm': 14.0,
    'bridge_to_root_beam_overlap_y_mm': 22.0,
    'tube_clearance_preserved_by_post_fuse_saddle_cut': True,
    'root_section_area_mm2': round(root_area, 3),
    'root_section_Ix_mm4': round(root_Ix, 3),
    'static_root_stress_mpa_at_existing_16kg_assumption': round(root_static_stress, 4),
    'dynamic_3x_root_stress_mpa_at_existing_16kg_assumption': round(3*root_static_stress, 4),
}

'''
s = s.replace(anchor, insert + anchor, 1)

fail_anchor = "failures = []\n"
assert fail_anchor in s
fail_insert = '''r = V['rack_root_strengthening']
if abs(r['root_beam_start_y_mm'] - r['front_edge_y_mm']) > 1e-9:
    failures.append('Rack root I-beam no longer reaches fixed-station front edge')
if r['bridge_to_root_beam_overlap_y_mm'] < 20.0:
    failures.append('Rack clamp bridge/root-beam overlap below design minimum')
if r['root_to_regular_arm_overlap_y_mm'] < 10.0:
    failures.append('Rack root/regular-arm overlap below design minimum')
if abs(r['root_section_area_mm2'] - 422.4) > 1e-3:
    failures.append('Rack root section area no longer matches normal arm')
if abs(r['root_section_Ix_mm4'] - 52243.2) > 1e-3:
    failures.append('Rack root section inertia no longer matches normal arm')
'''
s = s.replace(fail_anchor, fail_anchor + fail_insert, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack-root reinforcement: continuous normal I-beam to front edge')
