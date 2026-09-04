import glob, json, os, sys, tempfile, subprocess, shutil
import trimesh

root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out_arg=sys.argv[1] if len(sys.argv)>1 else 'build'
out=os.path.join(root,out_arg)
results={}
failed=[]
paths=sorted(glob.glob(os.path.join(out,'*.stl')))
if not paths:
    raise SystemExit('No STL files found in '+out)


def inspect(path):
    m=trimesh.load(path, force='mesh', process=True)
    return m, {
        'watertight': bool(m.is_watertight),
        'winding_consistent': bool(m.is_winding_consistent),
        'components': int(len(m.split(only_watertight=False))),
        'faces': int(len(m.faces)),
        'volume_mm3': float(abs(m.volume)),
        'bounds_mm': [[float(x) for x in row] for row in m.bounds.tolist()],
    }


def good(info):
    return (info['watertight'] and info['winding_consistent'] and
            info['components'] == 1 and info['volume_mm3'] > 0)


def trimesh_cleanup(path):
    m=trimesh.load(path, force='mesh', process=True)
    # CAD face tessellations can leave coincident seam vertices which are
    # topologically separate in STL. Merge only at 1e-5 mm precision: far
    # below FDM tolerances and therefore not a dimensional repair.
    m.merge_vertices(digits_vertex=5)
    try:
        m.update_faces(m.unique_faces())
    except Exception:
        pass
    m.remove_unreferenced_vertices()
    try:
        trimesh.repair.fix_normals(m, multibody=True)
    except TypeError:
        trimesh.repair.fix_normals(m)
    tmp=path+'.trimesh.stl'
    m.export(tmp)
    _, info=inspect(tmp)
    if good(info):
        os.replace(tmp,path)
        return True, info
    if os.path.exists(tmp):
        os.unlink(tmp)
    return False, info


def openscad_normalize(path):
    # CGAL re-union is a second, geometry-preserving topology normalization.
    # It is used only if the sub-micron seam merge above is insufficient.
    outstl=path+'.cgal.stl'
    scad=path+'.normalize.scad'
    src=os.path.abspath(path).replace('\\','/')
    dst=os.path.abspath(outstl)
    with open(scad,'w') as f:
        f.write('render(convexity=20) import("'+src+'", convexity=20);\n')
    try:
        cp=subprocess.run(['openscad','-o',dst,scad], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, timeout=300)
        if cp.returncode != 0 or not os.path.exists(outstl) or os.path.getsize(outstl)==0:
            return False, {'openscad_log': cp.stdout[-4000:]}
        _, info=inspect(outstl)
        if good(info):
            os.replace(outstl,path)
            return True, info
        return False, info
    finally:
        for q in (scad,outstl):
            if os.path.exists(q):
                os.unlink(q)

for p in paths:
    name=os.path.basename(p)
    _, before=inspect(p)
    info=dict(before)
    info['normalization']='none'

    if not good(before):
        ok, after=trimesh_cleanup(p)
        info['trimesh_cleanup_result']=after
        if ok:
            _, info2=inspect(p)
            info.update(info2)
            info['normalization']='trimesh_seam_merge_1e-5mm'
        else:
            ok2, after2=openscad_normalize(p)
            info['openscad_cleanup_result']=after2
            if ok2:
                _, info2=inspect(p)
                info.update(info2)
                info['normalization']='openscad_cgal_render'

    results[name]=info
    if not good(info):
        failed.append(name)

with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:
    json.dump({'meshes':results,'failed':failed},f,indent=2)

print(json.dumps({'directory':out_arg,'count':len(results),'failed':failed,
                  'failed_details':{n:results[n] for n in failed}},indent=2))
if failed:
    raise SystemExit('Mesh validation failed: '+', '.join(failed))
