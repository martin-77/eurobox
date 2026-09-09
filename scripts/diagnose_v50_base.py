import FreeCAD as App, Part, json, os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
out = os.path.join(root, 'build_v50')
os.makedirs(out, exist_ok=True)
validation_path = os.path.join(out, 'VALIDATION_v50_source.json')
report_path = os.path.join(out, 'BASE_DEBUG_v50.json')

# If the main CAD build reached source validation, BASE was already constructed
# and the actionable failure list is available. Re-running the entire FreeCAD
# model here adds several minutes but cannot improve that diagnosis.
if os.path.isfile(validation_path) and os.path.getsize(validation_path) > 0:
    with open(validation_path, encoding='utf-8') as f:
        validation = json.load(f)
    report = {
        'rebuild_skipped': True,
        'reason': 'main build already reached source validation',
        'source_failures': validation.get('failures', []),
        'base_box_rim_common_mm3': validation.get('base_box_rim_common_mm3'),
        'plate_motion': validation.get('plate_motion'),
        'thread_kinematics': validation.get('thread_kinematics'),
        'lead_nut_checks': validation.get('lead_nut_checks'),
        'printability': validation.get('printability'),
        'handed_base_geometry': validation.get('handed_base_geometry'),
    }
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print('BASE_DEBUG=' + json.dumps(report, default=str))
    raise SystemExit(0)

# Early CAD/topology failures may occur before source validation exists. Only in
# that case rebuild under a namespace so we can capture the last available BASE
# shape and export a diagnostic BRep.
ns = {
    '__name__': '__main__',
    '__file__': os.path.join(os.path.dirname(__file__), 'build_v50.py'),
}
err = None
try:
    code = compile(open(ns['__file__'], encoding='utf-8').read(), ns['__file__'], 'exec')
    exec(code, ns)
except BaseException as e:
    err = repr(e)

out = ns.get('OUT', out)
os.makedirs(out, exist_ok=True)
base = ns.get('BASE')
report = {'caught_build_error': err, 'rebuild_skipped': False}
if base is not None:
    report.update({
        'base_is_valid': base.isValid(),
        'base_solids': len(base.Solids),
        'base_shells': len(base.Shells),
        'base_faces': len(base.Faces),
        'base_volume_mm3': base.Volume,
        'base_bbox': [
            base.BoundBox.XMin, base.BoundBox.XMax,
            base.BoundBox.YMin, base.BoundBox.YMax,
            base.BoundBox.ZMin, base.BoundBox.ZMax,
        ],
        'solid_components': [],
    })
    for i, solid in enumerate(base.Solids):
        report['solid_components'].append({
            'i': i,
            'valid': solid.isValid(),
            'volume_mm3': solid.Volume,
            'bbox': [
                solid.BoundBox.XMin, solid.BoundBox.XMax,
                solid.BoundBox.YMin, solid.BoundBox.YMax,
                solid.BoundBox.ZMin, solid.BoundBox.ZMax,
            ],
            'faces': len(solid.Faces),
        })
    try:
        base.exportBrep(os.path.join(out, 'DEBUG_v50_base.brep'))
    except Exception as e:
        report['brep_export_error'] = repr(e)
    try:
        report['check_text'] = base.check(True)
    except Exception as e:
        report['check_error'] = repr(e)

with open(os.path.join(out, 'BASE_DEBUG_v50.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, default=str)
print('BASE_DEBUG=' + json.dumps(report, default=str))