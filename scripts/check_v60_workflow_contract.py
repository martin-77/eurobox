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
assert len(box['cartridge_insertion']) == 8, box
assert all(q['base_common_mm3'] <= 0.0001 for q in box['cartridge_insertion']), box['cartridge_insertion']
assert box['final_assembly_replaceable_module_count'] == 0, box
assert box['final_assembly_contains_separate_lead_nut_hardware'] is True, box
assert box['final_assembly_lead_nut_cartridge_count'] == 4, box
assert box['final_assembly_lead_nut_pin_count'] == 4, box
assert box['final_assembly_lead_nut_clip_count'] == 4, box
assert box['final_assembly_box_clamp_knob_count'] == 4, box
assert box['final_assembly_knob_retainer_count'] == 4, box
assert box['final_assembly_plate_retainer_clip_count'] == 4, box
assert box['final_assembly_installed_spindle_x_mm'] == expected_spindles, box
assert all(q['base_common_mm3'] <= 0.0001 for q in box['thread_motion']), box['thread_motion']
assert box['thread_brep_common_tolerance_mm3'] == 1.20, box
assert all(q['cartridge_common_mm3'] <= box['thread_brep_common_tolerance_mm3'] for q in box['thread_motion']), box['thread_motion']

# Lead screw must be the exact closed printable CGAL mesh, with a full 7 mm
# knob hex and true RH8x2 on both male thread sections.
ls = box['lead_screw']
assert ls['knob_hex_length_mm'] == ls['knob_thickness_mm'] == 7.0, ls
assert ls['mesh_topology']['boundary_edges'] == 0, ls
assert ls['mesh_topology']['nonmanifold_edges'] == 0, ls
assert len(ls['main_thread_samples']) == 8, ls
assert all(q['ridge_center_solid'] for q in ls['main_thread_samples']), ls
assert all(not q['between_turns_solid'] for q in ls['main_thread_samples']), ls

pr = box['plate_spindle_retention']
assert pr['clip_count_final_assembly'] == 4, pr
assert len(pr['checks']) == 2, pr
assert all(q['spindle_common_mm3'] <= 0.0001 for q in pr['checks']), pr
assert all(q['plate_common_mm3'] <= 0.0001 for q in pr['checks']), pr
assert pr['service_channel_width_mm'] >= 11.2, pr
assert pr['service_channel_depth_mm'] == 2.0, pr
assert len(pr['clip_insertion_path']) == 10, pr
assert all(q['plate_common_mm3'] <= 0.00001 for q in pr['clip_insertion_path']), pr

ms = box['mounting_sequence']
assert ms['order'] == [
    'lead_nut_into_base',
    'lead_nut_cross_pin',
    'lead_nut_pin_clip',
    'lead_screw_through_plate',
    'plate_retainer_clip_via_bottom_service_channel',
    'plate_spindle_subassembly_threaded_into_fixed_lead_nut',
    'knob_on_full_7mm_hex',
    'knob_retainer_nut_on_outer_RH8x2_stud',
], ms
assert len(ms['threaded_plate_approach']) == 10, ms
assert all(q['plate_base_common_mm3'] <= 0.0001 for q in ms['threaded_plate_approach']), ms
assert all(q['spindle_base_common_mm3'] <= 0.0001 for q in ms['threaded_plate_approach']), ms
assert all(q['spindle_lead_nut_common_mm3'] <= box['thread_brep_common_tolerance_mm3'] for q in ms['threaded_plate_approach']), ms
assert all(q['knob_base_common_mm3'] <= 0.0001 for q in ms['threaded_plate_approach']), ms
assert all(q['knob_retainer_base_common_mm3'] <= 0.0001 for q in ms['threaded_plate_approach']), ms
assert len(ms['operating_knob_clearance']) == 14, ms
assert all(q['knob_base_common_mm3'] <= 0.0001 for q in ms['operating_knob_clearance']), ms
assert all(q['retainer_base_common_mm3'] <= 0.0001 for q in ms['operating_knob_clearance']), ms

# The removable lead-nut wear cartridge must contain a real printable RH8x2
# female helix.  Direct final-part samples prevent a smooth cylindrical bore
# from ever satisfying the workflow contract again.
ln = box['lead_nut_thread']
assert ln['standard'] == 'RH8x2 true radial/axial printable matched pair', ln
assert ln['pitch_mm'] == 2.0, ln
assert ln['male_major_d_mm'] == 8.0, ln
assert ln['male_crest_width_mm'] >= 0.50, ln
assert ln['female_crest_material_between_turns_mm'] >= 0.45, ln
assert ln['radial_thread_engagement_mm'] >= 0.40, ln
assert len(ln['samples']) == 8, ln
assert all(not q['groove_center_solid'] for q in ln['samples']), ln
assert all(q['between_turns_solid'] for q in ln['samples']), ln
assert ln['validated_export_part'] == 'eurobox_v60_lead_nut', ln

# The separate box-clamp knob retainer must contain a real printable RH8x2
# female helix, matched to the actual outer stud on the exported lead screw.
kr = box['knob_retainer_thread']
assert kr['standard'] == 'RH8x2 true radial/axial printable pair', kr
assert kr['pitch_mm'] == 2.0, kr
assert kr['male_major_d_mm'] == 8.0, kr
assert kr['male_crest_width_mm'] >= 0.50, kr
assert kr['female_crest_material_between_turns_mm'] >= 0.45, kr
assert kr['radial_core_clearance_mm'] >= 0.20, kr
assert kr['radial_major_clearance_mm'] >= 0.20, kr
assert len(kr['samples']) == 4, kr
assert all(q['male_ridge_center_solid'] for q in kr['samples']), kr
assert all(not q['male_between_turns_solid'] for q in kr['samples']), kr
assert all(not q['female_groove_center_solid'] for q in kr['samples']), kr
assert all(q['female_between_turns_solid'] for q in kr['samples']), kr
assert kr['validated_export_part'] == 'eurobox_v60_knob_retainer_nut', kr

# Rack retainer: one final printable 12x3 pair only.  The contract checks the
# actual radial/axial profile dimensions and direct point samples from the final
# BASE/retainer, rather than expensive whole-body phase booleans.
closure = full['rack']['m4_closure']
assert closure['carrier_bottom_plane_z_mm'] == 9.54, closure
assert closure['carrier_top_plane_z_mm'] == 39.54, closure
assert closure['lower_closure_thickness_mm'] == 7.0, closure
assert closure['upper_nut_pocket_af_mm'] == 6.9, closure
assert closure['screw_length_mm'] == 30.0, closure
assert closure['retainer_pitch_mm'] == 3.0, closure
assert closure['retainer_male_major_d_mm'] == 12.0, closure
assert closure['retainer_female_major_d_mm'] >= 12.5, closure
assert closure['retainer_thread_profile_generator'] == 'true_radial_axial_OCC_fused', closure
assert closure['entry_clear_d_mm'] >= closure['retainer_male_major_d_mm'] + 0.8, closure
assert 0.35 <= closure['entry_clear_depth_mm'] <= 0.60, closure
assert closure['female_thread_start_recess_mm'] <= 0.60, closure
assert len(closure['female_thread_removed_mm3']) == 2, closure
assert all(v >= 8.0 for v in closure['female_thread_removed_mm3']), closure

p = closure['thread_printability']
assert p['pitch_mm'] == 3.0, p
assert p['male_crest_width_mm'] >= 0.70, p
assert p['female_crest_material_between_turns_mm'] >= 0.80, p
assert 7.5 <= p['approx_full_turns'] <= 8.5, p
assert p['radial_core_clearance_mm'] >= 0.20, p
assert p['radial_major_clearance_mm'] >= 0.20, p
assert p['axial_root_clearance_mm'] >= 0.25, p
assert p['axial_crest_clearance_mm'] >= 0.25, p
assert p['target_nozzle_mm'] == 0.4, p

mouth = closure['female_helical_witness']
assert len(mouth) == 2, mouth
assert all(q['blocked_sample_points'] == 0 for q in mouth), mouth

female_samples = closure['female_thread_point_samples']
assert len(female_samples) == 16, female_samples
assert all(not q['groove_center_solid'] for q in female_samples), female_samples
assert all(q['between_turns_solid'] for q in female_samples), female_samples

male_samples = closure['male_thread_point_samples']
assert len(male_samples) == 8, male_samples
assert all(q['ridge_center_solid'] for q in male_samples), male_samples
assert all(not q['between_turns_solid'] for q in male_samples), male_samples

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
