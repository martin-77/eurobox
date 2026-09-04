import FreeCAD as App
import Part
import Mesh
import importCSG
import os, math, json, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build_v50')
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)

# -----------------------------
# Hard measured datums
# -----------------------------
BOX_W = 600.0
BOX_L = 400.0
RIM_H = 16.45
RIM_Y = 16.45
RACK_D = 12.42
RACK_R = RACK_D / 2.0
RACK_CTC = 110.67
RACK_OUTER_W = 123.09
TUBE_TO_BOX_EDGE = 244.665
BOX_EDGE_Y = 244.665
BOX_RIM_INNER_Y = BOX_EDGE_Y - RIM_Y
BOX_SUPPORT_Z = 39.54
RIM_BOTTOM_Z = BOX_SUPPORT_Z - RIM_H
MUDGUARD_TOP_Z = 34.54
CLAMP_X = (-90.0, 90.0)

# -----------------------------
# v50 design parameters
# -----------------------------
ARM_W = 32.0
ARM_H = 30.0
FLANGE_T = 4.5
WEB_T = 3.2
ARM_TOP_Z = BOX_SUPPORT_Z
ARM_BOTTOM_Z = ARM_TOP_Z - ARM_H
ARM_Y0 = 24.0
ARM_Y1 = 220.0

PLATE_X = 140.0
PLATE_Y = 8.0
PLATE_Z0 = 16.0
PLATE_Z1 = 46.0
PLATE_OPEN = 4.5
PLATE_HOLE_D = 6.5
JOURNAL_D = 6.0
SHOULDER_D = 11.0
UNDERHOOK = 4.2
UNDERHOOK_T = 4.0
SPINDLE_X = (-42.0, 42.0)
SPINDLE_Z = 31.0

GUIDE_SIDE_CLEAR = 0.4
GUIDE_Z_CLEAR = 0.4

UPPER_SADDLE_R = 6.31
LOWER_SADDLE_R = 6.15
PIN_D = 4.0
PIN_HOLE_D = 4.6
PIN_Y = 3.0
PIN_Z = -10.5

STOP_FACE_Y = -6.46
STOP_INNER_Y = -12.46
STOP_Z0 = -8.0
STOP_Z1 = 5.0
STOP_X_W = 24.0

THREAD_MAJOR = 8.0
THREAD_PITCH = 2.0
THREAD_CORE_R = 3.25
THREAD_FEMALE_CORE_R = 3.42
THREAD_FEMALE_MAJOR_R = 4.22
LEAD_THREAD_LEN = 22.2
NUT_THREAD_LEN = 14.0
NUT_Y0 = 260.465
NUT_Y1 = NUT_Y0 + NUT_THREAD_LEN
CAGE_Y0 = 258.265
CAGE_Y1 = 276.665
SPINDLE_LOCAL_JOURNAL = 8.0
SPINDLE_LOCAL_SHOULDER = 1.8
HEX_LEN = 4.5
OUTER_STUD_LEN = 4.5


def fuse_all(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


def cyl_y(r, length, x=0.0, y=0.0, z=0.0):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def cyl_x(r, length, x=0.0, y=0.0, z=0.0):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(1, 0, 0))


def hex_z(af, height, z0=0.0):
    R = af / math.sqrt(3.0)
    pts = [App.Vector(R * math.cos(math.radians(30 + 60*i)),
                      R * math.sin(math.radians(30 + 60*i)), z0)
           for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0, 0, height))


def z_to_y(shape, x=0.0, y=0.0, z=0.0):
    s = shape.copy()
    s.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90)
    s.translate(App.Vector(x, y, z))
    return s


def make_i_beam_y(xc, y0, y1):
    L = y1 - y0
    top = box(xc-ARM_W/2, y0, ARM_TOP_Z-FLANGE_T, ARM_W, L, FLANGE_T)
    bot = box(xc-ARM_W/2, y0, ARM_BOTTOM_Z, ARM_W, L, FLANGE_T)
    web_h = ARM_H - 2*FLANGE_T
    web_z = ARM_BOTTOM_Z + FLANGE_T
    w1 = box(xc-8.0-WEB_T/2, y0, web_z, WEB_T, L, web_h)
    w2 = box(xc+8.0-WEB_T/2, y0, web_z, WEB_T, L, web_h)
    return fuse_all([top, bot, w1, w2])


def write_thread_scad(path, core_r, major_r, pitch, length, root_w, crest_w):
    txt = f'''$fn=72;\nmodule thread_solid(){{\n  union(){{\n    cylinder(r={core_r},h={length});\n    linear_extrude(height={length},twist=360*{length}/{pitch},slices=ceil({length}/{pitch}*28),convexity=30)\n      polygon(points=[[{core_r}-0.08,-{root_w}/2],[{major_r},-{crest_w}/2],[{major_r},{crest_w}/2],[{core_r}-0.08,{root_w}/2]]);\n  }}\n}}\nthread_solid();\n'''
    with open(path, 'w') as f:
        f.write(txt)


def import_scad_shape(path):
    d = importCSG.open(path)
    d.recompute()
    candidates = []
    for o in d.Objects:
        if hasattr(o, 'Shape') and not o.Shape.isNull() and len(o.Shape.Solids) > 0 and o.Shape.isValid():
            candidates.append((abs(o.Shape.Volume), o.Shape.copy()))
    if not candidates:
        raise RuntimeError('No valid solid from '+path)
    s = max(candidates, key=lambda x: x[0])[1]
    App.closeDocument(d.Name)
    return s


def export_part(name, shape):
    if not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(f'{name}: invalid source solid')
    step = os.path.join(OUT, name+'.step')
    stl = os.path.join(OUT, name+'.stl')
    fcstd = os.path.join(OUT, name+'.FCStd')
    shape.exportStep(step)
    d = App.newDocument('doc_'+name)
    o = d.addObject('Part::Feature', name)
    o.Shape = shape
    d.recompute()
    d.saveAs(fcstd)
    Mesh.export([o], stl)
    App.closeDocument(d.Name)
    rt = Part.Shape(); rt.read(step)
    return {
        'source_valid': shape.isValid(),
        'source_solids': len(shape.Solids),
        'step_valid': rt.isValid(),
        'step_solids': len(rt.Solids),
        'volume_mm3': round(shape.Volume, 4),
        'step_volume_delta_mm3': round(abs(shape.Volume-rt.Volume), 6),
        'bbox_mm': [round(shape.BoundBox.XLength,3), round(shape.BoundBox.YLength,3), round(shape.BoundBox.ZLength,3)],
    }

# -----------------------------
# Thread master geometry
# -----------------------------
MALE_SCAD = os.path.join(OUT, 'thread_RH_8x2_male.scad')
FEMALE_SCAD = os.path.join(OUT, 'thread_RH_8x2_female_cutter.scad')
write_thread_scad(MALE_SCAD, THREAD_CORE_R, THREAD_MAJOR/2, THREAD_PITCH, LEAD_THREAD_LEN, 0.58, 0.24)
write_thread_scad(FEMALE_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, NUT_THREAD_LEN, 0.76, 0.40)
MALE = import_scad_shape(MALE_SCAD).common(Part.makeCylinder(4.06, LEAD_THREAD_LEN)).removeSplitter()
FEMALE = import_scad_shape(FEMALE_SCAD).common(Part.makeCylinder(4.28, NUT_THREAD_LEN)).removeSplitter()

MALE_STUD_SCAD = os.path.join(OUT, 'thread_RH_8x2_stud.scad')
FEMALE_STUD_SCAD = os.path.join(OUT, 'thread_RH_8x2_cap_cutter.scad')
write_thread_scad(MALE_STUD_SCAD, THREAD_CORE_R, THREAD_MAJOR/2, THREAD_PITCH, OUTER_STUD_LEN, 0.58, 0.24)
write_thread_scad(FEMALE_STUD_SCAD, THREAD_FEMALE_CORE_R, THREAD_FEMALE_MAJOR_R, THREAD_PITCH, OUTER_STUD_LEN, 0.76, 0.40)
MALE_STUD = import_scad_shape(MALE_STUD_SCAD).common(Part.makeCylinder(4.06, OUTER_STUD_LEN)).removeSplitter()
FEMALE_STUD = import_scad_shape(FEMALE_STUD_SCAD).common(Part.makeCylinder(4.28, OUTER_STUD_LEN)).removeSplitter()

# -----------------------------
# Rack clamp station and base
# -----------------------------
def make_upper_station(xc):
    bridge = box(xc-17.0, -12.5, 0.0, 34.0, 26.5, 16.0)
    cheek_l = box(xc-17.0, -6.0, -14.0, 4.0, 19.0, 14.5)
    cheek_r = box(xc+13.0, -6.0, -14.0, 4.0, 19.0, 14.5)
    stop = box(xc-STOP_X_W/2, STOP_INNER_Y, STOP_Z0,
               STOP_X_W, STOP_FACE_Y-STOP_INNER_Y, STOP_Z1-STOP_Z0)
    transition = box(xc-16.0, 10.0, ARM_BOTTOM_Z, 32.0, 20.0, ARM_H)
    s = fuse_all([bridge, cheek_l, cheek_r, stop, transition])
    s = s.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc-20.0, 0.0, 0.0))
    s = s.cut(cyl_x(PIN_HOLE_D/2, 40.0, xc-20.0, PIN_Y, PIN_Z))
    return s.removeSplitter()

base_parts = [make_upper_station(x) for x in CLAMP_X]
base_parts += [make_i_beam_y(x, ARM_Y0, ARM_Y1) for x in CLAMP_X]

# Crosshead stays clear of the hanging 16.45 x 16.45 mm box rim.
base_parts += [
    box(-106.0, 216.0, ARM_TOP_Z-FLANGE_T, 212.0, BOX_RIM_INNER_Y-216.2, FLANGE_T),
    box(-106.0, 216.0, ARM_BOTTOM_Z, 212.0, 42.2, FLANGE_T),
    box(-106.0, 216.0, ARM_BOTTOM_Z+FLANGE_T, 212.0, 4.5, ARM_H-2*FLANGE_T),
]

# Plate guide cage, outside the actual box edge.
base_parts += [
    box(-78.0, BOX_EDGE_Y, 14.0, 7.6, 14.0, 35.8),
    box(70.4, BOX_EDGE_Y, 14.0, 7.6, 14.0, 35.8),
    box(-70.0, BOX_EDGE_Y, PLATE_Z1+GUIDE_Z_CLEAR, 140.0, 14.0, 3.4),
    box(-70.0, BOX_EDGE_Y, 12.0, 140.0, 14.0, PLATE_Z0-GUIDE_Z_CLEAR-12.0),
]

# Outer screw frame.
base_parts += [
    box(-78.0, CAGE_Y0-0.1, 20.0, 156.0, CAGE_Y1-CAGE_Y0+0.2, 4.0),
    box(-78.0, CAGE_Y0-0.1, 38.0, 156.0, CAGE_Y1-CAGE_Y0+0.2, 4.0),
]
for sx in SPINDLE_X:
    base_parts.append(box(sx-11.0, CAGE_Y0, 20.0, 22.0, CAGE_Y1-CAGE_Y0, 24.0))

BASE = fuse_all(base_parts)
for sx in SPINDLE_X:
    pocket = box(sx-8.35, NUT_Y0-0.35, 23.65, 16.7, NUT_THREAD_LEN+0.7, 21.0)
    BASE = BASE.cut(pocket)
    BASE = BASE.cut(cyl_y(4.45, CAGE_Y1-(BOX_EDGE_Y+8.0)+1.0, sx, BOX_EDGE_Y+8.0, SPINDLE_Z))
    BASE = BASE.cut(cyl_x(1.7, 24.0, sx-12.0, (NUT_Y0+NUT_Y1)/2, 40.0))
BASE = BASE.removeSplitter()

# -----------------------------
# Rack lower clamp
# -----------------------------
LOWER = box(-12.6, -5.8, -14.0, 25.2, 17.8, 14.0)
LOWER = LOWER.cut(cyl_x(LOWER_SADDLE_R, 27.2, -13.6, 0.0, 0.0))
LOWER = LOWER.cut(cyl_x(PIN_HOLE_D/2, 27.2, -13.6, PIN_Y, PIN_Z))
LOWER = LOWER.removeSplitter()

# Main rack pin: head + shaft + reduced groove + end section.
PIN = fuse_all([
    cyl_x(2.0, 33.5, -18.4, 0, 0),
    cyl_x(1.55, 1.5, 15.1, 0, 0),
    cyl_x(2.0, 1.7, 16.6, 0, 0),
    cyl_x(3.75, 2.4, -20.8, 0, 0),
])

def make_c_clip(outer_r, inner_r, thickness, opening_w):
    ring = Part.makeCylinder(outer_r, thickness).cut(Part.makeCylinder(inner_r, thickness))
    opening = box(-opening_w/2, 0.0, -0.2, opening_w, outer_r+1.0, thickness+0.4)
    return ring.cut(opening).removeSplitter()

PIN_CLIP = make_c_clip(4.2, 1.65, 1.5, 3.0)

# -----------------------------
# Clamp plate
# -----------------------------
PLATE = box(-PLATE_X/2, BOX_EDGE_Y, PLATE_Z0, PLATE_X, PLATE_Y, PLATE_Z1-PLATE_Z0)
PLATE = PLATE.fuse(box(-PLATE_X/2, BOX_EDGE_Y-UNDERHOOK, RIM_BOTTOM_Z-UNDERHOOK_T,
                       PLATE_X, UNDERHOOK, UNDERHOOK_T))
for sx in SPINDLE_X:
    PLATE = PLATE.cut(cyl_y(PLATE_HOLE_D/2, PLATE_Y+1.0, sx, BOX_EDGE_Y-0.5, SPINDLE_Z))
    PLATE = PLATE.cut(cyl_y(6.0, 2.0, sx, BOX_EDGE_Y, SPINDLE_Z))
PLATE = PLATE.removeSplitter()

# -----------------------------
# Lead nut cartridge and retainer pin
# -----------------------------
LEAD_NUT = box(-8.0, 0.0, -7.0, 16.0, NUT_THREAD_LEN, 14.0)
LEAD_NUT = LEAD_NUT.fuse(box(-6.0, 3.0, 7.0, 12.0, 8.0, 4.0))
LEAD_NUT = LEAD_NUT.cut(z_to_y(FEMALE, 0, 0, 0))
LEAD_NUT = LEAD_NUT.cut(cyl_x(1.7, 20.0, -10.0, 7.0, 9.0))
LEAD_NUT = LEAD_NUT.removeSplitter()

NUT_PIN = fuse_all([
    cyl_x(1.5, 23.5, -11.75, 0, 0),
    cyl_x(3.0, 2.0, -13.75, 0, 0),
])
NUT_PIN_CLIP = make_c_clip(3.2, 1.25, 1.3, 2.4)

# -----------------------------
# Separate lead spindle, knob, cap nut, plate retaining clip
# -----------------------------
SPINDLE = fuse_all([
    cyl_y(3.0, 0.4, 0, 0.0, 0),
    cyl_y(2.5, 1.4, 0, 0.4, 0),
    cyl_y(3.0, SPINDLE_LOCAL_JOURNAL-1.8, 0, 1.8, 0),
    cyl_y(SHOULDER_D/2, SPINDLE_LOCAL_SHOULDER, 0, SPINDLE_LOCAL_JOURNAL, 0),
    z_to_y(MALE, 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER, 0),
    z_to_y(hex_z(10.0, HEX_LEN), 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN, 0),
    z_to_y(MALE_STUD, 0, SPINDLE_LOCAL_JOURNAL+SPINDLE_LOCAL_SHOULDER+LEAD_THREAD_LEN+HEX_LEN, 0),
]).removeSplitter()

KNOB = cyl_y(15.0, 7.0, 0, 0, 0)
for a in range(0, 360, 45):
    rr = 16.2
    x = rr * math.cos(math.radians(a))
    z = rr * math.sin(math.radians(a))
    KNOB = KNOB.cut(cyl_y(3.4, 7.4, x, -0.2, z))
KNOB = KNOB.cut(cyl_y(4.3, 7.4, 0, -0.2, 0))
KNOB = KNOB.cut(z_to_y(hex_z(10.35, 5.2), 0, 0, 0)).removeSplitter()

CAP_NUT = z_to_y(hex_z(13.0, 4.2), 0, 0, 0)
CAP_NUT = CAP_NUT.cut(z_to_y(FEMALE_STUD, 0, 0, 0)).removeSplitter()

PLATE_CLIP = make_c_clip(5.4, 2.45, 1.4, 3.8)

PARTS = {
    'eurobox_v50_base': BASE,
    'eurobox_v50_rack_lower': LOWER,
    'eurobox_v50_rack_pin': PIN,
    'eurobox_v50_rack_pin_clip': PIN_CLIP,
    'eurobox_v50_clamp_plate': PLATE,
    'eurobox_v50_lead_nut_print': LEAD_NUT,
    'eurobox_v50_lead_nut_retaining_pin': NUT_PIN,
    'eurobox_v50_lead_nut_pin_clip': NUT_PIN_CLIP,
    'eurobox_v50_lead_screw_print': SPINDLE,
    'eurobox_v50_knob': KNOB,
    'eurobox_v50_knob_retainer_nut': CAP_NUT,
    'eurobox_v50_plate_retainer_clip': PLATE_CLIP,
}

# -----------------------------
# Validation
# -----------------------------
V = {
    'version': 'v50',
    'freecad_version': '.'.join(App.Version()[:3]),
    'hard_datums': {
        'rack_tube_diameter_mm': RACK_D,
        'rack_outer_width_mm': RACK_OUTER_W,
        'rack_center_distance_mm': RACK_CTC,
        'tube_to_box_edge_mm': TUBE_TO_BOX_EDGE,
        'box_edge_y_mm': BOX_EDGE_Y,
        'box_rim_inner_y_mm': BOX_RIM_INNER_Y,
        'box_support_z_mm': BOX_SUPPORT_Z,
        'rim_bottom_z_mm': RIM_BOTTOM_Z,
    },
    'parts': {},
}

TUBE = cyl_x(RACK_R, 240.0, -120.0, 0.0, 0.0)
V['tube_base_common_mm3'] = round(BASE.common(TUBE).Volume, 6)

V['rack_lower_checks'] = []
for xc in CLAMP_X:
    lo = LOWER.copy(); lo.translate(App.Vector(xc, 0, 0))
    V['rack_lower_checks'].append({
        'x_mm': xc,
        'base_common_mm3': round(BASE.common(lo).Volume, 6),
        'tube_preload_common_mm3': round(TUBE.common(lo).Volume, 6),
    })

V['rack_pin_checks'] = []
for xc in CLAMP_X:
    p = PIN.copy(); p.translate(App.Vector(xc, PIN_Y, PIN_Z))
    lo = LOWER.copy(); lo.translate(App.Vector(xc, 0, 0))
    V['rack_pin_checks'].append({
        'x_mm': xc,
        'base_common_mm3': round(BASE.common(p).Volume, 6),
        'lower_common_mm3': round(lo.common(p).Volume, 6),
    })

# Anti-rotation contact: nominally free; a small downward-outboard rotation must hit the rack edge/tube.
V['anti_rotation'] = []
for deg in [0.0, -0.5, -1.0, -1.5, -2.0, -3.0, -5.0]:
    b = BASE.copy()
    b.rotate(App.Vector(0,0,0), App.Vector(1,0,0), deg)
    V['anti_rotation'].append({'rotation_deg': deg, 'tube_common_mm3': round(b.common(TUBE).Volume, 6)})

RIM = box(-200.0, BOX_RIM_INNER_Y, RIM_BOTTOM_Z, 400.0, RIM_Y, RIM_H)
V['base_box_rim_common_mm3'] = round(BASE.common(RIM).Volume, 6)
V['plate_motion'] = []
for d in [0, 1, 2, 3, 4, 4.5]:
    pl = PLATE.copy(); pl.translate(App.Vector(0,d,0))
    V['plate_motion'].append({
        'open_mm': d,
        'base_common_mm3': round(BASE.common(pl).Volume, 6),
        'rim_common_mm3': round(RIM.common(pl).Volume, 6),
        'underhook_inner_y_mm': round(BOX_EDGE_Y-UNDERHOOK+d, 3),
    })

V['plate_hole_probe_common_mm3'] = []
for sx in SPINDLE_X:
    probe = cyl_y(PLATE_HOLE_D/2-0.05, PLATE_Y+1.0, sx, BOX_EDGE_Y-0.5, SPINDLE_Z)
    V['plate_hole_probe_common_mm3'].append(round(PLATE.common(probe).Volume, 6))

V['lead_nut_checks'] = []
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx, NUT_Y0, SPINDLE_Z))
    V['lead_nut_checks'].append({
        'x_mm': sx,
        'base_common_mm3': round(BASE.common(nut).Volume, 6),
        'distance_to_base_mm': round(BASE.distToShape(nut)[0], 6),
    })

V['thread_kinematics'] = []
for d in [0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5]:
    q = SPINDLE.copy()
    q.rotate(App.Vector(0,0,0), App.Vector(0,1,0), -360.0*d/THREAD_PITCH)
    q.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+d, SPINDLE_Z))
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(SPINDLE_X[0], NUT_Y0, SPINDLE_Z))
    V['thread_kinematics'].append({
        'open_mm': d,
        'rotation_deg': -360.0*d/THREAD_PITCH,
        'nut_common_mm3': round(nut.common(q).Volume, 6),
        'base_common_mm3': round(BASE.common(q).Volume, 6),
    })

wrong = SPINDLE.copy()
wrong.rotate(App.Vector(0,0,0), App.Vector(0,1,0), +90.0)
wrong.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y+0.5, SPINDLE_Z))
nut0 = LEAD_NUT.copy(); nut0.translate(App.Vector(SPINDLE_X[0], NUT_Y0, SPINDLE_Z))
V['wrong_phase_0_5mm_nut_common_mm3'] = round(nut0.common(wrong).Volume, 6)

sp0 = SPINDLE.copy(); sp0.translate(App.Vector(SPINDLE_X[0], BOX_EDGE_Y, SPINDLE_Z))
V['spindle_plate_common_mm3'] = round(sp0.common(PLATE).Volume, 6)

hex_y = SPINDLE_LOCAL_JOURNAL + SPINDLE_LOCAL_SHOULDER + LEAD_THREAD_LEN
kb = KNOB.copy(); kb.translate(App.Vector(0, hex_y, 0))
cap_y = hex_y + 7.0
cn = CAP_NUT.copy(); cn.translate(App.Vector(0, cap_y, 0))
V['knob_interface'] = {
    'spindle_knob_common_mm3': round(SPINDLE.common(kb).Volume, 6),
    'spindle_cap_nut_common_mm3': round(SPINDLE.common(cn).Volume, 6),
    'knob_cap_nut_common_mm3': round(kb.common(cn).Volume, 6),
}

web_h = ARM_H - 2*FLANGE_T
area = 2*ARM_W*FLANGE_T + 2*WEB_T*web_h
I = 2*((ARM_W*FLANGE_T**3)/12.0 + (ARM_W*FLANGE_T)*(ARM_H/2.0-FLANGE_T/2.0)**2) + 2*(WEB_T*web_h**3/12.0)
F_arm = 16.0*9.81/4.0
L_check = 220.0
E = 1500.0
V['beam_sanity'] = {
    'section_area_mm2': round(area, 3),
    'Ix_mm4': round(I, 3),
    'assumed_length_mm': L_check,
    'E_petg_mpa': E,
    'static_stress_mpa': round(F_arm*L_check*(ARM_H/2)/I, 4),
    'static_tip_deflection_mm': round(F_arm*L_check**3/(3*E*I), 4),
    'dynamic_3x_stress_mpa': round(3*F_arm*L_check*(ARM_H/2)/I, 4),
    'dynamic_3x_tip_deflection_mm': round(3*F_arm*L_check**3/(3*E*I), 4),
}

spindle_outer_local_y = BOX_EDGE_Y + (SPINDLE_LOCAL_JOURNAL + SPINDLE_LOCAL_SHOULDER + LEAD_THREAD_LEN + HEX_LEN + OUTER_STUD_LEN)
V['system_width_estimate_mm'] = {
    'closed': round(BOX_W + 2*(spindle_outer_local_y-BOX_EDGE_Y), 3),
    'open_4_5mm': round(BOX_W + 2*((spindle_outer_local_y+4.5)-BOX_EDGE_Y), 3),
}

failures = []
if V['tube_base_common_mm3'] > 1e-4:
    failures.append('Base intersects real Ø12.42 rack tube')
for c in V['rack_lower_checks']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Rack lower intersects base at X='+str(c['x_mm']))
for c in V['rack_pin_checks']:
    if c['base_common_mm3'] > 1e-4 or c['lower_common_mm3'] > 1e-4:
        failures.append('Rack pin does not pass cleanly at X='+str(c['x_mm']))
if V['base_box_rim_common_mm3'] > 1e-4:
    failures.append('Base intersects conservative Eurobox rim')
for c in V['plate_motion']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Plate/base collision at open='+str(c['open_mm']))
    if c['rim_common_mm3'] > 1e-4:
        failures.append('Plate/rim volume collision at open='+str(c['open_mm']))
for x in V['plate_hole_probe_common_mm3']:
    if x > 1e-4:
        failures.append('Clamp plate through-hole is blocked')
for c in V['lead_nut_checks']:
    if c['base_common_mm3'] > 1e-4:
        failures.append('Lead nut collides with cage at X='+str(c['x_mm']))
for c in V['thread_kinematics']:
    if c['nut_common_mm3'] > 0.5:
        failures.append('Lead thread collision in correct phase at open='+str(c['open_mm']))
    if c['base_common_mm3'] > 0.5:
        failures.append('Spindle collides with base at open='+str(c['open_mm']))
if V['wrong_phase_0_5mm_nut_common_mm3'] < 1.0:
    failures.append('Wrong-phase thread test did not create meaningful interference')
if V['anti_rotation'][0]['tube_common_mm3'] > 1e-4:
    failures.append('Anti-rotation stop collides at nominal position')
if max(x['tube_common_mm3'] for x in V['anti_rotation'][1:]) < 0.1:
    failures.append('Anti-rotation stop does not contact rack tube within 5 degrees')

for name, sh in PARTS.items():
    try:
        V['parts'][name] = export_part(name, sh)
    except Exception as e:
        failures.append(name+': '+repr(e))

# -----------------------------
# Assembly: two identical modules; left is same part rotated 180° around Z
# -----------------------------
doc = App.newDocument('Eurobox_v50_assembly')
def add_obj(name, sh):
    o = doc.addObject('Part::Feature', name); o.Shape = sh; return o

RY = RACK_CTC/2.0
LY = -RACK_CTC/2.0

right_base = BASE.copy(); right_base.translate(App.Vector(0, RY, 0)); add_obj('RIGHT_base', right_base)
right_plate = PLATE.copy(); right_plate.translate(App.Vector(0, RY, 0)); add_obj('RIGHT_plate', right_plate)
for xc in CLAMP_X:
    lo = LOWER.copy(); lo.translate(App.Vector(xc, RY, 0)); add_obj('RIGHT_lower_'+str(int(xc)), lo)
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx, RY+NUT_Y0, SPINDLE_Z)); add_obj('RIGHT_nut_'+str(int(sx)), nut)
    sp = SPINDLE.copy(); sp.translate(App.Vector(sx, RY+BOX_EDGE_Y, SPINDLE_Z)); add_obj('RIGHT_spindle_'+str(int(sx)), sp)
    k = KNOB.copy(); k.translate(App.Vector(sx, RY+BOX_EDGE_Y+hex_y, SPINDLE_Z)); add_obj('RIGHT_knob_'+str(int(sx)), k)

def left_transform(sh):
    s = sh.copy(); s.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 180); s.translate(App.Vector(0, LY, 0)); return s
add_obj('LEFT_base', left_transform(BASE))
add_obj('LEFT_plate', left_transform(PLATE))
for xc in CLAMP_X:
    lo = LOWER.copy(); lo.translate(App.Vector(xc,0,0)); add_obj('LEFT_lower_'+str(int(xc)), left_transform(lo))
for sx in SPINDLE_X:
    nut = LEAD_NUT.copy(); nut.translate(App.Vector(sx,NUT_Y0,SPINDLE_Z)); add_obj('LEFT_nut_'+str(int(sx)), left_transform(nut))
    sp = SPINDLE.copy(); sp.translate(App.Vector(sx,BOX_EDGE_Y,SPINDLE_Z)); add_obj('LEFT_spindle_'+str(int(sx)), left_transform(sp))

add_obj('REF_right_rack_tube', cyl_x(RACK_R, 240.0, -120.0, RY, 0.0))
add_obj('REF_left_rack_tube', cyl_x(RACK_R, 240.0, -120.0, LY, 0.0))
right_rim = RIM.copy(); right_rim.translate(App.Vector(0,RY,0)); add_obj('REF_right_box_rim', right_rim)
left_rim = RIM.copy(); left_rim.rotate(App.Vector(),App.Vector(0,0,1),180); left_rim.translate(App.Vector(0,LY,0)); add_obj('REF_left_box_rim', left_rim)

info = doc.addObject('App::FeaturePython','DesignParameters')
for prop,val in [
    ('RackTubeDiameter',RACK_D),('RackTubeCenterDistance',RACK_CTC),('RackOuterWidth',RACK_OUTER_W),
    ('BoxWidth',BOX_W),('BoxLength',BOX_L),('BoxEdgeLocalY',BOX_EDGE_Y),('BoxSupportZ',BOX_SUPPORT_Z),
    ('ArmWidth',ARM_W),('ArmHeight',ARM_H),('LeadThreadDiameter',THREAD_MAJOR),('LeadThreadPitch',THREAD_PITCH),
    ('PlateTravel',PLATE_OPEN),('PlateHoleDiameter',PLATE_HOLE_D),('RackPinDiameter',PIN_D),('RackPinHoleDiameter',PIN_HOLE_D),
    ('AntiRotationStopFaceY',STOP_FACE_Y),('AntiRotationStopZMin',STOP_Z0),('AntiRotationStopZMax',STOP_Z1)
]:
    info.addProperty('App::PropertyLength', prop); setattr(info, prop, val)
doc.recompute(); doc.saveAs(os.path.join(OUT,'eurobox_v50_assembly.FCStd'))
App.closeDocument(doc.Name)

V['failures'] = failures
with open(os.path.join(OUT, 'VALIDATION_v50_source.json'), 'w') as f:
    json.dump(V, f, indent=2)

with open(os.path.join(OUT, 'README_BUILD_v50.txt'), 'w') as f:
    f.write('Eurobox v50 clean-sheet build for FOCUS THRON2 6.8 EQP MY2023.\n')
    f.write('No diagonal-stay V saddle. Anti-rotation is integrated into both rack-clamp roots.\n')
    f.write('Printed test lead screw: RH 8x2, separate screw / lead nut / knob / retainers.\n')
    f.write('See docs/V50_DESIGN.md, docs/MEASUREMENTS.md and VALIDATION_v50_source.json.\n')

print(json.dumps(V, indent=2))
if failures:
    raise SystemExit('V50 HARD CHECKS FAILED: ' + ' | '.join(failures))
