"""Canonical v60 full mechanism builder.

The historical v60 full builder is preserved in ``build_v60_full_baseline.py``.
The canonical path now applies, in order:
1. the widened 160 mm / +/-65 mm box-clamp front,
2. the FINAL full-depth support-free front DROPs only beside/between the
   rectangular screw blocks,
3. the M4x30 rack closure,
4. the FINAL explicitly witnessed printable 12x2 retainer thread pair.

The last two finalization passes exist specifically so a green build cannot be
mistaken for the requested geometry: the front pass probes the actual full-depth
webs at front/middle/back Y slices, and the retainer pass proves helical material,
female groove/land and phase-sensitive engagement in the final BRep.
"""

from build_v60_full_baseline import *  # noqa: F401,F403

# First establish the widened plate and screw datums, then replace its earlier
# thin rear ribs with the actual full-depth structural DROPs.
import apply_v60_front_rework as _front_pre
import apply_v60_front_final as _front

RIGHT_FULL = _front.RIGHT_FULL
LEFT_FULL = _front.LEFT_FULL
PLATE = _front.PLATE
SPINDLE_X = _front.SPINDLE_X

# Rack closure consumes the canonical front through this partially initialized
# module, therefore the final front variables above must be assigned first.
import apply_v60_rack_closure as _rack_closure

RIGHT_FULL = _rack_closure.RIGHT
LEFT_FULL = _rack_closure.LEFT
LOWER = _rack_closure.LOWER
RACK_NUT_RETAINER = _rack_closure.RACK_NUT_RETAINER
RACK_HAND_KNOB = _rack_closure.RACK_HAND_KNOB

# Rebuild and re-export the service retainer + BASE female threads from a
# deliberately pronounced matched pair and validate the actual final BRep.
import apply_v60_retainer_thread_final as _retainer_final

RIGHT_FULL = _retainer_final.RIGHT
LEFT_FULL = _retainer_final.LEFT
RACK_NUT_RETAINER = _retainer_final.RACK_NUT_RETAINER

RACK_M4_SCREW_LENGTH = _rack_closure.RACK_SCREW_LENGTH
RACK_M4_LOWER_CLEAR_D = _rack_closure.LOWER_CLEAR_D
RACK_M4_NUT_AF = _rack_closure.RACK_NUT_AF
RACK_M4_NUT_H = _rack_closure.RACK_NUT_H
RACK_M4_NUT_Z0 = _rack_closure.RACK_NUT_Z0
RACK_RETAINER_PITCH = _retainer_final.PITCH
RACK_RETAINER_BORE_D = _rack_closure.RETAINER_BORE_D
RACK_RETAINER_MALE_MAJOR_D = 2.0 * _retainer_final.MALE_MAJOR_R
RACK_RETAINER_FEMALE_MAJOR_D = 2.0 * _retainer_final.FEMALE_MAJOR_R
RACK_LOWER_CLOSURE_THICKNESS = _rack_closure.LOWER_PAD_Z1 - _rack_closure.LOWER_PAD_Z0

print(
    'V60_STAGE canonical actual full-depth front + explicit witnessed retainer threads active',
    flush=True,
)
