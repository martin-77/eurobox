import FreeCAD as App
import Part, Mesh
import os, math, json, subprocess, tempfile, shutil

ROOT = os.getcwd()
OUT = os.path.join(ROOT, "build_v50")
os.makedirs(OUT, exist_ok=True)

# -----------------------------
# Hard measured datums
# -----------------------------
TUBE_D = 12.42
TUBE_R = TUBE_D / 2.0
BOX_EDGE_Y = 244.665
BOX_SUPPORT_Z = 39.54
BOX_RIM = 16.45
BOX_RIM_BOTTOM_Z = BOX_SUPPORT_Z - BOX_RIM
CLAMP_X = (-90.0, 90.0)
SCREW_X = (-42.0, 42.0)
SCREW_Z = 31.0
PLATE_TRAVEL = 4.5

# Prototype lead screw. Deliberately larger than final metal M4.
LEAD_MAJOR = 8.0
LEAD_CORE = 6.4
LEAD_PITCH = 2.0
LEAD_CLEAR = 0.28

# -----------------------------
# Utilities
# -----------------------------
def fuse_all(shapes):
    s = shapes[0]
    for q in shapes[1:]:
        s = s.fuse(q)
    return s.removeSplitter()


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


def cyl_y(r, length, x, y, z):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def cyl_x(r, length, x, y, z):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(1, 0, 0))


def cyl_z(r, length, x, y, z):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(0, 0, 1))


def prism_y(points_xz, y0, length):
    pts = [App.Vector(x, y0, z) for x, z in points_xz]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, length, 0))


def prism_x(points_yz, x0, length):
    pts = [App.Vector(x0, y, z) for y, z in points_yz]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(length, 0, 0))


def hex_prism_y(af, length, x, y, z):
    # regular hex with vertices radius af/sqrt(3), extruded along Y
    r = af / math.sqrt(3.0)
    pts = []
    for i in range(6):
        a = math.radians(30 + i * 60)
        pts.append((x + r * math.cos(a), z + r * math.sin(a)))
    return prism_y(pts, y, length)


def mesh_to_solid(stl_path, tol=0.04):
    m = Mesh.Mesh(stl_path)
    sh = Part.Shape()
    sh.makeShapeFromMesh(m.Topology, tol)
    if sh.ShapeType == "Shell":
        sh = Part.makeSolid(sh)
    elif sh.ShapeType == "Compound" and len(sh.Shells) == 1:
        sh = Part.makeSolid(sh.Shells[0])
    return sh.removeSplitter()


def openscad_thread_z(name, length, major, core, pitch, profile_scale=1.0):
    scad = os.path.join(OUT, name + ".scad")
    stl = os.path.join(OUT, name + ".stl")
    depth = (major - core) / 2.0
    halfroot = pitch * 0.24 * profile_scale
    halfcrest = pitch * 0.105 * profile_scale
    slices = max(48, int(math.ceil(length / pitch * 36)))
    txt = f'''$fn=96;
major={major}; core={core}; pitch={pitch}; length={length}; depth=(major-core)/2;
union() {{
  cylinder(h=length,d=core);
  linear_extrude(height=length, twist=360*length/pitch, slices={slices}, convexity=20)
    translate([core/2,0,0])
      polygon(points=[[0,-{halfroot}],[depth,-{halfcrest}],[depth,{halfcrest}],[0,{halfroot}]]);
}}
'''
    with open(scad, "w") as f:
        f.write(txt)
    subprocess.run(["openscad", "-o", stl, scad], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return mesh_to_solid(stl)


def zthread_to_y(shape, x, y, z):
    s = shape.copy()
    s.rotate(App.Vector(0,0,0), App.Vector(1,0,0), -90.0)  # +Z -> +Y
    s.translate(App.Vector(x, y, z))
    return s


def export_part(name, shape):
    if not shape.isValid():
        raise RuntimeError(name + " is invalid before export")
    step = os.path.join(OUT, name + ".step")
    stl = os.path.join(OUT, name + ".stl")
    shape.exportStep(step)
    doc = App.newDocument("exp_" + name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()
    Mesh.export([obj], stl)
    fcstd = os.path.join(OUT, name + ".FCStd")
    doc.saveAs(fcstd)
    App.closeDocument(doc.Name)
    # mandatory STEP round-trip
    rt = Part.Shape(); rt.read(step)
    if not rt.isValid() or len(rt.Solids) != 1:
        raise RuntimeError(name + " failed STEP roundtrip")
    return {
        "valid": True,
        "solids": len(rt.Solids),
        "volume_mm3": round(rt.Volume, 3),
        "bbox": [round(v, 3) for v in (rt.BoundBox.XLength, rt.BoundBox.YLength, rt.BoundBox.ZLength)]
    }

# -----------------------------
# Thread masters
# -----------------------------
# Main male lead thread and a deliberately larger female cutter.
thread_male_z = openscad_thread_z("thread_male_D8x2", 24.0, LEAD_MAJOR, LEAD_CORE, LEAD_PITCH, 1.0)
thread_female_cutter_z = openscad_thread_z(
    "thread_female_cutter_D8x2", 14.0,
    LEAD_MAJOR + 2*LEAD_CLEAR,
    LEAD_CORE + 2*LEAD_CLEAR,
    LEAD_PITCH, 1.07
)

# -----------------------------
# Tube clamp – new clean split clamp
# -----------------------------
def make_upper_clamp(cx):
    # Crown begins above the tube centre; rigid saddle has clearance to Ø12.42.
    crown = box(cx-17, -15.5, 0.6, 34, 31, 19.4)
    tube_cut = cyl_x(6.27, 40, cx-20, 0, 0)
    crown = crown.cut(tube_cut)

    ears = []
    for py in (-11.5, 11.5):
        ears += [
            box(cx-17, py-4.0, -10.0, 6.0, 8.0, 11.0),
            box(cx+11, py-4.0, -10.0, 6.0, 8.0, 11.0),
        ]
    s = fuse_all([crown] + ears)
    for py in (-11.5, 11.5):
        s = s.cut(cyl_x(2.30, 40, cx-20, py, -5.5))
    return s.removeSplitter()


def make_rack_lower():
    # Local around x=0. Fits between the outer ears of the upper clamp.
    raw = box(-10.5, -16.0, -12.0, 21.0, 32.0, 12.4)
    # Slight PETG preload: lower saddle nominal Ø12.30.
    raw = raw.cut(cyl_x(6.15, 30, -15, 0, 0))
    # Add local material around the two pin axes.
    ears = []
    for py in (-11.5, 11.5):
        ears.append(box(-10.5, py-4.1, -10.2, 21.0, 8.2, 10.8))
    s = fuse_all([raw] + ears)
    for py in (-11.5, 11.5):
        s = s.cut(cyl_x(2.30, 30, -15, py, -5.5))
    return s.removeSplitter()

rack_lower = make_rack_lower()

# -----------------------------
# Load arms – double-web I section
# -----------------------------
def make_arm(cx):
    y0, y1 = 15.5, 220.0
    L = y1-y0
    x0 = cx-16.0
    z0 = BOX_SUPPORT_Z-30.0
    # top/bottom flanges + two webs
    shapes = [
        box(x0, y0, BOX_SUPPORT_Z-4.5, 32, L, 4.5),
        box(x0, y0, z0, 32, L, 4.5),
        box(cx-8.0-1.6, y0, z0+4.5, 3.2, L, 21.0),
        box(cx+8.0-1.6, y0, z0+4.5, 3.2, L, 21.0),
    ]
    # short root web / gusset; no void carved into the clamp
    root = prism_x([
        (7.0, 7.0), (15.5, z0), (40.0, z0), (40.0, BOX_SUPPORT_Z), (7.0, 20.0)
    ], cx-16.0, 32.0)
    return fuse_all(shapes + [root])

# -----------------------------
# Main base
# -----------------------------
base_parts = []
for cx in CLAMP_X:
    base_parts.append(make_upper_clamp(cx))
    base_parts.append(make_arm(cx))

# Outer box support: solid central pad + perimeter/cross beams.
base_parts += [
    box(-112, 204.0, BOX_SUPPORT_Z-4.5, 224, 11, 4.5),
    box(-112, 234.0, BOX_SUPPORT_Z-4.5, 224, BOX_EDGE_Y-234.0, 4.5),
    box(-70, 204.0, BOX_SUPPORT_Z-4.5, 140, BOX_EDGE_Y-204.0, 4.5),
    box(-112, 204.0, BOX_SUPPORT_Z-18.0, 8, 40.665, 13.5),
    box(104, 204.0, BOX_SUPPORT_Z-18.0, 8, 40.665, 13.5),
]

# Broad transitions from arms into outer frame; no decorative weakening cut-outs.
for sx in (-1, 1):
    cx = sx*90.0
    x_start = cx-16.0
    # simple full-depth transition block plus diagonal top rib
    base_parts.append(box(x_start, 218.0, BOX_SUPPORT_Z-30.0, 32, 20.0, 30.0))

# Plate guide rails. Plate has additive lugs x=±58..65, z 26..52.
for sign in (-1,1):
    if sign > 0:
        base_parts += [
            box(65.4, 243.5, 23.0, 2.6, 16.0, 32.0),
            box(58.4, 243.5, 52.4, 7.0, 16.0, 2.6),
            box(58.4, 243.5, 23.0, 7.0, 16.0, 2.6),
        ]
    else:
        base_parts += [
            box(-68.0, 243.5, 23.0, 2.6, 16.0, 32.0),
            box(-65.4, 243.5, 52.4, 7.0, 16.0, 2.6),
            box(-65.4, 243.5, 23.0, 7.0, 16.0, 2.6),
        ]

# Lead-nut posts and wide load path into support frame.
for sx in SCREW_X:
    base_parts += [
        box(sx-11.5, 260.5, 20.0, 23.0, 13.5, 25.0),
        box(sx-17.0, 244.0, 20.0, 34.0, 16.5, 6.0),
        box(sx-17.0, 244.0, 52.0, 34.0, 16.5, 6.0),
    ]

# Outer bracket cross ties.
base_parts += [
    box(-65, 260.5, 20.0, 130, 6.0, 6.0),
    box(-65, 260.5, 52.0, 130, 6.0, 6.0),
]

base = fuse_all(base_parts)

# Cut lead-nut top-loading pockets + screw clearances.
for sx in SCREW_X:
    # pocket open to top; nut is held by separate cap
    base = base.cut(box(sx-8.3, 261.2, 21.5, 16.6, 10.6, 30.0))
    # screw passage through inner and outer post faces
    base = base.cut(cyl_y(4.5, 20.0, sx, 257.0, SCREW_Z))

base = base.removeSplitter()

# -----------------------------
# Clamp plate – solid, real holes, additive guide lugs
# -----------------------------
plate_parts = [
    box(-58.0, BOX_EDGE_Y, 20.5, 116.0, 8.0, 36.5),
    box(-65.0, 247.0, 26.0, 7.0, 5.665, 26.0),
    box(58.0, 247.0, 26.0, 7.0, 5.665, 26.0),
    # 4.3 mm under-hook below conservative rim bottom
    box(-58.0, BOX_EDGE_Y-4.30, 20.5, 116.0, 4.30, 2.50),
]
plate = fuse_all(plate_parts)
for sx in SCREW_X:
    plate = plate.cut(cyl_y(3.25, 12.0, sx, BOX_EDGE_Y-1.0, SCREW_Z))
    # recessed inner retainer pocket; remains flush with box-contact plane
    plate = plate.cut(cyl_y(6.10, 2.65, sx, BOX_EDGE_Y, SCREW_Z))
plate = plate.removeSplitter()

# -----------------------------
# Lead nut + cap
# -----------------------------
def make_lead_nut():
    body = box(-8.0, 261.5, 22.0, 16.0, 10.0, 18.0)
    # small T flange for seating under cap
    body = body.fuse(box(-9.5, 261.0, 38.0, 19.0, 11.0, 3.0))
    cutter = zthread_to_y(thread_female_cutter_z, 0, 260.0, SCREW_Z)
    return body.cut(cutter).removeSplitter()

lead_nut = make_lead_nut()

lead_nut_cap = fuse_all([
    box(-62.0, 260.0, 41.0, 124.0, 13.5, 4.0),
    box(-50.2, 261.3, 38.8, 16.4, 10.4, 2.4),
    box(33.8, 261.3, 38.8, 16.4, 10.4, 2.4),
])

# -----------------------------
# Lead screw, plate retainer, knob, knob cap nut
# -----------------------------
def make_lead_screw():
    main_thread = zthread_to_y(thread_male_z.common(cyl_z(6.0, 18.0, 0,0,0)), 0, 254.8, SCREW_Z)
    # In case common crop above loses the crest, use a direct 17.7 mm master.
    master = openscad_thread_z("main_screw_thread_exact", 17.7, LEAD_MAJOR, LEAD_CORE, LEAD_PITCH, 1.0)
    main_thread = zthread_to_y(master, 0, 254.8, SCREW_Z)
    journal = cyl_y(3.0, 7.8, 0, 245.0, SCREW_Z)
    shoulder = cyl_y(5.5, 2.0, 0, 252.8, SCREW_Z)
    # groove for recessed C-retainer
    # journal is built in two pieces around a smaller groove section
    journal = fuse_all([
        cyl_y(3.0, 0.5, 0, 245.0, SCREW_Z),
        cyl_y(2.40, 1.25, 0, 245.5, SCREW_Z),
        cyl_y(3.0, 6.05, 0, 246.75, SCREW_Z),
    ])
    drive = hex_prism_y(10.0, 7.0, 0, 272.5, SCREW_Z)
    retain_thread_z = openscad_thread_z("knob_retainer_male", 6.5, LEAD_MAJOR, LEAD_CORE, LEAD_PITCH, 1.0)
    retain_thread = zthread_to_y(retain_thread_z, 0, 279.5, SCREW_Z)
    return fuse_all([journal, shoulder, main_thread, drive, retain_thread])

lead_screw = make_lead_screw()

# C-clip-like plate retainer, printed flat. Axis is Y in assembly.
outer = cyl_y(5.75, 1.20, 0, 245.5, SCREW_Z)
inner = cyl_y(2.45, 2.0, 0, 245.1, SCREW_Z)
plate_retainer = outer.cut(inner)
# radial opening for snap installation
plate_retainer = plate_retainer.cut(box(-1.4, 245.0, SCREW_Z, 2.8, 2.0, 8.0)).removeSplitter()

# Separate knob, centered around screw axis at assembly position.
knob = cyl_y(16.0, 9.3, 0, 272.7, SCREW_Z)
knob = knob.cut(hex_prism_y(10.35, 7.4, 0, 272.5, SCREW_Z))
knob = knob.cut(cyl_y(4.35, 12.0, 0, 278.8, SCREW_Z)).removeSplitter()

# Separate threaded retaining cap. Female D8x2, does not transmit knob torque.
knob_cap = cyl_y(10.0, 6.0, 0, 282.0, SCREW_Z)
cap_cutter_z = openscad_thread_z("knob_cap_female_cutter", 8.0,
    LEAD_MAJOR + 2*LEAD_CLEAR, LEAD_CORE + 2*LEAD_CLEAR, LEAD_PITCH, 1.07)
knob_cap = knob_cap.cut(zthread_to_y(cap_cutter_z, 0, 280.5, SCREW_Z)).removeSplitter()

# -----------------------------
# Clamp pin + snap clip
# -----------------------------
def make_pin():
    # exported along X; shaft spans complete 34 mm clamp plus reserve
    shaft = cyl_x(2.0, 40.0, -20.0, 0, 0)
    head = cyl_x(4.0, 3.0, -23.0, 0, 0)
    # circumferential retaining groove near far end
    p = shaft.fuse(head)
    groove = Part.makeCylinder(2.45, 1.5, App.Vector(16.8,0,0), App.Vector(1,0,0))
    p = p.cut(groove)
    return p.removeSplitter()

pin = make_pin()
# Clip in YZ plane for pin groove; open on +Y side.
pin_clip = cyl_x(4.0, 1.6, 0, 0, 0).cut(cyl_x(1.62, 2.0, -0.2, 0, 0))
pin_clip = pin_clip.cut(box(-1, 0.6, -5, 3, 5, 10)).removeSplitter()

# -----------------------------
# Focus diagonal-stay anti-flop saddle
# -----------------------------
stay_saddle = box(-16, -12, 0, 32, 24, 16)
# broad V groove along X; not a fake exact tube diameter
vcut = prism_x([(-11,16),(0,5.5),(11,16)], -18, 36)
stay_saddle = stay_saddle.cut(vcut)
# two real zip-tie passages
for sx in (-9.0, 9.0):
    stay_saddle = stay_saddle.cut(box(sx-2.0, -4.0, -1.0, 4.0, 8.0, 18.0))
# vertical support boss offset to side of V groove
stay_saddle = stay_saddle.fuse(cyl_z(8.0, 12.0, 0, -9.0, 8.0))
stay_thread_cutter = thread_female_cutter_z.copy(); stay_thread_cutter.translate(App.Vector(0,-9.0,7.0))
stay_saddle = stay_saddle.cut(stay_thread_cutter).removeSplitter()

stay_thread = openscad_thread_z("stay_support_male", 18.0, LEAD_MAJOR, LEAD_CORE, LEAD_PITCH, 1.0)
stay_support_screw = stay_thread.translated(App.Vector(0,0,0)) if hasattr(stay_thread,'translated') else stay_thread.copy()
# add broad upper contact pad; screw is mountable from above with hex pad
stay_support_screw = fuse_all([
    stay_support_screw,
    cyl_z(8.0, 4.0, 0,0,18.0),
    hex_prism_y(10.0, 4.0, 0,-2.0,22.0).rotate(App.Vector(0,0,0),App.Vector(1,0,0),90) if False else cyl_z(9.0,3.0,0,0,22.0)
])

# -----------------------------
# Analytical arm sanity check
# -----------------------------
def arm_section_properties():
    # z=0 bottom; rectangles: bottom flange, top flange, two webs
    rects = [
        (32.0,4.5,2.25),
        (32.0,4.5,27.75),
        (3.2,21.0,15.0),
        (3.2,21.0,15.0),
    ]
    A = sum(b*h for b,h,z in rects)
    zc = sum(b*h*z for b,h,z in rects)/A
    I = sum(b*h**3/12.0 + b*h*(z-zc)**2 for b,h,z in rects)
    return A,zc,I

A,zc,I = arm_section_properties()
load_total_N = 16.0*9.81
F_arm_static = load_total_N/4.0
L_eff = 220.0
E = 1500.0
M = F_arm_static*L_eff
c = max(zc,30.0-zc)
stress_static = M*c/I
defl_static = F_arm_static*L_eff**3/(3*E*I)

# -----------------------------
# Validation geometry
# -----------------------------
validation = {
    "hard_datums": {
        "tube_diameter_mm": TUBE_D,
        "box_edge_y_mm": BOX_EDGE_Y,
        "box_support_z_mm": BOX_SUPPORT_Z,
        "clamp_x_mm": list(CLAMP_X),
        "screw_x_mm": list(SCREW_X),
        "screw_z_mm": SCREW_Z,
        "plate_travel_mm": PLATE_TRAVEL,
    },
    "arm_section": {
        "area_mm2": round(A,3), "centroid_z_mm": round(zc,3), "Ix_mm4": round(I,3),
        "static_16kg_stress_MPa": round(stress_static,3),
        "static_16kg_tip_deflection_mm": round(defl_static,3),
        "three_g_stress_MPa": round(3*stress_static,3),
        "three_g_tip_deflection_mm": round(3*defl_static,3),
        "E_MPa_assumed": E,
    },
    "checks": {}
}

# Rigid upper base vs real tube at both clamp positions.
for cx in CLAMP_X:
    tube = cyl_x(TUBE_R, 36.0, cx-18.0, 0, 0)
    cv = base.common(tube).Volume
    validation["checks"][f"rigid_base_tube_common_x{cx:+.0f}"] = round(cv,6)
    if cv > 1e-4:
        raise RuntimeError(f"Rigid base intersects real Ø12.42 tube at x={cx}: {cv}")

# Lower nominal preload is expected and recorded.
tube_local = cyl_x(TUBE_R, 21.0, -10.5, 0, 0)
lower_preload = rack_lower.common(tube_local).Volume
validation["checks"]["rack_lower_preload_common_mm3"] = round(lower_preload,6)
if lower_preload <= 0:
    raise RuntimeError("Rack lower has no intended preload")

# Closed lower vs upper at both locations: no material collision.
for cx in CLAMP_X:
    lo = rack_lower.copy(); lo.translate(App.Vector(cx,0,0))
    cv = base.common(lo).Volume
    validation["checks"][f"base_lower_common_x{cx:+.0f}"] = round(cv,6)
    if cv > 1e-4:
        raise RuntimeError(f"Base/rack_lower collision at {cx}: {cv}")

# Plate travel against base.
for dy in (0,1,2,3,4,4.5):
    p = plate.copy(); p.translate(App.Vector(0,dy,0))
    cv = base.common(p).Volume
    validation["checks"][f"base_plate_common_open_{dy:.1f}"] = round(cv,6)
    if cv > 1e-4:
        raise RuntimeError(f"Plate collides with base at opening {dy}: {cv}")

# Conservative 16.45 x 16.45 rim volume.
box_rim = box(-200, BOX_EDGE_Y-BOX_RIM, BOX_RIM_BOTTOM_Z, 400, BOX_RIM, BOX_RIM)
closed_box_overlap = plate.common(box_rim).Volume
popen = plate.copy(); popen.translate(App.Vector(0,PLATE_TRAVEL,0))
open_box_overlap = popen.common(box_rim).Volume
validation["checks"]["plate_box_closed_common_mm3"] = round(closed_box_overlap,6)
validation["checks"]["plate_box_open_common_mm3"] = round(open_box_overlap,6)
if closed_box_overlap > 1e-4 or open_box_overlap > 1e-4:
    raise RuntimeError("Plate intrudes into conservative box rim volume")
# Hook must move beyond outer edge when open.
hook_inner_closed = BOX_EDGE_Y-4.30
hook_inner_open = hook_inner_closed + PLATE_TRAVEL
validation["checks"]["hook_inner_closed_y"] = hook_inner_closed
validation["checks"]["hook_inner_open_y"] = hook_inner_open
if hook_inner_open <= BOX_EDGE_Y:
    raise RuntimeError("Opened hook does not clear box outer edge")

# Lead thread kinematics: male must stay inside larger female cutter for the correct pitch phase.
# We test in Z before transforming; crop away end effects.
male_test = openscad_thread_z("thread_test_male", 12.0, LEAD_MAJOR, LEAD_CORE, LEAD_PITCH, 1.0)
female_void = openscad_thread_z("thread_test_female_void", 16.0,
    LEAD_MAJOR+2*LEAD_CLEAR, LEAD_CORE+2*LEAD_CLEAR, LEAD_PITCH, 1.07)
# Baseline phase is intentionally aligned. Determine correct quarter-turn sign by containment.
def thread_excess(angle_deg, dz):
    m = male_test.copy()
    m.rotate(App.Vector(0,0,0),App.Vector(0,0,1),angle_deg)
    m.translate(App.Vector(0,0,2.0+dz))
    crop = cyl_z(10.0, 8.0, 0,0,4.0)
    return m.common(crop).cut(female_void.common(crop)).Volume
qplus = thread_excess(+90,0.5)
qminus = thread_excess(-90,0.5)
correct_sign = +90 if qplus < qminus else -90
correct_excess = min(qplus,qminus)
wrong_excess = max(qplus,qminus)
validation["checks"]["lead_quarter_turn_correct_deg"] = correct_sign
validation["checks"]["lead_quarter_turn_correct_excess_mm3"] = round(correct_excess,6)
validation["checks"]["lead_quarter_turn_wrong_excess_mm3"] = round(wrong_excess,6)
if correct_excess > 0.5:
    raise RuntimeError(f"Lead thread correct phase has excessive overlap: {correct_excess}")
if wrong_excess <= correct_excess + 0.5:
    raise RuntimeError("Lead thread phase test cannot distinguish correct/wrong rotation")

# Overall closed width with two mirrored modules, using closed knob cap max Y.
module_max_y = max(base.BoundBox.YMax, lead_screw.BoundBox.YMax, knob.BoundBox.YMax, knob_cap.BoundBox.YMax)
full_width = 2*(55.335 + module_max_y)
validation["checks"]["module_max_y_closed_mm"] = round(module_max_y,3)
validation["checks"]["full_system_width_closed_mm"] = round(full_width,3)

# -----------------------------
# Export
# -----------------------------
parts = {
    "eurobox_v50_base": base,
    "eurobox_v50_clamp_plate": plate,
    "eurobox_v50_rack_lower": rack_lower,
    "eurobox_v50_lead_screw_print": lead_screw,
    "eurobox_v50_lead_nut_print": lead_nut,
    "eurobox_v50_lead_nut_cap": lead_nut_cap,
    "eurobox_v50_knob": knob,
    "eurobox_v50_knob_retainer_cap": knob_cap,
    "eurobox_v50_plate_retainer_clip": plate_retainer,
    "eurobox_v50_pin": pin,
    "eurobox_v50_pin_clip": pin_clip,
    "eurobox_v50_stay_saddle": stay_saddle,
    "eurobox_v50_stay_support_screw": stay_support_screw,
}

validation["parts"] = {}
for name,shape in parts.items():
    validation["parts"][name] = export_part(name,shape)

# Assembly FCStd: one side module, both lower clamps, two screws/nuts/knobs in closed position.
doc = App.newDocument("eurobox_v50_assembly")
for name,shape in parts.items():
    if name in ("eurobox_v50_rack_lower", "eurobox_v50_pin", "eurobox_v50_pin_clip"):
        continue
    if name in ("eurobox_v50_lead_screw_print","eurobox_v50_lead_nut_print","eurobox_v50_knob","eurobox_v50_knob_retainer_cap","eurobox_v50_plate_retainer_clip"):
        for sx in SCREW_X:
            q=shape.copy(); q.translate(App.Vector(sx,0,0))
            o=doc.addObject("Part::Feature",name+f"_{sx:+.0f}"); o.Shape=q
    else:
        o=doc.addObject("Part::Feature",name); o.Shape=shape
for cx in CLAMP_X:
    q=rack_lower.copy(); q.translate(App.Vector(cx,0,0)); o=doc.addObject("Part::Feature",f"rack_lower_{cx:+.0f}"); o.Shape=q
    for py in (-11.5,11.5):
        q=pin.copy(); q.translate(App.Vector(cx,py,-5.5)); o=doc.addObject("Part::Feature",f"pin_{cx:+.0f}_{py:+.1f}"); o.Shape=q

doc.recompute(); doc.saveAs(os.path.join(OUT,"eurobox_v50_assembly.FCStd")); App.closeDocument(doc.Name)

with open(os.path.join(OUT,"VALIDATION_v50.json"),"w") as f:
    json.dump(validation,f,indent=2,sort_keys=True)

with open(os.path.join(OUT,"README_BUILD.txt"),"w") as f:
    f.write("Eurobox v50 clean-sheet build for Focus THRON2 EQP 2023\n")
    f.write("Measured datums and design rationale: docs/MEASUREMENTS.md and docs/V50_DESIGN.md\n")
    f.write(f"Closed full-system width estimate: {full_width:.2f} mm\n")
    f.write(f"Arm Ix: {I:.1f} mm^4; static 16 kg deflection sanity check: {defl_static:.2f} mm; 3g: {3*defl_static:.2f} mm\n")

print(json.dumps(validation,indent=2,sort_keys=True))
print("BUILD_OK", OUT)
