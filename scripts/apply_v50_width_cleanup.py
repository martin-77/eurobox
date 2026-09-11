# Width cleanup intentionally performs no geometry rewrite.
#
# The previous pass rebuilt the proven box-clamp mechanism inboard and caused
# multiple mechanical regressions (weakened base regions, altered clamp thrust
# geometry, extra service holes and reoriented threaded hardware). Width is now
# handled only after the restored mechanism has passed its functional gates.
#
# The handed-base fixup adds a final STL regression gate. Do not require exact
# mirrored vertex clouds there: FreeCAD/OCC can tessellate geometrically
# symmetric cylindrical faces with different triangle phase, so equivalent
# mirrored BReps need not have identical STL vertex coordinates. Keep the hard
# guarantees that caught the original regression: distinct files, mirrored
# envelopes, equal mesh volume/face count and opposite handed backstop sides.
from pathlib import Path

vp = Path('scripts/validate_meshes.py')
vs = vp.read_text(encoding='utf-8')
old = "    handed_ok=bool(distinct_files and bounds_mirror_ok and vertex_mirror_ok and side_envelopes)\n"
new = (
    "    volume_mirror_ok=abs(abs(rm.volume)-abs(lm.volume)) <= 0.05\n"
    "    face_count_match=(len(rm.faces) == len(lm.faces))\n"
    "    handed_ok=bool(distinct_files and bounds_mirror_ok and volume_mirror_ok and face_count_match and side_envelopes)\n"
)
if old not in vs:
    raise SystemExit('Could not locate handed STL mirror gate for tessellation-safe cleanup')
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

print('Width cleanup: geometry rewrite disabled; preserve proven clamp mechanics')
print('Mesh cleanup: handed STL gate is robust to equivalent OCC tessellation')
