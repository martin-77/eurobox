import glob, json, os, trimesh
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out=os.path.join(root,'build')
results={}
failed=[]
for p in sorted(glob.glob(os.path.join(out,'*.stl'))):
    m=trimesh.load(p, force='mesh')
    name=os.path.basename(p)
    info={
        'watertight': bool(m.is_watertight),
        'winding_consistent': bool(m.is_winding_consistent),
        'components': int(len(m.split(only_watertight=False))),
        'faces': int(len(m.faces)),
        'volume_mm3': float(abs(m.volume)),
        'bounds_mm': [[float(x) for x in row] for row in m.bounds.tolist()],
    }
    results[name]=info
    if not info['watertight'] or not info['winding_consistent'] or info['components'] != 1:
        failed.append(name)
with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:
    json.dump({'meshes':results,'failed':failed},f,indent=2)
print(json.dumps({'count':len(results),'failed':failed},indent=2))
if failed:
    raise SystemExit('Mesh validation failed: '+', '.join(failed))
