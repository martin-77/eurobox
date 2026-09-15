import os
import math
import json
import subprocess
import FreeCAD as App
import Part
import Mesh
import build_v60 as C

OUT = C.OUT
RIM_BOTTOM_Z = C.BOX_SUPPORT_Z - C.RIM_H
PLATE_X = 140.0
PLATE_Y = 8.0
PLATE_Z0 = 16.0
PLATE_Z1 = 46.0
PLATE_OPEN = 5.5
PLATE_HOLE_D = 6.5
UNDERHOOK = 4.2
UNDERHOOK_T = 4.0
SPINDLE_X = (-42.0, 42.0)
SPINDLE_Z = 31.0
THREAD_MAJOR = 8.0
THREAD_PITCH = 2.0
THREAD_CORE_R = 3.25
THREAD_FEMALE_CORE_R = 3.42
THREAD_FEMALE_MAJOR_R = 4.22
LEAD_THREAD_LEN = 22.2
NUT_THREAD_LEN = 14.0
SHOULDER_D = 11.0
SPINDLE_LOCAL_JOURNAL = 8.0
SPINDLE_LOCAL_SHOULDER = 1.8
HEX_LEN = 4.5
OUTER_STUD_LEN = 7.0

PLATE_SPINDLE_Y = C.BOX_RIM_INNER_Y
NUT_ANCHOR_OFFSET = 15.8
NUT_Y0 = PLATE_SPINDLE_Y - NUT_ANCHOR_OFFSET
NUT_THREAD_Y0 = NUT_Y0 - NUT_THREAD_LEN
CAGE_Y0 = PLATE_SPINDLE_Y - 37.535
CAGE_Y1 = PLATE_SPINDLE_Y - 13.600
WIDTH_RIM_CLEAR = 0.20
PRINT_GUIDE_Y0 = CAGE_Y1 - 0.40
PRINT_GUIDE_Y1 = C.BOX_RIM_INNER_Y - WIDTH_RIM_CLEAR
PRINT_GUIDE_Z0 = 14.0
PRINT_GUIDE_Z1 = 49.8
PRINT_FRAME_BOSS_Z0 = 20.0
PRINT_FRAME_BOSS_Z1 = 44.0
PRINT_FRAME_TIE_T = 3.4
FINAL_DECK_Z0 = C.ARM_BOTTOM_Z
FINAL_DECK_Z1 = PRINT_GUIDE_Z0
LOWER_SADDLE_R = 6.15


def stage(msg):
    print('V60_STAGE ' + msg, flush=True)


def cyl_y(r, length, x=0.0, y=0.0, z=0.0):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def hex_z(af, height, z0=0.0):
    r = af / math.sqrt(3.0)
    pts = [App.Vector(r*math.cos(math.radians(30+60*i)),
                      r*math.sin(math.radians(30+60*i)), z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0,0,height))


def z_to_y(shape, x=0.0, y=0.0, z=0.0):
    q = shape.copy()
    q.rotate(App.Vector(0,0,0), App.Vector(1,0,0), -90.0)
    q.translate(App.Vector(x,y,z))
    return q


def rotate_z180(shape):
    q = shape.copy()
    q.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180.0)
    return q.removeSplitter()


def write_thread_scad(path, core_r, major_r, pitch, length, root_w, crest_w):
    txt = f'''$fn=48;\nmodule thread_solid(){{\n union(){{\n  cylinder(r={core_r},h={length});\n  linear_extrude(height={length},twist=360*{length}/{pitch},slices=ceil({length}/{pitch}*18),convexity=30)\n   polygon(points=[[{core_r}-0.08,-{root_w}/2],[{major_r},-{crest_w}/2],[{major_r},{crest_w}/2],[{core_r}-0.08,{root_w}/2]]);\n }}\n}}\nthread_solid();\n'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt)


def import_scad_shape(path):
    stl = os.path.splitext(path)[0] + '_compiled.stl'
    subprocess.run(['openscad','-o',stl,path], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = Mesh.Mesh(stl)
    sh = Part.Shape(); sh.makeShapeFromMesh(m.Topology, 0.035)
    if sh.ShapeType == 'Shell':
        sh = Part.makeSolid(sh)
    elif sh.ShapeType == 'Compound':
        solids = []
        for shell in sh.Shells:
            try:
                q = Part.makeSolid(shell)
                if q.isValid() and q.Volume > 0:
                    solids.append(q)
            except Exception:
                pass
        if not solids:
            raise RuntimeError('No solid reconstructed from ' + stl)
        sh = C.fuse_seq(solids, 'compiled-thread-solids')
    sh = sh.removeSplitter()
    C.require_single(sh, 'compiled thread ' + os.path.basename(path))
    return sh


def make_c_clip(outer_r, inner_r, thickness, opening_w):
    ring = Part.makeCylinder(outer_r, thickness).cut(Part.makeCylinder(inner_r, thickness))
    opening = C.box(-opening_w/2, 0, -0.2, opening_w, outer_r+1, thickness+0.4)
    q = ring.cut(opening).removeSplitter()
    C.require_single(q, 'c-clip')
    return q


stage('lower hardware')
lower_shell = C.box(-12.6,-7.0,-14.5,25.2,24.0,14.5)
lower_pivot = C.cyl_x(5.0,25.2,-12.6,C.PIN_Y,C.PIN_Z)
lower_web = C.box(-12.6,C.PIN_Y,-10.5,25.2,7.0,10.5)
LOWER = C.fuse_seq([lower_shell,lower_pivot,lower_web], 'lower-rack-jaw')
LOWER = LOWER.cut(C.cyl_x(LOWER_SADDLE_R,27.2,-13.6,0,0)).removeSplitter()
LOWER = LOWER.cut(C.cyl_x(C.PIN_HOLE_D/2,27.2,-13.6,C.PIN_Y,C.PIN_Z)).removeSplitter()
C.require_single(LOWER, 'lower-rack-jaw-final')
PIN = C.fuse_seq([
    C.cyl_x(2.0,33.5,-18.4,0,0),
    C.cyl_x(1.55,1.5,15.1,0,0),
    C.cyl_x(2.0,1.7,16.6,0,0),
    C.cyl_x(3.75,2.4,-20.8,0,0),
], 'rack-pin')
PIN_CLIP = make_c_clip(4.2,1.65,1.5,3.0)
PLATE_CLIP = make_c_clip(5.4,2.45,1.4,3.8)


def make_cage_structure():
    parts = [
        C.box(-78.0, PRINT_GUIDE_Y0, PRINT_GUIDE_Z0, 7.6,
              PRINT_GUIDE_Y1-PRINT_GUIDE_Y0, PRINT_GUIDE_Z1-PRINT_GUIDE_Z0),
        C.box(70.4, PRINT_GUIDE_Y0, PRINT_GUIDE_Z0, 7.6,
              PRINT_GUIDE_Y1-PRINT_GUIDE_Y0, PRINT_GUIDE_Z1-PRINT_GUIDE_Z0),
        C.box(-78.0, CAGE_Y0-0.10, PRINT_GUIDE_Z1-PRINT_FRAME_TIE_T,
              156.0, CAGE_Y1-CAGE_Y0+0.20, PRINT_FRAME_TIE_T),
        C.box(-70.4, CAGE_Y0, FINAL_DECK_Z0, 140.8,
              PRINT_GUIDE_Y1-CAGE_Y0, FINAL_DECK_Z1-FINAL_DECK_Z0),
        C.box(-78.0, CAGE_Y0-0.10, PRINT_GUIDE_Z0, 7.6,
              PRINT_GUIDE_Y0-(CAGE_Y0-0.10)+0.35, PRINT_GUIDE_Z1-PRINT_GUIDE_Z0),
        C.box(70.4, CAGE_Y0-0.10, PRINT_GUIDE_Z0, 7.6,
              PRINT_GUIDE_Y0-(CAGE_Y0-0.10)+0.35, PRINT_GUIDE_Z1-PRINT_GUIDE_Z0),
    ]
    for sx in SPINDLE_X:
        parts.append(C.box(sx-11.0,CAGE_Y0,PRINT_FRAME_BOSS_Z0,22.0,
                           CAGE_Y1-CAGE_Y0,PRINT_FRAME_BOSS_Z1-PRINT_FRAME_BOSS_Z0))
        parts.append(C.box(sx-11.35,CAGE_Y0,FINAL_DECK_Z1-0.35,22.70,
                           CAGE_Y1-CAGE_Y0,
                           PRINT_FRAME_BOSS_Z0-(FINAL_DECK_Z1-0.35)+0.35))
    return C.fuse_seq(parts, 'direct-final-box-clamp-cage')


stage('cage fusion')
CAGE = make_cage_structure()
RIGHT_FULL = C.RIGHT.fuse(CAGE).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT full before thread machining')

stage('thread solids')
MALE_SCAD = os.path.join(OUT,'v60_thread_RH_8x2_male.scad')
FEMALE_SCAD = os.path.join(OUT,'v60_thread_RH_8x2_female.scad')
CAP_FEMALE_SCAD = os.path.join(OUT,'v60_thread_RH_8x2_cap_female.scad')
write_thread_scad(MALE_SCAD,THREAD_CORE_R,THREAD_MAJOR/2,THREAD_PITCH,LEAD_THREAD_LEN,0.58,0.24)
write_thread_scad(FEMALE_SCAD,THREAD_FEMALE_CORE_R,THREAD_FEMALE_MAJOR_R,THREAD_PITCH,NUT_THREAD_LEN,0.76,0.40)
write_thread_scad(CAP_FEMALE_SCAD,3.36,4.34,THREAD_PITCH,5.4,1.05,0.24)
MALE_Z = import_scad_shape(MALE_SCAD).common(Part.makeCylinder(4.06,LEAD_THREAD_LEN)).removeSplitter()
FEMALE_Z = import_scad_shape(FEMALE_SCAD).common(Part.makeCylinder(4.28,NUT_THREAD_LEN)).removeSplitter()
CAP_FEMALE_Z = import_scad_shape(CAP_FEMALE_SCAD).common(Part.makeCylinder(4.38,5.4)).removeSplitter()

stage('integral thread machining')
FEMALE_NEGY = rotate_z180(z_to_y(FEMALE_Z))
for sx in SPINDLE_X:
    inner_y0 = CAGE_Y0 - 0.50
    RIGHT_FULL = RIGHT_FULL.cut(cyl_y(5.90,
        NUT_THREAD_Y0-inner_y0+0.20, sx, inner_y0, SPINDLE_Z)).removeSplitter()
    cutter = FEMALE_NEGY.copy(); cutter.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z))
    RIGHT_FULL = RIGHT_FULL.cut(cutter).removeSplitter()
    outer_y0 = NUT_Y0
    RIGHT_FULL = RIGHT_FULL.cut(cyl_y(4.45,
        (PLATE_SPINDLE_Y-SPINDLE_LOCAL_JOURNAL-SPINDLE_LOCAL_SHOULDER)-outer_y0+0.40,
        sx, outer_y0, SPINDLE_Z)).removeSplitter()
    shoulder_y0 = PLATE_SPINDLE_Y-SPINDLE_LOCAL_JOURNAL-SPINDLE_LOCAL_SHOULDER-0.35
    RIGHT_FULL = RIGHT_FULL.cut(cyl_y(SHOULDER_D/2+0.30,
        SPINDLE_LOCAL_SHOULDER+0.70, sx, shoulder_y0, SPINDLE_Z)).removeSplitter()
    journal_y0 = PLATE_SPINDLE_Y-SPINDLE_LOCAL_JOURNAL-0.35
    RIGHT_FULL = RIGHT_FULL.cut(cyl_y(3.35,
        SPINDLE_LOCAL_JOURNAL+0.70, sx, journal_y0, SPINDLE_Z)).removeSplitter()
C.require_single(RIGHT_FULL, 'RIGHT full after integral lead threads')

pin_bore_clearance = []
for xc in C.CLAMP_X:
    probe = C.cyl_x(C.PIN_HOLE_D/2-0.05,38.0,xc-19.0,C.PIN_Y,C.PIN_Z)
    cv = RIGHT_FULL.common(probe).Volume
    pin_bore_clearance.append({'x_mm':xc,'probe_common_mm3':round(cv,9)})
    if cv > 1e-5:
        raise RuntimeError(f'Rack pin bore closed at X={xc}: {cv:.6f} mm3')
C.require_single(RIGHT_FULL, 'RIGHT full final')
LEFT_FULL = C.mirror_x(RIGHT_FULL)

stage('plate')
PLATE_BODY_Y0 = C.BOX_RIM_INNER_Y - PLATE_Y
PLATE_HOOK_Y0 = C.BOX_RIM_INNER_Y - WIDTH_RIM_CLEAR
PLATE_HOOK_Y1 = C.BOX_RIM_INNER_Y + UNDERHOOK
PLATE = C.box(-PLATE_X/2,PLATE_BODY_Y0,PLATE_Z0,PLATE_X,PLATE_Y,PLATE_Z1-PLATE_Z0)
PLATE = PLATE.fuse(C.box(-PLATE_X/2,PLATE_HOOK_Y0,RIM_BOTTOM_Z-UNDERHOOK_T,
                         PLATE_X,PLATE_HOOK_Y1-PLATE_HOOK_Y0,UNDERHOOK_T))
for sx in SPINDLE_X:
    PLATE = PLATE.cut(cyl_y(PLATE_HOLE_D/2,PLATE_Y+1,sx,PLATE_BODY_Y0-0.5,SPINDLE_Z))
    PLATE = PLATE.cut(cyl_y(6.0,2.0,sx,PLATE_BODY_Y0,SPINDLE_Z))
PLATE = PLATE.removeSplitter(); C.require_single(PLATE,'box-clamp-plate')

stage('lead screw and knob')
SPINDLE_POSY = C.fuse_seq([
    cyl_y(3.0,0.4), cyl_y(2.5,1.4,0,0.4,0),
    cyl_y(3.0,SPINDLE_LOCAL_JOURNAL-1.8,0,1.8,0),
    cyl_y(SHOULDER_D/2,SPINDLE_LOCAL_SHOULDER,0,SPINDLE_LOCAL_JOURNAL,0),
    z_to_y(MALE_Z,0,SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER,0),
    z_to_y(hex_z(10.0,HEX_LEN),0,SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN,0),
], 'lead-spindle-positive-y')
STUD_SCAD = os.path.join(OUT,'v60_thread_RH_8x2_stud.scad')
write_thread_scad(STUD_SCAD,THREAD_CORE_R,THREAD_MAJOR/2,THREAD_PITCH,OUTER_STUD_LEN,0.58,0.24)
STUD_Z = import_scad_shape(STUD_SCAD).common(Part.makeCylinder(4.06,OUTER_STUD_LEN)).removeSplitter()
SPINDLE_POSY = SPINDLE_POSY.fuse(z_to_y(STUD_Z,0,
    SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN+HEX_LEN,0)).removeSplitter()
C.require_single(SPINDLE_POSY,'lead-spindle-with-stud')
SPINDLE = rotate_z180(SPINDLE_POSY)
KNOB = cyl_y(15.0,7.0)
for a in range(0,360,45):
    rr=16.2; x=rr*math.cos(math.radians(a)); z=rr*math.sin(math.radians(a))
    KNOB=KNOB.cut(cyl_y(3.4,7.4,x,-0.2,z))
KNOB=KNOB.cut(cyl_y(4.3,7.4,0,-0.2,0))
KNOB=KNOB.cut(z_to_y(hex_z(10.35,5.2))).removeSplitter(); KNOB=rotate_z180(KNOB)
CAP_FEMALE_NEGY=rotate_z180(z_to_y(CAP_FEMALE_Z))
CAP_NUT=rotate_z180(z_to_y(hex_z(13.0,5.4)))
CAP_NUT=CAP_NUT.cut(CAP_FEMALE_NEGY).removeSplitter(); C.require_single(CAP_NUT,'lead-knob-retainer-nut')

stage('hard validation')
failures=[]
def fail(msg): failures.append(msg)
for side,sh in (('RIGHT',RIGHT_FULL),('LEFT',LEFT_FULL)):
    C.require_single(sh,side+' full')
    if sh.BoundBox.XLength>C.V60_X_TARGET_MAX+1e-6: fail(f'{side} full base exceeds 296 mm X target: {sh.BoundBox.XLength:.3f}')
    if sh.BoundBox.YLength>C.INDX_Y_MAX+1e-6: fail(f'{side} full base exceeds 275 mm Y: {sh.BoundBox.YLength:.3f}')
left_back=C.mirror_x(LEFT_FULL)
full_mirror_delta=abs(RIGHT_FULL.Volume-left_back.Volume)
mirror_bound_delta=max(abs(RIGHT_FULL.BoundBox.XMin-left_back.BoundBox.XMin),abs(RIGHT_FULL.BoundBox.XMax-left_back.BoundBox.XMax),abs(RIGHT_FULL.BoundBox.YMin-left_back.BoundBox.YMin),abs(RIGHT_FULL.BoundBox.YMax-left_back.BoundBox.YMax),abs(RIGHT_FULL.BoundBox.ZMin-left_back.BoundBox.ZMin),abs(RIGHT_FULL.BoundBox.ZMax-left_back.BoundBox.ZMax))
mirror_face_delta=abs(len(RIGHT_FULL.Faces)-len(left_back.Faces))
if full_mirror_delta>1e-4 or mirror_bound_delta>1e-6 or mirror_face_delta!=0: fail('full handed bases are not exact construction mirrors')
stage('mirror gate complete')

tube=C.cyl_x(C.RACK_R,400,-200,0,0)
lower_sweep=[]
for xc in C.CLAMP_X:
    for deg in (0,-15,-30,-45,-60,-75,-90):
        lo=LOWER.copy(); lo.rotate(App.Vector(0,C.PIN_Y,C.PIN_Z),App.Vector(1,0,0),deg); lo.translate(App.Vector(xc,0,0))
        bc=RIGHT_FULL.common(lo).Volume; tc=tube.common(lo).Volume
        lower_sweep.append({'x_mm':xc,'deg':deg,'base_common_mm3':round(bc,6),'tube_common_mm3':round(tc,6)})
        if bc>1e-4: fail(f'lower jaw/base collision X={xc} deg={deg}: {bc:.6f} mm3')
for xc in C.CLAMP_X:
    if next(q for q in lower_sweep if q['x_mm']==xc and q['deg']==-45)['tube_common_mm3']>0.05: fail(f'lower jaw has not released tube by -45 deg at X={xc}')
stage('lower sweep complete')

pin_checks=[]
for xc in C.CLAMP_X:
    p=PIN.copy(); p.translate(App.Vector(xc,C.PIN_Y,C.PIN_Z)); lo=LOWER.copy(); lo.translate(App.Vector(xc,0,0))
    bc=RIGHT_FULL.common(p).Volume; lc=lo.common(p).Volume
    pin_checks.append({'x_mm':xc,'base_common_mm3':round(bc,6),'lower_common_mm3':round(lc,6)})
    if bc>1e-4 or lc>1e-4: fail(f'pivot pin blocked at X={xc}')
stage('pin checks complete')

rim=C.box(-220,C.BOX_RIM_INNER_Y,RIM_BOTTOM_Z,440,C.RIM_Y,C.RIM_H)
plate_motion=[]
for d in (0,1,2,3,4,4.5,5.0,5.5):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-d,0)); bc=RIGHT_FULL.common(pl).Volume; rc=rim.common(pl).Volume
    plate_motion.append({'open_mm':d,'base_common_mm3':round(bc,6),'rim_common_mm3':round(rc,6),'rim_release_clearance_mm':round(C.BOX_RIM_INNER_Y-(PLATE_HOOK_Y1-d),3)})
    if bc>1e-4: fail(f'plate/base collision at open={d}: {bc:.6f} mm3')
    if rc>1e-4: fail(f'plate/rim collision at open={d}: {rc:.6f} mm3')
stage('plate motion complete')

thread_motion=[]
for d in (0,0.5,1.0,2.0,3.0,4.0,5.5):
    q=SPINDLE.copy(); q.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*d/THREAD_PITCH); q.translate(App.Vector(SPINDLE_X[0],PLATE_SPINDLE_Y-d,SPINDLE_Z))
    bc=RIGHT_FULL.common(q).Volume
    thread_motion.append({'open_mm':d,'rotation_deg':360*d/THREAD_PITCH,'base_common_mm3':round(bc,6)})
    if bc>1.0: fail(f'lead screw grossly collides with base at open={d}: {bc:.6f} mm3')
stage('thread motion complete')

def local_y_extent(d):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-d,0)); sp=SPINDLE.copy(); sp.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*d/THREAD_PITCH); sp.translate(App.Vector(0,PLATE_SPINDLE_Y-d,SPINDLE_Z))
    return max(RIGHT_FULL.BoundBox.YMax,pl.BoundBox.YMax,sp.BoundBox.YMax)
width_states={str(d):local_y_extent(d) for d in (0.0,5.5)}
holder_half=C.RACK_CTC/2+max(width_states.values())
if holder_half>C.BOX_W/2+0.02: fail(f'complete holder exceeds 600 mm box width: {2*holder_half:.3f} mm')

V={'version':'v60','stage':'full_direct_mechanism','architecture':'clean structural core + direct mechanics; no source rewriting','base':{'right_bbox_mm':[round(RIGHT_FULL.BoundBox.XLength,3),round(RIGHT_FULL.BoundBox.YLength,3),round(RIGHT_FULL.BoundBox.ZLength,3)],'left_bbox_mm':[round(LEFT_FULL.BoundBox.XLength,3),round(LEFT_FULL.BoundBox.YLength,3),round(LEFT_FULL.BoundBox.ZLength,3)],'mirror_delta_mm3':round(full_mirror_delta,9),'mirror_bound_delta_mm':round(mirror_bound_delta,9),'mirror_face_delta':mirror_face_delta,'pin_bore_clearance':pin_bore_clearance},'rack':{'clamp_spacing_mm':C.CLAMP_SPACING,'lower_sweep':lower_sweep,'pin_checks':pin_checks},'box_clamp':{'plate_travel_mm':PLATE_OPEN,'plate_motion':plate_motion,'spindle_x_mm':list(SPINDLE_X),'spindle_z_mm':SPINDLE_Z,'thread':'RH 8x2','integral_female_threads':True,'thread_motion':thread_motion,'width_states_local_y_mm':{k:round(v,3) for k,v in width_states.items()},'effective_total_width_mm':round(max(C.BOX_W,2*holder_half),3)},'failures':failures}
with open(os.path.join(OUT,'VALIDATION_v60_full.json'),'w',encoding='utf-8') as f: json.dump(V,f,indent=2)
if failures:
    print(json.dumps(V,indent=2),flush=True); raise SystemExit('V60 FULL HARD CHECKS FAILED: '+' | '.join(failures))

stage('exports')
parts={'eurobox_v60_base_right':RIGHT_FULL,'eurobox_v60_base_left':LEFT_FULL,'eurobox_v60_rack_lower':LOWER,'eurobox_v60_rack_pin':PIN,'eurobox_v60_rack_pin_clip':PIN_CLIP,'eurobox_v60_clamp_plate':PLATE,'eurobox_v60_lead_screw':SPINDLE,'eurobox_v60_knob':KNOB,'eurobox_v60_knob_retainer_nut':CAP_NUT,'eurobox_v60_plate_retainer_clip':PLATE_CLIP}
for name,sh in parts.items(): C.require_single(sh,name); C.export_shape(name,sh)

stage('assembly')
doc=App.newDocument('Eurobox_v60_assembly')
def add_obj(name,sh): o=doc.addObject('Part::Feature',name); o.Shape=sh; return o
RY=C.RACK_CTC/2; LY=-C.RACK_CTC/2
rb=RIGHT_FULL.copy(); rb.translate(App.Vector(0,RY,0)); add_obj('RIGHT_base',rb)
rp=PLATE.copy(); rp.translate(App.Vector(0,RY,0)); add_obj('RIGHT_plate',rp)
for xc in C.CLAMP_X:
    lo=LOWER.copy(); lo.translate(App.Vector(xc,RY,0)); add_obj('RIGHT_lower_'+str(int(xc)),lo)
for sx in SPINDLE_X:
    sp=SPINDLE.copy(); sp.translate(App.Vector(sx,RY+PLATE_SPINDLE_Y,SPINDLE_Z)); add_obj('RIGHT_spindle_'+str(int(sx)),sp)
def left_transform(sh):
    q=sh.copy(); q.rotate(App.Vector(0,0,0),App.Vector(0,0,1),180); q.translate(App.Vector(0,LY,0)); return q
add_obj('LEFT_base',left_transform(LEFT_FULL)); add_obj('LEFT_plate',left_transform(PLATE))
for xc in C.CLAMP_X:
    lo=LOWER.copy(); lo.translate(App.Vector(xc,0,0)); add_obj('LEFT_lower_'+str(int(xc)),left_transform(lo))
for sx in SPINDLE_X:
    sp=SPINDLE.copy(); sp.translate(App.Vector(sx,PLATE_SPINDLE_Y,SPINDLE_Z)); add_obj('LEFT_spindle_'+str(int(sx)),left_transform(sp))
add_obj('REF_right_rack_tube',C.cyl_x(C.RACK_R,400,-200,RY,0)); add_obj('REF_left_rack_tube',C.cyl_x(C.RACK_R,400,-200,LY,0))
doc.recompute(); doc.saveAs(os.path.join(OUT,'eurobox_v60_assembly.FCStd')); App.closeDocument(doc.Name)
with open(os.path.join(OUT,'README_BUILD_v60_full.txt'),'w',encoding='utf-8') as f:
    f.write('Eurobox v60 direct full mechanism build.\nNo apply_v60 source transforms. RIGHT is canonical; LEFT is exact X mirror.\n160 mm rack-clamp spacing, 20 mm front body reserve, 249..299 mm physical backstop, rear support at 299 mm.\nCORE One L INDX hard envelope 298 x 275 mm; v60 base X target <=296 mm.\n')
stage('complete'); print(json.dumps(V,indent=2),flush=True)
