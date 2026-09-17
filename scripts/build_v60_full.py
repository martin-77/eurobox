"""Canonical v60 full mechanism builder.

Production order:
1. structural full baseline;
2. phase-matched RH8x2 cartridge prerequisite + complete spindle sweep;
3. 160 mm main clamp face with outboard drive ears and cartridge/drop load paths;
4. position-only correction of the complete front topology;
5. M4x30 rack closure;
6. explicit printable 12x2 rack-retainer thread pair;
7. lightweight final inspection assembly.

Each stage emits V60_TIMING records into build_v60/TIMING_v60.json so later
runtime/cost work can target measured hotspots instead of guessing.
"""

from v60_timing import start_timer, stop_timer

_t = start_timer('full.import_structural_baseline')
from build_v60_full_baseline import *  # noqa: F401,F403,E402
stop_timer('full.import_structural_baseline', _t)

# The separate cartridge uses a female profile derived from the exact spindle
# master and clears the full spindle envelope at the final outboard axes.
_t = start_timer('full.apply_box_clamp_prerequisite')
import apply_v60_box_clamp_prereq as _box_clamp_prereq  # noqa: F401,E402
stop_timer('full.apply_box_clamp_prerequisite', _t)

_t = start_timer('full.apply_outboard_box_clamp_front')
import apply_v60_front_final as _front  # noqa: E402
stop_timer('full.apply_outboard_box_clamp_front', _t)

# Installed-orientation inspection showed that the complete clamp front was
# centred too far left on the asymmetric carrier.  Apply only the X-position
# correction here; clamp geometry/kinematics remain unchanged.
_t = start_timer('full.apply_front_position_fix')
import apply_v60_front_position_fix as _front_position  # noqa: E402
stop_timer('full.apply_front_position_fix', _t)

RIGHT_FULL = _front_position.RIGHT_FULL
LEFT_FULL = _front_position.LEFT_FULL
PLATE = _front_position.PLATE
SPINDLE_X = _front_position.SPINDLE_X
LEAD_NUT = _front.LEAD_NUT
NUT_PIN = _front.NUT_PIN
NUT_PIN_CLIP = _front.NUT_PIN_CLIP
LEAD_NUT_PIN_LOCAL_Y = _front.LEAD_NUT_PIN_LOCAL_Y
LEAD_NUT_PIN_LOCAL_Z = _front.LEAD_NUT_PIN_LOCAL_Z
NUT_PIN_CLIP_X = _front.NUT_PIN_CLIP_X
PIN_Y_BOX_CLAMP = _front.PIN_Y
PIN_Z_BOX_CLAMP = _front.PIN_Z

# Rack closure consumes the canonical front through this partially initialized
# module, so the variables above must be assigned first.
_t = start_timer('full.apply_rack_closure')
import apply_v60_rack_closure as _rack_closure  # noqa: E402
stop_timer('full.apply_rack_closure', _t)

RIGHT_FULL = _rack_closure.RIGHT
LEFT_FULL = _rack_closure.LEFT
LOWER = _rack_closure.LOWER
RACK_NUT_RETAINER = _rack_closure.RACK_NUT_RETAINER
RACK_HAND_KNOB = _rack_closure.RACK_HAND_KNOB

# Final rack service thread is rebuilt from one explicit matched pair and
# witnessed in the final BRep.
_t = start_timer('full.apply_final_retainer_thread')
import apply_v60_retainer_thread_final as _retainer_final  # noqa: E402
stop_timer('full.apply_final_retainer_thread', _t)

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

_t = start_timer('full.build_lightweight_final_assembly')
import apply_v60_final_assembly as _final_assembly  # noqa: F401,E402
stop_timer('full.build_lightweight_final_assembly', _t)

print(
    'V60_STAGE repositioned outboard box-clamp front + integrated outer DROPs + explicit rack retainer threads active',
    flush=True,
)
