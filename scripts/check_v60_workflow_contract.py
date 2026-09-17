"""Post-build contract checks for the canonical v60 GitHub Actions build."""

import json


with open('build_v60/VALIDATION_v60.json', encoding='utf-8') as fh:
    core = json.load(fh)
with open('build_v60/VALIDATION_v60_full.json', encoding='utf-8') as fh:
    full = json.load(fh)

assert not core['failures'], core['failures']
assert not full['failures'], full['failures']
assert core['stage'] == 'clean_structural_core_continuous_carrier', core['stage']
assert full['stage'] == 'full_direct_mechanism_v50_box_clamp_and_explicit_retainer_threads', full['stage']
assert core['datums']['clamp_spacing_mm'] == 160.0
assert full['rack']['clamp_spacing_mm'] == 160.0
assert full['base']['right_bbox_mm'][0] <= 296.0
assert full['base']['right_bbox_mm'][1] <= 275.0
assert full['base']['mirror_delta_mm3'] <= 0.0001
assert full['box_clamp']['effective_total_width_mm'] <= 600.02
assert full['handed_stl_export']['byte_distinct']
assert full['handed_stl_export']['mirror_geometry_ok']
assert full['handed_stl_export']['mirror_bounds_ok']
assert full['handed_stl_export']['mirror_vertex_set_ok']

# BOX CLAMP: 160 mm main clamp face, but the drive hardware itself is outside
# that face. Narrow moving ears pick up the +/-88 mm spindle axes while the
# fixed cartridge bosses merge directly into the broad outer Y/Z DROPs.
front = full['box_clamp']
assert front['plate_width_mm'] == 160.0, front
assert front['spindle_x_mm'] == [-88.0, 88.0], front
assert front['spindle_spacing_mm'] == 176.0, front
assert front['spindle_outboard_of_main_face_mm'] == 8.0, front
assert front['plate_total_outer_x_mm'] == 98.0, front
assert front['fixed_cartridge_boss_outer_x_mm'] == 99.0, front
assert front['plate_drive_ear_x_mm'][0] < 80.0, front
assert front['plate_drive_ear_x_mm'][1] > 88.0, front
assert front['lead_nut_mode'] == 'separate_RH8x2_cartridge_cross_pin_external_C_clip', front
assert front['integral_female_threads'] is False, front
assert front['base_has_working_lead_thread'] is False, front
assert front['triangular_front_drops'] is False, front
assert front['cartridge_bosses_outside_main_plate_x'] is True, front
assert front['final_assembly_contains_separate_lead_nut_hardware'] is True, front
assert front['final_assembly_lead_nut_cartridge_count'] == 4, front
assert front['final_assembly_lead_nut_pin_count'] == 4, front
assert front['final_assembly_lead_nut_clip_count'] == 4, front

drops = front['outer_support_drops']
assert len(drops) == 2, drops
assert all(q['outside_main_plate_x'] for q in drops), drops
assert all(q['flank_angle_from_horizontal_deg'] >= 45.0 for q in drops), drops
assert all(q['material_fraction'] >= 0.995 for q in drops), drops
assert all(q['integrated_with_cartridge_boss_common_mm3'] >= 20.0 for q in drops), drops

voids = front['base_thread_void_checks']
assert len(voids) == 2, voids
assert all(q['base_common_mm3'] <= 0.0001 for q in voids), voids

cartridges = front['cartridge_checks']
assert len(cartridges) == 2, cartridges
assert all(q['nut_base_common_mm3'] <= 0.0001 for q in cartridges), cartridges
assert all(q['pin_base_common_mm3'] <= 0.0001 for q in cartridges), cartridges
assert all(q['pin_nut_common_mm3'] <= 0.0001 for q in cartridges), cartridges
assert all(q['clip_base_common_mm3'] <= 0.0001 for q in cartridges), cartridges
assert front['axial_slide_without_rotation_common_mm3'] >= 0.5, front
assert front['half_pitch_wrong_phase_common_mm3'] >= 0.5, front
assert any(q['travel_mm'] == -0.5 for q in front['plate_motion']), front['plate_motion']
assert any(q['travel_mm'] == 5.5 for q in front['plate_motion']), front['plate_motion']

closure = full['rack']['m4_closure']
assert closure['carrier_bottom_plane_z_mm'] == 9.54, closure
assert closure['carrier_top_plane_z_mm'] == 39.54, closure
assert closure['lower_closure_thickness_mm'] == 7.0, closure
assert closure['retainer_top_recess_mm'] <= 0.35, closure
assert closure['upper_nut_pocket_af_mm'] == 6.9, closure
assert closure['screw_length_mm'] == 30.0, closure

# RETAINER THREAD: require real helical male material, material removed from
# final BASE, retained female lands and a phase-sensitive interference witness.
assert closure['retainer_pitch_mm'] == 2.0, closure
assert closure['retainer_male_major_d_mm'] == 12.0, closure
assert closure['retainer_female_major_d_mm'] >= 12.4, closure
assert closure['male_helical_material_mm3'] >= 12.0, closure
assert len(closure['female_thread_removed_mm3']) == 2, closure
assert all(v >= 8.0 for v in closure['female_thread_removed_mm3']), closure
fw = closure['female_helical_witness']
assert len(fw) == 2, fw
assert all(0.35 <= q['annular_material_fraction'] <= 0.995 for q in fw), fw
pf = closure['retainer_phase_fit_checks']
assert len(pf) == 2, pf
assert all(q['nominal_common_mm3'] <= 2.0 for q in pf), pf
assert all(
    q['half_pitch_wrong_phase_common_mm3'] >= q['nominal_common_mm3'] + 2.0
    for q in pf
), pf

cc = core['geometry']['continuous_carrier']
assert cc['material_fraction'] >= 0.995, cc
assert cc['rack_tube_common_mm3'] <= 0.0001, cc
assert cc['front_holm_common_mm3'] >= 100.0, cc
assert cc['rear_holm_common_mm3'] >= 100.0, cc
assert cc['backstop_common_mm3'] >= 100.0, cc
assert len(cc['clamp_overlaps']) == 2
assert all(q['carrier_common_mm3'] >= 100.0 for q in cc['clamp_overlaps']), cc

checks = full['installed_support_orientation']['checks']
assert len(checks) == 2
for q in checks:
    assert q['right_outward_extent_mm'] >= 210.0, q
    assert q['left_outward_extent_mm'] >= 210.0, q
    assert q['right_inward_extent_mm'] <= 30.0, q
    assert q['left_inward_extent_mm'] <= 30.0, q

print('V60_WORKFLOW_CONTRACT all post-build hard checks passed', flush=True)
