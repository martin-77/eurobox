import math

import FreeCAD as App
import Part

# Canonical v60 rack hand-knob component.
#
# Kept separate from apply_v60_rack_closure.py on purpose: changing only the
# removable knob must not rebuild/mirror/re-thread both BASE parts or regenerate
# the complete inspection assembly.

KNOB_R = 13.0
KNOB_H = 8.0
KNOB_NUT_AF = 6.90
KNOB_NUT_H = 3.60
KNOB_NUT_Z0 = 3.20
KNOB_BORE_D = 4.60


def ngon_z(n, radius, height, z0=0.0):
    pts = [
        App.Vector(
            radius * math.cos(2.0 * math.pi * i / n),
            radius * math.sin(2.0 * math.pi * i / n),
            z0,
        )
        for i in range(n)
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(
        App.Vector(0, 0, height)
    )


def hex_z(af, height, z0=0.0):
    radius = af / math.sqrt(3.0)
    pts = [
        App.Vector(
            radius * math.cos(math.radians(30.0 + 60.0 * i)),
            radius * math.sin(math.radians(30.0 + 60.0 * i)),
            z0,
        )
        for i in range(6)
    ]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(
        App.Vector(0, 0, height)
    )


def build_rack_hand_knob():
    """Return the canonical rack hand knob BRep.

    This first extraction intentionally preserves the existing geometry exactly;
    ergonomic/functional redesigns can now be validated and published without
    invoking the complete v60 BASE pipeline.
    """
    q = ngon_z(12, KNOB_R, KNOB_H)
    q = q.cut(
        Part.makeCylinder(
            KNOB_BORE_D / 2.0,
            KNOB_NUT_Z0 + 0.2,
            App.Vector(0, 0, -0.1),
        )
    ).removeSplitter()
    q = q.cut(
        hex_z(KNOB_NUT_AF, KNOB_NUT_H + 0.20, KNOB_NUT_Z0)
    ).removeSplitter()
    return q
