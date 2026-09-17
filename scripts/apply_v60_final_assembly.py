import json
import os

import FreeCAD as App
import MeshPart

import apply_v60_front_final as P
import apply_v60_rack_closure as R
import apply_v60_retainer_thread_final as T
import build_v60 as C
import build_v60_full_baseline as B
from v60_timing import start_timer, stop_timer


def stage(msg):
    print('V60_FINAL_ASSEMBLY ' + msg, flush=True)


# The production hard-checks operate on exact BRep geometry. The complete
# assembly is an installed-orientation inspection artifact, so store tessellated
# representations of those exact final shapes instead of serialising every BRep
# again. Per-object meshing is timed because it is an obvious future cost target.
ASSEMBLY_LINEAR_DEFLECTION = 0.12
ASSEMBLY_ANGULAR_DEFLECTION = 0.35

stage('rewrite lightweight final assembly including separate box-clamp hardware')
_t_total = start_timer('assembly.total')
assembly_path = os.path.join(C.OUT, 'eurobox_v60_assembly.FCStd')
try:
    if App.ActiveDocument:
        App.closeDocument(App.ActiveDocument.Name)
except Exception:
    pass

doc = App.newDocument('Eurobox_v60_assembly')


def add_obj(name, shape):
    label = 'assembly.mesh.' + name
    _t = start_timer(label)
    obj = doc.addObject('Mesh::Feature', name)
    obj.Mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=ASSEMBLY_LINEAR_DEFLECTION,
        AngularDeflection=ASSEMBLY_ANGULAR_DEFLECTION,
        Relative=False,
    )
    if obj.Mesh.CountFacets <= 0:
        raise RuntimeError(f'Final assembly mesh is empty for {name}')
    stop_timer(label, _t, facets=obj.Mesh.CountFacets)
    return obj


RY = C.RACK_CTC / 2.0
LY = -C.RACK_CTC / 2.0
FRONT_CENTER_X = 0.5 * (min(P.SPINDLE_X) + max(P.SPINDLE_X))


def right_finish(shape, rack_y):
    shape.translate(App.Vector(0, rack_y, 0))
    return shape


def left_turnaround(shape, rack_y):
    # LEFT_base is generated as mirror-X(RIGHT) and then installed with a 180
    # degree Z rotation.  That net base transform is a Y mirror, so the shifted
    # +40 mm front stays at the same installed X coordinates as RIGHT.
    #
    # Clamp plate, spindle and lead-nut are real reusable parts, not mirrored
    # thread geometry.  Turn them around rigidly about the shifted front centre
    # rather than about global X=0.  This preserves RH8x2 handedness and maps
    # the two spindle axes onto the same {-48,+128} installed X set.
    shape.rotate(
        App.Vector(FRONT_CENTER_X, 0, 0),
        App.Vector(0, 0, 1),
        180.0,
    )
    shape.translate(App.Vector(0, rack_y, 0))
    return shape


def left_cross_hardware(shape, rack_y):
    # Retaining pins and C-clips run along X.  The installed LEFT base is the
    # RIGHT base mirrored in Y, therefore their X head/clip side must NOT be
    # reversed.  Mirror only Y for these non-threaded service parts.
    shape.mirror(App.Vector(0, 0, 0), App.Vector(0, 1, 0))
    shape.translate(App.Vector(0, rack_y, 0))
    return shape


def add_box_clamp_hardware(prefix, rack_y, left=False):
    plate = P.PLATE.copy()
    if left:
        plate = left_turnaround(plate, rack_y)
    else:
        plate = right_finish(plate, rack_y)

    expected_plate_x = (P.PLATE.BoundBox.XMin, P.PLATE.BoundBox.XMax)
    actual_plate_x = (plate.BoundBox.XMin, plate.BoundBox.XMax)
    if any(abs(a - b) > 1e-6 for a, b in zip(actual_plate_x, expected_plate_x)):
        raise RuntimeError(
            f'{prefix} clamp plate X placement changed: '
            f'{actual_plate_x} != {expected_plate_x}'
        )
    add_obj(prefix + '_plate', plate)

    installed_spindle_centres = []
    for sx in P.SPINDLE_X:
        spindle = B.SPINDLE.copy()
        spindle.translate(App.Vector(sx, B.PLATE_SPINDLE_Y, B.SPINDLE_Z))
        if left:
            spindle = left_turnaround(spindle, rack_y)
            installed_spindle_centres.append(2.0 * FRONT_CENTER_X - sx)
        else:
            spindle = right_finish(spindle, rack_y)
            installed_spindle_centres.append(sx)
        add_obj(prefix + '_spindle_' + str(int(sx)), spindle)

        nut = P.LEAD_NUT.copy()
        nut.translate(App.Vector(sx, B.NUT_Y0, B.SPINDLE_Z))
        if left:
            nut = left_turnaround(nut, rack_y)
        else:
            nut = right_finish(nut, rack_y)
        add_obj(prefix + '_lead_nut_' + str(int(sx)), nut)

        pin = P.NUT_PIN.copy()
        pin.translate(App.Vector(sx, P.PIN_Y, P.PIN_Z))
        if left:
            pin = left_cross_hardware(pin, rack_y)
        else:
            pin = right_finish(pin, rack_y)
        add_obj(prefix + '_lead_nut_pin_' + str(int(sx)), pin)

        clip = P.NUT_PIN_CLIP.copy()
        clip.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
        clip.translate(App.Vector(sx + P.NUT_PIN_CLIP_X, P.PIN_Y, P.PIN_Z))
        if left:
            clip = left_cross_hardware(clip, rack_y)
        else:
            clip = right_finish(clip, rack_y)
        add_obj(prefix + '_lead_nut_clip_' + str(int(sx)), clip)

    expected_centres = sorted(float(x) for x in P.SPINDLE_X)
    actual_centres = sorted(float(x) for x in installed_spindle_centres)
    if any(abs(a - b) > 1e-9 for a, b in zip(actual_centres, expected_centres)):
        raise RuntimeError(
            f'{prefix} installed spindle X centres wrong: '
            f'{actual_centres} != {expected_centres}'
        )


right_base = T.RIGHT.copy()
right_base.translate(App.Vector(0, RY, 0))
add_obj('RIGHT_base', right_base)
add_box_clamp_hardware('RIGHT', RY, left=False)

for xc in C.CLAMP_X:
    lower = R.LOWER.copy()
    lower.translate(App.Vector(xc, RY, 0))
    add_obj('RIGHT_lower_' + str(int(xc)), lower)

    retainer = T.RACK_NUT_RETAINER.copy()
    retainer.translate(App.Vector(xc, RY + C.RACK_CLOSURE_Y, T.THREAD_Z0))
    add_obj('RIGHT_rack_nut_retainer_' + str(int(xc)), retainer)

    knob = R.RACK_HAND_KNOB.copy()
    knob.translate(App.Vector(xc, RY + C.RACK_CLOSURE_Y, R.LOWER_PAD_Z0 - R.KNOB_H))
    add_obj('RIGHT_rack_hand_knob_' + str(int(xc)), knob)


def left_transform(shape):
    shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0)
    shape.translate(App.Vector(0, LY, 0))
    return shape


add_obj('LEFT_base', left_transform(T.LEFT.copy()))
add_box_clamp_hardware('LEFT', LY, left=True)

for xc in C.CLAMP_X:
    lower = R.LOWER.copy()
    lower.translate(App.Vector(xc, 0, 0))
    add_obj('LEFT_lower_' + str(int(xc)), left_transform(lower))

    retainer = T.RACK_NUT_RETAINER.copy()
    retainer.translate(App.Vector(xc, C.RACK_CLOSURE_Y, T.THREAD_Z0))
    add_obj('LEFT_rack_nut_retainer_' + str(int(xc)), left_transform(retainer))

    knob = R.RACK_HAND_KNOB.copy()
    knob.translate(App.Vector(xc, C.RACK_CLOSURE_Y, R.LOWER_PAD_Z0 - R.KNOB_H))
    add_obj('LEFT_rack_hand_knob_' + str(int(xc)), left_transform(knob))

add_obj('REF_right_rack_tube', C.cyl_x(C.RACK_R, 400, -200, RY, 0))
add_obj('REF_left_rack_tube', C.cyl_x(C.RACK_R, 400, -200, LY, 0))

_t = start_timer('assembly.recompute_and_save_FCStd')
doc.recompute()
object_names = [obj.Name for obj in doc.Objects]
required_tokens = ('lead_nut_', 'lead_nut_pin_', 'lead_nut_clip_')
for token in required_tokens:
    matches = [name for name in object_names if token in name]
    if len(matches) < 4:
        raise RuntimeError(f'Final assembly missing box-clamp hardware {token}: {matches}')
doc.saveAs(assembly_path)
App.closeDocument(doc.Name)
stop_timer('assembly.recompute_and_save_FCStd', _t)

if not os.path.isfile(assembly_path) or os.path.getsize(assembly_path) <= 0:
    raise RuntimeError('Final lightweight assembly FCStd was not written')
stage(f'assembly saved: {os.path.getsize(assembly_path)} bytes')

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_v50_box_clamp_and_explicit_retainer_threads'
validation['box_clamp']['final_assembly_contains_separate_lead_nut_hardware'] = True
validation['box_clamp']['final_assembly_lead_nut_cartridge_count'] = 4
validation['box_clamp']['final_assembly_lead_nut_pin_count'] = 4
validation['box_clamp']['final_assembly_lead_nut_clip_count'] = 4
validation['box_clamp']['final_assembly_installed_spindle_x_mm'] = list(P.SPINDLE_X)
validation['box_clamp']['final_assembly_left_hardware_transform'] = (
    'rigid 180deg turnaround about shifted front centre for plate/spindle/lead-nut; '
    'Y mirror only for non-threaded cross-pin and C-clip service hardware'
)
validation['final_assembly'] = {
    'representation': 'tessellated exact-final-shape inspection proof',
    'linear_deflection_mm': ASSEMBLY_LINEAR_DEFLECTION,
    'angular_deflection_rad': ASSEMBLY_ANGULAR_DEFLECTION,
    'mechanical_validation_uses_exact_brep': True,
    'file_bytes': os.path.getsize(assembly_path),
}
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

with open(os.path.join(C.OUT, 'README_BUILD_v60_full.txt'), 'a', encoding='utf-8') as fh:
    fh.write('Final assembly includes all four separate lead-nut cartridges, retaining pins and C-clips.\n')
    fh.write('LEFT clamp hardware is positioned about the shifted front centre without mirroring RH8x2 thread geometry.\n')
    fh.write('Assembly FCStd is a lightweight tessellated inspection proof; all hard checks and neutral CAD exports use exact BRep geometry.\n')

stop_timer('assembly.total', _t_total, file_bytes=os.path.getsize(assembly_path))
stage('complete')
