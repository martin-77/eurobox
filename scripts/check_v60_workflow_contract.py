"""Post-build contract checks for the canonical v60 GitHub Actions build."""

import json

# CI trigger marker: serviceable v50-style cartridge/access architecture audit.

with open('build_v60/VALIDATION_v60.json', encoding='utf-8') as fh:
    core = json.load(fh)
with open('build_v60/VALIDATION_v60_full.json', encoding='utf-8') as fh:
    full = json.load(fh)

assert not core['failures'], core['failures']
assert not full['failures'], full['failures']
assert core['stage'] == 'clean_structural_core_continuous_carrier', core['stage']
assert full['stage'] == 'full_direct_mechanism_clean_modular_front_v6_all_threads_accessible', full['stage']
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

# CLEAN MODULAR FRONT: fixed front is one closed v60-style structural carrier.
# It has two cassette bays. All working RH8x2 wear threads remain separately
# replaceable and every user-operated threaded interface has a real service path.
front = full['box_clamp']
assert front['architecture'] == 'clean_modular_front_v6_full_handle_travel_and_all_RH8x2_service_access', front
assert front['plate_width_mm'] == 160.0, front
assert front['plate_main_x_mm'] == [-40.0, 120.0], front
assert front['spindle_x_mm'] == [-48.0, 128.0], front
assert front['spindle_spacing_mm'] == 176.0, front
assert front['integral_female_threads'] is False, front
assert front['base_has_working_lead_thread'] is False, front
assert front['module_has_working_lead_thread'] is False, front
assert front['module_count_per_base'] == 2, front
assert front['module_attachment'] == 'top-drop cassette, two M3 screws into heat-set inserts per module', front
assert front['lead_nut_mode'] == 'separate_RH8x2_cartridge_cross_pin_external_C_clip_inside_replaceable_module', front
assert front['rear_drive_service_open'] is True, front
assert front['lead_nut_tail_to_hex_preload_clearance_mm'] >= 0.5, front
assert front['knob_retainer_thread']['open_ended'] is True, front
assert front['knob_retainer_thread']['core_blockage_mm3'] <= 0.0001, front
assert front['knob_retainer_thread']['stud_engagement_mm'] >= 4.0, front
assert front['final_assembly_replaceable_module_count'] == 4, front
assert front['final_assembly_contains_separate_lead_nut_hardware'] is True, front
assert front['final_assembly_lead_nut_cartridge_count'] == 4, front
assert front['final_assembly_lead_nut_pin_count'] == 4, front
assert front['final_assembly_lead_nut_clip_count'] == 4, front
assert front['final_assembly_box_clamp_knob_count'] == 4, front
assert front['final_assembly_knob_retainer_count'] == 4, front
assert front['final_assembly_installed_spindle_x_mm'] == [-48.0, 128.0], front

mods = front['module_checks']
assert len(mods) == 2, mods
assert all(q['base_common_mm3'] <= 0.0001 for q in mods), mods

cartridges = front['cartridge_checks']
assert len(cartridges) == 2, cartridges
assert all(q['nut_module_common_mm3'] <= 0.0001 for q in cartridges), cartridges
assert all(q['pin_module_common_mm3'] <= 0.0001 for q in cartridges), cartridges
assert all(q['clip_module_common_mm3'] <= 0.0001 for q in cartridges), cartridges

# v50 service principle remains nested inside each replaceable cassette. Once
# spindle, C-clip and cross-pin are removed, the RH8x2 wear cartridge must slide
# out through the module's +Y service mouth without touching the module housing.
extract = front['cartridge_extraction_plus_y']
assert len(extract) >= 5, extract
assert extract[0]['travel_y_mm'] == 0.0, extract
assert extract[-1]['travel_y_mm'] >= 16.0, extract
assert all(q['module_common_mm3'] <= 0.0001 for q in extract), extract

assert front['axial_slide_without_rotation_common_mm3'] >= 0.5, front
assert front['half_pitch_wrong_phase_common_mm3'] >= 0.5, front
assert any(q['travel_mm'] == -0.5 for q in front['plate_motion']), front['plate_motion']
assert any(q['travel_mm'] == 5.5 for q in front['plate_motion']), front['plate_motion']
assert any(q['travel_mm'] == -0.5 for q in front['thread_motion']), front['thread_motion']
assert any(q['travel_mm'] == 5.5 for q in front['thread_motion']), front['thread_motion']

# Ø30 hand knob + its open-ended RH8x2 retainer must be exposed over every
# tested clamp position, through both fixed carrier and replaceable cassette.
handle = front['handle_wall_access_checks']
assert len(handle) == 16, handle
assert {q['travel_mm'] for q in handle} == {-0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.5}, handle
assert all(q['knob_base_common_mm3'] <= 0.0001 for q in handle), handle
assert all(q['knob_module_common_mm3'] <= 0.0001 for q in handle), handle
assert all(q['cap_nut_base_common_mm3'] <= 0.0001 for q in handle), handle
assert all(q['cap_nut_module_common_mm3'] <= 0.0001 for q in handle), handle

closure = full['rack']['m4_closure']
assert closure['carrier_bottom_plane_z_mm'] == 9.54, closure
assert closure['carrier_top_plane_z_mm'] == 39.54, closure
assert closure['lower_closure_thickness_mm'] == 7.0, closure
assert closure['retainer_top_recess_mm'] <= 0.35, closure
assert closure['upper_nut_pocket_af_mm'] == 6.9, closure
assert closure['screw_length_mm'] == 30.0, closure

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

# Consolidated final thread audit: all printed working threads plus the metal M4
# service path must be physically accessible in the final geometry.
audit = full['thread_access_audit']
assert audit['all_printed_threads_checked'] is True, audit
assert audit['no_thread_behind_closed_wall'] is True, audit
assert len(audit['printed_thread_interfaces']) == 3, audit
assert audit['rack_retainer_top_recess_mm'] <= 0.35, audit
rm = audit['rack_retainer_unscrew_motion']
assert len(rm) == 10, rm
assert all(q['base_common_mm3'] <= 2.0 for q in rm), rm

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
