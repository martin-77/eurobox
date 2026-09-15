import FreeCAD as App
import Part
import Mesh
import json
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build_v60')
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)

# -----------------------------------------------------------------------------
# v60 hard datums -- no source-rewriting fixup chain
# -----------------------------------------------------------------------------
BOX_W = 600.0
BOX_L = 400.0
RIM_H = 16.45
RIM_Y = 16.45
RACK_D = 12.42
RACK_R = RACK_D / 2.0
RACK_CTC = 110.67
RACK_OUTER_W = 123.09
BOX_EDGE_Y = 244.665
BOX_RIM_INNER_Y = BOX_EDGE_Y - RIM_Y
BOX_SUPPORT_Z = 39.54

ARM_W = 32.0
ARM_H = 30.0
FLANGE_T = 4.5
WEB_T = 3.2
ARM_TOP_Z = BOX_SUPPORT_Z
ARM_BOTTOM_Z = ARM_TOP_Z - ARM_H
ARM_Y0 = 24.0
ARM_Y1 = 220.0

# Final longitudinal layout.
FRONT_CLAMP_X = -80.0
REAR_CLAMP_X = 80.0
CLAMP_X = (FRONT_CLAMP_X, REAR_CLAMP_X)
CLAMP_SPACING = REAR_CLAMP_X - FRONT_CLAMP_X
REAR_SUPPORT_X = 180.0

# Physical rack-axis coordinate system: front fixed clamp body begins at 20 mm.
FIXED_STATION_HALF_X = 19.0
PHYSICAL_X_ORIGIN = 20.0 - (FRONT_CLAMP_X - FIXED_STATION_HALF_X)
FRONT_CLAMP_PHYS_X = FRONT_CLAMP_X + PHYSICAL_X_ORIGIN
REAR_CLAMP_PHYS_X = REAR_CLAMP_X + PHYSICAL_X_ORIGIN

# Rear sequence: clamp -> old 31 mm service gap -> 50 mm backstop.
BACKSTOP_X0 = REAR_CLAMP_X + 50.0
BACKSTOP_X1 = BACKSTOP_X0 + 50.0
BACKSTOP_W = BACKSTOP_X1 - BACKSTOP_X0
BACKSTOP_PHYS_X0 = BACKSTOP_X0 + PHYSICAL_X_ORIGIN
BACKSTOP_PHYS_X1 = BACKSTOP_X1 + PHYSICAL_X_ORIGIN
REAR_SUPPORT_PHYS_X = REAR_SUPPORT_X + PHYSICAL_X_ORIGIN

# Clamp geometry frozen from the repaired v50 mechanism.
UPPER_SADDLE_R = 6.26
PIN_HOLE_D = 4.6
PIN_Y = -12.0
PIN_Z = -5.5
STOP_FACE_Y = -6.46
STOP_INNER_Y = -12.46
STOP_Z0 = -8.0
STOP_Z1 = 5.0
STOP_X_W = 24.0

# Printer hard envelope after CORE One L -> INDX conversion.
INDX_X_MAX = 298.0
INDX_Y_MAX = 275.0
V60_X_TARGET_MAX = 296.0


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


def cyl_x(r, length, x=0.0, y=0.0, z=0.0):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(1, 0, 0))


def fuse_seq(shapes, label):
    if not shapes:
        raise RuntimeError(label + ': no shapes')
    out = shapes[0]
    for i, sh in enumerate(shapes[1:], 1):
        out = out.fuse(sh).removeSplitter()
        if not out.isValid():
            raise RuntimeError(f'{label}: invalid after fuse {i}')
    return out.removeSplitter()


def require_single(sh, label):
    if sh.isNull() or not sh.isValid() or len(sh.Solids) != 1:
        raise RuntimeError(f'{label}: expected one valid solid, got {len(sh.Solids)} solids')


def make_i_beam_y(xc, y0, y1):
    length = y1 - y0
    web_h = ARM_H - 2.0 * FLANGE_T
    web_z = ARM_BOTTOM_Z + FLANGE_T
    return fuse_seq([
        box(xc - ARM_W / 2.0, y0, ARM_TOP_Z - FLANGE_T, ARM_W, length, FLANGE_T),
        box(xc - ARM_W / 2.0, y0, ARM_BOTTOM_Z, ARM_W, length, FLANGE_T),
        box(xc - 8.0 - WEB_T / 2.0, y0, web_z, WEB_T, length, web_h),
        box(xc + 8.0 - WEB_T / 2.0, y0, web_z, WEB_T, length, web_h),
    ], f'i-beam@{xc}')


def make_upper_station(xc):
    bridge = box(xc - 17.0, -12.5, 0.0, 34.0, 26.5, 16.0)
    cheek_l = box(xc - 17.0, -16.0, -14.0, 4.0, 29.0, 14.5)
    cheek_r = box(xc + 13.0, -16.0, -14.0, 4.0, 29.0, 14.5)
    stop = box(xc - STOP_X_W / 2.0, STOP_INNER_Y, STOP_Z0,
               STOP_X_W, STOP_FACE_Y - STOP_INNER_Y, STOP_Z1 - STOP_Z0)
    transition = box(xc - 16.0, 10.0, ARM_BOTTOM_Z, 32.0, 20.0, ARM_H)
    station = fuse_seq([bridge, cheek_l, cheek_r, stop, transition], f'upper-station@{xc}')
    station = station.cut(cyl_x(UPPER_SADDLE_R, 40.0, xc - 20.0, 0.0, 0.0)).removeSplitter()
    station = station.cut(cyl_x(PIN_HOLE_D / 2.0, 40.0, xc - 20.0, PIN_Y, PIN_Z)).removeSplitter()
    require_single(station, f'upper-station@{xc}')
    return station


def make_clamp_wall():
    # Full-height wall between fixed stations. It deliberately overlaps both
    # station bodies; the real rack tube is carved out of the wall afterwards.
    x0 = FRONT_CLAMP_X + 8.0
    x1 = REAR_CLAMP_X - 8.0
    wall = box(x0, -8.0, 0.0, x1 - x0, 16.0, BOX_SUPPORT_Z)
    wall = wall.cut(cyl_x(UPPER_SADDLE_R, (x1 - x0) + 2.0,
                           x0 - 1.0, 0.0, 0.0)).removeSplitter()
    require_single(wall, 'central-clamp-wall')
    return wall


def make_crosshead():
    # Direct final span: front support outer face -> rear support outer face.
    x0 = FRONT_CLAMP_X - ARM_W / 2.0
    x1 = REAR_SUPPORT_X + ARM_W / 2.0
    y0 = 216.0
    y1 = BOX_RIM_INNER_Y - 0.20
    web_h = ARM_H - 2.0 * FLANGE_T
    return fuse_seq([
        box(x0, y0, ARM_TOP_Z - FLANGE_T, x1 - x0, y1 - y0, FLANGE_T),
        box(x0, y0, ARM_BOTTOM_Z, x1 - x0, y1 - y0, FLANGE_T),
        box(x0, y0, ARM_BOTTOM_Z + FLANGE_T, x1 - x0, 4.5, web_h),
    ], 'crosshead')


def make_backstop():
    # No diagonal gusset. Broad hanging plate plus rectangular bridge into the
    # moved rear support; this is an assembly aid, not a third clamp.
    panel = box(BACKSTOP_X0, -16.0, -42.0, BACKSTOP_W, 4.0, 50.0)
    bridge = box(BACKSTOP_X0, -16.0, 7.0, BACKSTOP_W, 36.0, BOX_SUPPORT_Z - 7.0)
    return fuse_seq([panel, bridge], 'rear-backstop')


def make_right_core():
    front_station = make_upper_station(FRONT_CLAMP_X)
    rear_station = make_upper_station(REAR_CLAMP_X)
    wall = make_clamp_wall()
    front_support = make_i_beam_y(FRONT_CLAMP_X, ARM_Y0, ARM_Y1)
    rear_support = make_i_beam_y(REAR_SUPPORT_X, 0.0, ARM_Y1)
    crosshead = make_crosshead()
    backstop = make_backstop()

    # Sequential construction is intentional: every named structure is final
    # geometry. Nothing is created at +80 and later cut away to impersonate the
    # moved +180 rear support.
    core = fuse_seq([
        front_station,
        wall,
        rear_station,
        front_support,
        crosshead,
        rear_support,
        backstop,
    ], 'RIGHT structural core')

    # Re-cut both pin bores after structural fusions so no later wall can close
    # them. This is a final feature operation, not a source-code fixup.
    for xc in CLAMP_X:
        core = core.cut(cyl_x(PIN_HOLE_D / 2.0, 40.0, xc - 20.0, PIN_Y, PIN_Z)).removeSplitter()
    require_single(core, 'RIGHT structural core after pin bores')
    return core


def mirror_x(sh):
    out = sh.copy()
    out.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))
    require_single(out, 'mirrored LEFT structural core')
    return out


def export_shape(name, sh):
    sh.exportStep(os.path.join(OUT, name + '.step'))
    doc = App.newDocument(name)
    obj = doc.addObject('Part::Feature', name)
    obj.Shape = sh
    doc.recompute()
    doc.saveAs(os.path.join(OUT, name + '.FCStd'))
    Mesh.export([obj], os.path.join(OUT, name + '.stl'))
    App.closeDocument(doc.Name)


RIGHT = make_right_core()
LEFT = mirror_x(RIGHT)

# -----------------------------------------------------------------------------
# Hard checks -- fail early, before this architecture grows further.
# -----------------------------------------------------------------------------
failures = []

if abs(CLAMP_SPACING - 160.0) > 1e-9:
    failures.append('Clamp centre spacing is not 160 mm')
if abs(FRONT_CLAMP_PHYS_X - 39.0) > 1e-9:
    failures.append('Front clamp physical centre is not 39 mm')
if abs(REAR_CLAMP_PHYS_X - 199.0) > 1e-9:
    failures.append('Rear clamp physical centre is not 199 mm')
if abs(BACKSTOP_PHYS_X0 - 249.0) > 1e-9 or abs(BACKSTOP_PHYS_X1 - 299.0) > 1e-9:
    failures.append('Backstop physical range is not 249..299 mm')
if abs(REAR_SUPPORT_PHYS_X - 299.0) > 1e-9:
    failures.append('Rear support physical centre is not 299 mm')

for side, sh in (('RIGHT', RIGHT), ('LEFT', LEFT)):
    require_single(sh, side)
    if sh.BoundBox.XLength > INDX_X_MAX + 1e-6:
        failures.append(f'{side} exceeds INDX X: {sh.BoundBox.XLength:.3f} mm')
    if sh.BoundBox.XLength > V60_X_TARGET_MAX + 1e-6:
        failures.append(f'{side} exceeds v60 X reserve target: {sh.BoundBox.XLength:.3f} mm')
    if sh.BoundBox.YLength > INDX_Y_MAX + 1e-6:
        failures.append(f'{side} exceeds INDX Y: {sh.BoundBox.YLength:.3f} mm')

# Exact handedness at BREP level: mirror LEFT back and compare occupied volume.
LEFT_BACK = mirror_x(LEFT)
common_vol = RIGHT.common(LEFT_BACK).Volume
mirror_delta = abs(RIGHT.Volume + LEFT_BACK.Volume - 2.0 * common_vol)
if abs(RIGHT.Volume - LEFT.Volume) > 1e-5:
    failures.append('LEFT/RIGHT volumes differ')
if mirror_delta > 1e-4:
    failures.append(f'LEFT is not exact X mirror of RIGHT, delta={mirror_delta:.6f} mm3')

# Real rack tube must have clearance through both clamp stations/wall.
tube = cyl_x(RACK_R, 240.0, -120.0, 0.0, 0.0)
tube_common = RIGHT.common(tube).Volume
if tube_common > 1e-4:
    failures.append(f'RIGHT structural core intersects real rack tube by {tube_common:.6f} mm3')

# Moved rear support is above the tube and must be genuinely connected to both
# the rectangular backstop bridge and the crosshead.
rear_support_ref = make_i_beam_y(REAR_SUPPORT_X, 0.0, ARM_Y1)
backstop_ref = make_backstop()
crosshead_ref = make_crosshead()
support_backstop_common = rear_support_ref.common(backstop_ref).Volume
support_crosshead_common = rear_support_ref.common(crosshead_ref).Volume
if support_backstop_common < 500.0:
    failures.append('Moved rear support lacks substantial backstop overlap')
if support_crosshead_common < 300.0:
    failures.append('Moved rear support lacks substantial crosshead overlap')

V = {
    'version': 'v60',
    'stage': 'clean_structural_core',
    'freecad_version': '.'.join(App.Version()[:3]),
    'architecture': 'direct geometry; no apply_v60 source-rewriting patches',
    'datums': {
        'rack_tube_diameter_mm': RACK_D,
        'rack_center_distance_mm': RACK_CTC,
        'clamp_centres_local_x_mm': list(CLAMP_X),
        'clamp_spacing_mm': CLAMP_SPACING,
        'front_clamp_physical_x_mm': FRONT_CLAMP_PHYS_X,
        'rear_clamp_physical_x_mm': REAR_CLAMP_PHYS_X,
        'backstop_local_x_mm': [BACKSTOP_X0, BACKSTOP_X1],
        'backstop_physical_x_mm': [BACKSTOP_PHYS_X0, BACKSTOP_PHYS_X1],
        'rear_support_local_x_mm': REAR_SUPPORT_X,
        'rear_support_physical_x_mm': REAR_SUPPORT_PHYS_X,
        'indx_build_xy_mm': [INDX_X_MAX, INDX_Y_MAX],
        'v60_x_target_max_mm': V60_X_TARGET_MAX,
    },
    'geometry': {
        'right_bbox_mm': [round(RIGHT.BoundBox.XLength, 3), round(RIGHT.BoundBox.YLength, 3), round(RIGHT.BoundBox.ZLength, 3)],
        'left_bbox_mm': [round(LEFT.BoundBox.XLength, 3), round(LEFT.BoundBox.YLength, 3), round(LEFT.BoundBox.ZLength, 3)],
        'right_bounds_x_mm': [round(RIGHT.BoundBox.XMin, 3), round(RIGHT.BoundBox.XMax, 3)],
        'left_bounds_x_mm': [round(LEFT.BoundBox.XMin, 3), round(LEFT.BoundBox.XMax, 3)],
        'right_volume_mm3': round(RIGHT.Volume, 3),
        'left_volume_mm3': round(LEFT.Volume, 3),
        'mirror_delta_mm3': round(mirror_delta, 9),
        'rack_tube_common_mm3': round(tube_common, 9),
        'rear_support_backstop_common_mm3': round(support_backstop_common, 3),
        'rear_support_crosshead_common_mm3': round(support_crosshead_common, 3),
    },
    'failures': failures,
}

with open(os.path.join(OUT, 'VALIDATION_v60.json'), 'w', encoding='utf-8') as f:
    json.dump(V, f, indent=2)

if failures:
    print(json.dumps(V, indent=2))
    raise SystemExit('V60 HARD CHECKS FAILED: ' + ' | '.join(failures))

export_shape('eurobox_v60_base_right_core', RIGHT)
export_shape('eurobox_v60_base_left_core', LEFT)

with open(os.path.join(OUT, 'README_BUILD_v60.txt'), 'w', encoding='utf-8') as f:
    f.write('Eurobox v60 clean rebuild.\n')
    f.write('This first gate is the final rack-side structural core: direct RIGHT construction, LEFT exact X mirror.\n')
    f.write('No v50 source-rewriting fixups are executed.\n')

print(json.dumps(V, indent=2))
