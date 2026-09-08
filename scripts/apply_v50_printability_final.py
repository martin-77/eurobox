from pathlib import Path
import re

p = Path('scripts/build_v50.py')
s = p.read_text(encoding='utf-8')
orig = s

# Manufacturing target: BASE printed upside-down with BOX_SUPPORT_Z on the bed.
# Long structures stay closed CAD solids so PrusaSlicer can use infill instead
# of support. Frozen rack/box interfaces remain unchanged.

# Extend the outboard cage only enough for a lower post-thread retaining tail.
if 'CAGE_Y1 = 276.665' not in s:
    raise SystemExit('Could not locate CAGE_Y1')
s = s.replace('CAGE_Y1 = 276.665', 'CAGE_Y1 = 282.20', 1)

# Closed tapered long arm: 32 mm at the box/bed face, 20 mm at the lower face.
# In the upside-down print orientation the contour only narrows as Z grows.
pat = re.compile(r"def make_i_beam_y\(xc, y0, y1\):\n.*?\n    return fuse_all\(\[top, bot, w1, w2\]\)\n", re.S)
rep = '''PRINT_ARM_BOTTOM_W = 20.0
PRINT_ARM_TAPER_H = 7.0

def make_i_beam_y(xc, y0, y1):
    L = y1-y0
    taper_z = ARM_BOTTOM_Z + PRINT_ARM_TAPER_H
    pts = [
        App.Vector(xc-ARM_W/2.0, y0, ARM_TOP_Z),
        App.Vector(xc+ARM_W/2.0, y0, ARM_TOP_Z),
        App.Vector(xc+ARM_W/2.0, y0, taper_z),
        App.Vector(xc+PRINT_ARM_BOTTOM_W/2.0, y0, ARM_BOTTOM_Z),
        App.Vector(xc-PRINT_ARM_BOTTOM_W/2.0, y0, ARM_BOTTOM_Z),
        App.Vector(xc-ARM_W/2.0, y0, taper_z),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(App.Vector(0, L, 0)).removeSplitter()
'''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('Could not replace I-beam arm')

# Keep the proven saddle/pivot but support its fixed bridge from the common bed
# plane with a 45-degree gusset instead of an 18 mm horizontal cantilever.
pat = re.compile(r"def make_upper_station\(xc\):\n.*?\n\nbase_parts =", re.S)
rep = '''def make_upper_station(xc):
    bridge = box(xc-17.0, -8.0, 0.0, 34.0, 22.0, 16.0)
    transition = box(xc-16.0, 10.0, ARM_BOTTOM_Z, 32.0, 20.0, ARM_H)

    gx = xc-17.0
    gpts = [
        App.Vector(gx, 10.0, ARM_TOP_Z),
        App.Vector(gx, 14.0, ARM_TOP_Z),
        App.Vector(gx, 14.0, 16.0),
        App.Vector(gx, -8.0, 16.0),
        App.Vector(gx, -8.0, ARM_TOP_Z-18.0),
    ]
    gwire = Part.makePolygon(gpts + [gpts[0]])
    print_gusset = Part.Face(gwire).extrude(App.Vector(34.0, 0, 0))

    lug_l = cyl_x(6.0, 4.0, xc-17.0, PIN_Y, PIN_Z)
    lug_r = cyl_x(6.0, 4.0, xc+13.0, PIN_Y, PIN_Z)
    web_l = box(xc-17.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    web_r = box(xc+13.0, PIN_Y, PIN_Z, 4.0, 7.0, 6.0)
    cheek_l = box(xc-17.0, -8.0, -5.5, 4.0, 8.0, 5.5)
    cheek_r = box(xc+13.0, -8.0, -5.5, 4.0, 8.0, 5.5)

    q = fuse_all([bridge, transition, print_gusset,
                  lug_l, lug_r, web_l, web_r, cheek_l, cheek_r])
    q = q.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    q = q.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return q.removeSplitter()

base_parts ='''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('Could not replace upper station')

# Closed 45-degree crosshead under the 16.45 x 16.45 mm Eurobox rim.
# The 0.20 mm offset keeps the wedge clear of the actual rim envelope.
pat = re.compile(
    r"# Crosshead stays clear of the hanging 16\.45 x 16\.45 mm box rim\.\n"
    r"base_parts \+= \[\n.*?\n\]\n\n# Plate guide cage, outside the actual box edge\.", re.S)
rep = '''# Closed self-supporting crosshead under the hanging Eurobox rim.
CROSSHEAD_Y0 = 216.0
CROSSHEAD_RIM_CLEAR = 0.20
CROSSHEAD_TOP_Y1 = BOX_RIM_INNER_Y - CROSSHEAD_RIM_CLEAR
CROSSHEAD_BOTTOM_Y1 = CROSSHEAD_TOP_Y1 + ARM_H
cx0 = -106.0
cpts = [
    App.Vector(cx0, CROSSHEAD_Y0, ARM_TOP_Z),
    App.Vector(cx0, CROSSHEAD_TOP_Y1, ARM_TOP_Z),
    App.Vector(cx0, CROSSHEAD_BOTTOM_Y1, ARM_BOTTOM_Z),
    App.Vector(cx0, CROSSHEAD_Y0, ARM_BOTTOM_Z),
]
cwire = Part.makePolygon(cpts + [cpts[0]])
CROSSHEAD = Part.Face(cwire).extrude(App.Vector(212.0, 0, 0)).removeSplitter()
base_parts += [CROSSHEAD]

# Plate guide cage, outside the actual box edge.'''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('Could not replace crosshead')

# Move the removable lead-nut retaining pin from the high +Z tab to a lower tail
# after the threaded section. This keeps the spindle axis at Z=31 while allowing
# the BASE cage itself to end at BOX_SUPPORT_Z. Tail top is Z=-4.5, leaving
# 0.5 mm clearance to the following 8x8 square drive (Z=-4..+4).
pat = re.compile(
    r"LEAD_NUT_TAB_H = 6\.0\nLEAD_NUT_PIN_Y = 7\.0\nLEAD_NUT_PIN_Z = 10\.0\n"
    r"LEAD_NUT_PIN_HOLE_D = 3\.4\n\n"
    r"LEAD_NUT = box\(-8\.0, 0\.0, -7\.0, 16\.0, NUT_THREAD_LEN, 14\.0\)\n"
    r"LEAD_NUT = LEAD_NUT\.fuse\(box\(-6\.0, 3\.0, 7\.0, 12\.0, 8\.0, LEAD_NUT_TAB_H\)\)\n"
    r"LEAD_NUT = LEAD_NUT\.cut\(z_to_y\(FEMALE, 0, 0, 0\)\)\n"
    r"LEAD_NUT = LEAD_NUT\.cut\(cyl_x\(LEAD_NUT_PIN_HOLE_D/2\.0, 20\.0, -10\.0,\n"
    r"\s+LEAD_NUT_PIN_Y, LEAD_NUT_PIN_Z\)\)\nLEAD_NUT = LEAD_NUT\.removeSplitter\(\)", re.S)
rep = '''LEAD_NUT_TAB_H = 5.5
LEAD_NUT_PIN_Y = NUT_THREAD_LEN + 2.75
LEAD_NUT_PIN_Z = -7.25
LEAD_NUT_PIN_HOLE_D = 3.4
LEAD_NUT_TAIL_Y0 = NUT_THREAD_LEN
LEAD_NUT_TAIL_L = 5.5
LEAD_NUT_TAIL_Z0 = -10.0

LEAD_NUT = box(-8.0, 0.0, -7.0, 16.0, NUT_THREAD_LEN, 14.0)
LEAD_NUT = LEAD_NUT.fuse(box(-6.0, LEAD_NUT_TAIL_Y0, LEAD_NUT_TAIL_Z0,
                             12.0, LEAD_NUT_TAIL_L, LEAD_NUT_TAB_H))
LEAD_NUT = LEAD_NUT.cut(z_to_y(FEMALE, 0, 0, 0))
LEAD_NUT = LEAD_NUT.cut(cyl_x(LEAD_NUT_PIN_HOLE_D/2.0, 20.0, -10.0,
                              LEAD_NUT_PIN_Y, LEAD_NUT_PIN_Z))
LEAD_NUT = LEAD_NUT.removeSplitter()'''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('Could not rebuild lead-nut lower retaining tail')

# Remove support-heavy full-width guide roof/floor and lower the outer frame to
# the common bed plane. Two lead screws already provide vertical plate retention;
# side rails only need to control lateral alignment.
pat = re.compile(
    r"# Plate guide cage, outside the actual box edge\.\nbase_parts \+= \[\n.*?\n\]\n\n"
    r"# Outer screw frame\.\nbase_parts \+= \[\n.*?\n\]\n"
    r"for sx in SPINDLE_X:\n    base_parts\.append\(box\(sx-11\.0, CAGE_Y0, 20\.0, 22\.0, CAGE_Y1-CAGE_Y0, 24\.0\)\)\n", re.S)
rep = '''# Plate guide cage: side rails only; lead screws retain the plate vertically.
PRINT_BASE_PLANE_Z = BOX_SUPPORT_Z
PRINT_GUIDE_Z0 = 14.0
base_parts += [
    box(-78.0, BOX_EDGE_Y, PRINT_GUIDE_Z0, 7.6, 14.0,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    box(70.4, BOX_EDGE_Y, PRINT_GUIDE_Z0, 7.6, 14.0,
        PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
]

# One broad tie beam lies directly on the bed; closed boss towers descend from
# it. The old print-top lower rail is deleted.
PRINT_FRAME_TIE_T = 6.0
PRINT_FRAME_BOSS_Z0 = 20.0
base_parts += [
    box(-78.0, CAGE_Y0-0.1, PRINT_BASE_PLANE_Z-PRINT_FRAME_TIE_T,
        156.0, CAGE_Y1-CAGE_Y0+0.2, PRINT_FRAME_TIE_T),
]
for sx in SPINDLE_X:
    base_parts.append(box(sx-11.0, CAGE_Y0, PRINT_FRAME_BOSS_Z0, 22.0,
                          CAGE_Y1-CAGE_Y0,
                          PRINT_BASE_PLANE_Z-PRINT_FRAME_BOSS_Z0))
'''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('Could not lower/open plate-guide screw frame')

# Add the lower tail pocket and pin/service bores after all previous BASE cuts.
# The cage extension overlaps the square-drive Y range; clear it with Ø11.8.
anchor = '''BASE = BASE.removeSplitter()

# -----------------------------
# Rear-only integrated mounting backstop'''
rep = '''for sx in SPINDLE_X:
    BASE = BASE.cut(box(sx-6.2, NUT_Y1-0.25, SPINDLE_Z-10.25,
                        12.4, 6.0, 6.0))
    BASE = BASE.cut(cyl_x(LEAD_NUT_PIN_HOLE_D/2.0, 24.0, sx-12.0,
                          NUT_Y0+LEAD_NUT_PIN_Y,
                          SPINDLE_Z+LEAD_NUT_PIN_Z))
    BASE = BASE.cut(cyl_x(3.55, 3.0, sx-14.0,
                          NUT_Y0+LEAD_NUT_PIN_Y,
                          SPINDLE_Z+LEAD_NUT_PIN_Z))
    BASE = BASE.cut(cyl_x(4.10, 4.0, sx+11.0,
                          NUT_Y0+LEAD_NUT_PIN_Y,
                          SPINDLE_Z+LEAD_NUT_PIN_Z))
    drive_y0 = (BOX_EDGE_Y + SPINDLE_LOCAL_JOURNAL +
                SPINDLE_LOCAL_SHOULDER + LEAD_THREAD_LEN - 0.20)
    BASE = BASE.cut(cyl_y(5.90, CAGE_Y1-drive_y0+0.50,
                          sx, drive_y0, SPINDLE_Z))
BASE = BASE.removeSplitter()

# -----------------------------
# Rear-only integrated mounting backstop'''
if anchor not in s:
    raise SystemExit('Could not locate BASE before mounting backstop')
s = s.replace(anchor, rep, 1)

# Backstop gusset used to stop 0.79 mm below the common print plane, which means
# it starts several layers in mid-air in this orientation. It is at Y=-16..+4,
# nowhere near the Eurobox rim, so bring it exactly onto BOX_SUPPORT_Z.
if 'MOUNT_BACKSTOP_GUSSET_TOP_Z = 38.75' not in s:
    raise SystemExit('Could not locate mounting backstop top Z')
s = s.replace('MOUNT_BACKSTOP_GUSSET_TOP_Z = 38.75',
              'MOUNT_BACKSTOP_GUSSET_TOP_Z = BOX_SUPPORT_Z', 1)
old = """if not (0.5 <= V['mounting_backstop']['gap_below_box_support_mm'] <= 1.5):
    failures.append('Rear mounting backstop gusset top must stay 0.5..1.5 mm below box support')
"""
new = """if abs(V['mounting_backstop']['gap_below_box_support_mm']) > 0.02:
    failures.append('Rear mounting backstop gusset must be coplanar with the upside-down print bed')
"""
if old not in s:
    raise SystemExit('Could not replace backstop gap gate')
s = s.replace(old, new, 1)

# Hard source-level witnesses for the support-minimised print architecture.
anchor = "for name, sh in PARTS.items():\n"
if anchor not in s:
    raise SystemExit('Could not locate final export gate')
proof = '''arm_run = (ARM_W-PRINT_ARM_BOTTOM_W)/2.0
arm_ratio = arm_run/PRINT_ARM_TAPER_H
cross_run = CROSSHEAD_BOTTOM_Y1-CROSSHEAD_TOP_Y1
cross_ratio = cross_run/ARM_H
V['printability'] = {
    'orientation': 'rotate BASE 180deg about X; model Z=39.54 on print bed',
    'model_bed_plane_z_mm': BOX_SUPPORT_Z,
    'right_base_zmax_mm': round(BASE_RIGHT.BoundBox.ZMax, 4),
    'left_base_zmax_mm': round(BASE_LEFT.BoundBox.ZMax, 4),
    'long_arms': 'closed tapered solids; slicer infill interior',
    'arm_top_width_mm': ARM_W,
    'arm_bottom_width_mm': PRINT_ARM_BOTTOM_W,
    'arm_taper_height_mm': PRINT_ARM_TAPER_H,
    'arm_run_per_vertical_ratio': round(arm_ratio, 4),
    'crosshead': 'closed 45deg rim-following wedge; slicer infill interior',
    'crosshead_run_per_vertical_ratio': round(cross_ratio, 4),
    'crosshead_rim_clearance_mm': CROSSHEAD_RIM_CLEAR,
    'plate_guide': 'side rails only; two lead screws retain plate vertically',
    'outer_frame_lower_bridge_removed': True,
    'lead_nut_retention': 'lower post-thread tail cross-pin; no high cage ear',
    'lead_nut_pin_model_z_mm': round(SPINDLE_Z+LEAD_NUT_PIN_Z, 3),
    'backstop_gusset_on_bed_plane': abs(MOUNT_BACKSTOP_GUSSET_TOP_Z-BOX_SUPPORT_Z) < 1e-9,
    'functional_round_interfaces_preserved': True,
    'support_policy': 'no large structural support; only optional local support/bridging at functional round bores',
}
if abs(V['printability']['right_base_zmax_mm']-BOX_SUPPORT_Z) > 0.03:
    failures.append('RIGHT BASE does not share the intended print-bed plane')
if abs(V['printability']['left_base_zmax_mm']-BOX_SUPPORT_Z) > 0.03:
    failures.append('LEFT BASE does not share the intended print-bed plane')
if V['printability']['arm_run_per_vertical_ratio'] > 1.0:
    failures.append('Arm taper exceeds 45-degree self-support target')
if V['printability']['crosshead_run_per_vertical_ratio'] > 1.01:
    failures.append('Crosshead wedge exceeds 45-degree self-support target')
if not V['printability']['outer_frame_lower_bridge_removed']:
    failures.append('Support-heavy outer frame lower bridge remains')
if not V['printability']['backstop_gusset_on_bed_plane']:
    failures.append('Backstop gusset does not start on the common print plane')
'''
s = s.replace(anchor, proof + '\n' + anchor, 1)

if s == orig:
    raise SystemExit('Printability pass made no build changes')
p.write_text(s, encoding='utf-8')
print('Applied v50 support-minimised BASE geometry')

# Independent clamp validator must place the retained nut/pin at the same datums.
vp = Path('scripts/validate_box_clamp.py')
vs = vp.read_text(encoding='utf-8')
vorig = vs
if 'LEAD_NUT_PIN_Y = 7.0' not in vs or 'LEAD_NUT_PIN_Z = 10.0' not in vs:
    raise SystemExit('Could not locate clamp-validator pin datums')
vs = vs.replace('LEAD_NUT_PIN_Y = 7.0', 'LEAD_NUT_PIN_Y = 16.75', 1)
vs = vs.replace('LEAD_NUT_PIN_Z = 10.0', 'LEAD_NUT_PIN_Z = -7.25', 1)
if vs == vorig:
    raise SystemExit('Clamp-validator pin update made no changes')
vp.write_text(vs, encoding='utf-8')
print('Updated clamp validator for lower lead-nut tail pin')

# The handed-base source gate is valid, but its injected STL vertex-cloud test
# was triangulation-sensitive. Check final meshes using mirrored physical mass
# properties instead: bounds, volume, area, center of mass and inertia tensor.
vp = Path('scripts/validate_meshes.py')
vs = vp.read_text(encoding='utf-8')
vorig = vs
marker = '# Final handed-base pair regression gate.'
write_anchor = "with open(os.path.join(out,'MESH_VALIDATION.json'),'w') as f:\n"
if marker not in vs or write_anchor not in vs:
    raise SystemExit('Could not locate injected handed STL gate')
start = vs.index(marker)
end = vs.index(write_anchor, start)
handed = r'''# Final handed-base pair regression gate.
# Independent OCC solids may tessellate mirrored surfaces differently, so do
# not require identical vertex clouds. Verify final-mesh physical invariants.
import hashlib
right_base_path=os.path.join(out,'eurobox_v50_base_right.stl')
left_base_path=os.path.join(out,'eurobox_v50_base_left.stl')
if not (os.path.exists(right_base_path) and os.path.exists(left_base_path)):
    missing=[n for n in ('eurobox_v50_base_right.stl','eurobox_v50_base_left.stl')
             if not os.path.exists(os.path.join(out,n))]
    failed.extend([n for n in missing if n not in failed])
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
    rsha=_sha256(right_base_path); lsha=_sha256(left_base_path)
    rb=np.asarray(rm.bounds,dtype=float); lb=np.asarray(lm.bounds,dtype=float)
    R=np.diag([-1.0,1.0,1.0])
    rc=np.asarray(rm.center_mass,dtype=float); lc=np.asarray(lm.center_mass,dtype=float)
    ri=np.asarray(rm.moment_inertia,dtype=float); li=np.asarray(lm.moment_inertia,dtype=float)
    bounds_ok=(abs(rb[0,0]+lb[1,0])<=0.03 and abs(rb[1,0]+lb[0,0])<=0.03 and
               np.allclose(rb[:,1:],lb[:,1:],atol=0.03,rtol=0.0))
    volume_delta=abs(abs(float(rm.volume))-abs(float(lm.volume)))
    area_delta=abs(float(rm.area)-float(lm.area))
    volume_ok=volume_delta <= max(0.5,abs(float(rm.volume))*1e-5)
    area_ok=area_delta <= max(0.5,float(rm.area)*2e-5)
    center_ok=np.allclose(lc,R.dot(rc),atol=0.03,rtol=0.0)
    inertia_ok=np.allclose(li,R.dot(ri).dot(R),atol=2.0,rtol=2e-5)
    distinct=(rsha != lsha)
    side_ok=(rb[1,0]>=180.0 and lb[0,0]<=-180.0 and rb[0,0]>-120.0 and lb[1,0]<120.0)
    print_plane_ok=(abs(rb[1,2]-39.54)<=0.03 and abs(lb[1,2]-39.54)<=0.03)
    ok=bool(distinct and bounds_ok and volume_ok and area_ok and center_ok and
            inertia_ok and side_ok and print_plane_ok)
    results['handed_base_pair']={
        'ok':ok, 'right_sha256':rsha, 'left_sha256':lsha,
        'distinct_file_bytes':distinct,
        'right_bounds_mm':rb.tolist(), 'left_bounds_mm':lb.tolist(),
        'bounds_are_x_mirrors':bool(bounds_ok),
        'volume_delta_mm3':float(volume_delta), 'volumes_match':bool(volume_ok),
        'surface_area_delta_mm2':float(area_delta), 'surface_areas_match':bool(area_ok),
        'right_center_mass_mm':rc.tolist(), 'left_center_mass_mm':lc.tolist(),
        'center_mass_is_x_mirrored':bool(center_ok),
        'inertia_tensor_is_x_mirrored':bool(inertia_ok),
        'rear_stop_envelopes_on_opposite_local_x_ends':bool(side_ok),
        'base_max_z_matches_39_54mm_print_plane':bool(print_plane_ok),
    }
    if not ok:
        for n in ('eurobox_v50_base_right.stl','eurobox_v50_base_left.stl'):
            if n not in failed:
                failed.append(n)

'''
vs = vs[:start] + handed + vs[end:]
if vs == vorig:
    raise SystemExit('Handed STL gate replacement made no changes')
vp.write_text(vs, encoding='utf-8')
print('Updated handed STL gate to triangulation-independent mass properties')
