"""Post-build contract checks for the canonical v60 build.

This file only verifies the validation report produced by the canonical geometry
stages. It does not rebuild or independently substitute thread geometry.
"""

import json

with open('build_v60/VALIDATION_v60.json', encoding='utf-8') as fh:
    core = json.load(fh)
with open('build_v60/VALIDATION_v60_full.json', encoding='utf-8') as fh:
    full = json.load(fh)

assert not core['failures'], core['failures']
assert not full['failures'], full['failures']
assert core['stage'] == 'clean_structural_core_continuous_carrier', core['stage']
assert full['stage'] == 'full_direct_mechanism_v50_box_clamp_single_source', full['stage']

assert core['datums']['clamp_spacing_mm'] == 160.0
assert full['rack']['clamp_spacing_mm'] == 160.0
assert full['base']['right_bbox_mm'][0] <= 296.0
assert full['base']['right_bbox_mm'][1] <= 275.0
assert full['base']['mirror_delta_mm3'] <= 0.0001
assert full['handed_stl_export']['byte_distinct']
assert full['handed_stl_export']['mirror_geometry_ok']
assert full['handed_stl_export']['mirror_bounds_ok']
assert full['handed_stl_export']['mirror_vertex_set_ok']

# Box clamp: one v50-style architecture only. BASE is a smooth housing;
# the removable lead-nut cartridge contains the only working female RH8x2 thread.
box = full['box_clamp']
assert box['architecture'] == 'v50_direct_removable_lead_nut_cartridge_local_holm_stations', box
assert box['integral_female_threads'] is False, box
assert box['base_has_working_thread'] is False, box
assert box['working_female_thread_location'] == 'removable_lead_nut_cartridge', box
expected_spindles = core['datums']['box_clamp_spindle_x_mm']
assert box['spindle_x_mm'] == expected_spindles, box
assert abs(box['spindle_spacing_mm'] - (expected_spindles[1] - expected_spindles[0])) <= 1e-9, box
assert box['plate_x_mm'] == core['datums']['box_clamp_plate_x_mm'], box
assert box['plate_width_mm'] > 160.0, box
assert box['plate_travel_mm'] == 5.5, box
assert box['effective_total_width_mm'] <= 600.02, box
assert box['axial_slide_without_rotation_common_mm3'] >= 0.5, box
assert box['wrong_phase_common_mm3'] >= 0.5, box
assert len(box['cartridge_insertion']) == 8, box
assert all(q['base_common_mm3'] <= 0.0001 for q in box['cartridge_insertion']), box['cartridge_insertion']
assert box['final_assembly_replaceable_module_count'] == 0, box
assert box['final_assembly_contains_separate_lead_nut_hardware'] is True, box
assert box['final_assembly_lead_nut_cartridge_count'] == 4, box
assert box['final_assembly_lead_nut_pin_count'] == 4, box
assert box['final_assembly_lead_nut_clip_count'] == 4, box
assert box['final_assembly_box_clamp_knob_count'] == 4, box
assert box['final_assembly_knob_retainer_count'] == 4, box
assert box['final_assembly_installed_spindle_x_mm'] == expected_spindles, box
assert all(q['base_common_mm3'] <= 0.0001 for q in box['thread_motion']), box['thread_motion']
assert all(q['cartridge_common_mm3'] <= 0.10 for q in box['thread_motion']), box['thread_motion']

# Rack retainer: one final 12x2 pair only. The report must prove that the
# complete male-major envelope is open at the real BASE surface and that the
# actual retainer can enter from free space.
closure = full['rack']['m4_closure']
assert closure['carrier_bottom_plane_z_mm'] == 9.54, closure
assert closure['carrier_top_plane_z_mm'] == 39.54, closure
assert closure['lower_closure_thickness_mm'] == 7.0, closure
assert closure['upper_nut_pocket_af_mm'] == 6.9, closure
assert closure['screw_length_mm'] == 30.0, closure
assert closure['retainer_pitch_mm'] == 2.0, closure
assert closure['retainer_male_major_d_mm'] == 12.0, closure
assert closure['retainer_female_major_d_mm'] >= 12.4, closure
assert closure['entry_clear_d_mm'] > closure['retainer_male_major_d_mm'], closure
assert closure['entry_clear_depth_mm'] >= 1.0, closure
assert len(closure['female_thread_removed_mm3']) == 2, closure
assert all(v >= 8.0 for v in closure['female_thread_removed_mm3']), closure

mouth = closure['female_helical_witness']
assert len(mouth) == 2, mouth
assert all(q['mouth_block_mm3'] <= 0.0001 for q in mouth), mouth

fits = closure['retainer_phase_fit_checks']
assert len(fits) == 2, fits
assert all(q['nominal_common_mm3'] <= 0.20 for q in fits), fits
assert all(
    q['half_pitch_wrong_phase_common_mm3'] >= q['nominal_common_mm3'] + 2.0
    for q in fits
), fits

entry = closure['retainer_entry_checks']
assert len(entry) == 8, entry
assert {q['entry_depth_mm'] for q in entry} == {0.0, 0.5, 1.0, 2.0}, entry
assert all(q['base_common_mm3'] <= 0.20 for q in entry), entry

cc = core['geometry']['continuous_carrier']
assert cc['material_fraction'] >= 0.995, cc
assert cc['rack_tube_common_mm3'] <= 0.0001, cc
assert cc['front_holm_common_mm3'] >= 100.0, cc
assert cc['rear_holm_common_mm3'] >= 100.0, cc
assert cc['backstop_common_mm3'] >= 100.0, cc

checks = full['installed_support_orientation']['checks']
assert len(checks) == 2
for q in checks:
    assert q['right_outward_extent_mm'] >= 210.0, q
    assert q['left_outward_extent_mm'] >= 210.0, q
    assert q['right_inward_extent_mm'] <= 30.0, q
    assert q['left_inward_extent_mm'] <= 30.0, q

print('V60_WORKFLOW_CONTRACT canonical single-source geometry checks passed', flush=True)
