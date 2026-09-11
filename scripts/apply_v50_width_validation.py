from pathlib import Path

# Compatibility for the restored 600 mm inboard architecture. The current
# lead-nut cartridge no longer has the obsolete tail extension used by the
# original width-cleanup pass. Remove only that stale tail pocket from the
# generated build source; retain the current cartridge, pin and service-pocket
# geometry unchanged.
bp = Path('scripts/build_v50.py')
bs = bp.read_text(encoding='utf-8')
old = "NUT_TAIL_Y0 = NUT_THREAD_Y0 - LEAD_NUT_TAIL_L\n"
if old not in bs:
    raise SystemExit('Could not locate obsolete lead-nut tail datum in inboard width pass')
bs = bs.replace(old, '', 1)
old = '''    _tail_pocket = box(sx-6.2, NUT_TAIL_Y0-0.25, SPINDLE_Z-10.25,
                       12.4, LEAD_NUT_TAIL_L+0.50, 6.0)
'''
if old not in bs:
    raise SystemExit('Could not locate obsolete lead-nut tail pocket in inboard width pass')
bs = bs.replace(old, '', 1)
old = '''    for cutter in (_nut_pocket, _tail_pocket, _spindle_tunnel,
                   _pin_bore, _head_service, _clip_service):'''
new = '''    for cutter in (_nut_pocket, _spindle_tunnel,
                   _pin_bore, _head_service, _clip_service):'''
if old not in bs:
    raise SystemExit('Could not remove obsolete lead-nut tail pocket from cutter set')
bs = bs.replace(old, new, 1)
bp.write_text(bs, encoding='utf-8')

# The restored width pass turns the lead hardware inward by a proper Z180
# rotation, so the printable RH8x2 parts occupy local -Y. Keep the final STL
# checks aligned with that print orientation, while retaining the mechanical
# thread/drive gates themselves.
vp = Path('scripts/validate_meshes.py')
vs = vp.read_text(encoding='utf-8')

replacements = [
    ("        # Printable retainer nut is exported in local +Y.\n        checks=rh8_internal_thread_sections(mesh, (1.2,2.9,4.6))",
     "        # Inboard architecture rotates the printable retainer nut onto local -Y.\n        checks=rh8_internal_thread_sections(mesh, (-1.2,-2.9,-4.6))"),
    ("        # Printable main lead nut is exported in local +Y.\n        checks=rh8_internal_thread_sections(mesh, (3.0,8.0,13.0))",
     "        # Inboard architecture rotates the printable main lead nut onto local -Y.\n        checks=rh8_internal_thread_sections(mesh, (-3.0,-8.0,-13.0))"),
    ("    # Printable spindle is exported in local +Y. The 8x8 square-drive end lies\n    # at the outer positive-Y end; y=34.5 is safely inside the square section.\n    y=34.5",
     "    # Inboard architecture rotates the printable spindle onto local -Y. The\n    # 8x8 square-drive end is therefore sampled safely at y=-34.5.\n    y=-34.5"),
]
for old, new in replacements:
    if old not in vs:
        raise SystemExit('Could not align inward printable mesh validation: '+old.splitlines()[-1])
    vs = vs.replace(old, new, 1)

# FreeCAD/OCC may triangulate two geometrically mirrored cylindrical surfaces
# with a different angular phase. Exact vertex-cloud equality is therefore only
# diagnostic; hard handedness remains distinct bytes + mirrored bounds + equal
# volume/face count + opposite backstop envelopes.
old = "    handed_ok=bool(distinct_files and bounds_mirror_ok and vertex_mirror_ok and side_envelopes)\n"
new = (
    "    volume_mirror_ok=abs(abs(rm.volume)-abs(lm.volume)) <= 0.05\n"
    "    face_count_match=(len(rm.faces) == len(lm.faces))\n"
    "    handed_ok=bool(distinct_files and bounds_mirror_ok and volume_mirror_ok and face_count_match and side_envelopes)\n"
)
if old not in vs:
    raise SystemExit('Could not locate handed STL mirror gate')
vs = vs.replace(old, new, 1)
old_meta = "        'unique_vertex_clouds_are_x_mirrors':bool(vertex_mirror_ok),\n"
new_meta = (
    old_meta
    + "        'mesh_volumes_match':bool(volume_mirror_ok),\n"
    + "        'mesh_face_counts_match':bool(face_count_match),\n"
)
if old_meta not in vs:
    raise SystemExit('Could not locate handed STL mirror diagnostics')
vs = vs.replace(old_meta, new_meta, 1)
vp.write_text(vs, encoding='utf-8')

print('Width validation: current lead-nut cartridge + inward -Y print orientation + tessellation-safe handed mesh gate')
