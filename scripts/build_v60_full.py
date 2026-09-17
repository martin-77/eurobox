"""Canonical v60 full mechanism builder.

The structural v60 baseline is retained, but the production path applies the
final mechanisms in this order:
1. restore the proven v50 box-clamp function with a 160 mm moving plate,
   separate RH8x2 lead-nut cartridges and two outer Y/Z support DROPs;
2. apply the M4x30 rack closure;
3. rebuild/witness the explicit printable 12x2 rack-nut-retainer thread pair;
4. rewrite the final assembly including the removable box-clamp hardware.

The previous v60 experiment with integral BASE lead threads and a row of
triangular front DROPs is deliberately not part of the canonical output.
"""

from build_v60_full_baseline import *  # noqa: F401,F403

import apply_v60_front_final as _front

RIGHT_FULL = _front.RIGHT_FULL
LEFT_FULL = _front.LEFT_FULL
PLATE = _front.PLATE
SPINDLE_X = _front.SPINDLE_X
LEAD_NUT = _front.LEAD_NUT
NUT_PIN = _front.NUT_PIN
NUT_PIN_CLIP = _front.NUT_PIN_CLIP
LEAD_NUT_PIN_LOCAL_Y = _front.LEAD_NUT_PIN_LOCAL_Y
LEAD_NUT_PIN_LOCAL_Z = _front.LEAD_NUT_PIN_LOCAL_Z
NUT_PIN_CLIP_X = _front.NUT_PIN_CLIP_X
PIN_Y_BOX_CLAMP = _front.PIN_Y
PIN_Z_BOX_CLAMP = _front.PIN_Z

# Rack closure consumes the canonical box-clamp front through this partially
# initialized module, so the variables above must be assigned first.
import apply_v60_rack_closure as _rack_closure

RIGHT_FULL = _rack_closure.RIGHT
LEFT_FULL = _rack_closure.LEFT
LOWER = _rack_closure.LOWER
RACK_NUT_RETAINER = _rack_closure.RACK_NUT_RETAINER
RACK_HAND_KNOB = _rack_closure.RACK_HAND_KNOB

# Final rack service thread is rebuilt from one explicit matched pair and
# witnessed in the final BRep.
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

# Both rack finalizers rebuild the assembly while they run.  Rewrite it one last
# time after all geometry is final so the separate lead-nut cartridges, their
# pins and their clips cannot silently disappear from the published FCStd.
import apply_v60_final_assembly as _final_assembly  # noqa: F401,E402

print(
    'V60_STAGE canonical v50 box-clamp cartridges + outer DROPs + explicit rack retainer threads active',
    flush=True,
)
