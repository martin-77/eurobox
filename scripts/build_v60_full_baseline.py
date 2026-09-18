import os
import math
import json
import subprocess
import shutil
import struct
import FreeCAD as App
import Part
import Mesh
import build_v60 as C
import v60_knob_profile as KP

OUT = C.OUT
RIM_BOTTOM_Z = C.BOX_SUPPORT_Z - C.RIM_H

# The box-clamp stations are no longer symmetric around X=0.  Each station is
# positioned from the inner face of its nearest load-bearing holm with the same
# boss-to-holm clearance.  The plate keeps the proven 15 mm screw-to-edge margin
# on both ends and therefore grows with the useful station span.
SPINDLE_X = tuple(C.BOX_CLAMP_SPINDLE_X)
PLATE_X0 = C.BOX_CLAMP_PLATE_X0
PLATE_X1 = C.BOX_CLAMP_PLATE_X1
PLATE_X = PLATE_X1 - PLATE_X0
PLATE_Y = 8.0
PLATE_Z0 = 16.0
PLATE_Z1 = 46.0
PLATE_OPEN = 5.5
PLATE_HOLE_D = 6.5
PLATE_RETAINER_COUNTERBORE_D = 12.0
PLATE_RETAINER_COUNTERBORE_DEPTH = 2.0
# Radial service channel in the OUTBOARD face.  Without this, the C-clip could
# exist in CAD but could never be slid sideways into the shaft groove because
# the circular counterbore was completely enclosed by plate material.
PLATE_RETAINER_CHANNEL_W = 11.4
UNDERHOOK = 4.2
UNDERHOOK_T = 4.0
# Support-free DROP for the visible green underhook.  This is deliberately on
# the OUTBOARD / knob side of the clamp plate -- the previous support attempts
# modified BASE/holm geometry and could never appear under this ledge.
PLATE_UNDERHOOK_DROP_CLEARANCE = 0.40
PLATE_KNOB_RELIEF_Y_DEPTH = (
    UNDERHOOK - KNOB_STANDOFF + PLATE_UNDERHOOK_DROP_CLEARANCE
)
PLATE_KNOB_RELIEF_R = KP.KNOB_R + 0.50
SPINDLE_Z = 31.0
THREAD_MAJOR = 8.0
THREAD_PITCH = 2.0
THREAD_CORE_R = 3.25
# Real printable RH8x2 female geometry shared by BOTH printed female parts:
# the removable lead-nut wear cartridge and the knob-retainer nut.
THREAD_FEMALE_CORE_R = 3.50
THREAD_FEMALE_MAJOR_R = 4.25
CAP_THREAD_FEMALE_CORE_R = THREAD_FEMALE_CORE_R
CAP_THREAD_FEMALE_MAJOR_R = THREAD_FEMALE_MAJOR_R
RH8_MALE_ROOT_W = 1.20
RH8_MALE_CREST_W = 0.60
RH8_FEMALE_ROOT_W = 1.50
RH8_FEMALE_CREST_W = 0.90
RH8_FEMALE_CREST_MATERIAL_W = THREAD_PITCH - RH8_FEMALE_ROOT_W

LEAD_THREAD_LEN = 22.2
NUT_THREAD_LEN = 14.0
SHOULDER_D = 11.0
SPINDLE_LOCAL_JOURNAL = 8.0
SPINDLE_LOCAL_SHOULDER = 1.8
# The grip must sit clear of the underhook/drop on the OUTBOARD face of the
# moving clamp plate.  Keep the proven 7 mm full-depth hex engagement.  A
# 1.8 mm exposed stand-off plus a local hook-tip relief gives 0.4 mm running
# clearance while keeping the COMPLETE knob + retainer stack inside 600 mm.
KNOB_STANDOFF = 1.8
HEX_LEN = KNOB_STANDOFF + KP.KNOB_H
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
GUIDE_RUNNING_CLEAR_X = 0.40
GUIDE_T = 7.60
GUIDE_LEFT_INNER_X = PLATE_X0 - GUIDE_RUNNING_CLEAR_X
GUIDE_LEFT_OUTER_X = GUIDE_LEFT_INNER_X - GUIDE_T
GUIDE_RIGHT_INNER_X = PLATE_X1 + GUIDE_RUNNING_CLEAR_X
GUIDE_RIGHT_OUTER_X = GUIDE_RIGHT_INNER_X + GUIDE_T
STATION_TIE_OVERLAP_X = 0.35
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

# Structural cage reinforcement.  The removable lead-nut cartridge remains the
# wear part; these members reinforce only its fixed housing.  All reinforcement
# stays behind/below the moving clamp-plate envelope so cartridge insertion,
# spindle travel and plate opening remain serviceable.
CAGE_STRUCT_Y1 = min(CAGE_Y1, C.PLATE_SWEEP_Y0 - 0.20)
CAGE_CROSS_OVERLAP_X = 0.35
STATION_FLOOR_Y1 = min(PRINT_GUIDE_Y0, C.PLATE_SWEEP_Y0 - 0.10)
STATION_FLOOR_BOSS_OVERLAP_Z = 0.35

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
    # Legacy generator retained ONLY for the already-proven main spindle /
    # removable-cartridge pair.  Do not use this for new printed threads.
    txt = f'''$fn=48;\nmodule thread_solid(){{\n union(){{\n  cylinder(r={core_r},h={length});\n  linear_extrude(height={length},twist=360*{length}/{pitch},slices=ceil({length}/{pitch}*18),convexity=30)\n   polygon(points=[[{core_r}-0.08,-{root_w}/2],[{major_r},-{crest_w}/2],[{major_r},{crest_w}/2],[{core_r}-0.08,{root_w}/2]]);\n }}\n}}\nthread_solid();\n'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt)


def write_true_thread_scad(path, core_r, major_r, pitch, length, root_w, crest_w, overrun=0.0):
    # True radial/axial trapezoid swept around a helix.  root_w/crest_w are
    # actual axial dimensions, unlike the old twisted-XY-ribbon generator.
    if root_w >= pitch or crest_w >= pitch:
        raise RuntimeError(
            f'Invalid true RH thread profile: root={root_w:.3f} crest={crest_w:.3f} '
            f'must both be < pitch={pitch:.3f}'
        )
    inner_r = core_r - 0.12
    root_half = root_w / 2.0
    crest_half = crest_w / 2.0
    a0 = -360.0 * overrun / pitch
    a1 = 360.0 * (length + overrun) / pitch
    span = length + 2.0*overrun
    steps = max(48, int(math.ceil((a1-a0)/360.0 * 40.0)))
    txt = f'''$fn=96;
pitch={pitch};
core_r={core_r};
inner_r={inner_r};
major_r={major_r};
root_half={root_half};
crest_half={crest_half};
a0={a0};
a1={a1};
steps={steps};
overrun={overrun};
length={length};
function ang(i)=a0+(a1-a0)*i/steps;
function zc(i)=pitch*ang(i)/360;
function pt(r,a,z)=[r*cos(a),r*sin(a),z];
pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
       each [pt(inner_r,a,z-root_half),
             pt(major_r,a,z-crest_half),
             pt(major_r,a,z+crest_half),
             pt(inner_r,a,z+root_half)]];
side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
  [4*(i+1)+((j+1)%4),4*(i+1)+j,4*i+j],
  [4*i+((j+1)%4),4*(i+1)+((j+1)%4),4*i+j]
]];
start_face=[[2,1,0],[3,2,0]];
e=4*steps;
end_face=[[e+1,e+2,e+3],[e,e+1,e+3]];
union(){{
  translate([0,0,-overrun]) cylinder(r=core_r,h={span});
  polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=100);
}}
'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt)

def write_complete_spindle_scad(path):
    # One CGAL union creates the COMPLETE printable lead screw around the plate
    # datum.  z=0 is the OUTBOARD plate face:
    #   negative z -> outboard knob hex + retainer stud
    #   positive z -> journal through plate + shoulder + working thread
    # This is the only arrangement that keeps the hand knob accessible while
    # the working RH8x2 thread remains inside the fixed lead-nut cartridge.
    journal = SPINDLE_LOCAL_JOURNAL
    shoulder0 = journal
    main0 = journal + SPINDLE_LOCAL_SHOULDER
    main1 = main0 + LEAD_THREAD_LEN
    hex0 = -HEX_LEN
    stud0 = -(HEX_LEN + OUTER_STUD_LEN)
    main_steps = max(64, int(math.ceil(LEAD_THREAD_LEN / THREAD_PITCH * 40.0)))
    stud_steps = max(48, int(math.ceil(OUTER_STUD_LEN / THREAD_PITCH * 40.0)))
    txt = f'''$fn=96;
pitch={THREAD_PITCH};
core_r={THREAD_CORE_R};
major_r={THREAD_MAJOR/2.0};
root_half={RH8_MALE_ROOT_W/2.0};
crest_half={RH8_MALE_CREST_W/2.0};
inner_r={THREAD_CORE_R-0.12};

module ridge_rh(z0,len,steps){{
  a1=360*len/pitch;
  function ang(i)=a1*i/steps;
  function zc(i)=pitch*ang(i)/360;
  function pt(r,a,z)=[r*cos(a),r*sin(a),z];
  pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
         each [pt(inner_r,a,z-root_half),
               pt(major_r,a,z-crest_half),
               pt(major_r,a,z+crest_half),
               pt(inner_r,a,z+root_half)]];
  side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
    [4*(i+1)+((j+1)%4),4*(i+1)+j,4*i+j],
    [4*i+((j+1)%4),4*(i+1)+((j+1)%4),4*i+j]
  ]];
  start_face=[[2,1,0],[3,2,0]];
  e=4*steps;
  end_face=[[e+1,e+2,e+3],[e,e+1,e+3]];
  translate([0,0,z0])
    polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=100);
}}

module ridge_lh(z0,len,steps){{
  a1=-360*len/pitch;
  function ang(i)=a1*i/steps;
  function zc(i)=pitch*(-ang(i))/360;
  function pt(r,a,z)=[r*cos(a),r*sin(a),z];
  pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
         each [pt(inner_r,a,z-root_half),
               pt(major_r,a,z-crest_half),
               pt(major_r,a,z+crest_half),
               pt(inner_r,a,z+root_half)]];
  side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
    [4*(i+1)+((j+1)%4),4*(i+1)+j,4*i+j],
    [4*i+((j+1)%4),4*(i+1)+((j+1)%4),4*i+j]
  ]];
  start_face=[[2,1,0],[3,2,0]];
  e=4*steps;
  end_face=[[e+1,e+2,e+3],[e,e+1,e+3]];
  translate([0,0,z0])
    polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=100);
}}

module spindle_z(){{
  union(){{
    // OUTBOARD: retainer stud then the full 7 mm knob hex.
    translate([0,0,{stud0}]) cylinder(r=core_r,h={OUTER_STUD_LEN+0.25});
    ridge_lh({stud0},{OUTER_STUD_LEN},{stud_steps});
    translate([0,0,{hex0}]) cylinder(r={10.0/math.sqrt(3.0)},h={HEX_LEN},$fn=6);

    // Small internal bridge only inside the Ø6.5 plate hole, never enlarging
    // the journal or filling the C-clip groove.
    translate([0,0,-0.20]) cylinder(r=3.0,h=0.60);

    // Journal through the plate with the printable C-clip groove at the
    // outboard face.
    cylinder(r=3.0,h=0.4);
    translate([0,0,0.4]) cylinder(r=2.5,h=1.4);
    translate([0,0,1.8]) cylinder(r=3.0,h={SPINDLE_LOCAL_JOURNAL-1.8});

    // INBOARD: thrust shoulder and working lead thread.
    translate([0,0,{shoulder0}]) cylinder(r={SHOULDER_D/2.0},h={SPINDLE_LOCAL_SHOULDER});
    translate([0,0,{main0-0.25}]) cylinder(r=core_r,h={LEAD_THREAD_LEN+0.25});
    ridge_rh({main0},{LEAD_THREAD_LEN},{main_steps});
  }}
}}

// Exact installed orientation. +z goes inboard toward -Y; -z goes outboard.
rotate([0,0,180]) rotate([-90,0,0]) spindle_z();
'''
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(txt)


def stl_edge_topology(path, tol=1e-5):
    # Prusa-style mesh sanity gate using welded vertices.  A printable closed
    # part must have every undirected edge used by exactly two triangles.
    with open(path, 'rb') as fh:
        data = fh.read()

    tris = []
    if len(data) >= 84:
        n = struct.unpack_from('<I', data, 80)[0]
        if 84 + n * 50 == len(data):
            off = 84
            for _ in range(n):
                vals = struct.unpack_from('<12fH', data, off)
                tris.append((vals[3:6], vals[6:9], vals[9:12]))
                off += 50

    if not tris:
        verts = []
        text = data.decode('ascii', errors='ignore')
        for line in text.splitlines():
            q = line.strip().split()
            if len(q) == 4 and q[0] == 'vertex':
                verts.append(tuple(float(v) for v in q[1:]))
        if len(verts) % 3:
            raise RuntimeError(f'Cannot parse STL triangles: {path}')
        tris = [tuple(verts[i:i+3]) for i in range(0, len(verts), 3)]

    def vk(p):
        return tuple(int(round(float(c) / tol)) for c in p)

    edges = {}
    degenerate = 0
    for tri in tris:
        v = [vk(p) for p in tri]
        for a, b in ((v[0],v[1]),(v[1],v[2]),(v[2],v[0])):
            if a == b:
                degenerate += 1
                continue
            e = (a,b) if a < b else (b,a)
            edges[e] = edges.get(e,0) + 1

    return {
        'triangles': len(tris),
        'boundary_edges': sum(1 for n in edges.values() if n == 1),
        'nonmanifold_edges': sum(1 for n in edges.values() if n > 2),
        'degenerate_edges': degenerate,
    }


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
# Axial spindle retainer for the moving box-clamp plate.  The Ø5.0 shaft
# groove gets 0.05 mm radial running clearance; the 3.8 mm C-opening still
# snaps around the groove and cannot pass through the Ø6.5 plate hole.
PLATE_CLIP=make_c_clip(5.4,2.55,1.4,3.8)


def make_station_floor_gusset(sx):
    # A broad local wedge takes spindle/cartridge load down into the low deck in
    # front of each cage.  Its top remains below the cartridge pocket, and its
    # nose remains below the moving clamp plate.
    x0 = sx - C.BOX_CLAMP_BOSS_HALF_X - CAGE_CROSS_OVERLAP_X
    x1 = sx + C.BOX_CLAMP_BOSS_HALF_X + CAGE_CROSS_OVERLAP_X
    yz = [
        App.Vector(0.0,CAGE_Y0,FINAL_DECK_Z0),
        App.Vector(0.0,STATION_FLOOR_Y1,FINAL_DECK_Z0),
        App.Vector(0.0,STATION_FLOOR_Y1,FINAL_DECK_Z1),
        App.Vector(0.0,CAGE_Y0,PRINT_FRAME_BOSS_Z0+STATION_FLOOR_BOSS_OVERLAP_Z),
    ]
    face = Part.Face(Part.makePolygon(yz+[yz[0]]))
    q = face.extrude(App.Vector(x1-x0,0,0))
    q.translate(App.Vector(x0,0,0))
    return q.removeSplitter()


def make_cage_reinforcement():
    # The cage remains a service housing for the removable wear cartridge.
    # Reinforcement therefore wraps around the service volume instead of filling
    # it: full-area holm ties, a hollow cross-beam with vertical DROPs, and
    # low floor gussets beneath each station.
    left_sx, right_sx = SPINDLE_X
    left_boss_x0 = left_sx - C.BOX_CLAMP_BOSS_HALF_X
    left_boss_x1 = left_sx + C.BOX_CLAMP_BOSS_HALF_X
    right_boss_x0 = right_sx - C.BOX_CLAMP_BOSS_HALF_X
    right_boss_x1 = right_sx + C.BOX_CLAMP_BOSS_HALF_X

    # Replace the former narrow top ties with full-area connections across the
    # complete 12 mm holm-to-cage gaps.
    holm_left = C.box(
        C.FRONT_HOLM_INNER_X-STATION_TIE_OVERLAP_X,CAGE_Y0,FINAL_DECK_Z0,
        left_boss_x0-C.FRONT_HOLM_INNER_X+2.0*STATION_TIE_OVERLAP_X,
        CAGE_STRUCT_Y1-CAGE_Y0,PRINT_BASE_PLANE_Z-FINAL_DECK_Z0,
    )
    holm_right = C.box(
        right_boss_x1-STATION_TIE_OVERLAP_X,CAGE_Y0,FINAL_DECK_Z0,
        C.REAR_HOLM_INNER_X-right_boss_x1+2.0*STATION_TIE_OVERLAP_X,
        CAGE_STRUCT_Y1-CAGE_Y0,PRINT_BASE_PLANE_Z-FINAL_DECK_Z0,
    )

    # I/box-beam style connection between the two cage stations.  The two
    # vertical webs are the transverse equivalent of the side-holm DROPs.
    cross_x0 = left_boss_x1-CAGE_CROSS_OVERLAP_X
    cross_x1 = right_boss_x0+CAGE_CROSS_OVERLAP_X
    cross_y0 = CAGE_Y0
    cross_y1 = CAGE_STRUCT_Y1
    cross_web_z0 = FINAL_DECK_Z0 + C.FLANGE_T
    cross_web_z1 = PRINT_BASE_PLANE_Z - C.FLANGE_T
    cross = [
        C.box(cross_x0,cross_y0,FINAL_DECK_Z0,
              cross_x1-cross_x0,cross_y1-cross_y0,C.FLANGE_T),
        C.box(cross_x0,cross_y0,PRINT_BASE_PLANE_Z-C.FLANGE_T,
              cross_x1-cross_x0,cross_y1-cross_y0,C.FLANGE_T),
        C.box(cross_x0,cross_y0,cross_web_z0,
              cross_x1-cross_x0,C.WEB_T,cross_web_z1-cross_web_z0),
        C.box(cross_x0,cross_y1-C.WEB_T,cross_web_z0,
              cross_x1-cross_x0,C.WEB_T,cross_web_z1-cross_web_z0),
    ]

    probes = {
        'holm_left': holm_left,
        'holm_right': holm_right,
        'cross_bottom': cross[0],
        'cross_top': cross[1],
        'cross_drop_rear': cross[2],
        'cross_drop_front': cross[3],
        'station_floor_left': make_station_floor_gusset(left_sx),
        'station_floor_right': make_station_floor_gusset(right_sx),
    }
    return probes


def make_cage_structure():
    parts=[
        C.box(GUIDE_LEFT_OUTER_X,PRINT_GUIDE_Y0,PRINT_GUIDE_Z0,
              GUIDE_T,PRINT_GUIDE_Y1-PRINT_GUIDE_Y0,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(GUIDE_RIGHT_INNER_X,PRINT_GUIDE_Y0,PRINT_GUIDE_Z0,
              GUIDE_T,PRINT_GUIDE_Y1-PRINT_GUIDE_Y0,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(GUIDE_LEFT_OUTER_X,CAGE_Y0-0.10,PRINT_GUIDE_Z0,
              GUIDE_T,PRINT_GUIDE_Y0-(CAGE_Y0-0.10)+0.35,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
        C.box(GUIDE_RIGHT_INNER_X,CAGE_Y0-0.10,PRINT_GUIDE_Z0,
              GUIDE_T,PRINT_GUIDE_Y0-(CAGE_Y0-0.10)+0.35,PRINT_BASE_PLANE_Z-PRINT_GUIDE_Z0),
    ]

    for sx in SPINDLE_X:
        boss_x0 = sx - C.BOX_CLAMP_BOSS_HALF_X
        boss_x1 = sx + C.BOX_CLAMP_BOSS_HALF_X
        parts.append(C.box(
            boss_x0,CAGE_Y0,PRINT_FRAME_BOSS_Z0,
            boss_x1-boss_x0,CAGE_Y1-CAGE_Y0,PRINT_BASE_PLANE_Z-PRINT_FRAME_BOSS_Z0,
        ))
        parts.append(C.box(
            boss_x0,CAGE_Y0,FINAL_DECK_Z1-0.35,
            boss_x1-boss_x0,CAGE_Y1-CAGE_Y0,
            PRINT_FRAME_BOSS_Z0-(FINAL_DECK_Z1-0.35)+0.35,
        ))

    reinforcement = make_cage_reinforcement()
    parts.extend(reinforcement.values())
    return C.fuse_seq(parts,'serviceable-reinforced-box-clamp-cage')


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
FEMALE_SCAD=os.path.join(OUT,'v60_thread_RH_8x2_female.scad')
CAP_FEMALE_SCAD=os.path.join(OUT,'v60_thread_RH_8x2_cap_female_true.scad')

# The removable lead-nut gets the real radial/axial female RH8x2 cutter.
write_true_thread_scad(
    FEMALE_SCAD,THREAD_FEMALE_CORE_R,THREAD_FEMALE_MAJOR_R,
    THREAD_PITCH,NUT_THREAD_LEN,RH8_FEMALE_ROOT_W,RH8_FEMALE_CREST_W,
    overrun=THREAD_PITCH,
)
FEMALE_Z=import_scad_shape(FEMALE_SCAD)

# The knob-retainer gets its own real radial/axial female RH8x2 cutter.
write_true_thread_scad(
    CAP_FEMALE_SCAD,CAP_THREAD_FEMALE_CORE_R,CAP_THREAD_FEMALE_MAJOR_R,
    THREAD_PITCH,5.4,RH8_FEMALE_ROOT_W,RH8_FEMALE_CREST_W,
    overrun=THREAD_PITCH,
)
CAP_FEMALE_Z=import_scad_shape(CAP_FEMALE_SCAD)

stage('v50 direct cartridge pockets - no integral box-clamp threads in BASE')
FEMALE_NEGY=rotate_z180(z_to_y(FEMALE_Z))

# Canonical v50 box-clamp architecture: the BASE is only a smooth housing.
# The one and only working RH8x2 female thread lives in a removable cartridge.
LEAD_NUT_PIN_LOCAL_Y = -7.0
LEAD_NUT_PIN_LOCAL_Z = 10.0
LEAD_NUT_PIN_HOLE_D = 3.4
NUT_PIN_SHAFT_D = 3.0
NUT_PIN_GROOVE_D = 2.4
NUT_PIN_GROOVE_X0 = 11.4
NUT_PIN_GROOVE_W = 1.6
NUT_PIN_CLIP_T = 1.3
NUT_PIN_CLIP_X = NUT_PIN_GROOVE_X0 + (NUT_PIN_GROOVE_W-NUT_PIN_CLIP_T)/2.0

LEAD_NUT = C.box(-8.0,-NUT_THREAD_LEN,-7.0,16.0,NUT_THREAD_LEN,14.0)
LEAD_NUT = LEAD_NUT.fuse(C.box(-6.0,-11.0,7.0,12.0,8.0,6.0)).removeSplitter()
LEAD_NUT = LEAD_NUT.cut(FEMALE_NEGY).removeSplitter()
LEAD_NUT = LEAD_NUT.cut(C.cyl_x(
    LEAD_NUT_PIN_HOLE_D/2.0,20.0,-10.0,
    LEAD_NUT_PIN_LOCAL_Y,LEAD_NUT_PIN_LOCAL_Z,
)).removeSplitter()
C.require_single(LEAD_NUT,'v50-style removable RH8x2 lead-nut cartridge')

NUT_PIN = C.fuse_seq([
    C.cyl_x(NUT_PIN_SHAFT_D/2.0,23.4,-12.0,0,0),
    C.cyl_x(NUT_PIN_GROOVE_D/2.0,NUT_PIN_GROOVE_W,NUT_PIN_GROOVE_X0,0,0),
    C.cyl_x(NUT_PIN_SHAFT_D/2.0,1.7,NUT_PIN_GROOVE_X0+NUT_PIN_GROOVE_W,0,0),
    C.cyl_x(3.0,2.0,-14.0,0,0),
],'lead-nut-retaining-pin')
NUT_PIN_CLIP = make_c_clip(3.2,1.25,NUT_PIN_CLIP_T,2.4)

for sx in SPINDLE_X:
    # Cartridge pocket is open to the inboard service side and carries no thread.
    pocket = C.box(
        sx-8.35,NUT_THREAD_Y0-0.35,SPINDLE_Z-7.35,
        16.70,NUT_THREAD_LEN+0.70,20.70,
    )
    RIGHT_FULL = RIGHT_FULL.cut(pocket).removeSplitter()

    # Smooth full spindle corridor. It must cover the complete screw including
    # the rear stud at maximum 5.5 mm opening; the wider -65 mm station otherwise
    # enters the front rack-station structure behind the old cage face.
    spindle_rear_reach = (
        SPINDLE_LOCAL_JOURNAL + SPINDLE_LOCAL_SHOULDER
        + LEAD_THREAD_LEN + HEX_LEN + OUTER_STUD_LEN
    )
    tunnel_y0 = PLATE_SPINDLE_Y - PLATE_OPEN - spindle_rear_reach - 1.0
    tunnel_y1 = PLATE_SPINDLE_Y-PLATE_Y+0.50
    RIGHT_FULL = RIGHT_FULL.cut(
        cyl_y(5.90,tunnel_y1-tunnel_y0,sx,tunnel_y0,SPINDLE_Z)
    ).removeSplitter()

    pin_y = NUT_Y0 + LEAD_NUT_PIN_LOCAL_Y
    pin_z = SPINDLE_Z + LEAD_NUT_PIN_LOCAL_Z
    RIGHT_FULL = RIGHT_FULL.cut(
        C.cyl_x(LEAD_NUT_PIN_HOLE_D/2.0,24.0,sx-12.0,pin_y,pin_z)
    ).removeSplitter()
    RIGHT_FULL = RIGHT_FULL.cut(
        C.cyl_x(3.55,3.0,sx-14.0,pin_y,pin_z)
    ).removeSplitter()
    RIGHT_FULL = RIGHT_FULL.cut(
        C.cyl_x(4.10,4.0,sx+11.0,pin_y,pin_z)
    ).removeSplitter()

C.require_single(RIGHT_FULL,'RIGHT full with v50 cartridge pockets and smooth spindle corridors')

pin_bore_clearance=[]
for xc in C.CLAMP_X:
    probe=C.cyl_x(C.PIN_HOLE_D/2-0.05,38.0,xc-19.0,C.PIN_Y,C.PIN_Z); cv=RIGHT_FULL.common(probe).Volume
    pin_bore_clearance.append({'x_mm':xc,'probe_common_mm3':round(cv,9)})
    if cv>1e-5: raise RuntimeError(f'Rack pin bore closed at X={xc}: {cv:.6f} mm3')
C.require_single(RIGHT_FULL,'RIGHT full final'); LEFT_FULL=C.mirror_x(RIGHT_FULL)

def make_plate_underhook_drop():
    # The underhook's top face remains untouched because it is the functional
    # box-rim contact.  Only its underside gets a DROP on the same (+Y/outboard)
    # side as the visible green projection.
    #
    # Run = 4.2 mm from plate front face to hook tip.  Use the same rise so the
    # support envelope is 45 degrees in Y/Z.  That puts the root only 1.11 mm
    # below the old plate bottom and does not move either spindle hole upward.
    y_wall = PLATE_SPINDLE_Y
    y_tip = C.BOX_RIM_INNER_Y + UNDERHOOK
    z_flange = RIM_BOTTOM_Z - UNDERHOOK_T
    run = y_tip - y_wall
    z_root = z_flange - run
    curve = []
    for i in range(19):
        t = i/18.0
        y = y_wall + run*C._smoothstep(t)
        z = z_root + run*t
        curve.append(App.Vector(0.0,y,z))
    pts = [
        App.Vector(0.0,y_wall,z_flange),
        App.Vector(0.0,y_wall,z_root),
    ] + curve[1:] + [App.Vector(0.0,y_wall,z_flange)]
    face = Part.Face(Part.makePolygon(pts))
    q = face.extrude(App.Vector(PLATE_X,0,0))
    q.translate(App.Vector(PLATE_X0,0,0))
    return q.removeSplitter()


stage('plate')
PLATE_BODY_Y0=C.BOX_RIM_INNER_Y-PLATE_Y; PLATE_HOOK_Y0=C.BOX_RIM_INNER_Y-WIDTH_RIM_CLEAR; PLATE_HOOK_Y1=C.BOX_RIM_INNER_Y+UNDERHOOK
PLATE=C.box(PLATE_X0,PLATE_BODY_Y0,PLATE_Z0,PLATE_X,PLATE_Y,PLATE_Z1-PLATE_Z0)
PLATE=PLATE.fuse(C.box(PLATE_X0,PLATE_HOOK_Y0,RIM_BOTTOM_Z-UNDERHOOK_T,PLATE_X,PLATE_HOOK_Y1-PLATE_HOOK_Y0,UNDERHOOK_T))
PLATE_UNDERHOOK_DROP=make_plate_underhook_drop()
PLATE=PLATE.fuse(PLATE_UNDERHOOK_DROP).removeSplitter()

# The grip starts 1.8 mm in front of the plate.  Remove only the required
# outer 2.8 mm of hook/drop locally around each grip envelope, leaving the
# remainder of the hook and the entire front/drop untouched elsewhere.
for sx in SPINDLE_X:
    PLATE=PLATE.cut(cyl_y(
        PLATE_KNOB_RELIEF_R,
        PLATE_KNOB_RELIEF_Y_DEPTH+0.40,
        sx,
        PLATE_HOOK_Y1-PLATE_KNOB_RELIEF_Y_DEPTH,
        SPINDLE_Z,
    )).removeSplitter()

for sx in SPINDLE_X:
    PLATE=PLATE.cut(cyl_y(PLATE_HOLE_D/2,PLATE_Y+1,sx,PLATE_BODY_Y0-0.5,SPINDLE_Z))
    # Outboard retainer recess plus a bottom-open radial service channel.  The
    # channel is only counterbore-deep, so the remaining ~6 mm plate thickness
    # stays structurally continuous while the printed C-clip can actually be
    # installed after the spindle journal is through the plate.
    PLATE=PLATE.cut(cyl_y(
        PLATE_RETAINER_COUNTERBORE_D/2.0,
        PLATE_RETAINER_COUNTERBORE_DEPTH,
        sx,
        PLATE_SPINDLE_Y-PLATE_RETAINER_COUNTERBORE_DEPTH,
        SPINDLE_Z,
    ))
    PLATE=PLATE.cut(C.box(
        sx-PLATE_RETAINER_CHANNEL_W/2.0,
        PLATE_SPINDLE_Y-PLATE_RETAINER_COUNTERBORE_DEPTH,
        PLATE_Z0-0.50,
        PLATE_RETAINER_CHANNEL_W,
        PLATE_RETAINER_COUNTERBORE_DEPTH+0.10,
        SPINDLE_Z-PLATE_Z0+0.50,
    ))
PLATE=PLATE.removeSplitter(); C.require_single(PLATE,'box-clamp-plate')

stage('lead screw and knob')
SPINDLE_SCAD=os.path.join(OUT,'v60_lead_screw_complete.scad')
write_complete_spindle_scad(SPINDLE_SCAD)
SPINDLE=import_scad_shape(SPINDLE_SCAD)
C.require_single(SPINDLE,'complete manifold RH8x2 lead screw')
SPINDLE_COMPILED_STL=os.path.splitext(SPINDLE_SCAD)[0]+'_compiled.stl'
lead_screw_mesh=stl_edge_topology(SPINDLE_COMPILED_STL)
if lead_screw_mesh['boundary_edges'] != 0:
    raise RuntimeError(
        f"lead screw STL has open edges: {lead_screw_mesh['boundary_edges']}"
    )
if lead_screw_mesh['nonmanifold_edges'] != 0:
    raise RuntimeError(
        f"lead screw STL has non-manifold edges: {lead_screw_mesh['nonmanifold_edges']}"
    )

# The knob now sits entirely on a 7 mm hex.  Its hex pocket is through-going;
# the outer RH8x2 stud begins only after the knob's outer face.
KNOB=z_to_y(KP.build_scalloped_knob_body())
KNOB=KNOB.cut(cyl_y(4.3,KP.KNOB_H+0.4,0,-0.2,0))
KNOB=KNOB.cut(
    z_to_y(hex_z(10.35,KP.KNOB_H+0.40,-0.20))
).removeSplitter()
KNOB=rotate_z180(KNOB)
C.require_single(KNOB,'box-clamp knob full-depth hex')

CAP_NUT_Z=hex_z(13.0,5.4)
CAP_NUT_Z=CAP_NUT_Z.cut(CAP_FEMALE_Z).removeSplitter()
C.require_single(CAP_NUT_Z,'lead-knob-retainer-nut true RH8x2 Z master')
CAP_NUT=rotate_z180(z_to_y(CAP_NUT_Z))
C.require_single(CAP_NUT,'lead-knob-retainer-nut')

# Direct regression gate for the actual problem area: underhook/drop versus
# the two user-operated knobs.  The plate and knob are one moving subassembly,
# so this check is independent of clamp travel and covers a full revolution.
plate_knob_clearance=[]
for sx in SPINDLE_X:
    for deg in range(0,360,15):
        qkn=KNOB.copy()
        qkn.rotate(App.Vector(0,0,0),App.Vector(0,1,0),float(deg))
        qkn.translate(App.Vector(sx,PLATE_SPINDLE_Y+HEX_LEN,SPINDLE_Z))
        cv=PLATE.common(qkn).Volume
        plate_knob_clearance.append({
            'x_mm':sx,'deg':deg,'plate_knob_common_mm3':round(cv,9),
        })
        if cv>1e-5:
            raise RuntimeError(
                f'plate underhook/drop blocks knob X={sx} deg={deg}: {cv:.6f} mm3'
            )

# Prove the DROP itself is present on the visible/outboard side away from the
# two intentionally tiny knob-tip reliefs.
drop_probe=PLATE_UNDERHOOK_DROP.copy()
drop_sample=C.box(
    (SPINDLE_X[0]+SPINDLE_X[1])/2.0-8.0,
    PLATE_SPINDLE_Y,
    RIM_BOTTOM_Z-UNDERHOOK_T-UNDERHOOK,
    16.0,
    PLATE_HOOK_Y1-PLATE_SPINDLE_Y,
    UNDERHOOK+0.05,
)
drop_common=PLATE.common(drop_probe.common(drop_sample)).Volume
drop_sample_volume=drop_probe.common(drop_sample).Volume
plate_underhook_drop_fraction=(
    drop_common/drop_sample_volume if drop_sample_volume>1e-9 else 0.0
)
if plate_underhook_drop_fraction<0.999:
    raise RuntimeError(
        f'outboard clamp-plate underhook DROP missing: {plate_underhook_drop_fraction:.6f}'
    )

# The spindle journal is captive in the moving plate: shoulder on the inboard
# face, printable C-clip in the existing Ø12 x 2 mm outboard counterbore.
PLATE_CLIP_INSTALLED=rotate_z180(z_to_y(PLATE_CLIP))
PLATE_CLIP_INSTALLED.translate(App.Vector(0.0,-0.40,0.0))
C.require_single(PLATE_CLIP_INSTALLED,'installed plate-retainer clip local')

plate_retainer_checks=[]
plate_retainer_clip_insertion=[]
for sx in SPINDLE_X:
    sp=SPINDLE.copy()
    sp.translate(App.Vector(sx,PLATE_SPINDLE_Y,SPINDLE_Z))
    cl=PLATE_CLIP_INSTALLED.copy()
    cl.translate(App.Vector(sx,PLATE_SPINDLE_Y,SPINDLE_Z))

    spindle_common=sp.common(cl).Volume
    plate_common=PLATE.common(cl).Volume
    plate_retainer_checks.append({
        'x_mm':sx,
        'spindle_common_mm3':round(spindle_common,6),
        'plate_common_mm3':round(plate_common,6),
        'counterbore_d_mm':12.0,
        'counterbore_depth_mm':PLATE_RETAINER_COUNTERBORE_DEPTH,
        'service_channel_width_mm':PLATE_RETAINER_CHANNEL_W,
        'service_channel_depth_mm':PLATE_RETAINER_COUNTERBORE_DEPTH,
        'clip_outer_d_mm':10.8,
        'clip_inner_d_mm':5.1,
        'shaft_groove_d_mm':5.0,
        'shaft_groove_width_mm':1.4,
    })
    if spindle_common > 1e-4:
        raise RuntimeError(
            f'plate retainer clip intersects spindle at X={sx}: '
            f'{spindle_common:.6f} mm3'
        )
    if plate_common > 1e-4:
        raise RuntimeError(
            f'plate retainer clip intersects plate counterbore at X={sx}: '
            f'{plate_common:.6f} mm3'
        )

    # Rigid-body service-path check for the plate clip itself.  The opening in
    # the C-clip still snaps over the Ø5 groove, but its body must be able to
    # travel upward through the new outboard service channel without crossing
    # any plate material.
    for dz in (-10.0,-7.0,-4.0,-2.0,0.0):
        qcl=PLATE_CLIP_INSTALLED.copy()
        qcl.translate(App.Vector(sx,PLATE_SPINDLE_Y,SPINDLE_Z+dz))
        pc=PLATE.common(qcl).Volume
        plate_retainer_clip_insertion.append({
            'x_mm':sx,
            'centre_z_offset_mm':dz,
            'plate_common_mm3':round(pc,9),
        })
        if pc>1e-5:
            raise RuntimeError(
                f'plate retainer clip service path blocked by plate '
                f'X={sx} dz={dz}: {pc:.6f} mm3'
            )

stage('hard validation')
failures=[]

# Explicit regression gate for the exact part the user prints:
# cad/v60/STL/eurobox_v60_knob_retainer_nut.stl.  Sample the actual outer-stud
# master and actual cap-nut BRep at the helical centre and half a pitch away.
# A smooth bore or the former ~0.1 mm twisted-ribbon groove cannot pass.
def _inside(shape,x,y,z):
    return bool(shape.isInside(App.Vector(x,y,z),1e-5,False))

# Regression gate for the other printed female RH8x2 part:
# cad/v60/STL/eurobox_v60_lead_nut.stl.  Sample the ACTUAL exported cartridge
# local BRep at helical groove centres and half-pitch crest positions.
lead_nut_thread_samples=[]
lead_sample_r=(THREAD_FEMALE_CORE_R+THREAD_FEMALE_MAJOR_R)/2.0
for turn in (2,5):
    for angle_deg in (0.0,90.0,180.0,270.0):
        a=math.radians(angle_deg)
        zc=THREAD_PITCH*(turn+angle_deg/360.0)
        # FEMALE_NEGY transform maps Z-master [r,angle,zc] to
        # cartridge-local [-r*cos(a), -zc, -r*sin(a)].
        gx=-lead_sample_r*math.cos(a)
        gy=-zc
        gz=-lead_sample_r*math.sin(a)
        groove_solid=_inside(LEAD_NUT,gx,gy,gz)

        zcrest=zc+THREAD_PITCH/2.0
        crest_solid=_inside(
            LEAD_NUT,
            -lead_sample_r*math.cos(a),
            -zcrest,
            -lead_sample_r*math.sin(a),
        )
        rec={
            'turn':turn,
            'angle_deg':angle_deg,
            'radius_mm':round(lead_sample_r,3),
            'groove_center_solid':groove_solid,
            'between_turns_solid':crest_solid,
        }
        lead_nut_thread_samples.append(rec)
        if groove_solid:
            failures.append(
                f'RH8x2 lead-nut groove missing turn={turn} angle={angle_deg}'
            )
        if not crest_solid:
            failures.append(
                f'RH8x2 lead-nut crest missing between turns turn={turn} angle={angle_deg}'
            )

main_spindle_thread_samples=[]
knob_retainer_thread_samples=[]
male_sample_r=(THREAD_CORE_R+THREAD_MAJOR/2.0)/2.0
female_sample_r=(CAP_THREAD_FEMALE_CORE_R+CAP_THREAD_FEMALE_MAJOR_R)/2.0
main_start=SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER
# Outboard stud spans +Y = HEX_LEN .. HEX_LEN+OUTER_STUD_LEN after the final
# rigid spindle transform.  It is generated LH in the negative master-Z region
# so it is RH relative to the physical +Y outboard axis.
stud_tip_y=HEX_LEN+OUTER_STUD_LEN

# Sample the ACTUAL complete lead screw BRep, not a separate thread coupon.
for turn in (2,7):
    for angle_deg in (0.0,90.0,180.0,270.0):
        a=math.radians(angle_deg)
        zc=THREAD_PITCH*(turn+angle_deg/360.0)
        x=-male_sample_r*math.cos(a)
        y=-(main_start+zc)
        z=-male_sample_r*math.sin(a)
        ridge=_inside(SPINDLE,x,y,z)
        between=_inside(
            SPINDLE,x,-(main_start+zc+THREAD_PITCH/2.0),z
        )
        main_spindle_thread_samples.append({
            'turn':turn,
            'angle_deg':angle_deg,
            'ridge_center_solid':ridge,
            'between_turns_solid':between,
        })
        if not ridge:
            failures.append(
                f'RH8x2 main lead-screw ridge missing turn={turn} angle={angle_deg}'
            )
        if between:
            failures.append(
                f'RH8x2 main lead-screw fills between turns turn={turn} angle={angle_deg}'
            )

for angle_deg in (0.0,90.0,180.0,270.0):
    # The outboard stud is generated as a negative-angle master helix because
    # the final rigid transform reverses the master-Z axis into physical +Y.
    # Sample that actual phase with -angle; the female master remains +angle.
    a=math.radians(angle_deg)
    am=-a
    zc=THREAD_PITCH*(1.0+angle_deg/360.0)

    mx=-male_sample_r*math.cos(am)
    # ridge_lh starts at the outer tip in master Z and progresses toward the
    # knob.  After the rigid transform this maps from +Y tip toward +Y root.
    my=stud_tip_y-zc
    mz=-male_sample_r*math.sin(am)
    male_ridge=_inside(SPINDLE,mx,my,mz)
    male_between=_inside(
        SPINDLE,mx,stud_tip_y-(zc+THREAD_PITCH/2.0),mz
    )

    fx=female_sample_r*math.cos(a); fy=female_sample_r*math.sin(a)
    female_groove=_inside(CAP_NUT_Z,fx,fy,zc)
    female_between=_inside(CAP_NUT_Z,fx,fy,zc+THREAD_PITCH/2.0)

    rec={
        'angle_deg':angle_deg,
        'male_ridge_center_solid':male_ridge,
        'male_between_turns_solid':male_between,
        'female_groove_center_solid':female_groove,
        'female_between_turns_solid':female_between,
    }
    knob_retainer_thread_samples.append(rec)
    if not male_ridge:
        failures.append(f'RH8x2 outer stud ridge missing at angle={angle_deg}')
    if male_between:
        failures.append(f'RH8x2 outer stud fills space between turns at angle={angle_deg}')
    if female_groove:
        failures.append(f'RH8x2 knob-retainer groove missing at angle={angle_deg}')
    if not female_between:
        failures.append(f'RH8x2 knob-retainer crest missing between turns at angle={angle_deg}')

if RH8_MALE_CREST_W < 0.50:
    failures.append('RH8x2 male crest is too narrow for 0.4 mm FDM')
if RH8_FEMALE_CREST_MATERIAL_W < 0.45:
    failures.append('RH8x2 female crest material is too narrow for 0.4 mm FDM')
def fail(msg): failures.append(msg)
for side,sh in (('RIGHT',RIGHT_FULL),('LEFT',LEFT_FULL)):
    C.require_single(sh,side+' full')
    if sh.BoundBox.XLength>C.V60_X_TARGET_MAX+1e-6: fail(f'{side} full base exceeds 296 mm X target: {sh.BoundBox.XLength:.3f}')
    if sh.BoundBox.YLength>C.INDX_Y_MAX+1e-6: fail(f'{side} full base exceeds 275 mm Y: {sh.BoundBox.YLength:.3f}')
left_back=C.mirror_x(LEFT_FULL); full_mirror_delta=abs(RIGHT_FULL.Volume-left_back.Volume)
mirror_bound_delta=max(abs(RIGHT_FULL.BoundBox.XMin-left_back.BoundBox.XMin),abs(RIGHT_FULL.BoundBox.XMax-left_back.BoundBox.XMax),abs(RIGHT_FULL.BoundBox.YMin-left_back.BoundBox.YMin),abs(RIGHT_FULL.BoundBox.YMax-left_back.BoundBox.YMax),abs(RIGHT_FULL.BoundBox.ZMin-left_back.BoundBox.ZMin),abs(RIGHT_FULL.BoundBox.ZMax-left_back.BoundBox.ZMax)); mirror_face_delta=abs(len(RIGHT_FULL.Faces)-len(left_back.Faces))
if full_mirror_delta>1e-4 or mirror_bound_delta>1e-6 or mirror_face_delta!=0: fail('full handed bases are not exact construction mirrors')
stage('mirror gate complete')

cage_reinforcement_checks=[]
for name,probe in make_cage_reinforcement().items():
    pv=probe.Volume
    common=RIGHT_FULL.common(probe).Volume
    fraction=common/pv if pv>0 else 0.0
    cage_reinforcement_checks.append({
        'name':name,
        'material_fraction':round(fraction,6),
        'volume_mm3':round(pv,3),
    })
    # The retaining-pin service bores deliberately nick the station-side ends
    # of the right holm fill / cross top by well under 1 %.  Require essentially
    # complete reinforcement while preserving those service cuts.
    if fraction<0.990:
        fail(f'cage reinforcement {name} not structurally present: {fraction:.6f}')

holm_station_checks=[]
station_check_refs=(
    (SPINDLE_X[0],C.FRONT_HOLM_INNER_X,-1.0),
    (SPINDLE_X[1],C.REAR_HOLM_INNER_X,1.0),
)
for sx,holm_inner_x,side in station_check_refs:
    boss_near_holm = sx + side*C.BOX_CLAMP_BOSS_HALF_X
    gap = side*(holm_inner_x-boss_near_holm)
    holm_station_checks.append({'spindle_x_mm':round(sx,3),'holm_inner_x_mm':round(holm_inner_x,3),'boss_to_holm_gap_mm':round(gap,3)})
    if abs(gap-C.BOX_CLAMP_HOLM_CLEAR_X)>1e-6:
        fail(f'box-clamp station at X={sx} lost symmetric holm clearance: {gap:.3f} mm')

if C.UPPER_PIVOT_W<16.0: fail('Upper central rack-pivot bearing is too narrow')
if LOWER_FORK_EAR_T<4.2: fail('Replaceable Lower fork ears are too thin')
if not (0.6<=2*LOWER_FORK_SIDE_CLEAR<=1.2): fail('Upper/Lower fork running clearance outside 0.6..1.2 mm')
holm_mid_x = (C.FRONT_HOLM_INNER_X + C.REAR_HOLM_INNER_X)/2.0
spindle_mid_x = (SPINDLE_X[0] + SPINDLE_X[1])/2.0
left_plate_margin = SPINDLE_X[0] - PLATE_X0
right_plate_margin = PLATE_X1 - SPINDLE_X[1]
if abs(spindle_mid_x-holm_mid_x)>1e-9: fail('box-clamp screw pair is not centred between holm inner faces')
if abs(left_plate_margin-C.BOX_CLAMP_EDGE_MARGIN_X)>1e-9 or abs(right_plate_margin-C.BOX_CLAMP_EDGE_MARGIN_X)>1e-9:
    fail('box-clamp plate no longer has equal screw-to-edge margins')
if PLATE_X <= 160.0: fail(f'box-clamp plate did not widen: {PLATE_X:.3f} mm')
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

cartridge_insertion=[]
thread_motion=[]
knob_motion=[]
assembly_approach=[]
for sx in SPINDLE_X:
    nut=LEAD_NUT.copy(); nut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z))
    if RIGHT_FULL.common(nut).Volume>1e-4:
        fail(f'v50 lead-nut cartridge collides with BASE pocket at X={sx}')

    # Prove the real cartridge can be dropped into the real BASE from above.
    for lift in (10.0,5.0,2.0,0.0):
        qnut=LEAD_NUT.copy()
        qnut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z+lift))
        cv=RIGHT_FULL.common(qnut).Volume
        cartridge_insertion.append({
            'x_mm':sx,'lift_mm':lift,'base_common_mm3':round(cv,6),
        })
        if cv>1e-4:
            fail(f'v50 lead-nut cartridge insertion blocked X={sx} lift={lift}: {cv:.6f} mm3')
    for d in (0,0.5,1.0,2.0,3.0,4.0,5.5):
        q=SPINDLE.copy()
        # The final spindle axis points toward -Y.  For this right-hand helix an
        # inward axial shift therefore requires NEGATIVE rotation about +Y.
        # The former + sign only happened to pass at whole/half turns and failed
        # at the diagnostic 0.5 mm / 90 degree state.
        rot_deg=-360*d/THREAD_PITCH
        q.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        q.translate(App.Vector(sx,PLATE_SPINDLE_Y-d,SPINDLE_Z))
        bc=RIGHT_FULL.common(q).Volume
        nc=nut.common(q).Volume
        thread_motion.append({
            'x_mm':sx,'open_mm':d,'rotation_deg':rot_deg,
            'base_common_mm3':round(bc,6),'cartridge_common_mm3':round(nc,6),
        })
        if bc>1e-4:
            fail(f'lead screw blocked by smooth BASE corridor X={sx} open={d}: {bc:.6f} mm3')
        # Both parts now use the same true radial/axial RH8x2 geometry.  Keep a
        # small BRep contact-noise allowance, but any material overlap is a hard
        # failure well before it could represent a printable interference.
        if nc>1.20:
            fail(f'RH8x2 spindle/cartridge collision X={sx} open={d}: {nc:.6f} mm3')

        # Knob and its retainer are rigidly carried by the spindle.  Validate
        # their complete rotational envelope against the actual BASE over the
        # full 0..5.5 mm operating travel.
        knob_y=PLATE_SPINDLE_Y+HEX_LEN-d
        # CAP_NUT points toward -Y, so placing its origin 5.4 mm beyond the
        # knob face seats its inner face exactly against the knob.
        cap_y=PLATE_SPINDLE_Y+HEX_LEN+5.4-d

        qkn=KNOB.copy()
        qkn.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        qkn.translate(App.Vector(sx,knob_y,SPINDLE_Z))
        kbc=RIGHT_FULL.common(qkn).Volume

        qcap=CAP_NUT.copy()
        qcap.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        qcap.translate(App.Vector(sx,cap_y,SPINDLE_Z))
        cbc=RIGHT_FULL.common(qcap).Volume

        knob_motion.append({
            'x_mm':sx,
            'open_mm':d,
            'rotation_deg':rot_deg,
            'knob_base_common_mm3':round(kbc,6),
            'retainer_base_common_mm3':round(cbc,6),
        })
        if kbc>1e-4:
            fail(f'box-clamp knob/base collision X={sx} open={d}: {kbc:.6f} mm3')
        if cbc>1e-4:
            fail(f'knob retainer/base collision X={sx} open={d}: {cbc:.6f} mm3')

# The requested regression gate is intentionally local to the actual printed
# wear cartridge.  The direct lead_nut_thread_samples above prove that the final
# LEAD_NUT BRep has a helical groove and solid crest material between turns.
# The motion sweep above still proves the existing spindle travels through it
# without geometric collision.  Avoid rebuilding/validating unrelated long
# helical spindle geometry in this minimal lead-nut fix.
lead_thread_radial_engagement=THREAD_MAJOR/2.0-THREAD_FEMALE_CORE_R
if lead_thread_radial_engagement < 0.40:
    fail(
        f'RH8x2 spindle/lead-nut radial engagement too small: '
        f'{lead_thread_radial_engagement:.3f} mm'
    )

# Real mounting sequence for one station:
#   lead nut fixed in BASE -> plate/spindle subassembly starts outside guides ->
#   spindle is rotated into the fixed nut while the plate approaches its
#   working corridor.  At d=-16.5 the main-thread tip is still 0.3 mm clear of
#   the nut entrance; d=0 is the nominal closed datum.
for sx in SPINDLE_X:
    nut=LEAD_NUT.copy()
    nut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z))

    for d in (-16.5,-12.0,-8.0,-4.0,0.0):
        rot_deg=-360*d/THREAD_PITCH

        apl=PLATE.copy()
        apl.translate(App.Vector(0,-d,0))
        plate_base=RIGHT_FULL.common(apl).Volume

        asp=SPINDLE.copy()
        asp.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        asp.translate(App.Vector(sx,PLATE_SPINDLE_Y-d,SPINDLE_Z))
        spindle_base=RIGHT_FULL.common(asp).Volume
        spindle_nut=nut.common(asp).Volume

        knob_y=PLATE_SPINDLE_Y+HEX_LEN-d
        akn=KNOB.copy()
        akn.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        akn.translate(App.Vector(sx,knob_y,SPINDLE_Z))
        knob_base=RIGHT_FULL.common(akn).Volume

        cap_y=PLATE_SPINDLE_Y+HEX_LEN+5.4-d
        acap=CAP_NUT.copy()
        acap.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        acap.translate(App.Vector(sx,cap_y,SPINDLE_Z))
        cap_base=RIGHT_FULL.common(acap).Volume

        rec={
            'x_mm':sx,
            'assembly_d_mm':d,
            'rotation_deg':rot_deg,
            'plate_base_common_mm3':round(plate_base,6),
            'spindle_base_common_mm3':round(spindle_base,6),
            'spindle_lead_nut_common_mm3':round(spindle_nut,6),
            'knob_base_common_mm3':round(knob_base,6),
            'knob_retainer_base_common_mm3':round(cap_base,6),
        }
        assembly_approach.append(rec)
        if plate_base>1e-4:
            fail(f'plate cannot approach BASE during assembly X={sx} d={d}: {plate_base:.6f} mm3')
        if spindle_base>1e-4:
            fail(f'lead screw cannot approach BASE during assembly X={sx} d={d}: {spindle_base:.6f} mm3')
        if spindle_nut>1.20:
            fail(f'lead screw cannot thread into installed lead nut X={sx} d={d}: {spindle_nut:.6f} mm3')
        if knob_base>1e-4:
            fail(f'knob blocks assembly approach X={sx} d={d}: {knob_base:.6f} mm3')
        if cap_base>1e-4:
            fail(f'knob retainer blocks assembly approach X={sx} d={d}: {cap_base:.6f} mm3')

stage('thread motion complete')

def local_y_extent(d):
    pl=PLATE.copy(); pl.translate(App.Vector(0,-d,0))
    sp=SPINDLE.copy(); sp.rotate(App.Vector(0,0,0),App.Vector(0,1,0),-360*d/THREAD_PITCH); sp.translate(App.Vector(0,PLATE_SPINDLE_Y-d,SPINDLE_Z))
    kn=KNOB.copy(); kn.rotate(App.Vector(0,0,0),App.Vector(0,1,0),-360*d/THREAD_PITCH); kn.translate(App.Vector(SPINDLE_X[0],PLATE_SPINDLE_Y+HEX_LEN-d,SPINDLE_Z))
    cp=CAP_NUT.copy(); cp.rotate(App.Vector(0,0,0),App.Vector(0,1,0),-360*d/THREAD_PITCH); cp.translate(App.Vector(SPINDLE_X[0],PLATE_SPINDLE_Y+HEX_LEN+5.4-d,SPINDLE_Z))
    return max(RIGHT_FULL.BoundBox.YMax,pl.BoundBox.YMax,sp.BoundBox.YMax,kn.BoundBox.YMax,cp.BoundBox.YMax)
width_states={str(d):local_y_extent(d) for d in (0.0,5.5)}; holder_half=C.RACK_CTC/2+max(width_states.values())
if holder_half>C.BOX_W/2+0.02: fail(f'complete holder exceeds 600 mm box width: {2*holder_half:.3f} mm')

V={'version':'v60','stage':'full_direct_mechanism_v50_solutions_restored','architecture':'clean structural core + proven v50 rack joint/backstop/drop/cage solutions','base':{'right_bbox_mm':[round(RIGHT_FULL.BoundBox.XLength,3),round(RIGHT_FULL.BoundBox.YLength,3),round(RIGHT_FULL.BoundBox.ZLength,3)],'left_bbox_mm':[round(LEFT_FULL.BoundBox.XLength,3),round(LEFT_FULL.BoundBox.YLength,3),round(LEFT_FULL.BoundBox.ZLength,3)],'mirror_delta_mm3':round(full_mirror_delta,9),'mirror_bound_delta_mm':round(mirror_bound_delta,9),'mirror_face_delta':mirror_face_delta,'pin_bore_clearance':pin_bore_clearance,'holm_station_checks':holm_station_checks,'cage_reinforcement_checks':cage_reinforcement_checks,'cage_struct_y_mm':[round(CAGE_Y0,3),round(CAGE_STRUCT_Y1,3)],'station_floor_y1_mm':round(STATION_FLOOR_Y1,3),'cage_top_z_mm':PRINT_BASE_PLANE_Z},'rack':{'clamp_spacing_mm':C.CLAMP_SPACING,'joint':'v51 broad central Upper bearing + replaceable Lower fork','upper_pivot_width_mm':C.UPPER_PIVOT_W,'lower_fork_outer_width_mm':LOWER_FORK_W,'lower_fork_ear_thickness_mm':LOWER_FORK_EAR_T,'lower_web_top_z_mm':LOWER_WEB_TOP_Z,'lower_sweep':lower_sweep,'tightening_sweep':tightening_sweep,'pin_checks':pin_checks,'m4_closure_checks':closure_checks,'m4_closure':{'mode':'M4x20 from below into side-loaded captive M4 nut','screw_length_mm':RACK_M4_SCREW_LENGTH,'lower_clearance_d_mm':RACK_M4_LOWER_CLEAR_D,'base_clearance_d_mm':C.RACK_M4_BASE_CLEAR_D,'base_bore_z_mm':[RACK_M4_BASE_BORE_Z0,RACK_M4_BASE_BORE_Z1],'nut_pocket_af_mm':C.RACK_M4_NUT_AF,'nut_pocket_height_mm':C.RACK_M4_NUT_H,'closure_pad_x_mm':RACK_CLOSURE_PAD_X,'closure_pad_y_mm':[RACK_CLOSURE_PAD_Y0,RACK_CLOSURE_PAD_Y1],'closure_pad_z_mm':[RACK_CLOSURE_PAD_Z0,RACK_CLOSURE_PAD_Z1],'closure_pad_material_fraction':round(closure_pad_fraction,6),'nominal_gap_mm':round(closure_nominal_gap,3),'mapped_tube_adjustment_mm':round(closure_mapped_tube_adjustment,3),'required_tube_adjustment_mm':round(required_tube_adjustment,3),'nut_engagement_mm':round(rack_nut_engagement,3),'tip_clearance_mm':round(rack_tip_clearance,3),'front_ligament_mm':round(closure_front_ligament,3),'side_ligament_mm':round(closure_side_ligament,3)}},'box_clamp':{'architecture':'v50_direct_removable_lead_nut_cartridge_local_holm_stations','plate_travel_mm':PLATE_OPEN,'plate_motion':plate_motion,'plate_x_mm':[round(PLATE_X0,3),round(PLATE_X1,3)],'plate_width_mm':round(PLATE_X,3),'spindle_x_mm':[round(x,3) for x in SPINDLE_X],'spindle_spacing_mm':round(SPINDLE_X[1]-SPINDLE_X[0],3),'spindle_z_mm':SPINDLE_Z,'thread':'RH 8x2','integral_female_threads':False,'base_has_working_thread':False,'working_female_thread_location':'removable_lead_nut_cartridge','cartridge_insertion':cartridge_insertion,'thread_motion':thread_motion,'knob_motion':knob_motion,'assembly_approach':assembly_approach,'thread_brep_common_tolerance_mm3':1.20,'width_states_local_y_mm':{k:round(v,3) for k,v in width_states.items()},'effective_total_width_mm':round(max(C.BOX_W,2*holder_half),3)},'failures':failures}
V['box_clamp']['lead_screw']={
    'construction':'single OpenSCAD CGAL union; exact final printable STL retained',
    'main_thread':'true radial/axial RH8x2',
    'outer_stud_thread':'true radial/axial RH8x2',
    'journal_length_mm':SPINDLE_LOCAL_JOURNAL,
    'shoulder_length_mm':SPINDLE_LOCAL_SHOULDER,
    'main_thread_length_mm':LEAD_THREAD_LEN,
    'knob_hex_length_mm':HEX_LEN,
    'knob_thickness_mm':KP.KNOB_H,
    'knob_standoff_mm':KNOB_STANDOFF,
    'knob_hex_engagement_mm':KP.KNOB_H,
    'outer_stud_length_mm':OUTER_STUD_LEN,
    'knob_side':'outboard of clamp plate',
    'working_thread_side':'inboard toward fixed lead-nut cartridge',
    'outer_stack_y_from_plate_mm':[0.0,HEX_LEN,HEX_LEN+OUTER_STUD_LEN],
    'mesh_topology':lead_screw_mesh,
    'main_thread_samples':main_spindle_thread_samples,
}
V['box_clamp']['plate_underhook_printability']={
    'target':'visible green underhook on moving clamp plate',
    'drop_side':'outboard / knob side of clamp plate',
    'hook_top_contact_z_mm':RIM_BOTTOM_Z,
    'hook_outer_y_mm':PLATE_HOOK_Y1,
    'drop_root_z_mm':round((RIM_BOTTOM_Z-UNDERHOOK_T)-(PLATE_HOOK_Y1-PLATE_SPINDLE_Y),3),
    'drop_run_mm':round(PLATE_HOOK_Y1-PLATE_SPINDLE_Y,3),
    'drop_material_fraction_away_from_knobs':round(plate_underhook_drop_fraction,6),
    'knob_relief_y_depth_mm':PLATE_KNOB_RELIEF_Y_DEPTH,
    'knob_relief_radius_mm':PLATE_KNOB_RELIEF_R,
    'knob_standoff_mm':KNOB_STANDOFF,
    'plate_knob_clearance':plate_knob_clearance,
}
V['box_clamp']['plate_spindle_retention']={
    'mode':'inboard Ø11 shoulder + outboard printable C-clip in Ø12x2 counterbore with bottom-open service channel',
    'clip_export':'eurobox_v60_plate_retainer_clip',
    'clip_count_final_assembly':4,
    'service_channel_width_mm':PLATE_RETAINER_CHANNEL_W,
    'service_channel_depth_mm':PLATE_RETAINER_COUNTERBORE_DEPTH,
    'clip_insertion_path':plate_retainer_clip_insertion,
    'checks':plate_retainer_checks,
}
V['box_clamp']['mounting_sequence']={
    'order':[
        'lead_nut_into_base',
        'lead_nut_cross_pin',
        'lead_nut_pin_clip',
        'lead_screw_through_plate',
        'plate_retainer_clip_via_bottom_service_channel',
        'plate_spindle_subassembly_threaded_into_fixed_lead_nut',
        'knob_on_full_7mm_hex',
        'knob_retainer_nut_on_outer_RH8x2_stud',
    ],
    'lead_nut_drop_in':cartridge_insertion,
    'plate_clip_service_path':plate_retainer_clip_insertion,
    'threaded_plate_approach':assembly_approach,
    'operating_knob_clearance':knob_motion,
}
V['box_clamp']['lead_nut_thread']={
    'standard':'RH8x2 true radial/axial printable matched pair',
    'pitch_mm':THREAD_PITCH,
    'male_core_d_mm':round(2.0*THREAD_CORE_R,3),
    'male_major_d_mm':round(THREAD_MAJOR,3),
    'male_root_width_mm':RH8_MALE_ROOT_W,
    'male_crest_width_mm':RH8_MALE_CREST_W,
    'female_crest_bore_d_mm':round(2.0*THREAD_FEMALE_CORE_R,3),
    'female_groove_root_d_mm':round(2.0*THREAD_FEMALE_MAJOR_R,3),
    'female_groove_root_width_mm':RH8_FEMALE_ROOT_W,
    'female_groove_crest_width_mm':RH8_FEMALE_CREST_W,
    'female_crest_material_between_turns_mm':round(RH8_FEMALE_CREST_MATERIAL_W,3),
    'radial_thread_engagement_mm':round(lead_thread_radial_engagement,3),
    'samples':lead_nut_thread_samples,
    'validated_export_part':'eurobox_v60_lead_nut',
}
V['box_clamp']['knob_retainer_thread']={
    'standard':'RH8x2 true radial/axial printable pair',
    'pitch_mm':THREAD_PITCH,
    'male_core_d_mm':round(2.0*THREAD_CORE_R,3),
    'male_major_d_mm':round(THREAD_MAJOR,3),
    'female_crest_bore_d_mm':round(2.0*CAP_THREAD_FEMALE_CORE_R,3),
    'female_groove_root_d_mm':round(2.0*CAP_THREAD_FEMALE_MAJOR_R,3),
    'male_root_width_mm':RH8_MALE_ROOT_W,
    'male_crest_width_mm':RH8_MALE_CREST_W,
    'female_groove_root_width_mm':RH8_FEMALE_ROOT_W,
    'female_groove_crest_width_mm':RH8_FEMALE_CREST_W,
    'female_crest_material_between_turns_mm':round(RH8_FEMALE_CREST_MATERIAL_W,3),
    'radial_core_clearance_mm':round(CAP_THREAD_FEMALE_CORE_R-THREAD_CORE_R,3),
    'radial_major_clearance_mm':round(CAP_THREAD_FEMALE_MAJOR_R-THREAD_MAJOR/2.0,3),
    'samples':knob_retainer_thread_samples,
    'validated_export_part':'eurobox_v60_knob_retainer_nut',
}
with open(os.path.join(OUT,'VALIDATION_v60_full.json'),'w',encoding='utf-8') as f: json.dump(V,f,indent=2)
if failures:
    print(json.dumps(V,indent=2),flush=True); raise SystemExit('V60 FULL HARD CHECKS FAILED: '+' | '.join(failures))

stage('exports')
parts={'eurobox_v60_base_right':RIGHT_FULL,'eurobox_v60_base_left':LEFT_FULL,'eurobox_v60_rack_lower':LOWER,'eurobox_v60_rack_pin':PIN,'eurobox_v60_rack_pin_clip':PIN_CLIP,'eurobox_v60_clamp_plate':PLATE,'eurobox_v60_lead_nut':LEAD_NUT,'eurobox_v60_lead_nut_retaining_pin':NUT_PIN,'eurobox_v60_lead_nut_pin_clip':NUT_PIN_CLIP,'eurobox_v60_lead_screw':SPINDLE,'eurobox_v60_knob':KNOB,'eurobox_v60_knob_retainer_nut':CAP_NUT,'eurobox_v60_plate_retainer_clip':PLATE_CLIP}
for name,sh in parts.items(): C.require_single(sh,name); C.export_shape(name,sh)
# Preserve the exact closed CGAL mesh for the lead screw.  Re-tessellating the
# reconstructed BRep was the source of the 272/273 open edges reported by Prusa.
shutil.copyfile(
    SPINDLE_COMPILED_STL,
    os.path.join(OUT,'eurobox_v60_lead_screw.stl'),
)
lead_screw_export_topology=stl_edge_topology(
    os.path.join(OUT,'eurobox_v60_lead_screw.stl')
)
if lead_screw_export_topology['boundary_edges'] != 0:
    raise RuntimeError('exported lead screw regained open edges')
if lead_screw_export_topology['nonmanifold_edges'] != 0:
    raise RuntimeError('exported lead screw regained non-manifold edges')

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
    f.write('Outboard rear-stop contact wall, closed holm heads with DROPs; serviceable box-clamp cage uses full-area holm ties, a hollow transverse DROP beam and low station gussets while the lead-nut cartridges remain removable.\n')
    f.write(f'Final cage top is exactly the 39.54 mm box support plane; {PLATE_X:.1f} mm clamp plate with holm-referenced lead screws at {SPINDLE_X[0]:.2f}/{SPINDLE_X[1]:.2f} mm.\n')
    f.write('160 mm rack-clamp spacing; CORE One L INDX hard envelope 298 x 275 mm.\n')
stage('complete'); print(json.dumps(V,indent=2),flush=True)
