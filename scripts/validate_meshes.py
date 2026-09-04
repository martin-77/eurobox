import glob, json, os, sys, trimesh
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out_arg=sys.argv[1] if len(sys.argv)>1 else 'build'
out=os.path.join(root,out_arg)
results={}
failed=[]
paths=sorted(glob.glob(os.path.join(out,'*.stl')))
if not paths:
    raise SystemExit('No STL files found in '+out)
for p in paths:
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
    if not info['watertight'] or not info['winding_consistent'] or info['components'] != 1 or info['volume_mm3'] <= 0:
        failed.append(name)
with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:
    json.dump({'meshes':results,'failed':failed},f,indent=2)
print(json.dumps({'directory':out_arg,'count':len(results),'failed':failed},indent=2))
if failed:
    raise SystemExit('Mesh validation failed: '+', '.join(failed))
