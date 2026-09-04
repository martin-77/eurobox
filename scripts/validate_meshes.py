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
    m=trimesh.load(p, force='mesh', process=True)
    name=os.path.basename(p)
    components=list(m.split(only_watertight=False))
    signed_volumes=[float(c.volume) for c in components]
    positive=sum(v > 1e-6 for v in signed_volumes)
    negative=sum(v < -1e-6 for v in signed_volumes)
    near_zero=len(signed_volumes)-positive-negative

    # A BRep solid with enclosed voids legitimately tessellates into multiple
    # disconnected *surface shells*: one outward shell plus inward-oriented
    # cavity shells. Do not confuse that with multiple disconnected printed
    # bodies. Multiple positive-volume shells are still rejected.
    shells_form_one_body = (
        len(components) == 1 or
        (positive == 1 and negative == len(components)-1 and near_zero == 0)
    )

    info={
        'watertight': bool(m.is_watertight),
        'winding_consistent': bool(m.is_winding_consistent),
        'surface_shells': int(len(components)),
        'shells_form_one_body': bool(shells_form_one_body),
        'component_faces': [int(len(c.faces)) for c in components],
        'component_signed_volume_mm3': signed_volumes,
        'component_bounds_mm': [
            [[float(x) for x in row] for row in c.bounds.tolist()]
            for c in components
        ],
        'faces': int(len(m.faces)),
        'vertices': int(len(m.vertices)),
        'volume_mm3': float(abs(m.volume)),
        'bounds_mm': [[float(x) for x in row] for row in m.bounds.tolist()],
    }
    results[name]=info
    if (not info['watertight'] or
        not info['winding_consistent'] or
        not info['shells_form_one_body'] or
        info['volume_mm3'] <= 0):
        failed.append(name)

with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:
    json.dump({'meshes':results,'failed':failed},f,indent=2)
summary={'directory':out_arg,'count':len(results),'failed':failed}
print(json.dumps(summary,indent=2))
if failed:
    print('FAILED_MESH_DETAILS='+json.dumps({n:results[n] for n in failed},indent=2))
    raise SystemExit('Mesh validation failed: '+', '.join(failed))
