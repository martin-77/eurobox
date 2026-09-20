import json
import math
import os

import FreeCAD as App
import Part

import build_v60 as C
import build_v60_full as F
import v60_rack_hand_knob as K

# ---------------------------------------------------------------------------
# v60 rack closure: M4x30 hand screw + captive metal M4 nut in the fixed Upper.
#
# The closure housing is integrated into the rack-side carrier envelope.  On
# the closure side of each saddle the BASE now keeps the same continuous upper
# and lower carrier planes as the surrounding carrier instead of dropping a
# local bridge/boss below it.  The real M4 nut therefore sits higher, and the
# hollow printed retainer is correspondingly taller so it remains serviceable
# from the top surface while still allowing screw overrun above the metal nut.
# ---------------------------------------------------------------------------

RACK_SCREW_LENGTH = 30.0
RACK_SCREW_D = 4.0
# 4.60 mm matches the existing fixed-BASE M4 clearance datum and leaves more
# PETG under the 6.90 mm AF nut than the former Ø5.0 bore.
RACK_SCREW_CLEAR_D = 4.60

# Carrier envelope at the rack-side BASE.  The top plane is already the box
# support plane; the lower carrier plane is the 30 mm holm datum.  The rack tube
# itself occupies Z around zero, so the lower plane must remain above the tube.
CARRIER_BOTTOM_PLANE_Z = C.ARM_BOTTOM_Z
CARRIER_TOP_PLANE_Z = C.BOX_SUPPORT_Z
CLOSURE_RELIEF_Y0 = C.UPPER_SADDLE_R + 0.75
CLOSURE_RELIEF_Y1 = C.ARM_Y0 + 2.0
CLOSURE_RELIEF_X_HALF = C.FIXED_STATION_HALF_X

# Measured user hardware: approx. 6.81 mm across flats, <=7.8 mm across corners.
# 6.90 mm AF is intentionally a close printed fit.
RACK_NUT_AF = 6.90
RACK_NUT_NOMINAL_AF = 6.81
RACK_NUT_MAX_CORNER = 7.80
RACK_NUT_H = 3.60
# Keep the full 2.0 mm PETG floor under the metal nut.  The M4x30 length budget
# is recovered by moving this complete local nut station downward, not by
# thinning either the Lower or the hand knob.
RACK_NUT_FLOOR_T = 2.00
RACK_NUT_Z0 = 5.40
RACK_NUT_Z1 = RACK_NUT_Z0 + RACK_NUT_H
RACK_NUT_FLOOR_Z0 = RACK_NUT_Z0 - RACK_NUT_FLOOR_T

# Coarse printed service thread for the hollow nut retainer.  This is not the
# M4 load thread; it only traps the nut axially and is rarely cycled.  Its top
# ends 0.20 mm below the common carrier top plane so it never stands proud.
RETAINER_PITCH = 3.0
RETAINER_MALE_CORE_R = 5.00
RETAINER_MALE_MAJOR_R = 6.00
RETAINER_FEMALE_CORE_R = 5.25
RETAINER_FEMALE_MAJOR_R = 6.25
RETAINER_NOSE_OD = 7.60
# Give the retainer a 2 mm smooth nose above the complete metal-nut pocket.
# This creates enough axial room for a gradual printable female-bore transition
# without cutting away the nut's hex flats.
RETAINER_NOSE_LEN = 2.00
RETAINER_THREAD_Z0 = RACK_NUT_Z1 + RETAINER_NOSE_LEN
RETAINER_LEN = CARRIER_TOP_PLANE_Z - RETAINER_THREAD_Z0 - 0.20
RETAINER_THREAD_LEN = CARRIER_TOP_PLANE_Z - RETAINER_THREAD_Z0 + 1.00
RETAINER_BORE_D = 5.00
RETAINER_NOSE_CLEAR_D = 8.10
RETAINER_TOOL_HOLE_D = 2.20
RETAINER_TOOL_HOLE_R = 3.75
RETAINER_TOOL_HOLE_DEPTH = 3.00

# Full-height local closure column.  It shares both outside Z planes with the
# rack-side carrier; there is no local 0..18 mm step any more.
BOSS_X = 20.0
BOSS_Y = 20.0
BOSS_Z0 = RACK_NUT_FLOOR_Z0
BOSS_Z1 = CARRIER_TOP_PLANE_Z

# Lower closure tongue keeps the proven upper face at Z=-1.5 but now extends
# down to the existing Lower shell floor at Z=-14.5.  No saddle material is
# removed; the tongue simply gains 6 mm and becomes part of one flat print bed.
LOWER_PAD_X = F.LOWER_FORK_W
LOWER_PAD_Y0 = F.RACK_CLOSURE_PAD_Y0
LOWER_PAD_Y1 = F.RACK_CLOSURE_PAD_Y1
LOWER_PAD_Z0 = -14.50
LOWER_PAD_Z1 = -1.50
LOWER_CLEAR_D = 5.0

# Hand-knob geometry lives in its own component module so knob-only work no
# longer forces the BASE, rack-retainer and final assembly through the full CI.
KNOB_R = K.KNOB_R
KNOB_H = K.KNOB_H
KNOB_NUT_AF = K.KNOB_NUT_AF
KNOB_NUT_H = K.KNOB_NUT_H
KNOB_NUT_Z0 = K.KNOB_NUT_Z0
KNOB_BORE_D = K.KNOB_BORE_D


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


# Structural-only rack closure. The printable 12x3 retainer pair is
# generated exactly once by apply_v60_retainer_thread_final.py.

stage('rebuild fixed Upper closure stations on common carrier planes')
RIGHT = F.RIGHT_FULL
for xc in C.CLAMP_X:
    # Remove the historical closure-side bridge below the carrier lower plane.
    # Start outside the measured rack saddle so the actual tube-bearing geometry
    # and rear hinge remain untouched.  This eliminates the visible/structural
    # lower step without cutting into the saddle around the 12.42 mm rack tube.
    relief = C.box(
        xc - CLOSURE_RELIEF_X_HALF,
        CLOSURE_RELIEF_Y0,
        -0.20,
        2.0 * CLOSURE_RELIEF_X_HALF,
        CLOSURE_RELIEF_Y1 - CLOSURE_RELIEF_Y0,
        CARRIER_BOTTOM_PLANE_Z + 0.20,
    )
    RIGHT = RIGHT.cut(relief).removeSplitter()

    # The new closure column is exactly bounded by the same lower and upper Z
    # planes as the surrounding carrier.
    boss = C.box(
        xc - BOSS_X / 2.0,
        C.RACK_CLOSURE_Y - BOSS_Y / 2.0,
        BOSS_Z0,
        BOSS_X,
        BOSS_Y,
        BOSS_Z1 - BOSS_Z0,
    )
    RIGHT = RIGHT.fuse(boss).removeSplitter()

    # Preserve the real rack-tube saddle after adding material toward +Y.
    RIGHT = RIGHT.cut(
        C.cyl_x(C.UPPER_SADDLE_R, 40.0, xc - 20.0, 0.0, 0.0)
    ).removeSplitter()

    # M4 overrun path is deliberately through-going from below the common lower
    # surface right through the top service opening.
    RIGHT = RIGHT.cut(
        Part.makeCylinder(
            RACK_SCREW_CLEAR_D / 2.0,
            CARRIER_TOP_PLANE_Z - (BOSS_Z0 - 1.0) + 1.0,
            App.Vector(xc, C.RACK_CLOSURE_Y, BOSS_Z0 - 1.0),
            App.Vector(0, 0, 1),
        )
    ).removeSplitter()

    # Real metal M4 nut: close 6.90 mm AF pocket with a 1.5 mm structural floor
    # above the common carrier underside.
    nut_cut = F.hex_z(RACK_NUT_AF, RACK_NUT_H, RACK_NUT_Z0)
    nut_cut.translate(App.Vector(xc, C.RACK_CLOSURE_Y, 0.0))
    RIGHT = RIGHT.cut(nut_cut).removeSplitter()

    # Short straight relief lets the retainer nose descend onto the nut.
    RIGHT = RIGHT.cut(
        Part.makeCylinder(
            RETAINER_NOSE_CLEAR_D / 2.0,
            RETAINER_NOSE_LEN + 0.40,
            App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_Z1),
            App.Vector(0, 0, 1),
        )
    ).removeSplitter()

C.require_single(RIGHT, 'RIGHT base with flush carrier closure stations')
LEFT = C.mirror_x(RIGHT)
C.require_single(LEFT, 'LEFT base with flush carrier closure stations')

stage('extend Lower closure tongue to common -14.5mm print floor')
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
        App.Vector(0.0, C.RACK_CLOSURE_Y, LOWER_PAD_Z0 - 1.0),
        App.Vector(0, 0, 1),
    )
).removeSplitter()
C.require_single(LOWER, 'common-floor Lower rack closure tongue')

stage('build rack hand knob')
RACK_HAND_KNOB = K.build_rack_hand_knob()
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

# The measured rack tube must remain completely free.
tube = C.cyl_x(C.RACK_R, 400.0, -200.0, 0.0, 0.0)
tube_common = RIGHT.common(tube).Volume
if tube_common > 1e-4:
    fail(f'flush rack-closure carrier intersects rack tube: {tube_common:.6f} mm3')

# The intentionally lowered nut station is local only.  Below the normal
# carrier plane, material may exist inside the 20 mm closure boss but must not
# regrow the old full-width bridge on either side.
for xc in C.CLAMP_X:
    for side in (-1.0,1.0):
        x0 = xc + side*(BOSS_X/2.0 + 0.50)
        if side < 0:
            x0 -= 4.0
        side_probe = C.box(
            x0,
            CLOSURE_RELIEF_Y0 + 0.20,
            BOSS_Z0,
            4.0,
            min(BOSS_Y-0.40,CLOSURE_RELIEF_Y1-CLOSURE_RELIEF_Y0-0.40),
            CARRIER_BOTTOM_PLANE_Z-BOSS_Z0-0.02,
        )
        side_common=RIGHT.common(side_probe).Volume
        if side_common>1e-4:
            fail(
                f'lowered rack-nut boss spread outside local station '
                f'X={xc} side={side}: {side_common:.6f} mm3'
            )

    # The normal carrier lower plane must remain structural outside the intentional
    # lowered retainer/nose service opening.
    bottom_probe = C.box(
        xc - 9.0,
        C.RACK_CLOSURE_Y - 8.0,
        CARRIER_BOTTOM_PLANE_Z,
        18.0,
        16.0,
        0.40,
    ).cut(
        Part.makeCylinder(
            RETAINER_FEMALE_CORE_R + 0.20,
            0.60,
            App.Vector(xc, C.RACK_CLOSURE_Y, CARRIER_BOTTOM_PLANE_Z - 0.10),
        )
    )
    bottom_fraction = RIGHT.common(bottom_probe).Volume / bottom_probe.Volume
    if bottom_fraction < 0.985:
        fail(f'common carrier bottom surface incomplete at X={xc}: {bottom_fraction:.4f}')

    # Same check at the common top plane, excluding the intentional retainer
    # service opening.
    top_probe = C.box(
        xc - 9.0,
        C.RACK_CLOSURE_Y - 8.0,
        CARRIER_TOP_PLANE_Z - 0.40,
        18.0,
        16.0,
        0.40,
    ).cut(
        Part.makeCylinder(
            RETAINER_FEMALE_MAJOR_R + 0.20,
            0.60,
            App.Vector(xc, C.RACK_CLOSURE_Y, CARRIER_TOP_PLANE_Z - 0.50),
        )
    )
    top_fraction = RIGHT.common(top_probe).Volume / top_probe.Volume
    if top_fraction < 0.985:
        fail(f'common carrier top surface incomplete at X={xc}: {top_fraction:.4f}')

# Nominal real nut must fit in the close hex pocket and be radially trapped.
for xc in C.CLAMP_X:
    nut_proxy = F.hex_z(RACK_NUT_NOMINAL_AF, 3.20, RACK_NUT_Z0)
    nut_proxy.translate(App.Vector(xc, C.RACK_CLOSURE_Y, 0.0))
    nut_blocked = RIGHT.common(nut_proxy).Volume
    if nut_blocked > 1e-4:
        fail(f'6.81 mm AF M4 nut proxy blocked at X={xc}: {nut_blocked:.6f} mm3')

    # Validate the COMPLETE load-bearing floor thickness under the nut flats,
    # not just a 0.40 mm witness skin.  The relevant outer radius is the 6.90 mm
    # AF nut inradius; the inner radius is the actual final screw clearance.
    floor_outer_r = RACK_NUT_AF / 2.0
    floor_inner_r = RACK_SCREW_CLEAR_D / 2.0
    floor_ring = Part.makeCylinder(
        floor_outer_r, RACK_NUT_FLOOR_T,
        App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_FLOOR_Z0),
    ).cut(
        Part.makeCylinder(
            floor_inner_r, RACK_NUT_FLOOR_T,
            App.Vector(xc, C.RACK_CLOSURE_Y, RACK_NUT_FLOOR_Z0),
        )
    )
    floor_fraction = RIGHT.common(floor_ring).Volume / floor_ring.Volume
    if floor_fraction < 0.985:
        fail(f'M4 nut full support floor incomplete at X={xc}: {floor_fraction:.4f}')


# The Lower must keep the original 8.35 mm material under the saddle while the
# tongue now reaches exactly the same -14.5 mm floor.
lower_shell_floor_z = F.LOWER.BoundBox.ZMin
lower_saddle_under_material = abs(lower_shell_floor_z) - F.LOWER_SADDLE_R
if abs(LOWER_PAD_Z0-lower_shell_floor_z)>1e-6:
    fail(
        f'Lower tongue does not share shell print floor: '
        f'{LOWER_PAD_Z0:.3f} vs {lower_shell_floor_z:.3f}'
    )
if lower_saddle_under_material < 8.0:
    fail(
        f'Lower lost structural material below rack saddle: '
        f'{lower_saddle_under_material:.3f} mm'
    )

tongue_floor_probe = C.box(
    -LOWER_PAD_X/2.0,
    LOWER_PAD_Y0,
    LOWER_PAD_Z0,
    LOWER_PAD_X,
    LOWER_PAD_Y1-LOWER_PAD_Y0,
    0.40,
).cut(
    Part.makeCylinder(
        LOWER_CLEAR_D/2.0+0.05,
        0.60,
        App.Vector(0.0,C.RACK_CLOSURE_Y,LOWER_PAD_Z0-0.10),
    )
)
tongue_floor_fraction = LOWER.common(tongue_floor_probe).Volume / tongue_floor_probe.Volume
if tongue_floor_fraction < 0.995:
    fail(f'Lower common print floor incomplete: {tongue_floor_fraction:.6f}')

retainer_top_z = RETAINER_THREAD_Z0 + RETAINER_LEN
if retainer_top_z > CARRIER_TOP_PLANE_Z + 1e-6:
    fail(f'rack nut retainer stands proud: top Z={retainer_top_z:.3f}')
if CARRIER_TOP_PLANE_Z - retainer_top_z > 0.35:
    fail(f'rack nut retainer sits too deep for top service: recess={CARRIER_TOP_PLANE_Z-retainer_top_z:.3f}')

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

# M4x30 length budget after raising both the Lower tongue and Upper nut.  The
# 3.2 mm knob web leaves enough free shank to traverse the real M4 nut fully.
knob_nut_effective_h = 3.20
usable_above_knob = RACK_SCREW_LENGTH - KNOB_NUT_Z0 - knob_nut_effective_h
screw_tip_z = LOWER_PAD_Z0 + usable_above_knob
upper_nut_required_tip_z = RACK_NUT_Z0 + 3.20
screw_overrun_margin = screw_tip_z - upper_nut_required_tip_z
if usable_above_knob < 23.0:
    fail(f'M4x30 usable length above knob unexpectedly short: {usable_above_knob:.3f} mm')
if screw_overrun_margin < 0.30:
    fail(
        f'M4x30 full-nut engagement margin too small: {screw_overrun_margin:.3f} mm '
        f'(tip Z={screw_tip_z:.3f}, nut proxy top={upper_nut_required_tip_z:.3f})'
    )

# Central overrun path must remain clear from the top of the real nut all the
# way to the common top plane.
for xc in C.CLAMP_X:
    overrun_probe = Part.makeCylinder(
        2.0,
        CARRIER_TOP_PLANE_Z - RACK_NUT_Z1 + 0.20,
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
LOWER_PRINT = LOWER.copy()
LOWER_PRINT.translate(App.Vector(0,0,-LOWER_PRINT.BoundBox.ZMin))
C.require_single(LOWER_PRINT,'common-floor natural-print final rack Lower')
C.export_shape('eurobox_v60_rack_lower', LOWER_PRINT)
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
validation['stage'] = 'full_direct_mechanism_flush_carrier_m4x30_rack_closure'
validation['architecture'] = (
    'continuous rack-side carrier + local lowered rack-nut boss + hinged replaceable Lower; '
    'M4x30 hand screw into lowered top-service metal M4 nut retained by tall hollow '
    '12x3 printed service plug'
)
validation['base']['right_bbox_mm'] = [round(RIGHT.BoundBox.XLength, 3), round(RIGHT.BoundBox.YLength, 3), round(RIGHT.BoundBox.ZLength, 3)]
validation['base']['left_bbox_mm'] = [round(LEFT.BoundBox.XLength, 3), round(LEFT.BoundBox.YLength, 3), round(LEFT.BoundBox.ZLength, 3)]
validation['base']['mirror_delta_mm3'] = round(mirror_delta, 9)
validation['rack']['joint'] = 'integral fixed Upper in common carrier envelope + hinged replaceable Lower + raised top-retained metal M4 closure nut'
validation['rack']['lower_fork_outer_width_mm'] = round(F.LOWER_FORK_W, 3)
validation['rack']['m4_closure_checks'] = lower_sweep
validation['rack']['lower_printability'] = {
    'mechanical_geometry': 'proven Lower shell unchanged; closure tongue extended downward only',
    'print_orientation': 'natural Z-up on common shell/tongue floor',
    'common_floor_z_mm': round(LOWER_PAD_Z0,3),
    'common_floor_material_fraction': round(tongue_floor_fraction,6),
    'saddle_under_material_mm': round(lower_saddle_under_material,3),
    'rack_saddle': 'upward-open semicircular seat',
    'pivot_pin_bore': 'small horizontal round self-closing opening',
    'pivot_print_feet': {
        'z_mm': [F.LOWER_PIVOT_FOOT_Z0,F.LOWER_PIVOT_FOOT_Z1],
        'y_mm': [F.LOWER_PIVOT_FOOT_Y0,F.LOWER_PIVOT_FOOT_Y1],
        'ear_thickness_mm': F.LOWER_FORK_EAR_T,
    },
    'm4_clearance': 'vertical',
    'm4_clearance_d_mm': LOWER_CLEAR_D,
    'functional_round_pivot_bore_preserved': True,
}
validation['rack']['m4_closure'] = {
    'mode': 'M4x30 hand screw from below into raised top-loaded captive metal M4 nut',
    'screw_length_mm': RACK_SCREW_LENGTH,
    'carrier_bottom_plane_z_mm': round(CARRIER_BOTTOM_PLANE_Z, 3),
    'carrier_top_plane_z_mm': round(CARRIER_TOP_PLANE_Z, 3),
    'lower_clearance_d_mm': LOWER_CLEAR_D,
    'lower_closure_thickness_mm': LOWER_PAD_Z1 - LOWER_PAD_Z0,
    'lower_shell_floor_z_mm': round(lower_shell_floor_z,3),
    'lower_saddle_under_material_mm': round(lower_saddle_under_material,3),
    'lower_closure_z_mm': [LOWER_PAD_Z0, LOWER_PAD_Z1],
    'upper_nut_pocket_af_mm': RACK_NUT_AF,
    'measured_nut_af_mm': RACK_NUT_NOMINAL_AF,
    'measured_nut_max_corner_mm': RACK_NUT_MAX_CORNER,
    'upper_nut_pocket_height_mm': RACK_NUT_H,
    'upper_nut_pocket_z_mm': [round(RACK_NUT_Z0,3),round(RACK_NUT_Z1,3)],
    'upper_nut_floor_z_mm': round(RACK_NUT_FLOOR_Z0,3),
    'upper_nut_floor_thickness_mm': RACK_NUT_FLOOR_T,
    'upper_nut_floor_screw_clear_d_mm': RACK_SCREW_CLEAR_D,
    'upper_nut_floor_radial_ligament_mm': round(RACK_NUT_AF/2.0-RACK_SCREW_CLEAR_D/2.0,3),
    'upper_nut_floor_material_fraction': round(floor_fraction,6),
    'retainer_thread': 'reserved structural seat; final 12x3 pair generated once in apply_v60_retainer_thread_final',
    'retainer_pitch_mm': RETAINER_PITCH,
    'retainer_length_mm': round(RETAINER_LEN, 3),
    'retainer_top_z_mm': round(retainer_top_z, 3),
    'retainer_top_recess_mm': round(CARRIER_TOP_PLANE_Z - retainer_top_z, 3),
    'retainer_through_bore_d_mm': RETAINER_BORE_D,
    'retainer_adjustable_from_top': True,
    'screw_overrun_path': 'open through metal nut and tall hollow retainer to common carrier top plane',
    'knob_nut_pocket_af_mm': KNOB_NUT_AF,
    'knob_plastic_web_mm': KNOB_NUT_Z0,
    'usable_screw_length_above_knob_mm': round(usable_above_knob, 3),
    'calculated_screw_tip_z_mm': round(screw_tip_z, 3),
    'full_nut_screw_overrun_margin_mm': round(screw_overrun_margin,3),
    'base_tube_common_mm3': round(tube_common, 9),
}
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2)

readme_path = os.path.join(C.OUT, 'README_BUILD_v60_full.txt')
with open(readme_path, 'a', encoding='utf-8') as f:
    f.write(
        '\nRack closure revision: common carrier top/bottom planes, raised M4 nut, '
        'M4x30 hand screw, restored functional 7 mm Lower tongue with side-print export, 6.90 mm AF nut pocket, '
        'structural seat for the single final 12x3 service-retainer stage.\n'
    )

stage('complete')
