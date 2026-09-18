import math

import FreeCAD as App
import Part

# Shared external hand-wheel profile used by BOTH v60 knobs.
# This is the existing box-clamp knob geometry: Ø30 x 7 mm disc with eight
# rounded finger scallops cut from the perimeter.
KNOB_R = 15.0
KNOB_H = 7.0
SCALLOPS = 8
SCALLOP_CENTER_R = 16.2
SCALLOP_R = 3.4


def build_scalloped_knob_body():
    q = Part.makeCylinder(KNOB_R, KNOB_H)
    for angle_deg in range(0, 360, 45):
        a = math.radians(angle_deg)
        cx = SCALLOP_CENTER_R * math.cos(a)
        cy = SCALLOP_CENTER_R * math.sin(a)
        q = q.cut(
            Part.makeCylinder(
                SCALLOP_R,
                KNOB_H + 0.40,
                App.Vector(cx, cy, -0.20),
            )
        ).removeSplitter()
    return q
