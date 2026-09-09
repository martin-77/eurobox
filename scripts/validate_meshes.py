import glob, json, os, sys, subprocess, shutil
import numpy as np
import trimesh

root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out_arg=sys.argv[1] if len(sys.argv)>1 else 'build'
out=os.path.join(root,out_arg)
results={}
failed=[]

# Regenerate the canonical printable rack M4 nut from its standalone source of
# truth. The FreeCAD/STEP part imports this same SCAD geometry, so CAD and STL
# can no longer drift into two different nut constructions.
rack_nut=os.path.join(out,'eurobox_v50_rack_m4_nut_print.stl')
if os.path.exists(rack_nut):
    rack_nut_ref=os.path.join(out,'eurobox_v50_rack_m4_nut_BREP_export_reference.mesh-reference')
    shutil.copyfile(rack_nut, rack_nut_ref)
    scad=os.path.join(root,'scripts','rack_m4_nut.scad')
    cp=subprocess.run(
        ['openscad','-o',rack_nut,scad],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=300,
    )
    if cp.returncode != 0 or not os.path.exists(rack_nut) or os.path.getsize(rack_nut)==0:
        raise SystemExit('Could not generate standalone rack M4 nut STL via OpenSCAD/CGAL:\n'+cp.stdout[-4000:])

paths=sorted(glob.glob(os.path.join(out,'*.stl')))
if not paths:
    raise SystemExit('No STL files found in '+out)


def inspect(path):
    m=trimesh.load(path, force='mesh', process=True)
    comps=m.split(only_watertight=False)
    return m, {
        'watertight': bool(m.is_watertight),
        'winding_consistent': bool(m.is_winding_consistent),
        'surface_shells': int(len(comps)),
        'surface_shell_volumes_signed_mm3': [float(c.volume) for c in comps],
        'faces': int(len(m.faces)),
        'volume_mm3': float(abs(m.volume)),
        'bounds_mm': [[float(x) for x in row] for row in m.bounds.tolist()],
    }


def good(info):
    return (info['watertight'] and info['winding_consistent'] and
            info['volume_mm3'] > 0)


def rack_m4_thread_sections(mesh):
    checks=[]
    for z in (1.4, 2.8, 4.2):
        sec=mesh.section(plane_origin=[0.0,0.0,z], plane_normal=[0.0,0.0,1.0])
        if sec is None or len(sec.vertices) == 0:
            checks.append({'z_mm':z,'ok':False,'reason':'no section'})
            continue
        v=np.asarray(sec.vertices)
        r=np.sqrt(v[:,0]**2 + v[:,1]**2)
        inner=r[(r > 1.5) & (r < 2.6)]
        if len(inner) < 8:
            checks.append({'z_mm':z,'ok':False,'reason':'too few inner contour samples','samples':int(len(inner))})
            continue
        rmin=float(inner.min()); rmax=float(inner.max()); span=rmax-rmin
        checks.append({'z_mm':z,'inner_radius_min_mm':round(rmin,5),
                       'inner_radius_max_mm':round(rmax,5),'radial_span_mm':round(span,5),
                       'samples':int(len(inner)),
                       'ok':bool(rmin <= 1.82 and rmax >= 2.12 and span >= 0.30)})
    return checks


def rh8_internal_thread_sections(mesh, ys):
    """Prove an RH8x2 female bore contains a real exposed helix, not a smooth hole."""
    checks=[]
    for y in ys:
        sec=mesh.section(plane_origin=[0.0,y,0.0], plane_normal=[0.0,1.0,0.0])
        if sec is None or len(sec.vertices) == 0:
            checks.append({'y_mm':y,'ok':False,'reason':'no section'})
            continue
        v=np.asarray(sec.vertices)
        r=np.sqrt(v[:,0]**2 + v[:,2]**2)
        inner=r[(r > 3.0) & (r < 4.8)]
        if len(inner) < 12:
            checks.append({'y_mm':y,'ok':False,'reason':'too few inner contour samples','samples':int(len(inner))})
            continue
        rmin=float(inner.min()); rmax=float(inner.max()); span=rmax-rmin
        checks.append({'y_mm':y,'inner_radius_min_mm':round(rmin,5),
                       'inner_radius_max_mm':round(rmax,5),'radial_span_mm':round(span,5),
                       'samples':int(len(inner)),
                       'ok':bool(rmin <= 3.55 and rmax >= 4.05 and span >= 0.45)})
    return checks


def lead_screw_square_drive_section(mesh):
    y=34.5
    sec=mesh.section(plane_origin=[0.0,y,0.0], plane_normal=[0.0,1.0,0.0])
    if sec is None or len(sec.vertices) == 0:
        return {'y_mm':y,'ok':False,'reason':'no section'}
    v=np.asarray(sec.vertices)
    xspan=float(v[:,0].max()-v[:,0].min())
    zspan=float(v[:,2].max()-v[:,2].min())
    return {'y_mm':y,'x_span_mm':round(xspan,5),'z_span_mm':round(zspan,5),
            'expected_drive':'8x8 mm square',
            'ok':bool(7.90 <= xspan <= 8.10 and 7.90 <= zspan <= 8.10)}


def trimesh_cleanup(path):
    m=trimesh.load(path, force='mesh', process=True)
    m.merge_vertices(digits_vertex=5)
    try: m.update_faces(m.unique_faces())
    except Exception: pass
    m.remove_unreferenced_vertices()
    try: trimesh.repair.fix_normals(m, multibody=True)
    except TypeError: trimesh.repair.fix_normals(m)
    tmp=path+'.trimesh.stl'; m.export(tmp)
    _, info=inspect(tmp)
    if good(info):
        os.replace(tmp,path); return True, info
    if os.path.exists(tmp): os.unlink(tmp)
    return False, info


def openscad_normalize(path):
    outstl=path+'.cgal.stl'; scad=path+'.normalize.scad'
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
            os.replace(outstl,path); return True, info
        return False, info
    finally:
        for q in (scad,outstl):
            if os.path.exists(q): os.unlink(q)

for p in paths:
    name=os.path.basename(p)
    mesh, before=inspect(p)
    info=dict(before); info['normalization']='none'
    if name == 'eurobox_v50_rack_m4_nut_print.stl':
        info['canonical_mesh_source']='scripts/rack_m4_nut.scad — Ø4.40 root bore plus inward material helix'

    if not good(before):
        ok, after=trimesh_cleanup(p); info['trimesh_cleanup_result']=after
        if ok:
            mesh, info2=inspect(p); info.update(info2); info['normalization']='trimesh_seam_merge_1e-5mm'
        else:
            ok2, after2=openscad_normalize(p); info['openscad_cleanup_result']=after2
            if ok2:
                mesh, info2=inspect(p); info.update(info2); info['normalization']='openscad_cgal_render'

    if name == 'eurobox_v50_rack_m4_nut_print.stl' and good(info):
        checks=rack_m4_thread_sections(mesh); info['internal_thread_section_checks']=checks
        if not checks or not all(c.get('ok') for c in checks):
            info['internal_thread_mesh_gate']='FAILED: M4x0.7 helix missing on nut bore wall'; failed.append(name)
        else:
            info['internal_thread_mesh_gate']='PASS: M4x0.7 internal helix exposed'

    if name == 'eurobox_v50_knob_retainer_nut.stl' and good(info):
        checks=rh8_internal_thread_sections(mesh, (1.2,2.9,4.6))
        info['internal_RH8x2_thread_section_checks']=checks
        if not checks or not all(c.get('ok') for c in checks):
            info['internal_thread_mesh_gate']='FAILED: RH8x2 helix missing on knob-retainer nut'; failed.append(name)
        else:
            info['internal_thread_mesh_gate']='PASS: knob-retainer nut exposes RH8x2 internal helix'

    if name == 'eurobox_v50_lead_nut_print.stl' and good(info):
        # Main lead nut thread occupies the positive-Y threaded body before the retaining tab/tail.
        checks=rh8_internal_thread_sections(mesh, (3.0,8.0,13.0))
        info['internal_RH8x2_thread_section_checks']=checks
        if not checks or not all(c.get('ok') for c in checks):
            info['internal_thread_mesh_gate']='FAILED: RH8x2 helix missing on main lead nut'; failed.append(name)
        else:
            info['internal_thread_mesh_gate']='PASS: main lead nut exposes RH8x2 internal helix'

    if name == 'eurobox_v50_lead_screw_print.stl' and good(info):
        drive_check=lead_screw_square_drive_section(mesh); info['lead_drive_section_check']=drive_check
        if not drive_check.get('ok'):
            info['lead_drive_mesh_gate']='FAILED: final STL does not contain canonical 8x8 square drive'; failed.append(name)
        else:
            info['lead_drive_mesh_gate']='PASS: final STL contains canonical 8x8 square drive'

    results[name]=info
    if not good(info) and name not in failed: failed.append(name)

with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:
    json.dump({'meshes':results,'failed':failed,
               'note':'Every exported nut is hard-gated for a real exposed internal thread: rack M4x0.7, main lead RH8x2 and knob-retainer RH8x2. Lead screw square drive is also checked.'},f,indent=2)

print(json.dumps({'directory':out_arg,'count':len(results),'failed':failed,
                  'failed_details':{n:results[n] for n in failed}},indent=2))
if failed:
    raise SystemExit('Mesh validation failed: '+', '.join(failed))
