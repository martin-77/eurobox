import glob, json, os, sys, subprocess
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
    comps=m.split(only_watertight=False)
    return m, {
        'watertight': bool(m.is_watertight),
        'winding_consistent': bool(m.is_winding_consistent),
        # Surface-shell count is diagnostic, NOT a body-count gate. A single
        # OCC solid with enclosed cavities legitimately exports as one outer
        # shell plus one or more inner closed shells in STL. The upstream CAD
        # gate already requires source_solids==1 and STEP solids==1.
        'surface_shells': int(len(comps)),
        'surface_shell_volumes_signed_mm3': [float(c.volume) for c in comps],
        'faces': int(len(m.faces)),
        'volume_mm3': float(abs(m.volume)),
        'bounds_mm': [[float(x) for x in row] for row in m.bounds.tolist()],
    }


def good(info):
    return (info['watertight'] and info['winding_consistent'] and
            info['volume_mm3'] > 0)


def trimesh_cleanup(path):
    m=trimesh.load(path, force='mesh', process=True)
    # Merge only sub-micron CAD seam duplicates; do not alter design geometry.
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
    outstl=path+'.cgal.stl'
    scad=path+'.normalize.scad'
    src=os.path.abspath(path).replace('\\','/')
    with open(scad,'w') as f:
        f.write('render(convexity=30) import("'+src+'", convexity=30);\n')
    try:
        cp=subprocess.run(['openscad','-o',outstl,scad], stdout=subprocess.PIPE,
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
    json.dump({'meshes':results,'failed':failed,
               'note':'surface_shells is diagnostic; source/STEP single-solid checks are the body connectivity authority'},f,indent=2)

print(json.dumps({'directory':out_arg,'count':len(results),'failed':failed,
                  'failed_details':{n:results[n] for n in failed}},indent=2))
if failed:
    raise SystemExit('Mesh validation failed: '+', '.join(failed))
