from pathlib import Path

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# The previous 4.5 mm travel cleared the measured 244.665 mm box edge by only
# 0.30 mm (underhook inner face 244.965 mm). That is too little allowance for a
# real Eurobox plus FDM tolerances. Keep frozen datums and use 5.5 mm travel.
s = s.replace('PLATE_OPEN = 4.5', 'PLATE_OPEN = 5.5', 1)

if 'LEAD_THREAD_LEN = 22.2' not in s:
    raise SystemExit('Could not locate v50 lead-thread length')
s = s.replace('LEAD_THREAD_LEN = 22.2', 'LEAD_THREAD_LEN = 23.0', 1)

s = s.replace('for d in [0, 1, 2, 3, 4, 4.5]:',
              'for d in [0, 1, 2, 3, 4, 4.5, 5.0, 5.5]:', 1)
s = s.replace('for d in [0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5]:',
              'for d in [-0.5, 0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 5.5]:', 1)
s = s.replace("'open_4_5mm': round(BOX_W + 2*((spindle_outer_local_y+4.5)-BOX_EDGE_Y), 3),",
              "'open_5_5mm': round(BOX_W + 2*((spindle_outer_local_y+5.5)-BOX_EDGE_Y), 3),", 1)

if s == orig:
    raise SystemExit('Clamp travel/preload fixup did not modify build_v50.py')
if 'PLATE_OPEN = 5.5' not in s:
    raise SystemExit('Clamp travel fixup failed')
if 'LEAD_THREAD_LEN = 23.0' not in s:
    raise SystemExit('Spindle preload travel fixup failed')
if 'for d in [-0.5, 0, 0.5' not in s:
    raise SystemExit('Preload kinematics validation fixup failed')

p.write_text(s, encoding='utf-8')
print('Applied v50 clamp fixups: 5.5 mm opening + 0.5 mm preload spindle clearance')

for script_name, missing in [
    ('scripts/apply_v50_rack_root_reinforcement.py','Missing rack-root reinforcement fixup'),
    ('scripts/apply_v50_rack_lock.py','Missing rack-lock fixup'),
    ('scripts/apply_v50_rack_closure_massive.py','Missing continuous rack-closure fixup'),
    ('scripts/apply_v50_rack_female_threads.py','Missing rack female-thread correction'),
    ('scripts/apply_v50_hardware_cleanup.py','Missing v50 functional hardware cleanup'),
    ('scripts/apply_v50_nut_thread_fix.py','Missing v50 nut/thread correction'),
    ('scripts/apply_v50_lead_thread_master.py','Missing single-source RH8x2 lead-thread pass'),
    ('scripts/apply_v50_m4_thread_final_fix.py','Missing final printable rack M4 thread correction'),
    ('scripts/apply_v50_m4_pair_master.py','Missing matched rack M4 pair pass'),
    ('scripts/apply_v50_screw_hardware_cleanup.py','Missing final screw hardware cleanup'),
    ('scripts/apply_v50_rack_m4_nut_rebuild.py','Missing standalone rack M4 nut rebuild'),
    ('scripts/apply_v50_lead_hardware_final.py','Missing final v50 lead-hardware correction'),
    ('scripts/apply_v50_knob_retainer_thread_final.py','Missing final open RH8x2 knob-retainer thread rebuild'),
    ('scripts/apply_v50_true_rh8x2_threads_v54.py','Missing v54 true radial/axial RH8x2 thread generator'),
    ('scripts/apply_v50_thread_audit_final.py','Missing final all-thread open-bore/surface audit'),
    ('scripts/apply_v50_mounting_backstop.py','Missing integrated v50 mounting-backstop pass'),
    ('scripts/apply_v50_backstop_contact_side.py','Missing corrected backstop contact-side pass'),
    ('scripts/apply_v50_handed_base_export_final.py','Missing final explicit handed-base geometry/export correction'),
    ('scripts/apply_v50_rack_joint_v51.py','Missing v51 inverted rack-clevis refinement'),
    ('scripts/apply_v50_rack_joint_gusset_v52.py','Missing v52 teardrop Upper pivot-root reinforcement'),
]:
    q = Path(script_name)
    if not q.is_file():
        raise SystemExit(missing)
    exec(compile(q.read_text(encoding='utf-8'), str(q), 'exec'))

# Important: no global printability geometry rewrite here. Printability changes
# must remain local and may not replace proven rack roots, clamp kinematics or
# threaded hardware.
print('Restored proven v50 mechanics with true v54 RH8x2 profiles, final thread audit, corrected stop side, v51 rack joint and v52 Upper pivot gusset')
