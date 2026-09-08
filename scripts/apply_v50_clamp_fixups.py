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

reinforcement = Path('scripts/apply_v50_rack_root_reinforcement.py')
if not reinforcement.is_file():
    raise SystemExit('Missing rack-root reinforcement fixup')
exec(compile(reinforcement.read_text(encoding='utf-8'), str(reinforcement), 'exec'))

rack_lock = Path('scripts/apply_v50_rack_lock.py')
if not rack_lock.is_file():
    raise SystemExit('Missing rack-lock fixup')
exec(compile(rack_lock.read_text(encoding='utf-8'), str(rack_lock), 'exec'))

massive_closure = Path('scripts/apply_v50_rack_closure_massive.py')
if not massive_closure.is_file():
    raise SystemExit('Missing continuous rack-closure fixup')
exec(compile(massive_closure.read_text(encoding='utf-8'), str(massive_closure), 'exec'))

female_threads = Path('scripts/apply_v50_rack_female_threads.py')
if not female_threads.is_file():
    raise SystemExit('Missing rack female-thread correction')
exec(compile(female_threads.read_text(encoding='utf-8'), str(female_threads), 'exec'))

hardware_cleanup = Path('scripts/apply_v50_hardware_cleanup.py')
if not hardware_cleanup.is_file():
    raise SystemExit('Missing v50 functional hardware cleanup')
exec(compile(hardware_cleanup.read_text(encoding='utf-8'), str(hardware_cleanup), 'exec'))

nut_thread_fix = Path('scripts/apply_v50_nut_thread_fix.py')
if not nut_thread_fix.is_file():
    raise SystemExit('Missing v50 nut/thread correction')
exec(compile(nut_thread_fix.read_text(encoding='utf-8'), str(nut_thread_fix), 'exec'))

lead_thread_master = Path('scripts/apply_v50_lead_thread_master.py')
if not lead_thread_master.is_file():
    raise SystemExit('Missing single-source RH8x2 lead-thread pass')
exec(compile(lead_thread_master.read_text(encoding='utf-8'), str(lead_thread_master), 'exec'))

m4_thread_final = Path('scripts/apply_v50_m4_thread_final_fix.py')
if not m4_thread_final.is_file():
    raise SystemExit('Missing final printable rack M4 thread correction')
exec(compile(m4_thread_final.read_text(encoding='utf-8'), str(m4_thread_final), 'exec'))

m4_pair_master = Path('scripts/apply_v50_m4_pair_master.py')
if not m4_pair_master.is_file():
    raise SystemExit('Missing matched rack M4 pair pass')
exec(compile(m4_pair_master.read_text(encoding='utf-8'), str(m4_pair_master), 'exec'))

# Final architecture pass: screws stay screws, all threaded nuts stay separate.
screw_cleanup = Path('scripts/apply_v50_screw_hardware_cleanup.py')
if not screw_cleanup.is_file():
    raise SystemExit('Missing final screw hardware cleanup')
exec(compile(screw_cleanup.read_text(encoding='utf-8'), str(screw_cleanup), 'exec'))

# Absolute final rack-M4 nut pass: keep the final nut as a native FreeCAD/OCC
# boolean (7 mm AF hex minus the open radial-Z M4x0.7 cutter). The standalone
# SCAD remains a printable/reference source but is deliberately not imported
# back through importCSG, which can split the valid mesh into multiple solids.
rack_m4_nut_rebuild = Path('scripts/apply_v50_rack_m4_nut_rebuild.py')
if not rack_m4_nut_rebuild.is_file():
    raise SystemExit('Missing standalone rack M4 nut rebuild')
exec(compile(rack_m4_nut_rebuild.read_text(encoding='utf-8'), str(rack_m4_nut_rebuild), 'exec'))

# Absolute final box-clamp lead-hardware pass. This runs after all earlier
# architecture experiments so obsolete pin/clip and retainer-thread geometry
# cannot be reintroduced by a later patch.
lead_hardware_final = Path('scripts/apply_v50_lead_hardware_final.py')
if not lead_hardware_final.is_file():
    raise SystemExit('Missing final v50 lead-hardware correction')
exec(compile(lead_hardware_final.read_text(encoding='utf-8'), str(lead_hardware_final), 'exec'))

# Rebuild the separate knob retainer one final time with the same open-ended
# thread strategy that made the rack M4 nut reliable: one full pitch of cutter
# overrun beyond both faces. Tangent entry-cone booleans are deliberately
# omitted because they made the otherwise-valid BRep non-manifold after STL
# tessellation. The RH8x2 pitch, phase and engagement checks stay unchanged.
knob_retainer_thread_final = Path('scripts/apply_v50_knob_retainer_thread_final.py')
if not knob_retainer_thread_final.is_file():
    raise SystemExit('Missing final open RH8x2 knob-retainer thread rebuild')
exec(compile(knob_retainer_thread_final.read_text(encoding='utf-8'),
             str(knob_retainer_thread_final), 'exec'))

# Final mounting-aid pass. It runs last against the finished reinforced BASE.
# v50 now freezes -X=front and +X=rear and creates exactly one stop behind the
# rear clamp, with a deep root and gusset into the rear I-beam only. Existing
# lower-clamp, pin, tube and mesh checks remain authoritative.
mounting_backstop = Path('scripts/apply_v50_mounting_backstop.py')
if not mounting_backstop.is_file():
    raise SystemExit('Missing integrated v50 mounting-backstop pass')
exec(compile(mounting_backstop.read_text(encoding='utf-8'), str(mounting_backstop), 'exec'))

# Absolute final handed-base correction. FreeCAD 1.1.3 did not mutate the copied
# TopoShape via the previous mirror call, which made LEFT/RIGHT STL exports
# byte-identical. Construct both handed backstops explicitly from the symmetric
# core and add a final-STL X-mirror regression gate to validate_meshes.py.
handed_base_final = Path('scripts/apply_v50_handed_base_export_final.py')
if not handed_base_final.is_file():
    raise SystemExit('Missing final explicit handed-base geometry/export correction')
exec(compile(handed_base_final.read_text(encoding='utf-8'), str(handed_base_final), 'exec'))

# Absolute final manufacturing pass: close the long load paths for slicer infill,
# make the box-side crosshead/upper clamp transitions self-supporting in the
# upside-down print orientation, lower the outer guide/cage to the common bed
# plane and move the lead-nut retaining pin to a lower post-thread tail.
printability_final = Path('scripts/apply_v50_printability_final.py')
if not printability_final.is_file():
    raise SystemExit('Missing final v50 printability correction')
exec(compile(printability_final.read_text(encoding='utf-8'), str(printability_final), 'exec'))

# The printability pass moves the lead-nut cross-pin and adds its BASE bores
# before the lead-nut object itself is defined. Hoist the three pin datums into
# the design-parameter block so build_v50.py can use them while constructing BASE.
# The later identical assignments remain as local documentation and are harmless.
p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
first_use = s.find('BASE = BASE.cut(cyl_x(LEAD_NUT_PIN_HOLE_D/2.0')
first_def = s.find('LEAD_NUT_PIN_HOLE_D = 3.4')
if first_use < 0 or first_def < 0:
    raise SystemExit('Could not locate lower lead-nut pin use/definition after printability pass')
if first_def > first_use:
    anchor = 'CAGE_Y1 = 282.20\n'
    if anchor not in s:
        raise SystemExit('Could not locate final cage datum for lead-nut pin hoist')
    hoisted = (
        anchor +
        'LEAD_NUT_PIN_HOLE_D = 3.4\n' +
        'LEAD_NUT_PIN_Y = NUT_THREAD_LEN + 2.75\n' +
        'LEAD_NUT_PIN_Z = -7.25\n'
    )
    s = s.replace(anchor, hoisted, 1)
    p.write_text(s, encoding='utf-8')
    first_def = s.find('LEAD_NUT_PIN_HOLE_D = 3.4')
if first_def > first_use:
    raise SystemExit('Lead-nut pin datums are still defined after their first BASE use')
print('Hoisted lower lead-nut pin datums before BASE construction')

# CI trigger anchor: support-minimised handed v50 BASE + manifold functional hardware.
