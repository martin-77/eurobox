import FreeCAD as App, Part, json, os, traceback
ns = {'__name__':'__main__','__file__':os.path.join(os.path.dirname(__file__),'build_v50.py')}
err = None
try:
    code = compile(open(ns['__file__']).read(), ns['__file__'], 'exec')
    exec(code, ns)
except BaseException as e:
    err = repr(e)

out = ns.get('OUT', os.path.join(os.path.dirname(__file__),'..','build_v50'))
os.makedirs(out, exist_ok=True)
base = ns.get('BASE')
report = {'caught_build_error':err}
if base is not None:
    report.update({
        'base_is_valid':base.isValid(),
        'base_solids':len(base.Solids),
        'base_shells':len(base.Shells),
        'base_faces':len(base.Faces),
        'base_volume_mm3':base.Volume,
        'base_bbox':[base.BoundBox.XMin,base.BoundBox.XMax,base.BoundBox.YMin,base.BoundBox.YMax,base.BoundBox.ZMin,base.BoundBox.ZMax],
        'solid_components':[]
    })
    for i,s in enumerate(base.Solids):
        report['solid_components'].append({
            'i':i,
            'valid':s.isValid(),
            'volume_mm3':s.Volume,
            'bbox':[s.BoundBox.XMin,s.BoundBox.XMax,s.BoundBox.YMin,s.BoundBox.YMax,s.BoundBox.ZMin,s.BoundBox.ZMax],
            'faces':len(s.Faces)
        })
    try:
        base.exportBrep(os.path.join(out,'DEBUG_v50_base.brep'))
    except Exception as e:
        report['brep_export_error']=repr(e)
    try:
        report['check_text']=base.check(True)
    except Exception as e:
        report['check_error']=repr(e)
with open(os.path.join(out,'BASE_DEBUG_v50.json'),'w') as f:
    json.dump(report,f,indent=2,default=str)
print('BASE_DEBUG='+json.dumps(report,default=str))
