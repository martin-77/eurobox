import json
import math
import os

import FreeCAD as App
import Part

import build_v60 as C
import build_v60_full as F

# ---------------------------------------------------------------------------
# v60 rack closure: M4x30 hand screw + captive metal M4 nut in the fixed Upper.
#
# The original v60 side-loaded M4 nut is deliberately rebuilt here.  The fixed
# Upper remains integral with BASE.  A real M4 nut sits on a solid annular floor
# and is prevented from lifting/tilting while the screw starts by a separately
# printable threaded retainer screwed down from the top.  The retainer is hollow
# throughout so excess M4 screw length can pass freely above the nut.
# ---------------------------------------------------------------------------

RACK_SCREW_LENGTH = 30.0
RACK_SCREW_D = 4.0
RACK_SCREW_CLEAR_D = 5.0

# Measured user hardware: approx. 6.81 mm across flats, <=7.8 mm across corners.
# 6.90 mm AF is intentionally a close printed fit.
RACK_NUT_AF = 6.90
RACK_NUT_NOMINAL_AF = 6.81
RACK_NUT_MAX_CORNER = 7.80
RACK_NUT_H = 3.60
RACK_NUT_Z0 = 3.00
RACK_NUT_Z1 = RACK_NUT_Z0 + RACK_NUT_H

# Coarse printed service thread for the hollow nut retainer.  This is not the
# M4 load thread; it is only an axial anti-lift retainer and is rarely cycled.
RETAINER_PITCH = 2.0
RETAINER_MALE_CORE_R = 5.00
RETAINER_MALE_MAJOR_R = 5.78
RETAINER_FEMALE_CORE_R = 5.20
RETAINER_FEMALE_MAJOR_R = 5.98
RETAINER_THREAD_Z0 = 7.00
RETAINER_THREAD_LEN = 11.00
RETAINER_LEN = 10.50
RETAINER_BORE_D = 5.00
RETAINER_NOSE_OD = 7.60
RETAINER_NOSE_LEN = 1.00
RETAINER_NOSE_CLEAR_D = 8.10
RETAINER_TOOL_HOLE_D = 2.20
RETAINER_TOOL_HOLE_R = 3.75
RETAINER_TOOL_HOLE_DEPTH = 3.00

# Restore the old side-loading slot before cutting the new top-service pocket.
# The local closure boss is intentionally massive; BASE is not a wear part.
BOSS_X = 20.0
BOSS_Y = 20.0
BOSS_Z0 = 0.0
BOSS_Z1 = 18.0
RESTORE_X = 39.0
RESTORE_Y = 9.0
RESTORE_Z0 = 2.70
RESTORE_Z1 = 7.20

# Lower closure tongue: 7 mm structural thickness, no length-driven thinning.
LOWER_PAD_X = F.LOWER_FORK_W
LOWER_PAD_Y0 = F.RACK_CLOSURE_PAD_Y0
LOWER_PAD_Y1 = F.RACK_CLOSURE_PAD_Y1
LOWER_PAD_Z0 = -10.50
LOWER_PAD_Z1 = -3.50
LOWER_CLEAR_D = 5.0

# Hand knob.  The M4 nut is inserted from the Upper-facing side and can be
# glued together with the screw.  Glue is only anti-loosening: axial load is
# screw head -> knob material -> metal nut -> M4 screw.
KNOB_R = 13.0
KNOB_H = 8.0
KNOB_NUT_AF = 6.90
KNOB_NUT_H = 3.60
KNOB_NUT_Z0 = 4.40
KNOB_BORE_D = 4.60


def stage(msg):
    print('V60_RACK_CLOSURE ' + msg, flush=True)


def ngon_z(n, radius, height, z0=0.0):
    pts = [
        App.Vector(
            radius * math.cos(2.0 * math.pi * i / n),
            radius * math.sin(2.0 * math.pi * i / n),
            z0,
        )
        for i in range(n)
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0, 0, height))


def translated(shape, x=0.0, y=0.0, z=0.0):
    q = shape.copy()
    q.translate(App.Vector(x, y, z))
    return q


stage('compile coarse retainer threads')
ret_male_scad = os.path.join(C.OUT, 'v60_rack_nut_retainer_male.scad')
ret_female_scad = os.path.join(C.OUT, 'v60_rack_nut_retainer_female.scad')
F.write_thread_scad(
    ret_male_scad,
    RETAINER_MALE_CORE_R,
    RETAINER_MALE_MAJOR_R,
    RETAINER_PITCH,
    RETAINER_LEN,
    0.76,
    0.30,
)
F.write_thread_scad(
    ret_female_scad,
    RETAINER_FEMALE_CORE_R,
    RETAINER_FEMALE_MAJOR_R,
    RETAINER_PITCH,
    RETAINER_THREAD_LEN,
    0.92,
    0.46,
)
RETAINER_THREAD = F.import_scad_shape(ret_male_scad).common(
    Part.makeCylinder(RETAINER_MALE_MAJOR_R + 0.03, RETAINER_LEN)
).removeSplitter()
FEMALE_THREAD_CUTTER = F.import_scad_shape(ret_female_scad).common(
    Part.makeCylinder(RETAINER_FEMALE_MAJOR_R + 0.03, RETAINER_THREAD_LEN)
).removeSplitter()

# Hollow printed retainer.  A narrow annular nose reaches down into the hex
# pocket and bears on the metal nut; the larger threaded body can therefore be
# adjusted axially without needing a fixed head/shoulder.  Two top pin holes are
# simple service-tool features and do not obstruct the central M4 overrun bore.
retainer_nose = Part.makeCylinder(
    RETAINER_NOSE_OD / 2.0,
    RETAINER_NOSE_LEN,
    App.Vector(0, 0, -RETAINER_NOSE_LEN),
)
RACK_NUT_RETAINER = RETAINER_THREAD.fuse(retainer_nose).removeSplitter()
RACK_NUT_RETAINER = RACK_NUT_RETAINER.cut(
    Part.makeCylinder(RETAINER_BORE_D / 2.0, RETAINER_LEN + RETAINER_NOSE_LEN + 0.4, App.Vector(0, 0, -RETAINER_NOSE_LEN - 0.2))
).removeSplitter()
for sx in (-RETAINER_TOOL_HOLE_R, RETAINER_TOOL_HOLE_R):
    RACK_NUT_RETAINER = RACK_NUT_RETAINER.cut(
        Part.makeCylinder(
            RETAINER_TOOL_HOLE_D / 2.0,
            RETAINER_TOOL_HOLE_DEPTH + 0.2,
            App.Vector(sx, 0, RETAINER_LEN - RETAINER_TOOL_HOLE_DEPTH),
        )
    ).removeSplitter()
C.require_single(RACK_NUT_RETAINER, 'rack-nut-retainer')

stage('rebuild fixed Upper closure stations')
RIGHT = F.RIGHT_FULL
for xc in C.CLAMP_X:
    # Refill the previous side-loading slot/pocket completely, then add a local
    # 20x20 mm boss so the new coarse retainer thread has >=4 mm nominal wall.
    restore = C.box(
        xc - RESTORE_X / 2.0,
        C.RACK_CLOSURE_Y - RESTORE_Y / 2.0,
        RESTORE_Z0,
        RESTORE_X,
        RESTORE_Y,
        RESTORE_Z1 - RESTORE_Z0,
    )
    boss = C.box(
        xc - BOSS_X / 2.0,
        C.RACK_CLOSURE_Y - BOSS_Y / 2.0,
        BOSS_Z0,
        BOSS_X,
        BOSS_Y,
        BOSS_Z1 - BOSS_Z0,
    )
    RIGHT = RIGHT.fuse(restore).fuse(boss).removeSplitter()

    # Preserve the real rack-tube saddle after adding material near y=0.
    RIGHT = RIGHT.cut(
        C.cyl_x(C.UPPER_SADDLE_R, 40.0, xc - 20.0, 0.0, 0.0)
    ).removeSplitter()

    # M4 overrun path is deliberately through-going into the hollow retainer.
    RIGHT = RIGHT.cut(
        Part.makeCylinder(
            RACK_SCREW_CLEAR_D / 2.0,
            21.0,
            App.Vector(xc, C.RACK_CLOSURE_Y, -1.0),
            App.Vector(0, 0, 1),
        )
    ).removeSplitter()

    # Real metal M4 nut: close 6.90 mm AF pocket, entered from above before the
    # retainer is screwed in.  It rests on the annular floor at Z=3 mm.
    nut_cut = F.hex_z(RACK_NUT_AF, RACK_NUT_H, RACK_NUT_Z0)
    nut_cut.translate(App.Vector(xc, C.RACK_CLOSURE_Y, 0.0))
    RIGHT = RIGHT.cut(nut_cut).removeSplitter()

    # Short straight relief lets the retainer nose descend onto the nut.
    RIGHT = RIGHT.cut(
        Part.makeCylinder(
            RETAINER_NOSE_CLEAR_D / 2.0,
            1.60,
            App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_Z1 - 0.40),
            App.Vector(0, 0, 1),
        )
    ).removeSplitter()

    female = FEMALE_THREAD_CUTTER.copy()
    female.translate(App.Vector(xc, C.RACK_CLOSURE_Y, RETAINER_THREAD_Z0))
    RIGHT = RIGHT.cut(female).removeSplitter()

C.require_single(RIGHT, 'RIGHT base with top-loaded captive-nut retainers')
LEFT = C.mirror_x(RIGHT)
C.require_single(LEFT, 'LEFT base with top-loaded captive-nut retainers')

stage('thicken Lower closure tongue')
LOWER = F.LOWER.fuse(
    C.box(
        -LOWER_PAD_X / 2.0,
        LOWER_PAD_Y0,
        LOWER_PAD_Z0,
        LOWER_PAD_X,
        LOWER_PAD_Y1 - LOWER_PAD_Y0,
        LOWER_PAD_Z1 - LOWER_PAD_Z0,
    )
).removeSplitter()
# Re-cut features that the thickening operation may have refilled.
LOWER = LOWER.cut(
    C.cyl_x(F.LOWER_SADDLE_R, F.LOWER_FORK_W + 2.0, -F.LOWER_FORK_OUTER_HALF_X - 1.0, 0.0, 0.0)
).removeSplitter()
LOWER = LOWER.cut(
    Part.makeCylinder(
        LOWER_CLEAR_D / 2.0,
        18.0,
        App.Vector(0.0, C.RACK_CLOSURE_Y, -15.5),
        App.Vector(0, 0, 1),
    )
).removeSplitter()
C.require_single(LOWER, '7mm Lower rack closure tongue')

stage('build rack hand knob')
RACK_HAND_KNOB = ngon_z(12, KNOB_R, KNOB_H)
RACK_HAND_KNOB = RACK_HAND_KNOB.cut(
    Part.makeCylinder(KNOB_BORE_D / 2.0, KNOB_NUT_Z0 + 0.2, App.Vector(0, 0, -0.1))
).removeSplitter()
knob_nut = F.hex_z(KNOB_NUT_AF, KNOB_NUT_H + 0.20, KNOB_NUT_Z0)
RACK_HAND_KNOB = RACK_HAND_KNOB.cut(knob_nut).removeSplitter()
C.require_single(RACK_HAND_KNOB, 'rack-hand-knob')

stage('hard validation')
failures = []

def fail(msg):
    failures.append(msg)

# Exact handed construction.
left_back = C.mirror_x(LEFT)
mirror_delta = abs(RIGHT.Volume - left_back.Volume)
if mirror_delta > 1e-4:
    fail(f'new rack-closure bases are not exact mirrors: {mirror_delta:.6f} mm3')

# The boss must still leave the measured rack tube completely clear.
tube = C.cyl_x(C.RACK_R, 400.0, -200.0, 0.0, 0.0)
tube_common = RIGHT.common(tube).Volume
if tube_common > 1e-4:
    fail(f'new rack-closure boss intersects rack tube: {tube_common:.6f} mm3')

# Nominal real nut must fit in the close hex pocket and be radially trapped.
for xc in C.CLAMP_X:
    nut_proxy = F.hex_z(RACK_NUT_NOMINAL_AF, 3.20, RACK_NUT_Z0)
    nut_proxy.translate(App.Vector(xc, C.RACK_CLOSURE_Y, 0.0))
    nut_blocked = RIGHT.common(nut_proxy).Volume
    if nut_blocked > 1e-4:
        fail(f'6.81 mm AF M4 nut proxy blocked at X={xc}: {nut_blocked:.6f} mm3')

    # Solid annular floor under the nut must be present outside the M4 bore.
    floor_outer = Part.makeCylinder(3.75, 0.40, App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_Z0 - 0.40))
    floor_inner = Part.makeCylinder(RACK_SCREW_CLEAR_D / 2.0, 0.40, App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_Z0 - 0.40))
    floor_ring = floor_outer.cut(floor_inner)
    floor_fraction = RIGHT.common(floor_ring).Volume / floor_ring.Volume
    if floor_fraction < 0.92:
        fail(f'M4 nut support floor too weak at X={xc}: {floor_fraction:.4f}')

    # At the thread-aligned nominal position the separately printed retainer
    # must enter the BASE without gross collision.  Small tessellation/OCC
    # contact noise is tolerated because the male/female thread has clearance.
    ret = RACK_NUT_RETAINER.copy()
    ret.translate(App.Vector(xc, C.RACK_CLOSURE_Y, RETAINER_THREAD_Z0))
    ret_common = RIGHT.common(ret).Volume
    if ret_common > 1.5:
        fail(f'rack nut retainer does not fit female service thread X={xc}: {ret_common:.6f} mm3')

# Lower remains collision-free through open and positive tightening travel.
lower_sweep = []
for xc in C.CLAMP_X:
    for deg in (0, -15, -30, -45, -60, -75, -90, 0.5, 1.0, 2.0, 3.0):
        lo = LOWER.copy()
        lo.rotate(App.Vector(0, C.PIN_Y, C.PIN_Z), App.Vector(1, 0, 0), deg)
        lo.translate(App.Vector(xc, 0, 0))
        common = RIGHT.common(lo).Volume
        lower_sweep.append({'x_mm': xc, 'deg': deg, 'base_common_mm3': round(common, 6)})
        if common > 1e-4:
            fail(f'7mm Lower collides with BASE X={xc} deg={deg}: {common:.6f} mm3')

# M4x30 length budget with the planned nut-in-knob construction.  A 4.4 mm
# plastic web plus a 3.2 mm M4 nut still leaves >22 mm above the knob, enough to
# cross the 7 mm Lower, the closure gap and fully traverse the Upper M4 nut.
knob_nut_effective_h = 3.20
usable_above_knob = RACK_SCREW_LENGTH - KNOB_NUT_Z0 - knob_nut_effective_h
screw_tip_z = LOWER_PAD_Z0 + usable_above_knob
upper_nut_required_tip_z = RACK_NUT_Z0 + 3.20
if usable_above_knob < 22.0:
    fail(f'M4x30 usable length above knob unexpectedly short: {usable_above_knob:.3f} mm')
if screw_tip_z < upper_nut_required_tip_z:
    fail(f'M4x30 cannot fully traverse Upper M4 nut: tip Z={screw_tip_z:.3f}')

# Central overrun bore must be clear above the metal nut, so a longer screw does
# not bottom out in BASE or in the printed retainer.
for xc in C.CLAMP_X:
    overrun_probe = Part.makeCylinder(
        2.0,
        11.0,
        App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_Z1),
        App.Vector(0, 0, 1),
    )
    overrun_common = RIGHT.common(overrun_probe).Volume
    if overrun_common > 1e-4:
        fail(f'M4 overrun path blocked above Upper nut X={xc}: {overrun_common:.6f} mm3')

if failures:
    raise RuntimeError('V60 RACK CLOSURE HARD CHECKS FAILED: ' + ' | '.join(failures))

stage('export revised canonical parts')
F.RIGHT_FULL = RIGHT
F.LEFT_FULL = LEFT
F.LOWER = LOWER
C.export_shape('eurobox_v60_base_right', RIGHT)
C.export_shape('eurobox_v60_base_left', LEFT)
C.export_shape('eurobox_v60_rack_lower', LOWER)
C.export_shape('eurobox_v60_rack_nut_retainer', RACK_NUT_RETAINER)
C.export_shape('eurobox_v60_rack_hand_knob', RACK_HAND_KNOB)

stage('rewrite assembly with revised closure hardware')
assembly_path = os.path.join(C.OUT, 'eurobox_v60_assembly.FCStd')
try:
    if App.ActiveDocument:
        App.closeDocument(App.ActiveDocument.Name)
except Exception:
    pass

doc = App.newDocument('Eurobox_v60_assembly')

def add_obj(name, shape):
    obj = doc.addObject('Part::Feature', name)
    obj.Shape = shape
    return obj

RY = C.RACK_CTC / 2.0
LY = -C.RACK_CTC / 2.0
rb = RIGHT.copy(); rb.translate(App.Vector(0, RY, 0)); add_obj('RIGHT_base', rb)
rp = F.PLATE.copy(); rp.translate(App.Vector(0, RY, 0)); add_obj('RIGHT_plate', rp)
for xc in C.CLAMP_X:
    lo = LOWER.copy(); lo.translate(App.Vector(xc, RY, 0)); add_obj('RIGHT_lower_' + str(int(xc)), lo)
    ret = RACK_NUT_RETAINER.copy(); ret.translate(App.Vector(xc, RY + C.RACK_CLOSURE_Y, RETAINER_THREAD_Z0)); add_obj('RIGHT_rack_nut_retainer_' + str(int(xc)), ret)
    knob = RACK_HAND_KNOB.copy(); knob.translate(App.Vector(xc, RY + C.RACK_CLOSURE_Y, LOWER_PAD_Z0 - KNOB_H)); add_obj('RIGHT_rack_hand_knob_' + str(int(xc)), knob)
for sx in F.SPINDLE_X:
    sp = F.SPINDLE.copy(); sp.translate(App.Vector(sx, RY + F.PLATE_SPINDLE_Y, F.SPINDLE_Z)); add_obj('RIGHT_spindle_' + str(int(sx)), sp)

def left_transform(shape):
    q = shape.copy()
    q.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180)
    q.translate(App.Vector(0, LY, 0))
    return q

add_obj('LEFT_base', left_transform(LEFT))
add_obj('LEFT_plate', left_transform(F.PLATE))
for xc in C.CLAMP_X:
    lo = LOWER.copy(); lo.translate(App.Vector(xc, 0, 0)); add_obj('LEFT_lower_' + str(int(xc)), left_transform(lo))
    ret = RACK_NUT_RETAINER.copy(); ret.translate(App.Vector(xc, C.RACK_CLOSURE_Y, RETAINER_THREAD_Z0)); add_obj('LEFT_rack_nut_retainer_' + str(int(xc)), left_transform(ret))
    knob = RACK_HAND_KNOB.copy(); knob.translate(App.Vector(xc, C.RACK_CLOSURE_Y, LOWER_PAD_Z0 - KNOB_H)); add_obj('LEFT_rack_hand_knob_' + str(int(xc)), left_transform(knob))
for sx in F.SPINDLE_X:
    sp = F.SPINDLE.copy(); sp.translate(App.Vector(sx, F.PLATE_SPINDLE_Y, F.SPINDLE_Z)); add_obj('LEFT_spindle_' + str(int(sx)), left_transform(sp))
add_obj('REF_right_rack_tube', C.cyl_x(C.RACK_R, 400, -200, RY, 0))
add_obj('REF_left_rack_tube', C.cyl_x(C.RACK_R, 400, -200, LY, 0))
doc.recompute()
doc.saveAs(assembly_path)
App.closeDocument(doc.Name)

stage('update full validation report')
validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as f:
    validation = json.load(f)
validation['stage'] = 'full_direct_mechanism_top_retained_m4x30_rack_closure'
validation['architecture'] = (
    'continuous BASE/Upper + hinged replaceable Lower; M4x30 hand screw into '
    'top-loaded replaceable metal M4 nut retained by hollow 12x2 printed service plug'
)
validation['base']['right_bbox_mm'] = [round(RIGHT.BoundBox.XLength, 3), round(RIGHT.BoundBox.YLength, 3), round(RIGHT.BoundBox.ZLength, 3)]
validation['base']['left_bbox_mm'] = [round(LEFT.BoundBox.XLength, 3), round(LEFT.BoundBox.YLength, 3), round(LEFT.BoundBox.ZLength, 3)]
validation['base']['mirror_delta_mm3'] = round(mirror_delta, 9)
validation['rack']['joint'] = 'integral fixed Upper + hinged replaceable Lower + top-retained metal M4 closure nut'
validation['rack']['lower_fork_outer_width_mm'] = round(F.LOWER_FORK_W, 3)
validation['rack']['m4_closure_checks'] = lower_sweep
validation['rack']['m4_closure'] = {
    'mode': 'M4x30 hand screw from below into top-loaded captive metal M4 nut',
    'screw_length_mm': RACK_SCREW_LENGTH,
    'lower_clearance_d_mm': LOWER_CLEAR_D,
    'lower_closure_thickness_mm': LOWER_PAD_Z1 - LOWER_PAD_Z0,
    'upper_nut_pocket_af_mm': RACK_NUT_AF,
    'measured_nut_af_mm': RACK_NUT_NOMINAL_AF,
    'measured_nut_max_corner_mm': RACK_NUT_MAX_CORNER,
    'upper_nut_pocket_height_mm': RACK_NUT_H,
    'upper_nut_floor_z_mm': RACK_NUT_Z0,
    'retainer_thread': 'printed coarse 12x2-class service thread',
    'retainer_pitch_mm': RETAINER_PITCH,
    'retainer_male_major_d_mm': 2.0 * RETAINER_MALE_MAJOR_R,
    'retainer_female_major_d_mm': 2.0 * RETAINER_FEMALE_MAJOR_R,
    'retainer_length_mm': RETAINER_LEN,
    'retainer_through_bore_d_mm': RETAINER_BORE_D,
    'retainer_adjustable_from_top': True,
    'screw_overrun_path': 'open through metal nut and hollow retainer',
    'knob_nut_pocket_af_mm': KNOB_NUT_AF,
    'knob_plastic_web_mm': KNOB_NUT_Z0,
    'usable_screw_length_above_knob_mm': round(usable_above_knob, 3),
    'calculated_screw_tip_z_mm': round(screw_tip_z, 3),
    'base_tube_common_mm3': round(tube_common, 9),
}
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2)

readme_path = os.path.join(C.OUT, 'README_BUILD_v60_full.txt')
with open(readme_path, 'a', encoding='utf-8') as f:
    f.write('\nRack closure revision: M4x30 hand screw, 7 mm Lower tongue, top-loaded 6.90 mm AF M4 nut pocket, hollow screw-in printed nut retainer, through overrun bore.\n')

stage('complete')
