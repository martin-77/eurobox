from pathlib import Path

# Final handed-base geometry/export correction.
#
# The earlier rear-backstop pass correctly declared handed LEFT/RIGHT bases,
# but used TopoShape.mirror() as an in-place operation. With the FreeCAD 1.1.3
# API used in CI that left the copied shape unchanged, so the published LEFT and
# RIGHT STL files were byte-identical even though the metadata claimed mirrored
# backstops. Build each handed backstop explicitly from the common symmetric
# core instead, then add an actual final-STL mirror regression gate.

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

old = '''MOUNT_BACKSTOP = fuse_all([\n    MOUNT_BACKSTOP_PANEL,\n    MOUNT_BACKSTOP_ROOT,\n    MOUNT_BACKSTOP_GUSSET,\n])\nBASE = BASE.fuse(MOUNT_BACKSTOP).removeSplitter()\n\n# Preserve both frozen rack-pin bores after every final BASE fusion.\nfor xc in CLAMP_X:\n    BASE = BASE.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))\nBASE = BASE.removeSplitter()\n\nif not BASE.isValid() or len(BASE.Solids) != 1:\n    raise RuntimeError('Rear-only mounting backstop did not fuse into one valid BASE solid')\n\n# The old universal BASE was X-symmetric and could simply be rotated 180 deg for\n# the left side. The rear-only stop breaks that symmetry. Keep BASE/BASE_RIGHT\n# as the right printable part and mirror X for a dedicated left printable BASE.\nBASE_RIGHT = BASE.copy()\nBASE_LEFT = BASE.copy()\nBASE_LEFT.mirror(App.Vector(0,0,0), App.Vector(1,0,0))\nif (not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1 or\n        abs(BASE_LEFT.Volume-BASE_RIGHT.Volume) > 1e-4):\n    raise RuntimeError('Mirrored LEFT rear-backstop BASE is not a valid handed copy')\n'''

new = '''# Preserve the finished symmetric pre-backstop BASE as the shared core.\nBASE_CORE = BASE.copy()\n\n# RIGHT printable backstop at local +X.\nMOUNT_BACKSTOP_RIGHT = fuse_all([\n    MOUNT_BACKSTOP_PANEL,\n    MOUNT_BACKSTOP_ROOT,\n    MOUNT_BACKSTOP_GUSSET,\n])\nBASE_RIGHT = BASE_CORE.fuse(MOUNT_BACKSTOP_RIGHT).removeSplitter()\nfor xc in CLAMP_X:\n    BASE_RIGHT = BASE_RIGHT.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))\nBASE_RIGHT = BASE_RIGHT.removeSplitter()\n\n# LEFT printable backstop is constructed explicitly at local -X. Do not rely\n# on TopoShape.mirror() side effects/return semantics: the prior implementation\n# exported an unchanged copy and produced byte-identical LEFT/RIGHT STLs.\nMOUNT_BACKSTOP_LEFT_X0 = -MOUNT_BACKSTOP_X1\nMOUNT_BACKSTOP_LEFT_X1 = -MOUNT_BACKSTOP_X0\nMOUNT_BACKSTOP_PANEL_LEFT = box(\n    MOUNT_BACKSTOP_LEFT_X0, MOUNT_BACKSTOP_Y0, MOUNT_BACKSTOP_Z0,\n    MOUNT_BACKSTOP_W_X, MOUNT_BACKSTOP_T_Y, MOUNT_BACKSTOP_H)\nMOUNT_BACKSTOP_ROOT_LEFT = box(\n    MOUNT_BACKSTOP_LEFT_X0, MOUNT_BACKSTOP_ROOT_Y0, MOUNT_BACKSTOP_ROOT_Z0,\n    MOUNT_BACKSTOP_W_X, MOUNT_BACKSTOP_ROOT_Y1-MOUNT_BACKSTOP_ROOT_Y0,\n    MOUNT_BACKSTOP_ROOT_Z1-MOUNT_BACKSTOP_ROOT_Z0)\n\n# Exact X-mirror of the RIGHT gusset profile, listed in reverse order so the\n# polygon keeps a clean winding before extrusion. The LEFT local rear clamp is\n# FRONT_CLAMP_X (-90); after the existing proper 180-degree assembly rotation\n# it becomes the same global +X rear clamp as on the RIGHT module.\nMOUNT_BACKSTOP_LEFT_REAR_ROOT_X1 = FRONT_CLAMP_X + ARM_W/2.0\n_mount_backstop_left_profile = [\n    App.Vector(MOUNT_BACKSTOP_LEFT_X1, MOUNT_BACKSTOP_GUSSET_Y0, 20.0),\n    App.Vector(MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1, MOUNT_BACKSTOP_GUSSET_Y0, 24.0),\n    App.Vector(MOUNT_BACKSTOP_LEFT_REAR_ROOT_X1, MOUNT_BACKSTOP_GUSSET_Y0, MOUNT_BACKSTOP_GUSSET_TOP_Z),\n    App.Vector(MOUNT_BACKSTOP_LEFT_X0, MOUNT_BACKSTOP_GUSSET_Y0, MOUNT_BACKSTOP_GUSSET_TOP_Z),\n    App.Vector(MOUNT_BACKSTOP_LEFT_X0, MOUNT_BACKSTOP_GUSSET_Y0, 7.0),\n    App.Vector(MOUNT_BACKSTOP_LEFT_X1, MOUNT_BACKSTOP_GUSSET_Y0, 7.0),\n]\n_mount_backstop_left_wire = Part.makePolygon(\n    _mount_backstop_left_profile + [_mount_backstop_left_profile[0]])\nMOUNT_BACKSTOP_GUSSET_LEFT = Part.Face(_mount_backstop_left_wire).extrude(\n    App.Vector(0, MOUNT_BACKSTOP_GUSSET_Y1-MOUNT_BACKSTOP_GUSSET_Y0, 0))\nMOUNT_BACKSTOP_LEFT = fuse_all([\n    MOUNT_BACKSTOP_PANEL_LEFT,\n    MOUNT_BACKSTOP_ROOT_LEFT,\n    MOUNT_BACKSTOP_GUSSET_LEFT,\n])\nBASE_LEFT = BASE_CORE.fuse(MOUNT_BACKSTOP_LEFT).removeSplitter()\nfor xc in CLAMP_X:\n    BASE_LEFT = BASE_LEFT.cut(cyl_x(PIN_HOLE_D/2.0, 40.0, xc-20.0, PIN_Y, PIN_Z))\nBASE_LEFT = BASE_LEFT.removeSplitter()\n\n# Canonical legacy BASE remains the RIGHT version for existing source checks and\n# links. Explicit handed files are exported through PARTS below.\nBASE = BASE_RIGHT\n\n_left_rear_root_ref = make_i_beam_y(FRONT_CLAMP_X, -8.0, 36.0)\n_left_front_root_ref = make_i_beam_y(REAR_CLAMP_X, -8.0, 36.0)\nMOUNT_BACKSTOP_LEFT_REAR_ROOT_OVERLAP_MM3 = MOUNT_BACKSTOP_GUSSET_LEFT.common(_left_rear_root_ref).Volume\nMOUNT_BACKSTOP_LEFT_FRONT_ROOT_OVERLAP_MM3 = MOUNT_BACKSTOP_GUSSET_LEFT.common(_left_front_root_ref).Volume\n\nif (not BASE_RIGHT.isValid() or len(BASE_RIGHT.Solids) != 1 or\n        not BASE_LEFT.isValid() or len(BASE_LEFT.Solids) != 1):\n    raise RuntimeError('Explicit handed rear-backstop BASE is not one valid solid per side')\nif abs(BASE_LEFT.Volume-BASE_RIGHT.Volume) > 1e-4:\n    raise RuntimeError('Explicit LEFT/RIGHT rear-backstop BASE volumes differ')\nif BASE_RIGHT.BoundBox.XMax < 180.0 or BASE_LEFT.BoundBox.XMin > -180.0:\n    raise RuntimeError('Explicit handed BASE backstops are not on opposite local X ends')\n'''

if old not in s:
    raise SystemExit('Could not locate stale in-place handed BASE mirror block')
s = s.replace(old, new, 1)

# Add truthful source witnesses for both explicitly constructed connections.
old_meta = "    'front_i_beam_root_overlap_mm3': round(MOUNT_BACKSTOP_FRONT_ROOT_OVERLAP_MM3, 6),\n    'left_right_base_volume_delta_mm3': round(abs(BASE_LEFT.Volume-BASE_RIGHT.Volume), 6),\n"
new_meta = old_meta.replace(
    "    'left_right_base_volume_delta_mm3'",
    "    'left_rear_i_beam_root_overlap_mm3': round(MOUNT_BACKSTOP_LEFT_REAR_ROOT_OVERLAP_MM3, 3),\n"
    "    'left_front_i_beam_root_overlap_mm3': round(MOUNT_BACKSTOP_LEFT_FRONT_ROOT_OVERLAP_MM3, 6),\n"
    "    'right_base_x_bounds_mm': [round(BASE_RIGHT.BoundBox.XMin, 3), round(BASE_RIGHT.BoundBox.XMax, 3)],\n"
    "    'left_base_x_bounds_mm': [round(BASE_LEFT.BoundBox.XMin, 3), round(BASE_LEFT.BoundBox.XMax, 3)],\n"
    "    'left_right_base_volume_delta_mm3'"
)
if old_meta not in s:
    raise SystemExit('Could not locate mounting-backstop validation metadata anchor')
s = s.replace(old_meta, new_meta, 1)

gate_anchor = '''if V['mounting_backstop']['front_i_beam_root_overlap_mm3'] > 1e-4:\n    failures.append('RIGHT rear mounting backstop incorrectly reaches the front I-beam root')\n'''
extra_gates = gate_anchor + '''if V['mounting_backstop']['left_rear_i_beam_root_overlap_mm3'] < 1000.0:\n    failures.append('LEFT rear mounting backstop does not substantially overlap its local rear I-beam root')\nif V['mounting_backstop']['left_front_i_beam_root_overlap_mm3'] > 1e-4:\n    failures.append('LEFT rear mounting backstop incorrectly reaches its local front I-beam root')\nif V['mounting_backstop']['right_base_x_bounds_mm'][1] < 180.0:\n    failures.append('RIGHT printable BASE has no rear +X backstop envelope')\nif V['mounting_backstop']['left_base_x_bounds_mm'][0] > -180.0:\n    failures.append('LEFT printable BASE has no mirrored rear -X backstop envelope')\n'''
if gate_anchor not in s:
    raise SystemExit('Could not locate mounting-backstop right-root gate')
s = s.replace(gate_anchor, extra_gates, 1)

p.write_text(s, encoding='utf-8')
print('Applied final handed BASE geometry: explicit LEFT/RIGHT backstops, no ambiguous TopoShape.mirror()')

# Harden the final STL validator so metadata can never hide identical handed
# outputs again. This runs on the exact STL files that are later published.
vp = Path('scripts/validate_meshes.py')
vs = vp.read_text(encoding='utf-8')
vorig = vs
marker = '# Final handed-base pair regression gate.'
if marker not in vs:
    write_anchor = "with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:\n"
    if write_anchor not in vs:
        raise SystemExit('Could not locate mesh-validation report writer')
    handed_gate = r'''# Final handed-base pair regression gate.
# RIGHT and LEFT must be distinct printable meshes and exact X mirrors of each
# other. This specifically catches the FreeCAD mirror-API regression where both
# published files were byte-identical despite correct metadata.
import hashlib
right_base_path=os.path.join(out,'eurobox_v50_base_right.stl')
left_base_path=os.path.join(out,'eurobox_v50_base_left.stl')
if not (os.path.exists(right_base_path) and os.path.exists(left_base_path)):
    failed.extend([n for n in ('eurobox_v50_base_right.stl','eurobox_v50_base_left.stl') if n not in failed])
    results['handed_base_pair']={'ok':False,'reason':'explicit LEFT/RIGHT base STL missing'}
else:
    def _sha256(path):
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024), b''):
                h.update(chunk)
        return h.hexdigest()
    rm=trimesh.load(right_base_path, force='mesh', process=True)
    lm=trimesh.load(left_base_path, force='mesh', process=True)
    rsha=_sha256(right_base_path)
    lsha=_sha256(left_base_path)
    rb=np.asarray(rm.bounds,dtype=float)
    lb=np.asarray(lm.bounds,dtype=float)
    rv=np.unique(np.round(np.asarray(rm.vertices,dtype=float),4),axis=0)
    lv=np.asarray(lm.vertices,dtype=float).copy(); lv[:,0]*=-1.0
    lv=np.unique(np.round(lv,4),axis=0)
    def _sort_rows(a):
        return a[np.lexsort((a[:,2],a[:,1],a[:,0]))]
    vertex_mirror_ok=(rv.shape==lv.shape and np.allclose(_sort_rows(rv),_sort_rows(lv),atol=0.015,rtol=0.0))
    bounds_mirror_ok=(
        abs(rb[0,0]+lb[1,0]) <= 0.02 and
        abs(rb[1,0]+lb[0,0]) <= 0.02 and
        np.allclose(rb[:,1:],lb[:,1:],atol=0.02,rtol=0.0)
    )
    distinct_files=(rsha != lsha)
    side_envelopes=(rb[1,0] >= 180.0 and lb[0,0] <= -180.0 and rb[0,0] > -120.0 and lb[1,0] < 120.0)
    handed_ok=bool(distinct_files and bounds_mirror_ok and vertex_mirror_ok and side_envelopes)
    results['handed_base_pair']={
        'ok':handed_ok,
        'right_sha256':rsha,
        'left_sha256':lsha,
        'distinct_file_bytes':distinct_files,
        'right_bounds_mm':rb.tolist(),
        'left_bounds_mm':lb.tolist(),
        'bounds_are_x_mirrors':bool(bounds_mirror_ok),
        'unique_vertex_clouds_are_x_mirrors':bool(vertex_mirror_ok),
        'rear_stop_envelopes_on_opposite_local_x_ends':bool(side_envelopes),
        'assembly_meaning':'RIGHT local +X rear; LEFT local -X rear, then 180deg Z rotation -> both global +X rear',
    }
    if not handed_ok:
        for n in ('eurobox_v50_base_right.stl','eurobox_v50_base_left.stl'):
            if n not in failed:
                failed.append(n)

'''
    vs = vs.replace(write_anchor, handed_gate + write_anchor, 1)

if vs == vorig:
    raise SystemExit('Handed-base STL regression gate made no change')
vp.write_text(vs, encoding='utf-8')
print('Hardened mesh validation: LEFT/RIGHT base STLs must be distinct exact X mirrors')
