import json
import os
import sys

import FreeCAD as App
import MeshPart
import Part

sys.path.insert(0, 'scripts')
import v60_rack_hand_knob as K

OUT = os.path.abspath('build_v60_rack_knob')
os.makedirs(OUT, exist_ok=True)

shape = K.build_rack_hand_knob()
failures = []

if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
    failures.append(
        f'rack hand knob must be one valid solid, got solids={len(shape.Solids)}'
    )

# The actual measured nut must be insertable vertically from free space all the
# way to the seat.  This directly catches the former closed 1 mm roof.
nut_insertion = []
for lift in (4.0, 2.0, 1.0, 0.0):
    nut = K.hex_z(
        K.MEASURED_NUT_AF,
        K.MEASURED_NUT_H,
        K.KNOB_NUT_Z0 + lift,
    )
    common = shape.common(nut).Volume
    nut_insertion.append({
        'lift_mm': lift,
        'common_mm3': round(common, 9),
    })
    if common > 1e-5:
        failures.append(
            f'measured M4 nut blocked during top insertion at lift={lift}: '
            f'{common:.6f} mm3'
        )

# The central M4 shank path must be genuinely clear from the underside into the
# nut pocket.
bore_probe = Part.makeCylinder(
    K.KNOB_BORE_D / 2.0 - 0.05,
    K.KNOB_NUT_Z0 + 0.30,
    App.Vector(0, 0, -0.05),
)
bore_common = shape.common(bore_probe).Volume
if bore_common > 1e-5:
    failures.append(f'M4 shank path blocked: {bore_common:.6f} mm3')

# The nut still needs a real plastic support floor around the M4 bore.
floor_probe = K.hex_z(
    K.MEASURED_NUT_AF,
    0.25,
    K.KNOB_NUT_Z0 - 0.25,
).cut(
    Part.makeCylinder(
        K.KNOB_BORE_D / 2.0 + 0.10,
        0.45,
        App.Vector(0, 0, K.KNOB_NUT_Z0 - 0.35),
    )
)
floor_fraction = (
    shape.common(floor_probe).Volume / floor_probe.Volume
    if floor_probe.Volume > 0.0 else 0.0
)
if floor_fraction < 0.98:
    failures.append(
        f'nut support floor incomplete: fraction={floor_fraction:.5f}'
    )

# Interface/printability gates.
if K.KNOB_NUT_AF - K.MEASURED_NUT_AF < 0.20:
    failures.append('M4 nut pocket has insufficient FDM across-flat clearance')
if K.KNOB_H - K.KNOB_NUT_Z0 < K.MEASURED_NUT_H + 0.20:
    failures.append('top-open M4 nut pocket is too shallow')
usable_screw_above_knob = 30.0 - K.KNOB_NUT_Z0 - K.MEASURED_NUT_H
if usable_screw_above_knob < 23.0:
    failures.append(
        f'M4x30 usable shank above knob too short: '
        f'{usable_screw_above_knob:.3f} mm'
    )
grip_x = shape.BoundBox.XLength
grip_y = shape.BoundBox.YLength
# Same outer profile as the established box-clamp knob.  The scallops trim the
# exact cylinder extrema slightly, so validate the compact ~Ø30 envelope rather
# than requiring a mathematically full 30.0 mm bounding box in both axes.
if not (28.0 <= grip_x <= 30.5 and 28.0 <= grip_y <= 30.5):
    failures.append(
        f'grip envelope changed unexpectedly: X={grip_x:.3f} Y={grip_y:.3f} mm'
    )
if K.GRIP_SCALLOPS != 8:
    failures.append(f'shared knob profile must have 8 scallops, got {K.GRIP_SCALLOPS}')

if failures:
    raise RuntimeError('V60 RACK HAND KNOB CHECKS FAILED: ' + ' | '.join(failures))

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
if mesh.CountFacets < 200:
    raise RuntimeError(f'rack hand knob mesh suspiciously small: {mesh.CountFacets}')
mesh.write(stl_path)

validation = {
    'component': name,
    'scope': 'rack_hand_knob_only',
    'design': 'shared_box_knob_scalloped_profile_top_loaded_m4_nut',
    'single_valid_solid': True,
    'support_free_flat_print': True,
    'bbox_mm': [
        round(shape.BoundBox.XLength, 3),
        round(shape.BoundBox.YLength, 3),
        round(shape.BoundBox.ZLength, 3),
    ],
    'volume_mm3': round(shape.Volume, 6),
    'facets': mesh.CountFacets,
    'scallops': K.GRIP_SCALLOPS,
    'outer_diameter_mm': round(2.0 * K.KNOB_R, 3),
    'knob_height_mm': K.KNOB_H,
    'measured_nut_af_mm': K.MEASURED_NUT_AF,
    'nut_pocket_af_mm': K.KNOB_NUT_AF,
    'nut_entry_af_mm': K.KNOB_NUT_ENTRY_AF,
    'nut_height_mm': K.KNOB_NUT_H,
    'nut_pocket_z0_mm': K.KNOB_NUT_Z0,
    'nut_pocket_open_to_top': True,
    'nut_insertion': nut_insertion,
    'nut_floor_fraction': round(floor_fraction, 6),
    'screw_bore_d_mm': K.KNOB_BORE_D,
    'screw_bore_common_mm3': round(bore_common, 9),
    'usable_m4x30_shank_above_knob_mm': round(usable_screw_above_knob, 3),
}
with open(
    os.path.join(OUT, 'VALIDATION_v60_rack_hand_knob.json'),
    'w',
    encoding='utf-8',
) as fh:
    json.dump(validation, fh, indent=2)

print(json.dumps(validation, indent=2), flush=True)
