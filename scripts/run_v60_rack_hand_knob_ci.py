import json
import os
import sys

import FreeCAD as App
import MeshPart

sys.path.insert(0, 'scripts')
import v60_rack_hand_knob as K

OUT = os.path.abspath('build_v60_rack_knob')
os.makedirs(OUT, exist_ok=True)

shape = K.build_rack_hand_knob()
if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
    raise RuntimeError(
        f'rack hand knob must be one valid solid, got solids={len(shape.Solids)}'
    )

name = 'eurobox_v60_rack_hand_knob'
step_path = os.path.join(OUT, name + '.step')
fcstd_path = os.path.join(OUT, name + '.FCStd')
stl_path = os.path.join(OUT, name + '.stl')

shape.exportStep(step_path)
doc = App.newDocument('rack_hand_knob')
obj = doc.addObject('Part::Feature', name)
obj.Shape = shape
doc.recompute()
doc.saveAs(fcstd_path)
App.closeDocument(doc.Name)

mesh = MeshPart.meshFromShape(
    Shape=shape,
    LinearDeflection=0.06,
    AngularDeflection=0.20,
    Relative=False,
)
if mesh.CountFacets < 50:
    raise RuntimeError(f'rack hand knob mesh suspiciously small: {mesh.CountFacets}')
mesh.write(stl_path)

validation = {
    'component': name,
    'scope': 'rack_hand_knob_only',
    'single_valid_solid': True,
    'bbox_mm': [
        round(shape.BoundBox.XLength, 3),
        round(shape.BoundBox.YLength, 3),
        round(shape.BoundBox.ZLength, 3),
    ],
    'volume_mm3': round(shape.Volume, 6),
    'facets': mesh.CountFacets,
    'knob_height_mm': K.KNOB_H,
    'nut_af_mm': K.KNOB_NUT_AF,
    'nut_height_mm': K.KNOB_NUT_H,
    'nut_pocket_z0_mm': K.KNOB_NUT_Z0,
    'screw_bore_d_mm': K.KNOB_BORE_D,
}
with open(
    os.path.join(OUT, 'VALIDATION_v60_rack_hand_knob.json'),
    'w',
    encoding='utf-8',
) as fh:
    json.dump(validation, fh, indent=2)

print(json.dumps(validation, indent=2), flush=True)
