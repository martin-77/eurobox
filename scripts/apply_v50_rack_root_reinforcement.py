from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Carry the normal longitudinal I-beam section all the way to the front edge
# of each fixed rack-clamp station. Keep the proven saddle/pivot datums, but use
# substantially thicker fixed clevis cheeks around the rack-lower pivot. The
# moving lower jaw remains 25.2 mm wide with 0.8 mm total running clearance.
pattern = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
replacement = '''RACK_FIXED_LUG_T = 6.0
RACK_FIXED_LUG_INNER_X = 13.0
RACK_FIXED_LUG_OUTER_X = RACK_FIXED_LUG_INNER_X + RACK_FIXED_LUG_T

def make_upper_station(xc):
    bridge = box(xc-RACK_FIXED_LUG_OUTER_X, -8.0, 0.0,
                 2*RACK_FIXED_LUG_OUTER_X, 22.0, 16.0)

    # Same 32 x 30 mm double-web I-beam section as the normal arm, extended
    # from the fixed-station front edge to Y=36. This overlaps the regular arm
    # (which starts at Y=24) by 12 mm and removes the former solid root block.
    root_beam = make_i_beam_y(xc, -8.0, 36.0)

    # 6 mm fixed clevis lugs, grown OUTWARD so the proven 26.0 mm inner gap and
    # the lower-jaw running clearance are unchanged. The old 4 mm cheeks were
    # too fragile for PETG around a 4.6 mm pin bore.
    lug_l = cyl_x(7.0, RACK_FIXED_LUG_T,
                  xc-RACK_FIXED_LUG_OUTER_X, PIN_Y, PIN_Z)
    lug_r = cyl_x(7.0, RACK_FIXED_LUG_T,
                  xc+RACK_FIXED_LUG_INNER_X, PIN_Y, PIN_Z)
    web_l = box(xc-RACK_FIXED_LUG_OUTER_X, PIN_Y, PIN_Z,
                RACK_FIXED_LUG_T, 8.0, 7.0)
    web_r = box(xc+RACK_FIXED_LUG_INNER_X, PIN_Y, PIN_Z,
                RACK_FIXED_LUG_T, 8.0, 7.0)
    cheek_l = box(xc-RACK_FIXED_LUG_OUTER_X, -8.0, -7.0,
                  RACK_FIXED_LUG_T, 9.0, 7.0)
    cheek_r = box(xc+RACK_FIXED_LUG_INNER_X, -8.0, -7.0,
                  RACK_FIXED_LUG_T, 9.0, 7.0)

    q = fuse_all([bridge, root_beam,
                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])
    # The real rack-tube envelope and pin bore are cut only after all root
    # solids are fused. This preserves the exact interfaces while keeping at
    # least 6 mm material along X around the pivot on each side.
    q = q.cut(cyl_x(UPPER_SADDLE_R, 44.0, xc-22.0, 0.0, 0.0))
    q = q.cut(cyl_x(PIN_HOLE_D/2, 44.0, xc-22.0, PIN_Y, PIN_Z))
    return q.removeSplitter()

base_parts ='''
s, n = pattern.subn(replacement, s, count=1)
assert n == 1, 'upper station block not found'

anchor = "V['beam_sanity'] = {\n"
assert anchor in s
insert = '''root_area = 2*ARM_W*FLANGE_T + 2*WEB_T*(ARM_H-2*FLANGE_T)
root_Ix = 2*(ARM_W*FLANGE_T**3/12.0 + ARM_W*FLANGE_T*(ARM_H/2.0-FLANGE_T/2.0)**2) \\
          + 2*(WEB_T*(ARM_H-2*FLANGE_T)**3/12.0)
root_static_stress = F_arm * L_check * (ARM_H/2.0) / root_Ix
V['rack_root_strengthening'] = {
    'design': 'continuous_same_I_beam_as_long_arm_plus_6mm_fixed_clevis',
    'front_edge_y_mm': -8.0,
    'root_beam_start_y_mm': -8.0,
    'root_beam_end_y_mm': 36.0,
    'regular_arm_start_y_mm': ARM_Y0,
    'root_to_regular_arm_overlap_y_mm': 36.0-ARM_Y0,
    'bridge_start_y_mm': -8.0,
    'bridge_end_y_mm': 14.0,
    'bridge_to_root_beam_overlap_y_mm': 22.0,
    'tube_clearance_preserved_by_post_fuse_saddle_cut': True,
    'fixed_clevis_lug_thickness_mm': RACK_FIXED_LUG_T,
    'fixed_clevis_inner_gap_mm': 2*RACK_FIXED_LUG_INNER_X,
    'moving_lower_width_mm': 25.2,
    'total_lateral_running_clearance_mm': 2*RACK_FIXED_LUG_INNER_X-25.2,
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
if r['fixed_clevis_lug_thickness_mm'] < 6.0:
    failures.append('Rack lower fixed clevis support below 6 mm PETG minimum')
if not (0.6 <= r['total_lateral_running_clearance_mm'] <= 1.2):
    failures.append('Rack lower clevis running clearance outside 0.6..1.2 mm')
if abs(r['root_section_area_mm2'] - 422.4) > 1e-3:
    failures.append('Rack root section area no longer matches normal arm')
if abs(r['root_section_Ix_mm4'] - 52243.2) > 1e-3:
    failures.append('Rack root section inertia no longer matches normal arm')
'''
s = s.replace(fail_anchor, fail_anchor + fail_insert, 1)

assert s != orig
p.write_text(s, encoding='utf-8')
print('Applied v50 rack-root reinforcement: proven I-beam root + 6 mm fixed clevis cheeks')
