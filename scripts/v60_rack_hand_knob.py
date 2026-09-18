import math

import FreeCAD as App
import Part

# Canonical v60 rack hand-knob component.
#
# This removable part is intentionally independent from the heavy BASE/rack
# thread pipeline.  It prints flat, needs no support and accepts the real M4 nut
# from the Upper-facing side before the screw is fitted.

KNOB_H = 7.0
KNOB_HUB_R = 10.0
KNOB_LOBES = 6
KNOB_LOBE_CENTER_R = 10.0
KNOB_LOBE_R = 5.0
# Compatibility datum used by the rack-closure assembly/validation.
KNOB_R = KNOB_LOBE_CENTER_R + KNOB_LOBE_R

# User-measured M4 nut is ~6.81 mm AF.  Give a real FDM insertion clearance,
# rather than the former 6.90 mm almost-press-fit pocket.
MEASURED_NUT_AF = 6.81
MEASURED_NUT_H = 3.20
KNOB_NUT_AF = 7.10
KNOB_NUT_H = 3.60
KNOB_NUT_Z0 = 3.20
KNOB_NUT_ENTRY_AF = 7.40
KNOB_NUT_ENTRY_DEPTH = 0.60
KNOB_BORE_D = 4.60


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


def build_grip_body():
    # Rounded six-lobe hand wheel: substantially easier to grip than the former
    # featureless 12-gon puck, while staying compact under the rack clamp.
    q = Part.makeCylinder(KNOB_HUB_R, KNOB_H)
    for i in range(KNOB_LOBES):
        a = 2.0 * math.pi * i / KNOB_LOBES
        cx = KNOB_LOBE_CENTER_R * math.cos(a)
        cy = KNOB_LOBE_CENTER_R * math.sin(a)
        q = q.fuse(
            Part.makeCylinder(
                KNOB_LOBE_R,
                KNOB_H,
                App.Vector(cx, cy, 0.0),
            )
        )
    return q.removeSplitter()


def build_rack_hand_knob():
    """Return the support-free, top-loaded v60 rack hand knob BRep."""
    q = build_grip_body()

    # M4 shank from underside into the nut seat.
    q = q.cut(
        Part.makeCylinder(
            KNOB_BORE_D / 2.0,
            KNOB_NUT_Z0 + 0.40,
            App.Vector(0, 0, -0.10),
        )
    ).removeSplitter()

    # The old part stopped the hex pocket 1 mm below the top, so the nut could
    # not actually be inserted.  This pocket intentionally breaks through the
    # Upper-facing top surface.
    q = q.cut(
        hex_z(
            KNOB_NUT_AF,
            KNOB_H - KNOB_NUT_Z0 + 0.20,
            KNOB_NUT_Z0,
        )
    ).removeSplitter()

    # Slightly wider lead-in for the first 0.6 mm to make the measured metal nut
    # easy to start in PETG without weakening the load-bearing pocket below.
    q = q.cut(
        hex_z(
            KNOB_NUT_ENTRY_AF,
            KNOB_NUT_ENTRY_DEPTH + 0.20,
            KNOB_H - KNOB_NUT_ENTRY_DEPTH,
        )
    ).removeSplitter()

    return q
