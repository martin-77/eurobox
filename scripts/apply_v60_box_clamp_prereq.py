"""Prepare the matched RH8x2 cartridge cutter for the clean v60 front.

This stage now has one job only: derive the removable cartridge female cutter
from the exact production spindle master and prove phase containment.  It no
longer mutates the legacy structural core or monkey-patches ``fuse_seq``; the
new front builder owns all spindle/module clearances directly.
"""

import os

import FreeCAD as App
import Part

import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

C = F.C

# Final clean-front module axes.  They are direct construction datums, not a
# later +40 mm correction of an older symmetric front.
SPINDLE_X = (-48.0, 128.0)
LEAD_RADIAL_CLEARANCE = 0.18
LEAD_FLANK_CLEARANCE = 0.12

MALE_ROOT_W = 0.58
MALE_CREST_W = 0.24
FEMALE_ROOT_W = MALE_ROOT_W + 2.0 * LEAD_FLANK_CLEARANCE
FEMALE_CREST_W = MALE_CREST_W + 2.0 * LEAD_FLANK_CLEARANCE
FEMALE_CORE_R = F.THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
FEMALE_MAJOR_R = F.THREAD_MAJOR / 2.0 + LEAD_RADIAL_CLEARANCE

MALE_THREAD_START_Y = F.SPINDLE_LOCAL_JOURNAL + F.SPINDLE_LOCAL_SHOULDER
FEMALE_PHASE_Z0 = F.NUT_ANCHOR_OFFSET - MALE_THREAD_START_Y
if FEMALE_PHASE_Z0 < 0.0 or FEMALE_PHASE_Z0 + F.NUT_THREAD_LEN > F.LEAD_THREAD_LEN:
    raise RuntimeError('v60 lead-nut phase window falls outside the male RH8x2 master')

SPINDLE_TOTAL_LEN = (
    F.SPINDLE_LOCAL_JOURNAL
    + F.SPINDLE_LOCAL_SHOULDER
    + F.LEAD_THREAD_LEN
    + F.HEX_LEN
    + F.OUTER_STUD_LEN
)
SPINDLE_CLEARANCE_MARGIN = 0.80
SPINDLE_CLEAR_Y0 = (
    F.PLATE_SPINDLE_Y
    - F.PLATE_OPEN
    - SPINDLE_TOTAL_LEN
    - SPINDLE_CLEARANCE_MARGIN
)
SPINDLE_CLEAR_Y1 = F.PLATE_SPINDLE_Y - F.PLATE_Y + 0.50
SPINDLE_CLEAR_R = 5.90


def stage(msg):
    print('V60_BOX_CLAMP_PREREQ ' + msg, flush=True)


def cut_full_spindle_sweep(shape):
    q = shape
    for sx in SPINDLE_X:
        q = q.cut(F.cyl_y(
            SPINDLE_CLEAR_R,
            SPINDLE_CLEAR_Y1 - SPINDLE_CLEAR_Y0,
            sx, SPINDLE_CLEAR_Y0, F.SPINDLE_Z,
        )).removeSplitter()
    C.require_single(q, 'clean-front full spindle sweep clearance')
    return q


stage('derive phase-aligned cartridge female RH8x2 cutter from production spindle master')
_t = start_timer('box_prereq.compile_phase_matched_female_RH8x2')
female_scad = os.path.join(C.OUT, 'v60_box_clamp_matched_female_RH8x2.scad')
F.write_thread_scad(
    female_scad,
    FEMALE_CORE_R,
    FEMALE_MAJOR_R,
    F.THREAD_PITCH,
    F.LEAD_THREAD_LEN,
    FEMALE_ROOT_W,
    FEMALE_CREST_W,
)
female_full_z = F.import_scad_shape(female_scad)
C.require_single(female_full_z, 'full phase-matched cartridge female RH8x2 cutter')
stop_timer('box_prereq.compile_phase_matched_female_RH8x2', _t)

_t = start_timer('box_prereq.phase_crop_and_nominal_containment_witness')
WINDOW_HALF = max(FEMALE_MAJOR_R, F.THREAD_MAJOR / 2.0) + 1.0
phase_window = Part.makeBox(
    2.0 * WINDOW_HALF,
    2.0 * WINDOW_HALF,
    F.NUT_THREAD_LEN,
    App.Vector(-WINDOW_HALF, -WINDOW_HALF, FEMALE_PHASE_Z0),
)
female_z = female_full_z.common(phase_window).removeSplitter()
C.require_single(female_z, 'phase-windowed cartridge female RH8x2 cutter before rebase')
female_z.translate(App.Vector(0.0, 0.0, -FEMALE_PHASE_Z0))
C.require_single(female_z, 'phase-windowed cartridge female RH8x2 cutter')

male_segment = F.MALE_Z.common(phase_window).removeSplitter()
C.require_single(male_segment, 'nominal male RH8x2 cartridge engagement segment before rebase')
male_segment.translate(App.Vector(0.0, 0.0, -FEMALE_PHASE_Z0))
C.require_single(male_segment, 'nominal male RH8x2 cartridge engagement segment')
uncovered_male_volume = male_segment.cut(female_z).Volume
stage(f'nominal cutter uncovered male volume={uncovered_male_volume:.6f} mm3')
if uncovered_male_volume > 0.05:
    raise RuntimeError(
        'phase-aligned RH8x2 cartridge cutter does not contain actual male master: '
        f'{uncovered_male_volume:.6f} mm3 uncovered'
    )

F.FEMALE_NEGY = F.rotate_z180(F.z_to_y(female_z))
C.require_single(F.FEMALE_NEGY, 'matched cartridge female RH8x2 cutter -Y')
stop_timer('box_prereq.phase_crop_and_nominal_containment_witness', _t)

stage(
    'ready for clean modular front: axes '
    f'{SPINDLE_X}, spindle sweep Y={SPINDLE_CLEAR_Y0:.3f}..{SPINDLE_CLEAR_Y1:.3f} mm'
)
