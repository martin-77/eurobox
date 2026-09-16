"""Canonical v60 full mechanism builder.

The historical v60 full builder is preserved in ``build_v60_full_baseline.py``.
This canonical module loads that proven mechanism, replaces the box-clamp front
with the current wider support-free v60 front, and then applies the current
rack-closure architecture.  Every consumer of ``build_v60_full`` therefore sees
and exports the final geometry directly.

Front architecture:
- 160 mm clamp plate
- lead-screw axes at +/-65 mm (130 mm spacing)
- rectangular screw blocks retained
- DROPs only in the free fields beside/between those blocks
- all DROP flanks >=45 degrees from horizontal in canonical print Z

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

# Rebuild the complete box-clamp front from the clean structural core before the
# rack closure is applied.  Assign these canonical variables first because the
# rack module imports this partially-initialized module and must see the final
# wider plate/spindle datums while rebuilding the assembly.
import apply_v60_front_rework as _front

RIGHT_FULL = _front.RIGHT_FULL
LEFT_FULL = _front.LEFT_FULL
PLATE = _front.PLATE
SPINDLE_X = _front.SPINDLE_X

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

print('V60_STAGE canonical wider support-free front + top-retained M4x30 rack closure active', flush=True)
