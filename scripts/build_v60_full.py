"""Canonical v60 full mechanism builder.

The historical v60 full builder is preserved in ``build_v60_full_baseline.py``.
This canonical module loads that proven base mechanism first, then applies the
current rack closure architecture inside the canonical build import so every
consumer of ``build_v60_full`` sees and exports the final geometry directly.

Rack closure architecture:
- integral BASE/Upper
- hinged replaceable Lower
- M4x30 hand screw from below
- 7 mm Lower closure tongue
- top-loaded real M4 nut in a 6.90 mm AF hex pocket
- hollow, screw-in printed nut retainer with coarse 12x2-class thread
- through overrun bore above the metal nut
- separate rack hand knob with 6.90 mm AF metal-nut pocket
"""

from build_v60_full_baseline import *  # noqa: F401,F403
import apply_v60_rack_closure as _rack_closure

RIGHT_FULL = _rack_closure.RIGHT
LEFT_FULL = _rack_closure.LEFT
LOWER = _rack_closure.LOWER
RACK_NUT_RETAINER = _rack_closure.RACK_NUT_RETAINER
RACK_HAND_KNOB = _rack_closure.RACK_HAND_KNOB

RACK_M4_SCREW_LENGTH = _rack_closure.RACK_SCREW_LENGTH
RACK_M4_LOWER_CLEAR_D = _rack_closure.LOWER_CLEAR_D
RACK_M4_NUT_AF = _rack_closure.RACK_NUT_AF
RACK_M4_NUT_H = _rack_closure.RACK_NUT_H
RACK_M4_NUT_Z0 = _rack_closure.RACK_NUT_Z0
RACK_RETAINER_PITCH = _rack_closure.RETAINER_PITCH
RACK_RETAINER_BORE_D = _rack_closure.RETAINER_BORE_D
RACK_RETAINER_MALE_MAJOR_D = 2.0 * _rack_closure.RETAINER_MALE_MAJOR_R
RACK_RETAINER_FEMALE_MAJOR_D = 2.0 * _rack_closure.RETAINER_FEMALE_MAJOR_R
RACK_LOWER_CLOSURE_THICKNESS = _rack_closure.LOWER_PAD_Z1 - _rack_closure.LOWER_PAD_Z0

print('V60_STAGE canonical top-retained M4x30 rack closure active', flush=True)
