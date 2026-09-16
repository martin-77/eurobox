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
# v50 used +/-42 mm. v60 can use the available 140 mm plate more effectively:
# +/-55 keeps 15 mm between screw axes and plate edges, leaves 4.4 mm between
# each 22 mm boss and its outer guide, and materially improves anti-twist leverage.
SPINDLE_X = (-55.0, 55.0)
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
# Final v50 datum: the complete cage terminates on the box support plane.  The
# first v60 rebuild incorrectly grew the guides/tie to Z=49.8 and changed the
# front architecture substantially.
PRINT_BASE_PLANE_Z = C.BOX_SUPPORT_Z
PRINT_GUIDE_Z1 = PRINT_BASE_PLANE_Z
PRINT_FRAME_BOSS_Z0 = 20.0
PRINT_FRAME_BOSS_Z1 = PRINT_BASE_PLANE_Z
PRINT_FRAME_TIE_T = 6.0
FINAL_DECK_Z0 = C.ARM_BOTTOM_Z
FINAL_DECK_Z1 = PRINT_GUIDE_Z0
GUIDE_STITCH_OVERLAP = 0.20
LOWER_SADDLE_R = 6.15

LOWER_FORK_SIDE_CLEAR = 0.40
LOWER_FORK_EAR_T = 4.60
LOWER_FORK_INNER_HALF_X = C.UPPER_PIVOT_W/2.0 + LOWER_FORK_SIDE_CLEAR
LOWER_FORK_OUTER_HALF_X = LOWER_FORK_INNER_HALF_X + LOWER_FORK_EAR_T
LOWER_FORK_W = 2.0 * LOWER_FORK_OUTER_HALF_X
LOWER_PIVOT_R = 5.0
LOWER_WEB_Z0 = -10.5
LOWER_WEB_TOP_Z = -1.5
RACK_M4_LOWER_CLEAR_D = 5.0

# Rack clamp closure.  Keep the proven M4 screw + side-loaded captive nut, but
# do not make the moving Lower a full-depth block all the way to the screw.
# The former v60 geometry put the Lower top face directly against the fixed
# bridge at Z=0 and left an M4x20 only partial nut engagement.  A dedicated
# closure tongue restores tightening travel, gives the screw a proper bearing
# pad and keeps the saddle body clear of the fixed bridge while it closes.
RACK_M4_SCREW_LENGTH = 20.0
RACK_TUBE_MIN_D = 12.00
RACK_CLOSURE_MAIN_Y0 = -6.0
RACK_CLOSURE_MAIN_Y1 = 6.0
RACK_CLOSURE_PAD_X = 24.0
RACK_CLOSURE_PAD_Y0 = 4.0
RACK_CLOSURE_PAD_Y1 = 18.0
RACK_CLOSURE_PAD_Z0 = -8.0
RACK_CLOSURE_PAD_Z1 = -3.5
# The M4x20 starts at the underside of the Lower tongue (Z=-8) and ends at Z=12.
# Keep 1 mm blind-tip clearance above it while retaining 5 mm of fixed bridge
# material above the bore.  This prevents the screw tip from bottoming in BASE.
RACK_M4_BASE_BORE_Z0 = -1.0
RACK_M4_BASE_BORE_Z1 = 13.0


def stage(msg):
    print('V60_STAGE ' + msg, flush=True)


def cyl_y(r, length, x=0.0, y=0.0, z=0.0):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def hex_z(af, height, z0=0.0):
    r = af / math.sqrt(3.0)
    pts = [App.Vector(r*math.cos(math.radians(30+60*i)), r*math.sin(math.radians(30+60*i)), z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0,0,height))


def z_to_y(shape, x=0.0, y=0.0, z=0.0):
    q = shape.copy(); q.rotate(App.Vector(0,0,0), App.Vector(1,0,0), -90.0); q.translate(App.Vector(x,y,z)); return q


def rotate_z180(shape):
    q = shape.copy(); q.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180.0); return q.removeSplitter()


def write_thread_scad(path, core_r, major_r, pitch, length, root_w, crest_w):
    txt = f'''$fn=48;\nmodule thread_solid(){{\n union(){{\n  cylinder(r={core_r},h={length});\n  linear_extrude(height={length},twist=360*{length}/{pitch},slices=ceil({length}/{pitch}*18),convexity=30)\n   polygon(points=[[{core_r}-0.08,-{root_w}/2],[{major_r},-{crest_w}/2],[{major_r},{crest_w}/2],[{core_r}-0.08,{root_w}/2]]);\n }}\n}}\nthread_solid();\n'''
    with open(path, 'w', encoding='utf-8') as f: f.write(txt)


def import_scad_shape(path):
    stl = os.path.splitext(path)[0] + '_compiled.stl'
    subprocess.run(['openscad','-o',stl,path], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = Mesh.Mesh(stl); sh = Part.Shape(); sh.makeShapeFromMesh(m.Topology, 0.035)
    if sh.ShapeType == 'Shell': sh = Part.makeSolid(sh)
    elif sh.ShapeType == 'Compound':
        solids=[]
        for shell in sh.Shells:
            try:
                q=Part.makeSolid(shell)
                if q.isValid() and q.Volume>0: solids.append(q)
            except Exception: pass
        if not solids: raise RuntimeError('No solid reconstructed from '+stl)
        sh=C.fuse_seq(solids,'compiled-thread-solids')
    sh=sh.removeSplitter(); C.require_single(sh,'compiled thread '+os.path.basename(path)); return sh


def make_c_clip(outer_r, inner_r, thickness, opening_w):
    ring=Part.makeCylinder(outer_r,thickness).cut(Part.makeCylinder(inner_r,thickness))
    opening=C.box(-opening_w/2,0,-0.2,opening_w,outer_r+1,thickness+0.4)
    q=ring.cut(opening).removeSplitter(); C.require_single(q,'c-clip'); return q


stage('lower hardware')
# The main saddle body stops inside the rack-tube tangent region instead of
# continuing to Y=15 at full depth.  That removes the accidental Z=0 hard stop
# against the fixed bridge.  The separate closure tongue carries the M4 load
# and leaves 3.5 mm nominal closing space below the fixed base.
lower_shell = C.box(
    -LOWER_FORK_OUTER_HALF_X,
    RACK_CLOSURE_MAIN_Y0,
    -14.5,
    LOWER_FORK_W,
    RACK_CLOSURE_MAIN_Y1-RACK_CLOSURE_MAIN_Y0,
    14.5,
)
lower_pivot_l = C.cyl_x(LOWER_PIVOT_R,LOWER_FORK_EAR_T,-LOWER_FORK_OUTER_HALF_X,C.PIN_Y,C.PIN_Z)
lower_pivot_r = C.cyl_x(LOWER_PIVOT_R,LOWER_FORK_EAR_T,LOWER_FORK_INNER_HALF_X,C.PIN_Y,C.PIN_Z)
# Side webs stop below the fixed bridge.  At Z=0 the old webs formed a tiny
# wedge collision as soon as the jaw rotated in the tightening direction.  A
# -1.5 mm top keeps >1 mm kinematic clearance at +3 deg while preserving a deep
# overlap into the saddle body below the tube cut.
lower_web_l = C.box(-LOWER_FORK_OUTER_HALF_X,C.PIN_Y,LOWER_WEB_Z0,LOWER_FORK_EAR_T,8.0,LOWER_WEB_TOP_Z-LOWER_WEB_Z0)
lower_web_r = C.box(LOWER_FORK_INNER_HALF_X,C.PIN_Y,LOWER_WEB_Z0,LOWER_FORK_EAR_T,8.0,LOWER_WEB_TOP_Z-LOWER_WEB_Z0)
closure_pad = C.box(
    -RACK_CLOSURE_PAD_X/2.0,
    RACK_CLOSURE_PAD_Y0,
    RACK_CLOSURE_PAD_Z0,
    RACK_CLOSURE_PAD_X,
    RACK_CLOSURE_PAD_Y1-RACK_CLOSURE_PAD_Y0,
    RACK_CLOSURE_PAD_Z1-RACK_CLOSURE_PAD_Z0,
)
LOWER = C.fuse_seq(
    [lower_shell,lower_pivot_l,lower_pivot_r,lower_web_l,lower_web_r,closure_pad],
    'lower-rack-fork-with-m4-closure-tongue',
)
lower_fork_slot = C.box(-LOWER_FORK_INNER_HALF_X,-20.0,-13.0,2.0*LOWER_FORK_INNER_HALF_X,15.5,15.5)
LOWER = LOWER.cut(lower_fork_slot).removeSplitter()
LOWER = LOWER.cut(C.cyl_x(LOWER_SADDLE_R,LOWER_FORK_W+2.0,-LOWER_FORK_OUTER_HALF_X-1.0,0,0)).removeSplitter()
LOWER = LOWER.cut(C.cyl_x(C.PIN_HOLE_D/2,LOWER_FORK_W+2.0,-LOWER_FORK_OUTER_HALF_X-1.0,C.PIN_Y,C.PIN_Z)).removeSplitter()
LOWER = LOWER.cut(Part.makeCylinder(RACK_M4_LOWER_CLEAR_D/2.0,16.5,App.Vector(0.0,C.RACK_CLOSURE_Y,-15.5),App.Vector(0,0,1))).removeSplitter()
C.require_single(LOWER,'lower-rack-jaw-final')

PIN = C.fuse_seq([
    C.cyl_x(2.0,29.8,-14.8,0,0), C.cyl_x(1.55,1.5,15.0,0,0),
    C.cyl_x(2.0,1.7,16.5,0,0), C.cyl_x(3.75,2.4,-17.2,0,0),
],'rack-pin')
PIN_CLIP=make_c_clip(4.2,1.65,1.5,3.0)
PLATE_CLIP=make_c_clip(5.4,2.45,1.4,3.8)


def make_cage_structure():
    parts=[
        C.box(-78.0,PRINT_GUIDE_Y0,PRINT_GUIDE_Z0,7.6,PRINT_GUIDE_Y1-PRINT_GUIDE_Y0,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(70.4,PRINT_GUIDE_Y0,PRINT_GUIDE_Z0,7.6,PRINT_GUIDE_Y1-PRINT_GUIDE_Y0,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(-78.0,CAGE_Y0-0.10,PRINT_BASE_PLANE_Z-PRINT_FRAME_TIE_T,156.0,CAGE_Y1-CAGE_Y0+0.20,PRINT_FRAME_TIE_T),
        C.box(-70.4,CAGE_Y0,FINAL_DECK_Z0,140.8,PRINT_GUIDE_Y1-CAGE_Y0,FINAL_DECK_Z1-FINAL_DECK_Z0),
        C.box(-78.0,CAGE_Y0-0.10,PRINT_GUIDE_Z0,7.6,PRINT_GUIDE_Y0-(CAGE_Y0-0.10)+0.35,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(70.4,CAGE_Y0-0.10,PRINT_GUIDE_Z0,7.6,PRINT_GUIDE_Y0-(CAGE_Y0-0.10)+0.35,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(-70.4-GUIDE_STITCH_OVERLAP,CAGE_Y0,FINAL_DECK_Z1-GUIDE_STITCH_OVERLAP,
              2*GUIDE_STITCH_OVERLAP,PRINT_GUIDE_Y1-CAGE_Y0,2*GUIDE_STITCH_OVERLAP),
        C.box(70.4-GUIDE_STITCH_OVERLAP,CAGE_Y0,FINAL_DECK_Z1-GUIDE_STITCH_OVERLAP,
              2*GUIDE_STITCH_OVERLAP,PRINT_GUIDE_Y1-CAGE_Y0,2*GUIDE_STITCH_OVERLAP),
    ]
    for sx in SPINDLE_X:
        parts.append(C.box(sx-11.0,CAGE_Y0,PRINT_FRAME_BOSS_Z0,22.0,CAGE_Y1-CAGE_Y0,PRINT_BASE_PLANE_Z-PRINT_FRAME_BOSS_Z0))
        parts.append(C.box(sx-11.35,CAGE_Y0,FINAL_DECK_Z1-0.35,22.70,CAGE_Y1-CAGE_Y0,PRINT_FRAME_BOSS_Z0-(FINAL_DECK_Z1-0.35)+0.35))
    return C.fuse_seq(parts,'direct-final-box-clamp-cage')


stage('cage fusion')
CAGE=make_cage_structure(); RIGHT_FULL=C.RIGHT.fuse(CAGE).removeSplitter(); C.require_single(RIGHT_FULL,'RIGHT full before rack-closure machining')

# Re-machine the complete blind M4 path after all structural fusions.  The core
# station originally only needed a short closure guide; the final M4x20 needs a
# deeper blind clearance above the captive nut so its tip cannot bottom out.
for xc in C.CLAMP_X:
    RIGHT_FULL = RIGHT_FULL.cut(
        Part.makeCylinder(
            C.RACK_M4_BASE_CLEAR_D/2.0,
            RACK_M4_BASE_BORE_Z1-RACK_M4_BASE_BORE_Z0,
            App.Vector(xc,C.RACK_CLOSURE_Y,RACK_M4_BASE_BORE_Z0),
            App.Vector(0,0,1),
        )
    ).removeSplitter()
C.require_single(RIGHT_FULL,'RIGHT full after rack-closure machining')

stage('thread solids')
MALE_SCAD=os.path.join(OUT,'v60_thread_RH_8x2_male.scad'); FEMALE_SCAD=os.path.join(OUT,'v60_thread_RH_8x2_female.scad'); CAP_FEMALE_SCAD=os.path.join(OUT,'v60_thread_RH_8x2_cap_female.scad')
write_thread_scad(MALE_SCAD,THREAD_CORE_R,THREAD_MAJOR/2,THREAD_PITCH,LEAD_THREAD_LEN,0.58,0.24)
write_thread_scad(FEMALE_SCAD,THREAD_FEMALE_CORE_R,THREAD_FEMALE_MAJOR_R,THREAD_PITCH,NUT_THREAD_LEN,0.76,0.40)
write_thread_scad(CAP_FEMALE_SCAD,3.36,4.34,THREAD_PITCH,5.4,1.05,0.24)
MALE_Z=import_scad_shape(MALE_SCAD).common(Part.makeCylinder(4.06,LEAD_THREAD_LEN)).removeSplitter()
FEMALE_Z=import_scad_shape(FEMALE_SCAD).common(Part.makeCylinder(4.28,NUT_THREAD_LEN)).removeSplitter()
CAP_FEMALE_Z=import_scad_shape(CAP_FEMALE_SCAD).common(Part.makeCylinder(4.38,5.4)).removeSplitter()

stage('integral thread machining')
FEMALE_NEGY=rotate_z180(z_to_y(FEMALE_Z))
for sx in SPINDLE_X:
    inner_y0=CAGE_Y0-0.50
    RIGHT_FULL=RIGHT_FULL.cut(cyl_y(5.90,NUT_THREAD_Y0-inner_y0+0.20,sx,inner_y0,SPINDLE_Z)).removeSplitter()
    cutter=FEMALE_NEGY.copy(); cutter.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z)); RIGHT_FULL=RIGHT_FULL.cut(cutter).removeSplitter()
    outer_y0=NUT_Y0
    RIGHT_FULL=RIGHT_FULL.cut(cyl_y(SHOULDER_D/2+0.35,PLATE_SPINDLE_Y-outer_y0+0.70,sx,outer_y0,SPINDLE_Z)).removeSplitter()
C.require_single(RIGHT_FULL,'RIGHT full after integral lead threads')

pin_bore_clearance=[]
for xc in C.CLAMP_X:
    probe=C.cyl_x(C.PIN_HOLE_D/2-0.05,38.0,xc-19.0,C.PIN_Y,C.PIN_Z); cv=RIGHT_FULL.common(probe).Volume
    pin_bore_clearance.append({'x_mm':xc,'probe_common_mm3':round(cv,9)})
    if cv>1e-5: raise RuntimeError(f'Rack pin bore closed at X={xc}: {cv:.6f} mm3')
C.require_single(RIGHT_FULL,'RIGHT full final'); LEFT_FULL=C.mirror_x(RIGHT_FULL)

stage('plate')
PLATE_BODY_Y0=C.BOX_RIM_INNER_Y-PLATE_Y; PLATE_HOOK_Y0=C.BOX_RIM_INNER_Y-WIDTH_RIM_CLEAR; PLATE_HOOK_Y1=C.BOX_RIM_INNER_Y+UNDERHOOK
PLATE=C.box(-PLATE_X/2,PLATE_BODY_Y0,PLATE_Z0,PLATE_X,PLATE_Y,PLATE_Z1-PLATE_Z0)
PLATE=PLATE.fuse(C.box(-PLATE_X/2,PLATE_HOOK_Y0,RIM_BOTTOM_Z-UNDERHOOK_T,PLATE_X,PLATE_HOOK_Y1-PLATE_HOOK_Y0,UNDERHOOK_T))
for sx in SPINDLE_X:
    PLATE=PLATE.cut(cyl_y(PLATE_HOLE_D/2,PLATE_Y+1,sx,PLATE_BODY_Y0-0.5,SPINDLE_Z))
    # v50 final: retainer counterbore belongs on the outboard face after Z180.
    PLATE=PLATE.cut(cyl_y(6.0,2.0,sx,PLATE_SPINDLE_Y-2.0,SPINDLE_Z))
PLATE=PLATE.removeSplitter(); C.require_single(PLATE,'box-clamp-plate')

stage('lead screw and knob')
SPINDLE_POSY=C.fuse_seq([cyl_y(3.0,0.4),cyl_y(2.5,1.4,0,0.4,0),cyl_y(3.0,SPINDLE_LOCAL_JOURNAL-1.8,0,1.8,0),cyl_y(SHOULDER_D/2,SPINDLE_LOCAL_SHOULDER,0,SPINDLE_LOCAL_JOURNAL,0),z_to_y(MALE_Z,0,SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER,0),z_to_y(hex_z(10.0,HEX_LEN),0,SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN,0)],'lead-spindle-positive-y')
STUD_SCAD=os.path.join(OUT,'v60_thread_RH_8x2_stud.scad'); write_thread_scad(STUD_SCAD,THREAD_CORE_R,THREAD_MAJOR/2,THREAD_PITCH,OUTER_STUD_LEN,0.58,0.24)
STUD_Z=import_scad_shape(STUD_SCAD).common(Part.makeCylinder(4.06,OUTER_STUD_LEN)).removeSplitter(); SPINDLE_POSY=SPINDLE_POSY.fuse(z_to_y(STUD_Z,0,SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN+HEX_LEN,0)).removeSplitter(); C.require_single(SPINDLE_POSY,'lead-spindle-with-stud')
SPINDLE=rotate_z180(SPINDLE_POSY)
KNOB=cyl_y(15.0,7.0)
for a in range(0,360,45):
    rr=16.2; x=rr*math.cos(math.radians(a)); z=rr*math.sin(math.radians(a)); KNOB=KNOB.cut(cyl_y(3.4,7.4,x,-0.2,z))
KNOB=KNOB.cut(cyl_y(4.3,7.4,0,-0.2,0)); KNOB=KNOB.cut(z_to_y(hex_z(10.35,5.2))).removeSplitter(); KNOB=rotate_z180(KNOB)
CAP_FEMALE_NEGY=rotate_z180(z_to_y(CAP_FEMALE_Z)); CAP_NUT=rotate_z180(z_to_y(hex_z(13.0,5.4))); CAP_NUT=CAP_NUT.cut(CAP_FEMALE_NEGY).removeSplitter(); C.require_single(CAP_NUT,'lead-knob-retainer-nut')

stage('hard validation')
failures=[]
def fail(msg): failures.append(msg)
for side,sh in (('RIGHT',RIGHT_FULL),('LEFT',LEFT_FULL)):
    C.require_single(sh,side+' full')
    if sh.BoundBox.XLength>C.V60_X_TARGET_MAX+1e-6: fail(f'{side} full base exceeds 296 mm X target: {sh.BoundBox.XLength:.3f}')
    if sh.BoundBox.YLength>C.INDX_Y_MAX+1e-6: fail(f'{side} full base exceeds 275 mm Y: {sh.BoundBox.YLength:.3f}')
left_back=C.mirror_x(LEFT_FULL); full_mirror_delta=abs(RIGHT_FULL.Volume-left_back.Volume)
mirror_bound_delta=max(abs(RIGHT_FULL.BoundBox.XMin-left_back.BoundBox.XMin),abs(RIGHT_FULL.BoundBox.XMax-left_back.BoundBox.XMax),abs(RIGHT_FULL.BoundBox.YMin-left_back.BoundBox.YMin),abs(RIGHT_FULL.BoundBox.YMax-left_back.BoundBox.YMax),abs(RIGHT_FULL.BoundBox.ZMin-left_back.BoundBox.ZMin),abs(RIGHT_FULL.BoundBox.ZMax-left_back.BoundBox.ZMax)); mirror_face_delta=abs(len(RIGHT_FULL.Faces)-len(left_back.Faces))
if full_mirror_delta>1e-4 or mirror_bound_delta>1e-6 or mirror_face_delta!=0: fail('full handed bases are not exact construction mirrors')
stage('mirror gate complete')

for x in (-70.4,70.4):
    stitch=C.box(x-GUIDE_STITCH_OVERLAP,CAGE_Y0,FINAL_DECK_Z1-GUIDE_STITCH_OVERLAP,2*GUIDE_STITCH_OVERLAP,PRINT_GUIDE_Y1-CAGE_Y0,2*GUIDE_STITCH_OVERLAP)
    if RIGHT_FULL.common(stitch).Volume/stitch.Volume<0.999: fail(f'guide/deck structural stitch missing at X={x}')

if C.UPPER_PIVOT_W<16.0: fail('Upper central rack-pivot bearing is too narrow')
if LOWER_FORK_EAR_T<4.2: fail('Replaceable Lower fork ears are too thin')
if not (0.6<=2*LOWER_FORK_SIDE_CLEAR<=1.2): fail('Upper/Lower fork running clearance outside 0.6..1.2 mm')
if abs(SPINDLE_X[0]+55.0)>1e-9 or abs(SPINDLE_X[1]-55.0)>1e-9: fail('v60 lead screws are not at widened +/-55 mm positions')
if abs(PRINT_BASE_PLANE_Z-C.BOX_SUPPORT_Z)>1e-9: fail('screw cage no longer terminates on box support plane')

# Rack M4 closure hard gates.  The screw bears on the underside of the dedicated
# tongue at Z=-8.0.  An M4x20 therefore reaches completely through the 3.6 mm
# captive nut instead of only catching part of it.  The tongue also leaves real
# closing travel rather than bottoming the Lower against the fixed bridge.
closure_nominal_gap = 0.0 - RACK_CLOSURE_PAD_Z1
closure_arm = C.RACK_CLOSURE_Y - C.PIN_Y
rack_tube_arm = 0.0 - C.PIN_Y
closure_mapped_tube_adjustment = closure_nominal_gap * rack_tube_arm / closure_arm
required_tube_adjustment = C.RACK_D - RACK_TUBE_MIN_D
rack_screw_tip_z = RACK_CLOSURE_PAD_Z0 + RACK_M4_SCREW_LENGTH
rack_nut_z1 = C.RACK_M4_NUT_Z0 + C.RACK_M4_NUT_H
rack_nut_engagement = max(0.0, min(rack_screw_tip_z, rack_nut_z1) - C.RACK_M4_NUT_Z0)
rack_tip_clearance = RACK_M4_BASE_BORE_Z1 - rack_screw_tip_z
closure_front_ligament = RACK_CLOSURE_PAD_Y1 - C.RACK_CLOSURE_Y - RACK_M4_LOWER_CLEAR_D/2.0
closure_side_ligament = (RACK_CLOSURE_PAD_X - RACK_M4_LOWER_CLEAR_D)/2.0
if closure_nominal_gap < 3.0: fail('Rack M4 closure lost its tightening gap')
if closure_mapped_tube_adjustment < required_tube_adjustment: fail('Rack M4 closure cannot cover measured rack-tube diameter range')
if rack_nut_engagement < 3.2: fail(f'M4x20 does not fully engage captive nut: {rack_nut_engagement:.3f} mm')
if rack_tip_clearance < 0.8: fail(f'M4x20 tip clearance in fixed BASE is too small: {rack_tip_clearance:.3f} mm')
if closure_front_ligament < 3.0: fail('Rack M4 closure tongue has insufficient material ahead of screw')
if closure_side_ligament < 6.0: fail('Rack M4 closure tongue has insufficient material beside screw')

# Verify the dedicated closure pad is materially tied into the moving jaw after
# the tube saddle and fork cuts.  A tiny edge-only connection must not pass.
closure_pad_probe=C.box(-RACK_CLOSURE_PAD_X/2.0,RACK_CLOSURE_PAD_Y0,RACK_CLOSURE_PAD_Z0,RACK_CLOSURE_PAD_X,RACK_CLOSURE_PAD_Y1-RACK_CLOSURE_PAD_Y0,RACK_CLOSURE_PAD_Z1-RACK_CLOSURE_PAD_Z0)
closure_pad_fraction=LOWER.common(closure_pad_probe).Volume/closure_pad_probe.Volume
if closure_pad_fraction<0.70: fail(f'Rack M4 closure tongue lost too much material: {closure_pad_fraction:.4f}')

tube=C.cyl_x(C.RACK_R,400,-200,0,0); lower_sweep=[]
for xc in C.CLAMP_X:
    for deg in (0,-15,-30,-45,-60,-75,-90):
        lo=LOWER.copy(); lo.rotate(App.Vector(0,C.PIN_Y,C.PIN_Z),App.Vector(1,0,0),deg); lo.translate(App.Vector(xc,0,0))
        bc=RIGHT_FULL.common(lo).Volume; tc=tube.common(lo).Volume
        lower_sweep.append({'x_mm':xc,'deg':deg,'base_common_mm3':round(bc,6),'tube_common_mm3':round(tc,6)})
        if bc>1e-4: fail(f'lower jaw/base collision X={xc} deg={deg}: {bc:.6f} mm3')
for xc in C.CLAMP_X:
    released = next(q for q in lower_sweep if q['x_mm']==xc and q['deg']==-45)
    if released['tube_common_mm3'] > 0.05:
        fail(f"lower jaw has not released tube by -45 deg at X={xc}")
stage('lower sweep complete')

# The previous full-depth Lower could only open: any positive closing movement
# immediately drove its Z=0 top face into the fixed bridge.  The revised saddle
# body must retain a small positive tightening sweep for real tube tolerances.
tightening_sweep=[]
for xc in C.CLAMP_X:
    for deg in (0,0.5,1.0,2.0,3.0):
        lo=LOWER.copy(); lo.rotate(App.Vector(0,C.PIN_Y,C.PIN_Z),App.Vector(1,0,0),deg); lo.translate(App.Vector(xc,0,0))
        bc=RIGHT_FULL.common(lo).Volume
        tightening_sweep.append({'x_mm':xc,'deg':deg,'base_common_mm3':round(bc,6)})
        if bc>1e-4: fail(f'lower jaw has no tightening travel X={xc} deg={deg}: {bc:.6f} mm3')
stage('tightening sweep complete')

pin_checks=[]
for xc in C.CLAMP_X:
    p=PIN.copy(); p.translate(App.Vector(xc,C.PIN_Y,C.PIN_Z)); lo=LOWER.copy(); lo.translate(App.Vector(xc,0,0))
    bc=RIGHT_FULL.common(p).Volume; lc=lo.common(p).Volume
    pin_checks.append({'x_mm':xc,'base_common_mm3':round(bc,6),'lower_common_mm3':round(lc,6)})
    if bc>1e-4 or lc>1e-4: fail(f'pivot pin blocked at X={xc}')
stage('pin checks complete')

closure_checks=[]
for xc in C.CLAMP_X:
    # Model the complete Ø4 metal screw shank from the underside of the Lower
    # tongue to the M4x20 tip.  BASE must be completely clear along that path;
    # the separate captive nut is intentionally not part of RIGHT_FULL.
    screw_probe=Part.makeCylinder(2.0,RACK_M4_SCREW_LENGTH,App.Vector(xc,C.RACK_CLOSURE_Y,RACK_CLOSURE_PAD_Z0),App.Vector(0,0,1))
    base_cv=RIGHT_FULL.common(screw_probe).Volume
    lo=LOWER.copy(); lo.translate(App.Vector(xc,0,0))
    lower_probe=Part.makeCylinder(RACK_M4_LOWER_CLEAR_D/2.0-0.05,16.0,App.Vector(xc,C.RACK_CLOSURE_Y,-15.0),App.Vector(0,0,1))
    lower_cv=lo.common(lower_probe).Volume
    tube_cv=tube.common(screw_probe).Volume
    closure_checks.append({'x_mm':xc,'base_probe_common_mm3':round(base_cv,6),'lower_probe_common_mm3':round(lower_cv,6),'tube_common_mm3':round(tube_cv,6)})
    if base_cv>1e-4: fail(f'M4x20 full screw path blocked in fixed BASE at X={xc}')
    if lower_cv>1e-4: fail(f'M4 Lower closure bore blocked at X={xc}')
    if tube_cv>1e-4: fail(f'M4 closure path intersects rack tube at X={xc}')

rim=C.box(-220,C.BOX_RIM_INNER_Y,RIM_BOTTOM_Z,440,C.RIM_Y,C.RIM_H); plate_motion=[]
for d in (0,1,2,3,4,4.5,5.0,5.5):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-d,0)); bc=RIGHT_FULL.common(pl).Volume; rc=rim.common(pl).Volume
    plate_motion.append({'open_mm':d,'base_common_mm3':round(bc,6),'rim_common_mm3':round(rc,6),'rim_release_clearance_mm':round(C.BOX_RIM_INNER_Y-(PLATE_HOOK_Y1-d),3)})
    if bc>1e-4: fail(f'plate/base collision at open={d}: {bc:.6f} mm3')
    if rc>1e-4: fail(f'plate/rim collision at open={d}: {rc:.6f} mm3')
stage('plate motion complete')

thread_motion=[]
for d in (0,0.5,1.0,2.0,3.0,4.0,5.5):
    q=SPINDLE.copy(); q.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*d/THREAD_PITCH); q.translate(App.Vector(SPINDLE_X[0],PLATE_SPINDLE_Y-d,SPINDLE_Z)); bc=RIGHT_FULL.common(q).Volume
    thread_motion.append({'open_mm':d,'rotation_deg':360*d/THREAD_PITCH,'base_common_mm3':round(bc,6)})
    if bc>1.0: fail(f'lead screw grossly collides with base at open={d}: {bc:.6f} mm3')
stage('thread motion complete')

def local_y_extent(d):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-d,0)); sp=SPINDLE.copy(); sp.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*d/THREAD_PITCH); sp.translate(App.Vector(0,PLATE_SPINDLE_Y-d,SPINDLE_Z)); return max(RIGHT_FULL.BoundBox.YMax,pl.BoundBox.YMax,sp.BoundBox.YMax)
width_states={str(d):local_y_extent(d) for d in (0.0,5.5)}; holder_half=C.RACK_CTC/2+max(width_states.values())
if holder_half>C.BOX_W/2+0.02: fail(f'complete holder exceeds 600 mm box width: {2*holder_half:.3f} mm')

V={'version':'v60','stage':'full_direct_mechanism_v50_solutions_restored','architecture':'clean structural core + proven v50 rack joint/backstop/drop/cage solutions','base':{'right_bbox_mm':[round(RIGHT_FULL.BoundBox.XLength,3),round(RIGHT_FULL.BoundBox.YLength,3),round(RIGHT_FULL.BoundBox.ZLength,3)],'left_bbox_mm':[round(LEFT_FULL.BoundBox.XLength,3),round(LEFT_FULL.BoundBox.YLength,3),round(LEFT_FULL.BoundBox.ZLength,3)],'mirror_delta_mm3':round(full_mirror_delta,9),'mirror_bound_delta_mm':round(mirror_bound_delta,9),'mirror_face_delta':mirror_face_delta,'pin_bore_clearance':pin_bore_clearance,'guide_stitch_overlap_mm':GUIDE_STITCH_OVERLAP,'cage_top_z_mm':PRINT_BASE_PLANE_Z},'rack':{'clamp_spacing_mm':C.CLAMP_SPACING,'joint':'v51 broad central Upper bearing + replaceable Lower fork','upper_pivot_width_mm':C.UPPER_PIVOT_W,'lower_fork_outer_width_mm':LOWER_FORK_W,'lower_fork_ear_thickness_mm':LOWER_FORK_EAR_T,'lower_web_top_z_mm':LOWER_WEB_TOP_Z,'lower_sweep':lower_sweep,'tightening_sweep':tightening_sweep,'pin_checks':pin_checks,'m4_closure_checks':closure_checks,'m4_closure':{'mode':'M4x20 from below into side-loaded captive M4 nut','screw_length_mm':RACK_M4_SCREW_LENGTH,'lower_clearance_d_mm':RACK_M4_LOWER_CLEAR_D,'base_clearance_d_mm':C.RACK_M4_BASE_CLEAR_D,'base_bore_z_mm':[RACK_M4_BASE_BORE_Z0,RACK_M4_BASE_BORE_Z1],'nut_pocket_af_mm':C.RACK_M4_NUT_AF,'nut_pocket_height_mm':C.RACK_M4_NUT_H,'closure_pad_x_mm':RACK_CLOSURE_PAD_X,'closure_pad_y_mm':[RACK_CLOSURE_PAD_Y0,RACK_CLOSURE_PAD_Y1],'closure_pad_z_mm':[RACK_CLOSURE_PAD_Z0,RACK_CLOSURE_PAD_Z1],'closure_pad_material_fraction':round(closure_pad_fraction,6),'nominal_gap_mm':round(closure_nominal_gap,3),'mapped_tube_adjustment_mm':round(closure_mapped_tube_adjustment,3),'required_tube_adjustment_mm':round(required_tube_adjustment,3),'nut_engagement_mm':round(rack_nut_engagement,3),'tip_clearance_mm':round(rack_tip_clearance,3),'front_ligament_mm':round(closure_front_ligament,3),'side_ligament_mm':round(closure_side_ligament,3)}},'box_clamp':{'plate_travel_mm':PLATE_OPEN,'plate_motion':plate_motion,'spindle_x_mm':list(SPINDLE_X),'spindle_spacing_mm':SPINDLE_X[1]-SPINDLE_X[0],'spindle_z_mm':SPINDLE_Z,'thread':'RH 8x2','integral_female_threads':True,'thread_motion':thread_motion,'width_states_local_y_mm':{k:round(v,3) for k,v in width_states.items()},'effective_total_width_mm':round(max(C.BOX_W,2*holder_half),3)},'failures':failures}
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
    f.write('Eurobox v60 direct build with proven v50 mechanical solutions restored.\n')
    f.write('Broad fixed Upper pivot, relieved replaceable Lower fork, positive M4 closure with dedicated tightening tongue and side-loaded captive nut.\n')
    f.write('Rack closure is dimensioned for an M4x20 from below with full captive-nut engagement, blind-tip clearance and positive tightening travel.\n')
    f.write('Outboard rear-stop contact wall, closed holm heads with DROPs, stitched cage/deck seams.\n')
    f.write('Final cage top is exactly the 39.54 mm box support plane; lead screws widened to +/-55 mm.\n')
    f.write('160 mm rack-clamp spacing; CORE One L INDX hard envelope 298 x 275 mm.\n')
stage('complete'); print(json.dumps(V,indent=2),flush=True)
