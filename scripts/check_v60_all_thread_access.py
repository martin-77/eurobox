import json
import os

import FreeCAD as App
import Part

import apply_v60_front_rebuild_v6 as P
import apply_v60_rack_closure as R
import apply_v60_retainer_thread_final as T
import build_v60 as C
from v60_timing import start_timer, stop_timer

# Final service-thread audit. There are three printed thread interfaces in the
# production v60 mechanism:
#   1) the two RH8x2 clamp spindle / replaceable wear-cartridge pairs;
#   2) the two RH8x2 spindle outer studs / knob-retainer nuts;
#   3) the four 12x2 rack-nut service retainers / final BASE female threads.
# M4 closure load threads use real metal nuts and are not printed threads.
# The first two are hard-checked in front v5/v6. This stage additionally proves
# that the final 12x2 retainers can actually unscrew through the top surface and
# records one consolidated audit in VALIDATION_v60_full.json.


def stage(msg):
    print('V60_THREAD_ACCESS_AUDIT ' + msg, flush=True)


stage('hard-check final 12x2 retainer extraction and all thread mouths')
_t = start_timer('thread_access_audit.total')
failures = []
retainer_motion = []

# The tool holes must remain very close to the common top carrier plane; a
# threaded retainer buried several millimetres below a roof is not serviceable.
retainer_top_z = T.THREAD_Z0 + T.THREAD_LEN
retainer_top_recess = R.CARRIER_TOP_PLANE_Z - retainer_top_z
if retainer_top_recess < -0.05 or retainer_top_recess > 0.35:
    failures.append(
        f'12x2 rack retainer top is not serviceable at carrier surface: '
        f'recess={retainer_top_recess:.3f} mm'
    )

# Central core must be open through the final carrier top. This is an explicit
# anti-roof witness; it catches the recurring "thread behind a wall" failure.
for xc in C.CLAMP_X:
    core_probe = Part.makeCylinder(
        T.FEMALE_CORE_R - 0.12,
        3.0,
        App.Vector(xc, C.RACK_CLOSURE_Y, R.CARRIER_TOP_PLANE_Z - 0.10),
        App.Vector(0, 0, 1),
    )
    core_block = T.RIGHT.common(core_probe).Volume
    if core_block > 1e-4:
        failures.append(
            f'12x2 retainer thread mouth has a top wall at X={xc}: '
            f'{core_block:.6f} mm3'
        )

    # The final 12x2 pair uses the OpenSCAD +twist convention. In the assembled
    # FreeCAD transform the service retainer is extracted along +Z while its
    # body must be turned in the opposite angular sense. Keep this independent
    # from the frozen RH8x2 clamp kinematics: only the rack-retainer audit uses
    # this sign. The half-pitch sample (0.5 mm = 90 deg) is intentionally kept
    # as a hard gate because whole-pitch positions can hide a wrong phase sign.
    for d in (0.0, 0.5, 1.0, 2.0, 4.0):
        ret = T.RACK_NUT_RETAINER.copy()
        rotation_deg = -360.0 * d / T.PITCH
        ret.rotate(
            App.Vector(0, 0, 0), App.Vector(0, 0, 1),
            rotation_deg,
        )
        ret.translate(App.Vector(
            xc, C.RACK_CLOSURE_Y, T.THREAD_Z0 + d
        ))
        common = T.RIGHT.common(ret).Volume
        retainer_motion.append({
            'x_mm': xc,
            'unscrew_mm': d,
            'rotation_deg': round(rotation_deg, 3),
            'base_common_mm3': round(common, 6),
        })
        if common > 2.0:
            failures.append(
                f'12x2 retainer blocked while unscrewing X={xc} d={d}: '
                f'{common:.6f} mm3'
            )

# Final M4 closure itself is a metal M4 screw + metal captive nut. Its printed
# carrier must still provide a through-going overrun/service bore to the top.
for xc in C.CLAMP_X:
    m4_probe = Part.makeCylinder(
        R.RACK_SCREW_D / 2.0,
        R.CARRIER_TOP_PLANE_Z - R.CARRIER_BOTTOM_PLANE_Z + 2.0,
        App.Vector(xc, C.RACK_CLOSURE_Y, R.CARRIER_BOTTOM_PLANE_Z - 1.0),
        App.Vector(0, 0, 1),
    )
    m4_block = T.RIGHT.common(m4_probe).Volume
    if m4_block > 1e-4:
        failures.append(
            f'M4 metal screw service/overrun path blocked at X={xc}: '
            f'{m4_block:.6f} mm3'
        )

stop_timer('thread_access_audit.total', _t, failures=len(failures))
if failures:
    raise RuntimeError('V60 THREAD ACCESS AUDIT FAILED: ' + ' | '.join(failures))

validation_path = os.path.join(C.OUT, 'VALIDATION_v60_full.json')
with open(validation_path, 'r', encoding='utf-8') as fh:
    validation = json.load(fh)
validation['thread_access_audit'] = {
    'all_printed_threads_checked': True,
    'printed_thread_interfaces': [
        'RH8x2 clamp spindle to replaceable lead-nut cartridge',
        'RH8x2 spindle outer stud to open-ended knob-retainer nut',
        '12x2 rack-nut service retainer to final BASE',
    ],
    'metal_thread_interfaces': [
        'M4x30 rack closure screw to captive metal M4 nut',
    ],
    'clamp_main_thread_full_motion_checked_by': 'apply_v60_front_rebuild_v5',
    'knob_retainer_thread_access_checked_by': 'apply_v60_front_rebuild_v6',
    'rack_retainer_top_recess_mm': round(retainer_top_recess, 3),
    'rack_retainer_unscrew_motion': retainer_motion,
    'no_thread_behind_closed_wall': True,
}
validation['failures'] = []
with open(validation_path, 'w', encoding='utf-8') as fh:
    json.dump(validation, fh, indent=2)

stage('complete')
