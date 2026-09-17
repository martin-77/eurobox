import json
import os

import FreeCAD as App
import MeshPart

import apply_v60_front_rebuild as P
import apply_v60_rack_closure as R
import apply_v60_retainer_thread_final as T
import build_v60 as C
import build_v60_full_baseline as B
from v60_timing import start_timer, stop_timer


def stage(msg):
    print('V60_FINAL_ASSEMBLY ' + msg, flush=True)


ASSEMBLY_LINEAR_DEFLECTION = 0.12
ASSEMBLY_ANGULAR_DEFLECTION = 0.35

stage('rewrite lightweight final assembly with replaceable front clamp cassettes')
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
FRONT_CENTER_X = P.PLATE_CENTER_X


def right_finish(shape, rack_y):
    shape.translate(App.Vector(0, rack_y, 0))
    return shape


def left_turnaround(shape, rack_y):
    # Reusable clamp parts are turned around rigidly, never reflected.  The
    # 180-degree turn about the clean-front centre preserves RH8x2 chirality and
    # swaps the two cassette positions onto the same installed {-48,+128} set.
    shape.rotate(
        App.Vector(FRONT_CENTER_X, 0, 0),
        App.Vector(0, 0, 1),
        180.0,
    )
    shape.translate(App.Vector(0, rack_y, 0))
    return shape


def add_box_clamp_hardware(prefix, rack_y, left=False):
    def finish(shape):
        return left_turnaround(shape, rack_y) if left else right_finish(shape, rack_y)

    plate = finish(P.PLATE.copy())
    expected_plate_x = (P.PLATE.BoundBox.XMin, P.PLATE.BoundBox.XMax)
    actual_plate_x = (plate.BoundBox.XMin, plate.BoundBox.XMax)
    if any(abs(a - b) > 1e-6 for a, b in zip(actual_plate_x, expected_plate_x)):
        raise RuntimeError(
            f'{prefix} clamp plate X placement changed: {actual_plate_x} != {expected_plate_x}'
        )
    add_obj(prefix + '_plate', plate)

    installed_spindle_centres = []
    for sx in P.SPINDLE_X:
        module = P.MODULE.copy()
        module.translate(App.Vector(sx, 0, 0))
        add_obj(prefix + '_clamp_module_' + str(int(sx)), finish(module))

        spindle = B.SPINDLE.copy()
        spindle.translate(App.Vector(sx, B.PLATE_SPINDLE_Y, B.SPINDLE_Z))
        add_obj(prefix + '_spindle_' + str(int(sx)), finish(spindle))

        nut = P.LEAD_NUT.copy()
        nut.translate(App.Vector(sx, B.NUT_Y0, B.SPINDLE_Z))
        add_obj(prefix + '_lead_nut_' + str(int(sx)), finish(nut))

        pin = P.NUT_PIN.copy()
        pin.translate(App.Vector(sx, P.PIN_Y, P.PIN_Z))
        add_obj(prefix + '_lead_nut_pin_' + str(int(sx)), finish(pin))

        clip = P.NUT_PIN_CLIP.copy()
        clip.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90.0)
        clip.translate(App.Vector(sx + P.NUT_PIN_CLIP_X, P.PIN_Y, P.PIN_Z))
        add_obj(prefix + '_lead_nut_clip_' + str(int(sx)), finish(clip))

        installed_spindle_centres.append(
            2.0 * FRONT_CENTER_X - sx if left else sx
        )

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
required_counts = {
    'clamp_module_': 4,
    'lead_nut_': 4,
    'lead_nut_pin_': 4,
    'lead_nut_clip_': 4,
}
for token, expected in required_counts.items():
    matches = [name for name in object_names if token in name]
    if len(matches) < expected:
        raise RuntimeError(f'Final assembly missing {token}: {matches}')
doc.saveAs(assembly_path)
App.closeDocument(doc.Name)
stop_timer('assembly.recompute_and_save_FCStd', _t)

if not os.path.isfile(assembly_path) or os.path.getsize(assembly_path) <= 0:
    raise RuntimeError('Final lightweight assembly FCStd was not written')
stage(f'assembly saved: {os.path.getsize(assembly_path)} bytes')

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['stage'] = 'full_direct_mechanism_clean_modular_front_and_explicit_retainer_threads'
validation['box_clamp']['final_assembly_contains_separate_lead_nut_hardware'] = True
validation['box_clamp']['final_assembly_lead_nut_cartridge_count'] = 4
validation['box_clamp']['final_assembly_lead_nut_pin_count'] = 4
validation['box_clamp']['final_assembly_lead_nut_clip_count'] = 4
validation['box_clamp']['final_assembly_replaceable_module_count'] = 4
validation['box_clamp']['final_assembly_installed_spindle_x_mm'] = list(P.SPINDLE_X)
validation['box_clamp']['final_assembly_left_hardware_transform'] = (
    'rigid 180deg turnaround about clean-front centre for complete reusable '
    'cassette/spindle/cartridge/pin/clip stack; no RH8x2 reflection'
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
    fh.write('Front is a clean closed carrier with four installed replaceable clamp cassettes (two per handed base).\n')
    fh.write('Each cassette contains a separately replaceable RH8x2 lead-nut cartridge retained by cross-pin and C-clip.\n')
    fh.write('Assembly FCStd is a lightweight tessellated inspection proof; hard checks and neutral CAD exports use exact BRep geometry.\n')

stop_timer('assembly.total', _t_total, file_bytes=os.path.getsize(assembly_path))
stage('complete')
