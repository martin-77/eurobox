import FreeCAD as App
import Part

import v60_knob_profile as KP

# Canonical v60 rack hand knob.
# External ergonomics are intentionally identical to eurobox_v60_knob:
# Ø30 x 7 mm with the same eight perimeter scallops.  Only the central M4/nut
# interface is different.
KNOB_R = KP.KNOB_R
KNOB_H = KP.KNOB_H
GRIP_SCALLOPS = KP.SCALLOPS

MEASURED_NUT_AF = 6.81
MEASURED_NUT_H = 3.20

# Real FDM clearance for the measured metal M4 nut.
KNOB_NUT_AF = 7.10
KNOB_NUT_H = 3.60
KNOB_NUT_Z0 = 3.20
KNOB_NUT_ENTRY_AF = 7.40
KNOB_NUT_ENTRY_DEPTH = 0.60
KNOB_BORE_D = 4.60


def hex_z(af, height, z0=0.0):
    import math
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
    q = KP.build_scalloped_knob_body()

    # M4 shank from underside to the captive nut seat.
    q = q.cut(
        Part.makeCylinder(
            KNOB_BORE_D / 2.0,
            KNOB_NUT_Z0 + 0.40,
            App.Vector(0, 0, -0.10),
        )
    ).removeSplitter()

    # Top-open captive nut pocket.  The former rack knob had a closed roof and
    # therefore could not actually accept the nut.
    q = q.cut(
        hex_z(
            KNOB_NUT_AF,
            KNOB_H - KNOB_NUT_Z0 + 0.20,
            KNOB_NUT_Z0,
        )
    ).removeSplitter()

    # Short wider lead-in at the top for reliable PETG insertion.
    q = q.cut(
        hex_z(
            KNOB_NUT_ENTRY_AF,
            KNOB_NUT_ENTRY_DEPTH + 0.20,
            KNOB_H - KNOB_NUT_ENTRY_DEPTH,
        )
    ).removeSplitter()

    return q
