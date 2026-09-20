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
# Keep the moving plate on the same real 30 mm vertical envelope as the
# carrier. This lets its screw/counterbore axis share the carrier mid-plane
# instead of creating a new weak lower edge when the base axis is lowered.
PLATE_Z0 = C.ARM_BOTTOM_Z
PLATE_Z1 = C.BOX_SUPPORT_Z
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
# Smooth BASE corridor around the largest inboard spindle feature (Ø11
# shoulder) with 0.40 mm radial FDM/service clearance.
SPINDLE_TUNNEL_R = SHOULDER_D/2.0 + 0.40
SPINDLE_LOCAL_JOURNAL = 8.0
SPINDLE_LOCAL_SHOULDER = 1.8

# Vertical, support-free lead-screw print geometry. The exact exported STL is
# generated on the screw axis (Z) and then transformed only for installed BRep
# validation/assembly.
#
# 1) A 0.80 mm smooth Ø6.5 pilot gives the screw a genuinely flat print foot.
# 2) The first 2.00 mm of the knob hex are a <=45deg hex frustum. The matching
#    knob pocket uses the same transition and retains 5 mm full AF10 drive.
# 3) The Ø11 thrust shoulder is supported by a 45deg cone in the last 2.50 mm
#    of the journal. The moving plate receives the matching countersink, so the
#    cone is also the real axial thrust seat rather than sacrificial geometry.
SPINDLE_PRINT_PILOT_H = 0.80
SPINDLE_HEX_AF = 10.0
SPINDLE_HEX_TAPER_H = 2.0
SPINDLE_HEX_TAPER_AF0 = (THREAD_MAJOR / 2.0) * math.sqrt(3.0)
SPINDLE_SHOULDER_TAPER_H = SHOULDER_D / 2.0 - 3.0
SPINDLE_SHOULDER_TAPER_R0 = 3.0
SPINDLE_SHOULDER_TAPER_R1 = SHOULDER_D / 2.0
PLATE_SHOULDER_CONE_CLEAR_R = SPINDLE_SHOULDER_TAPER_R1 + 0.25
KNOB_HEX_POCKET_AF = 10.35
KNOB_HEX_TAPER_H = SPINDLE_HEX_TAPER_H + 0.20
KNOB_HEX_TAPER_AF0 = SPINDLE_HEX_TAPER_AF0 + 0.30

# The knob is 7 mm thick.  Its complete thickness must sit on the hex before
# the outer RH8x2 stud begins; the old 4.5 mm hex put 2.5 mm of the knob over
# the retainer stud and left only ~4.5 mm usable thread.
HEX_LEN = KP.KNOB_H
OUTER_STUD_LEN = 7.0

PLATE_SPINDLE_Y = C.BOX_RIM_INNER_Y
NUT_ANCHOR_OFFSET = 15.8
NUT_Y0 = PLATE_SPINDLE_Y - NUT_ANCHOR_OFFSET
NUT_THREAD_Y0 = NUT_Y0 - NUT_THREAD_LEN
CAGE_Y0 = PLATE_SPINDLE_Y - 37.535
CAGE_Y1 = PLATE_SPINDLE_Y - 13.600
WIDTH_RIM_CLEAR = 0.20
# The old v50-style side guides projected toward the clamp plate and are no
# longer needed: the plate is constrained by its two captive lead screws.
# Keep only the structural cage/front-deck datums.
CAGE_FRONT_Y_DATUM = CAGE_Y1 - 0.40
LOW_DECK_Z1 = 14.0
STATION_TIE_OVERLAP_X = 0.35
PRINT_BASE_PLANE_Z = C.BOX_SUPPORT_Z
PRINT_FRAME_BOSS_Z0 = 20.0
PRINT_FRAME_BOSS_Z1 = PRINT_BASE_PLANE_Z
# The visible/load-bearing carrier is 30 mm high: ARM_BOTTOM_Z=9.54 to
# BOX_SUPPORT_Z=39.54. Centre the COMPLETE screw/thread axis in that REAL
# envelope, not in the artificial upper boss sub-volume that starts at Z=20.
# With the Ø11.8 spindle corridor this leaves 9.10 mm real material both above
# and below the corridor at the station wall.
SPINDLE_Z = (C.ARM_BOTTOM_Z + C.BOX_SUPPORT_Z) / 2.0
LEAD_NUT_SEMICIRCLE_R = 8.0
LEAD_NUT_BODY_Z0 = -LEAD_NUT_SEMICIRCLE_R
LEAD_NUT_BODY_Z1 = 7.0
LEAD_NUT_UPPER_LUG_Z0 = 5.0
LEAD_NUT_UPPER_LUG_Z1 = 11.0
LEAD_NUT_POCKET_FLOOR_Z = SPINDLE_Z + LEAD_NUT_BODY_Z0
LEAD_NUT_POCKET_X_CLEAR = 0.20
LEAD_NUT_POCKET_FREE_Y = 0.35
# Top-loaded carrier: the base needs a service opening from above, but the
# carrier itself closes that opening flush with the 39.54 mm carrier surface.
# Give the cap a 0.20 mm overlap into the upper retaining lug so LEAD_NUT is one
# printable solid rather than face-touching bodies.
LEAD_NUT_CAP_Z0 = 10.80
LEAD_NUT_CAP_Z1 = C.BOX_SUPPORT_Z - SPINDLE_Z  # 15.00 -> installed top Z=39.54

# True circular lower cartridge / matching BASE pocket profile.
# The BASE prints upside-down.  The lower half of the cartridge is a genuine
# R8 semicircle in X/Z and the pocket follows the same curve with only 0.20 mm
# X clearance.  In the inverted BASE print the cavity therefore closes
# progressively layer-by-layer like a horizontal round hole instead of ending
# in one wide flat roof.
LEAD_NUT_LOWER_TRANSITION_Z = 0.0
LEAD_NUT_PROFILE_STEPS = 40

FINAL_DECK_Z0 = C.ARM_BOTTOM_Z
FINAL_DECK_Z1 = LOW_DECK_Z1

# Structural cage reinforcement.  The removable lead-nut cartridge remains the
# wear part; these members reinforce only its fixed housing.  All reinforcement
# stays behind/below the moving clamp-plate envelope so cartridge insertion,
# spindle travel and plate opening remain serviceable.
CAGE_STRUCT_Y1 = min(CAGE_Y1, C.PLATE_SWEEP_Y0 - 0.20)
CAGE_CROSS_OVERLAP_X = 0.35
STATION_FLOOR_Y1 = min(CAGE_FRONT_Y_DATUM, C.PLATE_SWEEP_Y0 - 0.10)
STATION_FLOOR_BOSS_OVERLAP_Z = 0.35
STATION_FLOOR_POCKET_CLEAR_Z = 0.20

LOWER_SADDLE_R = 6.15

LOWER_FORK_SIDE_CLEAR = 0.40
LOWER_FORK_EAR_T = 4.60
LOWER_FORK_INNER_HALF_X = C.UPPER_PIVOT_W/2.0 + LOWER_FORK_SIDE_CLEAR
LOWER_FORK_OUTER_HALF_X = LOWER_FORK_INNER_HALF_X + LOWER_FORK_EAR_T
LOWER_FORK_W = 2.0 * LOWER_FORK_OUTER_HALF_X
LOWER_PIVOT_R = 5.0
LOWER_WEB_Z0 = -10.5
LOWER_WEB_TOP_Z = -1.5
# Natural Z-up print feet under both thin fork ears.  They span only the
# pivot-circle Y projection and ear thickness, from the common shell floor to
# 0.2 mm into the existing web/circle root.
LOWER_PIVOT_FOOT_Z0 = -14.5
LOWER_PIVOT_FOOT_Z1 = LOWER_WEB_Z0 + 0.20
LOWER_PIVOT_FOOT_Y0 = C.PIN_Y - LOWER_PIVOT_R
LOWER_PIVOT_FOOT_Y1 = C.PIN_Y + LOWER_PIVOT_R
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


def hex_wire_z(af, z):
    r = af / math.sqrt(3.0)
    pts = [
        App.Vector(
            r*math.cos(math.radians(30.0+60.0*i)),
            r*math.sin(math.radians(30.0+60.0*i)),
            z,
        )
        for i in range(6)
    ]
    return Part.makePolygon(pts + [pts[0]])


def hex_frustum_z(af0, af1, height, z0=0.0):
    q = Part.makeLoft(
        [hex_wire_z(af0, z0), hex_wire_z(af1, z0+height)],
        True,
        False,
    ).removeSplitter()
    C.require_single(q, 'hex-frustum')
    return q


def prism_xz_y(points, y0, y1, label):
    pts = [App.Vector(x, y0, z) for x, z in points]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    q = face.extrude(App.Vector(0, y1-y0, 0)).removeSplitter()
    C.require_single(q, label)
    return q


def prism_yz_x(points, x0, x1, label):
    pts = [App.Vector(x0, y, z) for y, z in points]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    q = face.extrude(App.Vector(x1-x0, 0, 0)).removeSplitter()
    C.require_single(q, label)
    return q


def lead_nut_half_x(z, clearance=0.0):
    if z <= -LEAD_NUT_SEMICIRCLE_R:
        return clearance
    if z >= LEAD_NUT_LOWER_TRANSITION_Z:
        return LEAD_NUT_SEMICIRCLE_R + clearance
    x = math.sqrt(max(
        0.0,
        LEAD_NUT_SEMICIRCLE_R*LEAD_NUT_SEMICIRCLE_R - z*z,
    ))
    return x + clearance


def lead_nut_xz_profile(z1, clearance=0.0):
    # Lower half is a true semicircle.  For the BASE pocket, clearance widens
    # the X coordinate only; the floor Z stays identical so the removable nut
    # retains a deterministic gravity/thrust seat instead of floating 0.2 mm.
    lower=[]
    for i in range(LEAD_NUT_PROFILE_STEPS+1):
        t=i/float(LEAD_NUT_PROFILE_STEPS)
        z=-LEAD_NUT_SEMICIRCLE_R + LEAD_NUT_SEMICIRCLE_R*t
        lower.append((lead_nut_half_x(z,clearance),z))

    pts=list(lower)
    pts.append((LEAD_NUT_SEMICIRCLE_R+clearance,z1))
    pts.append((-LEAD_NUT_SEMICIRCLE_R-clearance,z1))
    left=[(-x,z) for x,z in reversed(lower)]
    if clearance <= 1e-12:
        # Do not duplicate the single mathematical bottom point of the
        # semicircle; polygon closure supplies that final edge.
        left=left[:-1]
    pts.extend(left)
    return pts


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
    stud_thread_len = OUTER_STUD_LEN - SPINDLE_PRINT_PILOT_H
    stud_steps = max(48, int(math.ceil(stud_thread_len / THREAD_PITCH * 40.0)))
    stud_phase = -360.0 * SPINDLE_PRINT_PILOT_H / THREAD_PITCH
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

module ridge_lh(z0,len,steps,phase=0){{
  a1=-360*len/pitch;
  function ang(i)=phase+a1*i/steps;
  // Phase rotates the ridge only; it must never shift the physical axial
  // start.  zc therefore remains 0..len even when the first 0.8 mm are left
  // smooth as the vertical print foot.
  function zc(i)=len*i/steps;
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
    // OUTBOARD print foot + retainer stud. The first 0.80 mm are
    // smooth Ø6.5 so the exact STL stands on a real flat face; the remaining
    // 6.20 mm retain the same helical phase as the former full-length stud.
    translate([0,0,{stud0}]) cylinder(r=core_r,h={OUTER_STUD_LEN+0.25});
    ridge_lh(
      {stud0}+{SPINDLE_PRINT_PILOT_H},
      {OUTER_STUD_LEN-SPINDLE_PRINT_PILOT_H},
      {stud_steps},
      {stud_phase}
    );

    // Support-free knob drive: 2 mm hex frustum then 5 mm full AF10.  The
    // taper stays entirely inside the 7 mm knob envelope.
    translate([0,0,{hex0}])
      linear_extrude(
        height={SPINDLE_HEX_TAPER_H},
        scale={SPINDLE_HEX_AF/SPINDLE_HEX_TAPER_AF0},
        convexity=20
      )
        circle(r={SPINDLE_HEX_TAPER_AF0/math.sqrt(3.0)},$fn=6);
    translate([0,0,{hex0+SPINDLE_HEX_TAPER_H-0.05}])
      cylinder(
        r={SPINDLE_HEX_AF/math.sqrt(3.0)},
        h={HEX_LEN-SPINDLE_HEX_TAPER_H+0.05},
        $fn=6
      );

    // Small internal bridge only inside the Ø6.5 plate hole, never enlarging
    // the journal or filling the C-clip groove.
    translate([0,0,-0.20]) cylinder(r=3.0,h=0.60);

    // Journal through the plate with the printable C-clip groove at the
    // outboard face. The final 2.50 mm flare at exactly 45 degrees into the
    // Ø11 thrust shoulder; the plate carries a matching conical seat.
    cylinder(r=3.0,h=0.4);
    translate([0,0,0.4]) cylinder(r=2.5,h=1.4);
    translate([0,0,1.8])
      cylinder(r=3.0,h={SPINDLE_LOCAL_JOURNAL-SPINDLE_SHOULDER_TAPER_H-1.8+0.05});
    translate([0,0,{SPINDLE_LOCAL_JOURNAL-SPINDLE_SHOULDER_TAPER_H}])
      cylinder(
        r1={SPINDLE_SHOULDER_TAPER_R0},
        r2={SPINDLE_SHOULDER_TAPER_R1},
        h={SPINDLE_SHOULDER_TAPER_H}
      );

    // INBOARD: full thrust ring is now completely supported by that cone.
    translate([0,0,{shoulder0}]) cylinder(r={SHOULDER_D/2.0},h={SPINDLE_LOCAL_SHOULDER});
    translate([0,0,{main0-0.25}]) cylinder(r=core_r,h={LEAD_THREAD_LEN+0.25});
    ridge_rh({main0},{LEAD_THREAD_LEN},{main_steps});
  }}
}}

translate([0,0,{-stud0}]) spindle_z();
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
# Restore the proven mechanical Lower exactly.  Print optimisation is achieved
# by exporting this functional geometry on its broad X side, not by changing
# the hinge ear, web, saddle or closure-tongue load paths.
lower_shell = C.box(
    -LOWER_FORK_OUTER_HALF_X,
    RACK_CLOSURE_MAIN_Y0,
    -14.5,
    LOWER_FORK_W,
    RACK_CLOSURE_MAIN_Y1-RACK_CLOSURE_MAIN_Y0,
    14.5,
)
lower_pivot_l = C.cyl_x(
    LOWER_PIVOT_R,LOWER_FORK_EAR_T,
    -LOWER_FORK_OUTER_HALF_X,C.PIN_Y,C.PIN_Z,
)
lower_pivot_r = C.cyl_x(
    LOWER_PIVOT_R,LOWER_FORK_EAR_T,
    LOWER_FORK_INNER_HALF_X,C.PIN_Y,C.PIN_Z,
)
lower_web_l = C.box(
    -LOWER_FORK_OUTER_HALF_X,C.PIN_Y,LOWER_WEB_Z0,
    LOWER_FORK_EAR_T,8.0,LOWER_WEB_TOP_Z-LOWER_WEB_Z0,
)
lower_web_r = C.box(
    LOWER_FORK_INNER_HALF_X,C.PIN_Y,LOWER_WEB_Z0,
    LOWER_FORK_EAR_T,8.0,LOWER_WEB_TOP_Z-LOWER_WEB_Z0,
)
lower_pivot_foot_l = C.box(
    -LOWER_FORK_OUTER_HALF_X,
    LOWER_PIVOT_FOOT_Y0,
    LOWER_PIVOT_FOOT_Z0,
    LOWER_FORK_EAR_T,
    LOWER_PIVOT_FOOT_Y1-LOWER_PIVOT_FOOT_Y0,
    LOWER_PIVOT_FOOT_Z1-LOWER_PIVOT_FOOT_Z0,
)
lower_pivot_foot_r = C.box(
    LOWER_FORK_INNER_HALF_X,
    LOWER_PIVOT_FOOT_Y0,
    LOWER_PIVOT_FOOT_Z0,
    LOWER_FORK_EAR_T,
    LOWER_PIVOT_FOOT_Y1-LOWER_PIVOT_FOOT_Y0,
    LOWER_PIVOT_FOOT_Z1-LOWER_PIVOT_FOOT_Z0,
)
closure_pad = C.box(
    -RACK_CLOSURE_PAD_X/2.0,
    RACK_CLOSURE_PAD_Y0,
    RACK_CLOSURE_PAD_Z0,
    RACK_CLOSURE_PAD_X,
    RACK_CLOSURE_PAD_Y1-RACK_CLOSURE_PAD_Y0,
    RACK_CLOSURE_PAD_Z1-RACK_CLOSURE_PAD_Z0,
)
LOWER = C.fuse_seq(
    [
        lower_shell,
        lower_pivot_l,lower_pivot_r,
        lower_web_l,lower_web_r,
        lower_pivot_foot_l,lower_pivot_foot_r,
        closure_pad,
    ],
    'lower-rack-fork-with-supported-pivot-and-m4-closure-tongue',
)
lower_fork_slot = C.box(
    -LOWER_FORK_INNER_HALF_X,-20.0,-13.0,
    2.0*LOWER_FORK_INNER_HALF_X,15.5,15.5,
)
LOWER = LOWER.cut(lower_fork_slot).removeSplitter()
LOWER = LOWER.cut(
    C.cyl_x(
        LOWER_SADDLE_R,LOWER_FORK_W+2.0,
        -LOWER_FORK_OUTER_HALF_X-1.0,0,0,
    )
).removeSplitter()
# Keep the functional pivot bore truly round.  In the print-oriented export
# its axis is vertical, so no teardrop/V distortion is needed.
LOWER = LOWER.cut(
    C.cyl_x(
        C.PIN_HOLE_D/2,LOWER_FORK_W+2.0,
        -LOWER_FORK_OUTER_HALF_X-1.0,C.PIN_Y,C.PIN_Z,
    )
).removeSplitter()
LOWER = LOWER.cut(
    Part.makeCylinder(
        RACK_M4_LOWER_CLEAR_D/2.0,16.5,
        App.Vector(0.0,C.RACK_CLOSURE_Y,-15.5),
        App.Vector(0,0,1),
    )
).removeSplitter()
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
    # The carrier is inserted from ABOVE again, so the underside can and should
    # remain structurally closed. Route the full-width station wedge immediately
    # below the seated carrier floor; pocket machining must not nibble this load
    # path away.
    x0 = sx - C.BOX_CLAMP_BOSS_HALF_X - CAGE_CROSS_OVERLAP_X
    x1 = sx + C.BOX_CLAMP_BOSS_HALF_X + CAGE_CROSS_OVERLAP_X
    pocket_under_z = LEAD_NUT_POCKET_FLOOR_Z - STATION_FLOOR_POCKET_CLEAR_Z
    yz = [
        App.Vector(0.0,CAGE_Y0,FINAL_DECK_Z0),
        App.Vector(0.0,STATION_FLOOR_Y1,FINAL_DECK_Z0),
        App.Vector(0.0,STATION_FLOOR_Y1,FINAL_DECK_Z1),
        App.Vector(0.0,NUT_THREAD_Y0,pocket_under_z),
        App.Vector(0.0,CAGE_Y0,PRINT_FRAME_BOSS_Z0+STATION_FLOOR_BOSS_OVERLAP_Z),
    ]
    face = Part.Face(Part.makePolygon(yz+[yz[0]]))
    q = face.extrude(App.Vector(x1-x0,0,0))
    q.translate(App.Vector(x0,0,0))
    return q.removeSplitter()


def make_cage_cross_bottom_drop(cross_x0, cross_x1, cross_y0, cross_y1, side):
    # The cage transverse box beam has a lower flange at the same inverted-print
    # problem level.  Its two vertical webs are already structural; mirror the
    # long-holm strategy inside the box and let two smooth DROPs meet at centre.
    rear_inner = cross_y0 + C.WEB_T
    front_inner = cross_y1 - C.WEB_T
    centre = (rear_inner + front_inner) / 2.0
    root_y = rear_inner if side < 0 else front_inner
    tip_y = centre + (0.20 if side < 0 else -0.20)
    span = abs(tip_y-root_y)

    flange_top = FINAL_DECK_Z0 + C.FLANGE_T
    base_z = flange_top - 0.20
    root_z = flange_top + span
    tip_z = flange_top + 0.20

    curve=[]
    for i in range(19):
        t=i/18.0
        y=root_y + (tip_y-root_y)*C._smoothstep(t)
        z=root_z + (tip_z-root_z)*t
        curve.append(App.Vector(cross_x0,y,z))
    pts=[
        App.Vector(cross_x0,root_y,base_z),
        App.Vector(cross_x0,root_y,root_z),
    ] + curve[1:] + [
        App.Vector(cross_x0,tip_y,base_z),
        App.Vector(cross_x0,root_y,base_z),
    ]
    q=Part.Face(Part.makePolygon(pts)).extrude(
        App.Vector(cross_x1-cross_x0,0,0)
    ).removeSplitter()
    C.require_single(q,'cage-cross-bottom-drop')
    return q


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
    # The top-open pin recesses necessarily nibble the station-side ends of the
    # upper transverse flange. Add a real 12 mm rearward top backstrap, fully
    # behind the pin service Y-zone, and fuse it into the top flange. The first
    # 5 mm version still left only 98.894 % of the declared cross-top load path;
    # 12 mm restores real section area with >99 % reserve without relaxing the
    # structural validation threshold.
    CROSS_TOP_BACKSTRAP_DEPTH = 12.0
    cross_top_main = C.box(
        cross_x0,cross_y0,PRINT_BASE_PLANE_Z-C.FLANGE_T,
        cross_x1-cross_x0,cross_y1-cross_y0,C.FLANGE_T,
    )
    cross_top_backstrap = C.box(
        cross_x0,cross_y0-CROSS_TOP_BACKSTRAP_DEPTH,PRINT_BASE_PLANE_Z-C.FLANGE_T,
        cross_x1-cross_x0,CROSS_TOP_BACKSTRAP_DEPTH+0.35,C.FLANGE_T,
    )
    cross_top = C.fuse_seq(
        [cross_top_main,cross_top_backstrap],
        'cage-cross-top-with-rear-backstrap',
    )

    cross = [
        C.box(cross_x0,cross_y0,FINAL_DECK_Z0,
              cross_x1-cross_x0,cross_y1-cross_y0,C.FLANGE_T),
        cross_top,
        C.box(cross_x0,cross_y0,cross_web_z0,
              cross_x1-cross_x0,C.WEB_T,cross_web_z1-cross_web_z0),
        C.box(cross_x0,cross_y1-C.WEB_T,cross_web_z0,
              cross_x1-cross_x0,C.WEB_T,cross_web_z1-cross_web_z0),
        make_cage_cross_bottom_drop(cross_x0,cross_x1,cross_y0,cross_y1,-1),
        make_cage_cross_bottom_drop(cross_x0,cross_x1,cross_y0,cross_y1,1),
    ]

    probes = {
        'holm_left': holm_left,
        'holm_right': holm_right,
        'cross_bottom': cross[0],
        'cross_top': cross[1],
        'cross_drop_rear': cross[2],
        'cross_drop_front': cross[3],
        'cross_bottom_inner_drop_rear': cross[4],
        'cross_bottom_inner_drop_front': cross[5],
        'station_floor_left': make_station_floor_gusset(left_sx),
        'station_floor_right': make_station_floor_gusset(right_sx),
    }
    return probes


def make_cage_structure():
    # No projecting side-guide blocks. The two captive spindles locate the
    # moving plate; the fixed cage contains only load-bearing station structure.
    parts=[]

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
#
# With the screw axis now on the real carrier mid-plane (Z=24.54), retention
# belongs above the thread body again. A compact overlapping upper lug keeps
# the cross-pin well inside the 39.54 mm carrier top while preserving a clean
# gravity seat at the main cartridge body's lower face.
LEAD_NUT_PIN_LOCAL_Y = -7.0
# Restore the higher pin datum from the earlier carrier: with the corrected
# spindle axis this places the retaining pin at Z=34.54, 5 mm below the top.
# The seat is now open upward so the pin is installed from above.
LEAD_NUT_PIN_LOCAL_Z = 10.0
LEAD_NUT_PIN_HOLE_D = 3.4
LEAD_NUT_PIN_DROP_SLOT_W = 3.8
NUT_PIN_SHAFT_D = 3.0
NUT_PIN_GROOVE_D = 2.4
NUT_PIN_GROOVE_X0 = 11.4
NUT_PIN_GROOVE_W = 1.6
NUT_PIN_CLIP_T = 1.3
NUT_PIN_CLIP_X = NUT_PIN_GROOVE_X0 + (NUT_PIN_GROOVE_W-NUT_PIN_CLIP_T)/2.0
NUT_PIN_HEAD_R = 3.0
NUT_PIN_HEAD_T = 2.0
NUT_PIN_CLIP_OUTER_R = 3.2
NUT_PIN_SERVICE_CLEAR = 0.35
NUT_PIN_HEAD_POCKET_R = NUT_PIN_HEAD_R + NUT_PIN_SERVICE_CLEAR
NUT_PIN_HEAD_POCKET_X0 = -14.0 - NUT_PIN_SERVICE_CLEAR
NUT_PIN_HEAD_POCKET_LEN = NUT_PIN_HEAD_T + 2.0*NUT_PIN_SERVICE_CLEAR
NUT_PIN_CLIP_POCKET_R = NUT_PIN_CLIP_OUTER_R + NUT_PIN_SERVICE_CLEAR
NUT_PIN_CLIP_POCKET_X0 = NUT_PIN_CLIP_X - NUT_PIN_SERVICE_CLEAR
NUT_PIN_CLIP_POCKET_LEN = NUT_PIN_CLIP_T + 2.0*NUT_PIN_SERVICE_CLEAR
# The wear-cartridge body and BASE pocket share a true R8 lower semicircle.
# The inverted BASE print therefore closes the pocket progressively, exactly
# like a small horizontal round opening, instead of producing a flat roof.
LEAD_NUT = prism_xz_y(
    lead_nut_xz_profile(LEAD_NUT_BODY_Z1),
    -NUT_THREAD_LEN, 0.0,
    'true-semicircle lead-nut body',
)
LEAD_NUT = LEAD_NUT.fuse(C.box(
    -6.0,-11.0,LEAD_NUT_UPPER_LUG_Z0,
    12.0,8.0,LEAD_NUT_UPPER_LUG_Z1-LEAD_NUT_UPPER_LUG_Z0,
)).removeSplitter()
# Close the former upper gap completely. The pin bore and its narrow top-entry
# throat are cut afterwards and remain the only intentional opening here.
LEAD_NUT = LEAD_NUT.fuse(C.box(
    -8.0,-NUT_THREAD_LEN,LEAD_NUT_BODY_Z1-0.10,
    16.0,NUT_THREAD_LEN,
    LEAD_NUT_CAP_Z0-LEAD_NUT_BODY_Z1+0.20,
)).removeSplitter()
# Flush closure cap: full cartridge footprint, installed top exactly at the
# base top Z=39.54. The pocket remains a top service opening in the bare BASE,
# but the installed carrier closes it instead of leaving a visible rectangular
# hole in the assembly.
LEAD_NUT = LEAD_NUT.fuse(C.box(
    -8.0,-NUT_THREAD_LEN,LEAD_NUT_CAP_Z0,
    16.0,NUT_THREAD_LEN,LEAD_NUT_CAP_Z1-LEAD_NUT_CAP_Z0,
)).removeSplitter()
LEAD_NUT = LEAD_NUT.cut(FEMALE_NEGY).removeSplitter()

# Functional round pin cradle.  The Ø3.4 cylindrical seat is kept
# genuinely round and opens to the top through the existing straight service
# throat.  In the lead-nut print orientation the thread axis is vertical and
# this small round cross-hole closes progressively without support.
lead_nut_pin_cradle = C.cyl_x(
    LEAD_NUT_PIN_HOLE_D/2.0,20.0,-10.0,
    LEAD_NUT_PIN_LOCAL_Y,LEAD_NUT_PIN_LOCAL_Z,
)
lead_nut_pin_drop = C.box(
    -10.0,
    LEAD_NUT_PIN_LOCAL_Y-LEAD_NUT_PIN_DROP_SLOT_W/2.0,
    LEAD_NUT_PIN_LOCAL_Z,
    20.0,
    LEAD_NUT_PIN_DROP_SLOT_W,
    LEAD_NUT_CAP_Z1-LEAD_NUT_PIN_LOCAL_Z+0.50,
)
LEAD_NUT = LEAD_NUT.cut(
    lead_nut_pin_cradle.fuse(lead_nut_pin_drop).removeSplitter()
).removeSplitter()
C.require_single(
    LEAD_NUT,
    'closed-body top-loaded RH8x2 lead-nut carrier with round pin service opening',
)

lead_nut_gap_checks=[]
for label,x,y,z,expect_solid in (
    ('rear-wall',0.0,-12.5,9.0,True),
    ('front-wall',0.0,-1.5,9.0,True),
    ('pin-left-cheek',0.0,LEAD_NUT_PIN_LOCAL_Y-2.4,9.5,True),
    ('pin-right-cheek',0.0,LEAD_NUT_PIN_LOCAL_Y+2.4,9.5,True),
    ('pin-axis',0.0,LEAD_NUT_PIN_LOCAL_Y,LEAD_NUT_PIN_LOCAL_Z,False),
    ('pin-top-entry',0.0,LEAD_NUT_PIN_LOCAL_Y,12.5,False),
):
    solid=bool(LEAD_NUT.isInside(App.Vector(x,y,z),1e-5,False))
    lead_nut_gap_checks.append({
        'sample':label,'solid':solid,'expected_solid':expect_solid,
    })
    if solid != expect_solid:
        raise RuntimeError(
            f'lead-nut closed upper body wrong at {label}: '
            f'solid={solid} expected={expect_solid}'
        )

NUT_PIN = C.fuse_seq([
    C.cyl_x(NUT_PIN_SHAFT_D/2.0,23.4,-12.0,0,0),
    C.cyl_x(NUT_PIN_GROOVE_D/2.0,NUT_PIN_GROOVE_W,NUT_PIN_GROOVE_X0,0,0),
    C.cyl_x(NUT_PIN_SHAFT_D/2.0,1.7,NUT_PIN_GROOVE_X0+NUT_PIN_GROOVE_W,0,0),
    C.cyl_x(NUT_PIN_HEAD_R,NUT_PIN_HEAD_T,-14.0,0,0),
],'lead-nut-retaining-pin')
NUT_PIN_SERVICE_X0 = NUT_PIN.BoundBox.XMin - 0.35
NUT_PIN_SERVICE_X1 = NUT_PIN.BoundBox.XMax + 0.35
NUT_PIN_SERVICE_XLEN = NUT_PIN_SERVICE_X1 - NUT_PIN_SERVICE_X0
NUT_PIN_CLIP = make_c_clip(NUT_PIN_CLIP_OUTER_R,1.25,NUT_PIN_CLIP_T,2.4)

for sx in SPINDLE_X:
    # Top service opening for the removable carrier. The pocket has a real,
    # deterministic floor at the main-body datum; only its top is open. The
    # installed carrier's flush cap fills this opening to Z=39.54.
    pocket_y0 = NUT_THREAD_Y0
    pocket_profile = [
        (sx+x, SPINDLE_Z+z)
        for x, z in lead_nut_xz_profile(
            (PRINT_BASE_PLANE_Z + 0.50) - SPINDLE_Z,
            LEAD_NUT_POCKET_X_CLEAR,
        )
    ]
    pocket = prism_xz_y(
        pocket_profile,
        pocket_y0,
        pocket_y0 + NUT_THREAD_LEN + LEAD_NUT_POCKET_FREE_Y,
        f'true-semicircle lead-nut pocket@{sx}',
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
        cyl_y(SPINDLE_TUNNEL_R,tunnel_y1-tunnel_y0,sx,tunnel_y0,SPINDLE_Z)
    ).removeSplitter()

    pin_y = NUT_Y0 + LEAD_NUT_PIN_LOCAL_Y
    pin_z = SPINDLE_Z + LEAD_NUT_PIN_LOCAL_Z

    # The pin is laid in from above. A cylindrical cradle defines the final
    # position and a straight vertical throat opens that cradle to the top.
    # Head and clip ends receive matching top-open service recesses.
    shaft_cradle = C.cyl_x(
        LEAD_NUT_PIN_HOLE_D/2.0,
        NUT_PIN_SERVICE_XLEN,
        sx+NUT_PIN_SERVICE_X0,
        pin_y,pin_z,
    )
    shaft_drop = C.box(
        sx+NUT_PIN_SERVICE_X0,
        pin_y-LEAD_NUT_PIN_DROP_SLOT_W/2.0,
        pin_z,
        NUT_PIN_SERVICE_XLEN,
        LEAD_NUT_PIN_DROP_SLOT_W,
        PRINT_BASE_PLANE_Z-pin_z+0.50,
    )
    RIGHT_FULL = RIGHT_FULL.cut(
        shaft_cradle.fuse(shaft_drop).removeSplitter()
    ).removeSplitter()

    head_cradle = C.cyl_x(
        NUT_PIN_HEAD_POCKET_R,NUT_PIN_HEAD_POCKET_LEN,
        sx+NUT_PIN_HEAD_POCKET_X0,pin_y,pin_z,
    )
    head_drop = C.box(
        sx+NUT_PIN_HEAD_POCKET_X0,
        pin_y-NUT_PIN_HEAD_POCKET_R,
        pin_z,
        NUT_PIN_HEAD_POCKET_LEN,
        2.0*NUT_PIN_HEAD_POCKET_R,
        PRINT_BASE_PLANE_Z-pin_z+0.50,
    )
    RIGHT_FULL = RIGHT_FULL.cut(
        head_cradle.fuse(head_drop).removeSplitter()
    ).removeSplitter()

    clip_cradle = C.cyl_x(
        NUT_PIN_CLIP_POCKET_R,NUT_PIN_CLIP_POCKET_LEN,
        sx+NUT_PIN_CLIP_POCKET_X0,pin_y,pin_z,
    )
    clip_drop = C.box(
        sx+NUT_PIN_CLIP_POCKET_X0,
        pin_y-NUT_PIN_CLIP_POCKET_R,
        pin_z,
        NUT_PIN_CLIP_POCKET_LEN,
        2.0*NUT_PIN_CLIP_POCKET_R,
        PRINT_BASE_PLANE_Z-pin_z+0.50,
    )
    RIGHT_FULL = RIGHT_FULL.cut(
        clip_cradle.fuse(clip_drop).removeSplitter()
    ).removeSplitter()

C.require_single(RIGHT_FULL,'RIGHT full with v50 cartridge pockets and smooth spindle corridors')

pin_bore_clearance=[]
for xc in C.CLAMP_X:
    probe=C.cyl_x(C.PIN_HOLE_D/2-0.05,38.0,xc-19.0,C.PIN_Y,C.PIN_Z); cv=RIGHT_FULL.common(probe).Volume
    pin_bore_clearance.append({'x_mm':xc,'probe_common_mm3':round(cv,9)})
    if cv>1e-5: raise RuntimeError(f'Rack pin bore closed at X={xc}: {cv:.6f} mm3')
C.require_single(RIGHT_FULL,'RIGHT full final'); LEFT_FULL=C.mirror_x(RIGHT_FULL)

stage('plate')
PLATE_BODY_Y0=C.BOX_RIM_INNER_Y-PLATE_Y; PLATE_HOOK_Y0=C.BOX_RIM_INNER_Y-WIDTH_RIM_CLEAR; PLATE_HOOK_Y1=C.BOX_RIM_INNER_Y+UNDERHOOK
PLATE=C.box(PLATE_X0,PLATE_BODY_Y0,PLATE_Z0,PLATE_X,PLATE_Y,PLATE_Z1-PLATE_Z0)
PLATE=PLATE.fuse(C.box(PLATE_X0,PLATE_HOOK_Y0,RIM_BOTTOM_Z-UNDERHOOK_T,PLATE_X,PLATE_HOOK_Y1-PLATE_HOOK_Y0,UNDERHOOK_T))
for sx in SPINDLE_X:
    PLATE=PLATE.cut(cyl_y(PLATE_HOLE_D/2,PLATE_Y+1,sx,PLATE_BODY_Y0-0.5,SPINDLE_Z))
    # Matching inboard 45deg thrust countersink for the printable spindle cone.
    # The last 2.5 mm of the plate therefore support the Ø11 ring without a
    # horizontal printed underside while still acting as the real axial seat.
    shoulder_cone = Part.makeCone(
        PLATE_HOLE_D/2.0,
        PLATE_SHOULDER_CONE_CLEAR_R,
        SPINDLE_SHOULDER_TAPER_H,
        App.Vector(
            sx,
            PLATE_SPINDLE_Y-(SPINDLE_LOCAL_JOURNAL-SPINDLE_SHOULDER_TAPER_H),
            SPINDLE_Z,
        ),
        App.Vector(0,-1,0),
    )
    PLATE=PLATE.cut(shoulder_cone).removeSplitter()
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
SPINDLE_PRINT_Z=import_scad_shape(SPINDLE_SCAD)
C.require_single(SPINDLE_PRINT_Z,'print-oriented complete manifold RH8x2 lead screw')
# Master SCAD spans negative Z at the outboard stud. Shift only the printable
# export so its flat pilot sits exactly on the build plane.
SPINDLE_PRINT_Z.translate(App.Vector(0,0,-SPINDLE_PRINT_Z.BoundBox.ZMin))
C.require_single(SPINDLE_PRINT_Z,'build-plane lead screw')

# Mechanical model keeps the historical installed transform.  Recreate it from
# an unshifted master so all existing Y datums and RH8x2 chirality remain exact.
SPINDLE_MASTER_Z=import_scad_shape(SPINDLE_SCAD)
SPINDLE_MASTER_Z.translate(
    App.Vector(0,0,-(HEX_LEN+OUTER_STUD_LEN))
)
SPINDLE=rotate_z180(z_to_y(SPINDLE_MASTER_Z))
C.require_single(SPINDLE,'complete manifold RH8x2 lead screw installed')
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
KNOB_Z=KP.build_scalloped_knob_body()
KNOB_Z=KNOB_Z.cut(
    Part.makeCylinder(4.3,KP.KNOB_H+0.4,App.Vector(0,0,-0.2))
).removeSplitter()
# Outer 2.2 mm follow the lead-screw hex frustum; the remaining ~5 mm keep the
# full AF10.35 drive pocket used for hand torque.
KNOB_Z=KNOB_Z.cut(
    hex_frustum_z(
        KNOB_HEX_TAPER_AF0,
        KNOB_HEX_POCKET_AF,
        KNOB_HEX_TAPER_H,
        -0.10,
    )
).removeSplitter()
KNOB_Z=KNOB_Z.cut(
    hex_z(
        KNOB_HEX_POCKET_AF,
        KP.KNOB_H-KNOB_HEX_TAPER_H+0.40,
        KNOB_HEX_TAPER_H-0.20,
    )
).removeSplitter()
KNOB=rotate_z180(z_to_y(KNOB_Z))
C.require_single(KNOB,'box-clamp knob support-free tapered hex pocket')

CAP_NUT_Z=hex_z(13.0,5.4)
CAP_NUT_Z=CAP_NUT_Z.cut(CAP_FEMALE_Z).removeSplitter()
C.require_single(CAP_NUT_Z,'lead-knob-retainer-nut true RH8x2 Z master')
CAP_NUT=rotate_z180(z_to_y(CAP_NUT_Z))
C.require_single(CAP_NUT,'lead-knob-retainer-nut')

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

lead_nut_span_samples=[]
for local_z in (0.0,-2.0,-4.0,-6.0,-8.0):
    half=lead_nut_half_x(local_z,LEAD_NUT_POCKET_X_CLEAR)
    lead_nut_span_samples.append({
        'local_z_mm':local_z,
        'pocket_width_mm':round(2.0*half,3),
    })
lead_nut_printability = {
    'body_profile':'true R8 lower semicircle',
    'semicircle_radius_mm':LEAD_NUT_SEMICIRCLE_R,
    'body_full_width_mm':round(2.0*LEAD_NUT_SEMICIRCLE_R,3),
    'base_pocket_floor_bridge_mm':round(2.0*LEAD_NUT_POCKET_X_CLEAR,3),
    'closing_span_samples':lead_nut_span_samples,
    'pin_cradle':'round Ø3.4 top-open U-cradle',
    'upper_body':'closed except functional cross-pin bore/top-entry throat',
    'upper_gap_checks':lead_nut_gap_checks,
    'preferred_print_orientation':'rotate -90deg about X; RH8x2 axis vertical',
}
widths=[q['pocket_width_mm'] for q in lead_nut_span_samples]
if not all(widths[i] > widths[i+1] for i in range(len(widths)-1)):
    fail('lead-nut semicircular BASE pocket does not close progressively')
if lead_nut_printability['base_pocket_floor_bridge_mm'] > 0.5:
    fail('lead-nut semicircle leaves excessive final floor bridge')


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
    axis_to_holm = side*(holm_inner_x-sx)
    knob_to_holm = axis_to_holm-KP.KNOB_R
    holm_station_checks.append({
        'spindle_x_mm':round(sx,3),
        'holm_inner_x_mm':round(holm_inner_x,3),
        'boss_to_holm_gap_mm':round(gap,3),
        'axis_to_holm_mm':round(axis_to_holm,3),
        'knob_to_holm_clearance_mm':round(knob_to_holm,3),
    })
    if abs(gap-C.BOX_CLAMP_HOLM_CLEAR_X)>1e-6:
        fail(f'box-clamp station at X={sx} lost symmetric holm clearance: {gap:.3f} mm')
    if knob_to_holm < 20.0:
        fail(f'box-clamp knob at X={sx} has only {knob_to_holm:.3f} mm clearance to holm')

# Prove the screw corridor is centred in the REAL 30 mm carrier envelope.
# Do not use PRINT_FRAME_BOSS_Z0 here: Z=20 is only an internal upper-boss
# construction datum and previously made a visibly high hole look "centred".
carrier_spindle_ligaments={
    'carrier_z0_mm':round(C.ARM_BOTTOM_Z,3),
    'carrier_z1_mm':round(C.BOX_SUPPORT_Z,3),
    'spindle_axis_z_mm':round(SPINDLE_Z,3),
    'corridor_radius_mm':round(SPINDLE_TUNNEL_R,3),
    'lower_ligament_mm':round((SPINDLE_Z-SPINDLE_TUNNEL_R)-C.ARM_BOTTOM_Z,3),
    'upper_ligament_mm':round(C.BOX_SUPPORT_Z-(SPINDLE_Z+SPINDLE_TUNNEL_R),3),
}
if abs(carrier_spindle_ligaments['lower_ligament_mm']-carrier_spindle_ligaments['upper_ligament_mm'])>1e-6:
    fail('box-clamp spindle corridor is not centred vertically in real carrier')
if min(carrier_spindle_ligaments['lower_ligament_mm'],carrier_spindle_ligaments['upper_ligament_mm'])<9.0:
    fail('box-clamp spindle corridor leaves less than 9 mm real carrier ligament')

# Confirm against the final BRep in the ACTUAL continuous crosshead front wall.
# The lead-nut pocket ends behind this wall; only the local spindle corridor is
# allowed through it.  This directly proves the visible crosshead has equal real
# material above and below the screw bore.
carrier_wall_probe_y = C.CROSSHEAD_Y1 - 0.50
carrier_wall_material_checks=[]
for sx in SPINDLE_X:
    lower_edge = SPINDLE_Z-SPINDLE_TUNNEL_R
    upper_edge = SPINDLE_Z+SPINDLE_TUNNEL_R
    probe_states=[]
    for label,z in (
        ('lower_outer',C.ARM_BOTTOM_Z+0.40),
        ('lower_inner',lower_edge-0.40),
        ('upper_inner',upper_edge+0.40),
        ('upper_outer',C.BOX_SUPPORT_Z-0.40),
    ):
        solid=bool(RIGHT_FULL.isInside(App.Vector(sx,carrier_wall_probe_y,z),1e-5,True))
        probe_states.append({'sample':label,'z_mm':round(z,3),'solid':solid})
        if not solid:
            fail(f'real carrier material missing at {label}, X={sx}, Z={z:.3f}')
    centre_void=not bool(RIGHT_FULL.isInside(
        App.Vector(sx,carrier_wall_probe_y,SPINDLE_Z),1e-5,True
    ))
    if not centre_void:
        fail(f'spindle corridor centre is not actually open at X={sx}')
    carrier_wall_material_checks.append({
        'spindle_x_mm':round(sx,3),
        'probe_y_mm':round(carrier_wall_probe_y,3),
        'corridor_centre_void':centre_void,
        'samples':probe_states,
    })

# The moving plate is now on the same 30 mm vertical envelope, so the Ø12
# retainer counterbore is centred as well and must retain equal strong edges.
plate_counterbore_ligaments={
    'plate_z0_mm':round(PLATE_Z0,3),
    'plate_z1_mm':round(PLATE_Z1,3),
    'spindle_axis_z_mm':round(SPINDLE_Z,3),
    'counterbore_radius_mm':round(PLATE_RETAINER_COUNTERBORE_D/2.0,3),
    'lower_ligament_mm':round(SPINDLE_Z-PLATE_RETAINER_COUNTERBORE_D/2.0-PLATE_Z0,3),
    'upper_ligament_mm':round(PLATE_Z1-(SPINDLE_Z+PLATE_RETAINER_COUNTERBORE_D/2.0),3),
}
if min(plate_counterbore_ligaments['lower_ligament_mm'],plate_counterbore_ligaments['upper_ligament_mm'])<6.0:
    fail('box-clamp plate counterbore leaves less than 6 mm vertical ligament')

lead_nut_seat_checks=[]
lead_nut_pin_wall_checks=[]
lead_nut_pin_top_insertion=[]
lead_nut_top_closure_checks=[]
obsolete_guide_clearance_checks=[]
for sx in SPINDLE_X:
    nut_floor_z = SPINDLE_Z + LEAD_NUT.BoundBox.ZMin
    nut_top_z = SPINDLE_Z + LEAD_NUT.BoundBox.ZMax
    nut_inboard_y = NUT_Y0 + LEAD_NUT.BoundBox.YMin
    pin_y = NUT_Y0 + LEAD_NUT_PIN_LOCAL_Y
    pin_z = SPINDLE_Z + LEAD_NUT_PIN_LOCAL_Z
    pin_r = LEAD_NUT_PIN_HOLE_D/2.0
    pin_top_clearance = PRINT_BASE_PLANE_Z - (pin_z + pin_r)
    wall_inner = 8.0 + LEAD_NUT_POCKET_X_CLEAR
    wall_outer = C.BOX_CLAMP_BOSS_HALF_X
    wall_mid = (wall_inner + wall_outer)/2.0
    wall_thickness = wall_outer-wall_inner

    lead_nut_seat_checks.append({
        'spindle_x_mm':round(sx,3),
        'thread_axis_z_mm':round(SPINDLE_Z,3),
        'nut_floor_z_mm':round(nut_floor_z,3),
        'pocket_floor_z_mm':round(LEAD_NUT_POCKET_FLOOR_Z,3),
        'nut_top_z_mm':round(nut_top_z,3),
        'carrier_top_z_mm':round(PRINT_BASE_PLANE_Z,3),
        'flush_top_delta_mm':round(nut_top_z-PRINT_BASE_PLANE_Z,6),
        'nut_inboard_y_mm':round(nut_inboard_y,3),
        'pocket_inboard_stop_y_mm':round(NUT_THREAD_Y0,3),
        'pin_axis_y_mm':round(pin_y,3),
        'pin_axis_z_mm':round(pin_z,3),
        'pin_top_clearance_to_carrier_top_mm':round(pin_top_clearance,3),
        'side_wall_thickness_mm':round(wall_thickness,3),
    })

    if abs(nut_floor_z-LEAD_NUT_POCKET_FLOOR_Z)>1e-6:
        fail(f'lead-nut carrier does not seat on pocket floor at X={sx}')
    if abs(nut_top_z-PRINT_BASE_PLANE_Z)>1e-6:
        fail(f'lead-nut carrier cap is not flush with carrier top at X={sx}: {nut_top_z:.3f}')
    if abs(nut_inboard_y-NUT_THREAD_Y0)>1e-6:
        fail(f'lead-nut inboard Y datum does not match pocket stop at X={sx}')
    if pin_top_clearance < 3.0:
        fail(f'lead-nut retaining pin cradle too shallow below carrier top at X={sx}: {pin_top_clearance:.3f} mm')
    if wall_thickness < 2.5:
        fail(f'lead-nut retaining-pin side wall too thin at X={sx}: {wall_thickness:.3f} mm')

    # Validate the real top-open U-cradle: side cheeks and floor stay solid,
    # while the pin axis and its vertical insertion throat are deliberately air.
    sample_delta = pin_r + 0.80
    states=[]
    for xoff in (-wall_mid,wall_mid):
        for label,yy,zz,expect_solid in (
            ('y-',pin_y-sample_delta,pin_z,True),
            ('y+',pin_y+sample_delta,pin_z,True),
            ('z-',pin_y,pin_z-sample_delta,True),
            ('axis',pin_y,pin_z,False),
            ('top-throat',pin_y,min(PRINT_BASE_PLANE_Z-0.40,pin_z+3.0),False),
        ):
            solid=bool(RIGHT_FULL.isInside(
                App.Vector(sx+xoff,yy,zz),1e-5,False
            ))
            states.append({
                'wall_x_offset_mm':round(xoff,3),
                'sample':label,
                'solid':solid,
                'expected_solid':expect_solid,
            })
            if solid != expect_solid:
                fail(f'lead-nut top pin cradle wrong X={sx} wall={xoff:.3f} sample={label} solid={solid}')
    lead_nut_pin_wall_checks.append({
        'spindle_x_mm':round(sx,3),
        'mode':'round top-open U-cradle',
        'samples':states,
    })

    # Assembly proof: with the carrier seated, the complete retaining pin must
    # be lowerable vertically into its final cradle without any side insertion.
    installed_nut_for_pin=LEAD_NUT.copy()
    installed_nut_for_pin.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z))
    pin_path=[]
    for lift in (8.0,4.0,2.0,1.0,0.0):
        qp=NUT_PIN.copy()
        qp.translate(App.Vector(sx,pin_y,pin_z+lift))
        base_cv=RIGHT_FULL.common(qp).Volume
        nut_cv=installed_nut_for_pin.common(qp).Volume
        pin_path.append({
            'lift_mm':lift,
            'base_common_mm3':round(base_cv,6),
            'lead_nut_common_mm3':round(nut_cv,6),
        })
        if base_cv>1e-4 or nut_cv>1e-4:
            fail(f'lead-nut retaining pin cannot drop from top X={sx} lift={lift}: base={base_cv:.6f} nut={nut_cv:.6f}')
    lead_nut_pin_top_insertion.append({
        'spindle_x_mm':round(sx,3),
        'pin_axis_z_mm':round(pin_z,3),
        'service_x_local_mm':[
            round(NUT_PIN_SERVICE_X0,3),round(NUT_PIN_SERVICE_X1,3)
        ],
        'path':pin_path,
    })

    # A top-inserted removable carrier necessarily needs an opening in the bare
    # BASE. What must NOT remain is an open hole in the installed assembly.
    # Probe the final BASE + installed carrier at a 3x3 grid 0.40 mm below the
    # common top surface. The carrier cap must close every sample and sit flush.
    installed_nut=LEAD_NUT.copy()
    installed_nut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z))
    top_states=[]
    safe_y_samples=(
        NUT_THREAD_Y0+1.0,
        pin_y-LEAD_NUT_PIN_DROP_SLOT_W/2.0-0.80,
        NUT_Y0-0.50,
    )
    for xoff in (-6.0,0.0,6.0):
        for yy in safe_y_samples:
            p=App.Vector(sx+xoff,yy,PRINT_BASE_PLANE_Z-0.40)
            base_solid=bool(RIGHT_FULL.isInside(p,1e-5,False))
            carrier_solid=bool(installed_nut.isInside(p,1e-5,False))
            assembled_solid=base_solid or carrier_solid
            top_states.append({
                'x_offset_mm':xoff,'y_mm':round(yy,3),
                'base_solid':base_solid,
                'carrier_solid':carrier_solid,
                'assembled_solid':assembled_solid,
            })
            if not assembled_solid:
                fail(f'installed lead-nut carrier leaves unintended top opening X={sx+xoff:.3f} Y={yy:.3f}')

    recess_probe=App.Vector(sx,pin_y,PRINT_BASE_PLANE_Z-0.40)
    recess_open=(
        not bool(RIGHT_FULL.isInside(recess_probe,1e-5,False))
        and not bool(installed_nut.isInside(recess_probe,1e-5,False))
    )
    if not recess_open:
        fail(f'lead-nut top pin recess is not open at X={sx}')
    lead_nut_top_closure_checks.append({
        'spindle_x_mm':round(sx,3),
        'carrier_cap_top_z_mm':round(nut_top_z,3),
        'base_top_z_mm':round(PRINT_BASE_PLANE_Z,3),
        'allowed_pin_recess_width_mm':LEAD_NUT_PIN_DROP_SLOT_W,
        'pin_recess_open':recess_open,
        'samples':top_states,
    })

# The old plate guides are exactly the protruding blocks visible beside the
# clamp stations. Their former forward volumes must now be empty.
old_guide_t=7.60
old_left_x=PLATE_X0-0.40-old_guide_t/2.0
old_right_x=PLATE_X1+0.40+old_guide_t/2.0
for label,xx in (('left',old_left_x),('right',old_right_x)):
    states=[]
    for yy in (CAGE_Y1+1.0,C.BOX_RIM_INNER_Y-1.0):
        solid=bool(RIGHT_FULL.isInside(App.Vector(xx,yy,SPINDLE_Z),1e-5,False))
        states.append({'y_mm':round(yy,3),'solid':solid})
        if solid:
            fail(f'obsolete {label} plate-guide protrusion still present at Y={yy:.3f}')
    obsolete_guide_clearance_checks.append({
        'side':label,'x_mm':round(xx,3),'samples':states
    })

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

    # Prove the complete capped carrier can be lowered vertically from above
    # into its final seated position.
    for lift in (20.0,10.0,5.0,2.0,0.0):
        qnut=LEAD_NUT.copy()
        qnut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z+lift))
        cv=RIGHT_FULL.common(qnut).Volume
        cartridge_insertion.append({
            'x_mm':sx,'lift_mm':lift,'base_common_mm3':round(cv,6),
        })
        if cv>1e-4:
            fail(f'lead-nut top insertion blocked X={sx} lift={lift}: {cv:.6f} mm3')
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
        knob_y=PLATE_SPINDLE_Y+KP.KNOB_H-d
        # CAP_NUT points toward -Y, so placing its origin 5.4 mm beyond the
        # knob face seats its inner face exactly against the knob.
        cap_y=PLATE_SPINDLE_Y+KP.KNOB_H+5.4-d

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
lead_screw_printability={
    'preferred_print_orientation':'vertical on outer-stud pilot; screw axis +Z',
    'flat_pilot_d_mm':round(2.0*THREAD_CORE_R,3),
    'flat_pilot_h_mm':round(SPINDLE_PRINT_PILOT_H,3),
    'outer_thread_usable_mm':round(OUTER_STUD_LEN-SPINDLE_PRINT_PILOT_H,3),
    'hex_taper_h_mm':round(SPINDLE_HEX_TAPER_H,3),
    'hex_taper_af_mm':[round(SPINDLE_HEX_TAPER_AF0,3),round(SPINDLE_HEX_AF,3)],
    'full_hex_drive_h_mm':round(HEX_LEN-SPINDLE_HEX_TAPER_H,3),
    'shoulder_taper_h_mm':round(SPINDLE_SHOULDER_TAPER_H,3),
    'shoulder_taper_r_mm':[
        round(SPINDLE_SHOULDER_TAPER_R0,3),
        round(SPINDLE_SHOULDER_TAPER_R1,3),
    ],
    'shoulder_taper_max_slope_dr_dz':round(
        (SPINDLE_SHOULDER_TAPER_R1-SPINDLE_SHOULDER_TAPER_R0)
        / SPINDLE_SHOULDER_TAPER_H,6
    ),
    'plate_matching_conical_seat':True,
    'knob_matching_hex_frustum':True,
}
if lead_screw_printability['outer_thread_usable_mm'] < 5.8:
    fail('print pilot leaves too little knob-retainer thread')
if lead_screw_printability['full_hex_drive_h_mm'] < 4.8:
    fail('support-free hex taper leaves too little full hex drive')
if lead_screw_printability['shoulder_taper_max_slope_dr_dz'] > 1.0+1e-9:
    fail('lead-screw thrust shoulder support taper exceeds 45deg')

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

        knob_y=PLATE_SPINDLE_Y+KP.KNOB_H-d
        akn=KNOB.copy()
        akn.rotate(App.Vector(0,0,0),App.Vector(0,1,0),rot_deg)
        akn.translate(App.Vector(sx,knob_y,SPINDLE_Z))
        knob_base=RIGHT_FULL.common(akn).Volume

        cap_y=PLATE_SPINDLE_Y+KP.KNOB_H+5.4-d
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
    pl=PLATE.copy(); pl.translate(App.Vector(0,-d,0)); sp=SPINDLE.copy(); sp.rotate(App.Vector(0,0,0),App.Vector(0,1,0),360*d/THREAD_PITCH); sp.translate(App.Vector(0,PLATE_SPINDLE_Y-d,SPINDLE_Z)); return max(RIGHT_FULL.BoundBox.YMax,pl.BoundBox.YMax,sp.BoundBox.YMax)
width_states={str(d):local_y_extent(d) for d in (0.0,5.5)}; holder_half=C.RACK_CTC/2+max(width_states.values())
if holder_half>C.BOX_W/2+0.02: fail(f'complete holder exceeds 600 mm box width: {2*holder_half:.3f} mm')

V={'version':'v60','stage':'full_direct_mechanism_v50_solutions_restored','architecture':'clean structural core + proven v50 rack joint/backstop/drop/cage solutions','base':{'right_bbox_mm':[round(RIGHT_FULL.BoundBox.XLength,3),round(RIGHT_FULL.BoundBox.YLength,3),round(RIGHT_FULL.BoundBox.ZLength,3)],'left_bbox_mm':[round(LEFT_FULL.BoundBox.XLength,3),round(LEFT_FULL.BoundBox.YLength,3),round(LEFT_FULL.BoundBox.ZLength,3)],'mirror_delta_mm3':round(full_mirror_delta,9),'mirror_bound_delta_mm':round(mirror_bound_delta,9),'mirror_face_delta':mirror_face_delta,'pin_bore_clearance':pin_bore_clearance,'holm_station_checks':holm_station_checks,'cage_reinforcement_checks':cage_reinforcement_checks,'cage_struct_y_mm':[round(CAGE_Y0,3),round(CAGE_STRUCT_Y1,3)],'station_floor_y1_mm':round(STATION_FLOOR_Y1,3),'cage_top_z_mm':PRINT_BASE_PLANE_Z,'carrier_spindle_ligaments':carrier_spindle_ligaments,'carrier_wall_material_checks':carrier_wall_material_checks,'plate_counterbore_ligaments':plate_counterbore_ligaments,'lead_nut_seat_checks':lead_nut_seat_checks,'lead_nut_pin_wall_checks':lead_nut_pin_wall_checks,'lead_nut_pin_top_insertion':lead_nut_pin_top_insertion,'lead_nut_top_closure_checks':lead_nut_top_closure_checks,'obsolete_guide_clearance_checks':obsolete_guide_clearance_checks},'rack':{'clamp_spacing_mm':C.CLAMP_SPACING,'joint':'v51 broad central Upper bearing + replaceable Lower fork','upper_pivot_width_mm':C.UPPER_PIVOT_W,'lower_fork_outer_width_mm':LOWER_FORK_W,'lower_fork_ear_thickness_mm':LOWER_FORK_EAR_T,'lower_web_top_z_mm':LOWER_WEB_TOP_Z,'lower_sweep':lower_sweep,'tightening_sweep':tightening_sweep,'pin_checks':pin_checks,'m4_closure_checks':closure_checks,'m4_closure':{'mode':'M4x20 from below into side-loaded captive M4 nut','screw_length_mm':RACK_M4_SCREW_LENGTH,'lower_clearance_d_mm':RACK_M4_LOWER_CLEAR_D,'base_clearance_d_mm':C.RACK_M4_BASE_CLEAR_D,'base_bore_z_mm':[RACK_M4_BASE_BORE_Z0,RACK_M4_BASE_BORE_Z1],'nut_pocket_af_mm':C.RACK_M4_NUT_AF,'nut_pocket_height_mm':C.RACK_M4_NUT_H,'closure_pad_x_mm':RACK_CLOSURE_PAD_X,'closure_pad_y_mm':[RACK_CLOSURE_PAD_Y0,RACK_CLOSURE_PAD_Y1],'closure_pad_z_mm':[RACK_CLOSURE_PAD_Z0,RACK_CLOSURE_PAD_Z1],'closure_pad_material_fraction':round(closure_pad_fraction,6),'nominal_gap_mm':round(closure_nominal_gap,3),'mapped_tube_adjustment_mm':round(closure_mapped_tube_adjustment,3),'required_tube_adjustment_mm':round(required_tube_adjustment,3),'nut_engagement_mm':round(rack_nut_engagement,3),'tip_clearance_mm':round(rack_tip_clearance,3),'front_ligament_mm':round(closure_front_ligament,3),'side_ligament_mm':round(closure_side_ligament,3)}},'box_clamp':{'architecture':'v50_direct_removable_lead_nut_cartridge_local_holm_stations','plate_travel_mm':PLATE_OPEN,'plate_motion':plate_motion,'plate_x_mm':[round(PLATE_X0,3),round(PLATE_X1,3)],'plate_width_mm':round(PLATE_X,3),'spindle_x_mm':[round(x,3) for x in SPINDLE_X],'spindle_spacing_mm':round(SPINDLE_X[1]-SPINDLE_X[0],3),'spindle_z_mm':SPINDLE_Z,'thread':'RH 8x2','integral_female_threads':False,'base_has_working_thread':False,'working_female_thread_location':'removable_lead_nut_cartridge','cartridge_insertion':cartridge_insertion,'thread_motion':thread_motion,'knob_motion':knob_motion,'assembly_approach':assembly_approach,'thread_brep_common_tolerance_mm3':1.20,'width_states_local_y_mm':{k:round(v,3) for k,v in width_states.items()},'effective_total_width_mm':round(max(C.BOX_W,2*holder_half),3)},'failures':failures}
V['box_clamp']['lead_screw_printability']=lead_screw_printability
V['box_clamp']['lead_screw']={
    'construction':'single OpenSCAD CGAL union; exact vertical support-free printable STL retained',
    'main_thread':'true radial/axial RH8x2',
    'outer_stud_thread':'true radial/axial RH8x2',
    'journal_length_mm':SPINDLE_LOCAL_JOURNAL,
    'shoulder_length_mm':SPINDLE_LOCAL_SHOULDER,
    'main_thread_length_mm':LEAD_THREAD_LEN,
    'knob_hex_length_mm':HEX_LEN,
    'full_hex_drive_length_mm':round(HEX_LEN-SPINDLE_HEX_TAPER_H,3),
    'hex_taper_length_mm':SPINDLE_HEX_TAPER_H,
    'knob_thickness_mm':KP.KNOB_H,
    'outer_stud_length_mm':OUTER_STUD_LEN,
    'knob_side':'outboard of clamp plate',
    'working_thread_side':'inboard toward fixed lead-nut cartridge',
    'outer_stack_y_from_plate_mm':[0.0,HEX_LEN,HEX_LEN+OUTER_STUD_LEN],
    'mesh_topology':lead_screw_mesh,
    'main_thread_samples':main_spindle_thread_samples,
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
        'lead_nut_insert_from_top',
        'lead_nut_cross_pin',
        'lead_nut_pin_clip',
        'lead_screw_through_plate',
        'plate_retainer_clip_via_bottom_service_channel',
        'plate_spindle_subassembly_threaded_into_fixed_lead_nut',
        'knob_on_tapered_7mm_hex_with_5mm_full_drive',
        'knob_retainer_nut_on_outer_RH8x2_stud',
    ],
    'lead_nut_top_insertion':cartridge_insertion,
    'lead_nut_pin_top_insertion':lead_nut_pin_top_insertion,
    'plate_clip_service_path':plate_retainer_clip_insertion,
    'threaded_plate_approach':assembly_approach,
    'operating_knob_clearance':knob_motion,
}
V['rack']['lower_printability']={
    'mechanical_geometry':'proven circular-pivot Lower; final tongue extends to existing shell floor',
    'print_orientation':'natural Z-up on common Lower/tongue floor',
    'rack_saddle':'upward-open semicircular seat',
    'pivot_pin_bore':'small horizontal round self-closing opening',
    'pivot_print_feet':{
        'z_mm':[LOWER_PIVOT_FOOT_Z0,LOWER_PIVOT_FOOT_Z1],
        'y_mm':[LOWER_PIVOT_FOOT_Y0,LOWER_PIVOT_FOOT_Y1],
        'ear_thickness_mm':LOWER_FORK_EAR_T,
    },
    'm4_clearance':'vertical',
    'm4_clearance_d_mm':RACK_M4_LOWER_CLEAR_D,
    'functional_round_pivot_bore_preserved':True,
}
V['box_clamp']['lead_nut_printability']=lead_nut_printability
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
# The installed LEAD_NUT geometry is used for all kinematic/thread validation.
# Export only the printable component rotated so the RH8x2 axis is vertical:
# local -Y becomes +Z and the y=0 end face sits directly on the build plate.
LEAD_NUT_PRINT = LEAD_NUT.copy()
LEAD_NUT_PRINT.rotate(App.Vector(0,0,0),App.Vector(1,0,0),-90.0)
C.require_single(LEAD_NUT_PRINT,'print-oriented lead nut')
if abs(LEAD_NUT_PRINT.BoundBox.ZMin) > 1e-6:
    raise RuntimeError(
        f'print-oriented lead nut does not sit on Z=0: {LEAD_NUT_PRINT.BoundBox.ZMin:.6f}'
    )

# The final rack-closure stage extends the tongue down to the shell's existing
# Z=-14.5 floor. Keep the functional Lower in its natural Z-up orientation:
# the saddle is open upward, the M4 bore is vertical and only the small round
# pivot bore remains horizontal/self-closing.
LOWER_PRINT = LOWER.copy()
LOWER_PRINT.translate(App.Vector(0,0,-LOWER_PRINT.BoundBox.ZMin))
C.require_single(LOWER_PRINT,'natural-print-oriented functional rack Lower')
if abs(LOWER_PRINT.BoundBox.ZMin)>1e-6:
    raise RuntimeError('natural-print rack Lower does not sit on build plane')

parts={'eurobox_v60_base_right':RIGHT_FULL,'eurobox_v60_base_left':LEFT_FULL,'eurobox_v60_rack_lower':LOWER_PRINT,'eurobox_v60_rack_pin':PIN,'eurobox_v60_rack_pin_clip':PIN_CLIP,'eurobox_v60_clamp_plate':PLATE,'eurobox_v60_lead_nut':LEAD_NUT_PRINT,'eurobox_v60_lead_nut_retaining_pin':NUT_PIN,'eurobox_v60_lead_nut_pin_clip':NUT_PIN_CLIP,'eurobox_v60_lead_screw':SPINDLE_PRINT_Z,'eurobox_v60_knob':KNOB,'eurobox_v60_knob_retainer_nut':CAP_NUT,'eurobox_v60_plate_retainer_clip':PLATE_CLIP}
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
    f.write('Outboard rear-stop contact wall, closed holm heads with DROPs; serviceable box-clamp cage uses full-area holm ties, a hollow transverse DROP beam and low station gussets while the lead-nut cartridges remain removable. Lead-nut cartridges use a matching true R8 semicircular lower seat; their cross-pin cradle remains genuinely round and top-open, and the exported lead nut is print-oriented with the RH8x2 axis vertical. The mechanically proven rack Lower is unchanged and exported on its broad X side for support-free round saddle/pivot printing.\n')
    f.write(f'Final cage top is exactly the 39.54 mm box support plane; {PLATE_X:.1f} mm clamp plate with holm-referenced lead screws at {SPINDLE_X[0]:.2f}/{SPINDLE_X[1]:.2f} mm.\n')
    f.write('160 mm rack-clamp spacing; CORE One L INDX hard envelope 298 x 275 mm.\n')
stage('complete'); print(json.dumps(V,indent=2),flush=True)
