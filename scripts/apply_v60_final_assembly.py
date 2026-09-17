import json
import os

import FreeCAD as App
import MeshPart

import apply_v60_front_final as P
import apply_v60_rack_closure as R
import apply_v60_retainer_thread_final as T
import build_v60 as C
import build_v60_full_baseline as B


def stage(msg):
    print('V60_FINAL_ASSEMBLY ' + msg, flush=True)


# The production hard-checks above operate on the exact BRep geometry.  The
# complete assembly is only an installed-orientation proof/inspection artifact.
# Storing every detailed threaded BRep again in one FCStd made that document
# >100 MiB and, more importantly, spent tens of seconds serialising huge OCC
# shapes at the very end of an already long GitHub Actions job.  Hosted runners
# were repeatedly shut down during that final save even though every mechanical
# check had already passed.
#
# Keep the exact final shapes for all validation and STEP/STL exports, but make
# the assembly FCStd a tessellated representation of those same final shapes.
# This changes no design geometry and keeps the assembly useful for visual
# inspection while making the last stage fast and compact.
ASSEMBLY_LINEAR_DEFLECTION = 0.12
ASSEMBLY_ANGULAR_DEFLECTION = 0.35

stage('rewrite lightweight final assembly including separate box-clamp hardware')
assembly_path = os.path.join(C.OUT, 'eurobox_v60_assembly.FCStd')
try:
    if App.ActiveDocument:
        App.closeDocument(App.ActiveDocument.Name)
except Exception:
    pass

doc = App.newDocument('Eurobox_v60_assembly')


def add_obj(name, shape):
    obj = doc.addObject('Mesh::Feature', name)
    obj.Mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=ASSEMBLY_LINEAR_DEFLECTION,
        AngularDeflection=ASSEMBLY_ANGULAR_DEFLECTION,
        Relative=False,
    )
    if obj.Mesh.CountFacets <= 0:
        raise RuntimeError(f'Final assembly mesh is empty for {name}')
    return obj


def add_box_clamp_hardware(prefix, rack_y, left=False):
    def finish(shape):
        if not left:
            shape.translate(App.Vector(0, rack_y, 0))
            return shape
        shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 180.0)
        shape.translate(App.Vector(0, rack_y, 0))
        return shape

    plate = P.PLATE.copy()
    add_obj(prefix + '_plate', finish(plate))

    for sx in P.SPINDLE_X:
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


RY = C.RACK_CTC / 2.0
LY = -C.RACK_CTC / 2.0

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

doc.recompute()
object_names = [obj.Name for obj in doc.Objects]
required_tokens = ('lead_nut_', 'lead_nut_pin_', 'lead_nut_clip_')
for token in required_tokens:
    matches = [name for name in object_names if token in name]
    if len(matches) < 4:
        raise RuntimeError(f'Final assembly missing box-clamp hardware {token}: {matches}')
doc.saveAs(assembly_path)
App.closeDocument(doc.Name)

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
    fh.write('Assembly FCStd is a lightweight tessellated inspection proof; all hard checks and neutral CAD exports use exact BRep geometry.\n')

stage('complete')
