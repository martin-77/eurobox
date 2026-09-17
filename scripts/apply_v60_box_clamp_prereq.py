"""Prepare the canonical v60 front for the restored v50 box-clamp mechanism.

This module fixes two prerequisites before ``apply_v60_front_final`` runs:

1. The removable RH8x2 lead-nut cartridge gets a female cutter derived from
   the *actual* v60 spindle master, with the proven v50 print clearances and
   the exact same helix tessellation/phase as the male thread.
2. The smooth spindle corridor is cleared for the complete 43.5 mm spindle
   length plus the full 5.5 mm opening travel.

The final v60 front places the two drive axes outside the 160 mm main clamp
face.  The production hard checks in ``apply_v60_front_final`` remain
authoritative; this module deliberately does not relax any validation
thresholds.
"""

import os

import FreeCAD as App
import Part

import build_v60_full_baseline as F
from v60_timing import start_timer, stop_timer

C = F.C

# Outboard drive architecture: 160 mm main clamp face ends at +/-80 mm.  The
# spindle axes sit 8 mm outside that face and are picked up by narrow moving
# plate ears.  +/-88 also keeps the 22 mm fixed cartridge bosses inside the
# existing approx. +/-99 mm front structural envelope.
SPINDLE_X = (-88.0, 88.0)
LEAD_RADIAL_CLEARANCE = 0.18
LEAD_FLANK_CLEARANCE = 0.12

# These are the actual male profile values used by build_v60_full_baseline.
MALE_ROOT_W = 0.58
MALE_CREST_W = 0.24
FEMALE_ROOT_W = MALE_ROOT_W + 2.0 * LEAD_FLANK_CLEARANCE
FEMALE_CREST_W = MALE_CREST_W + 2.0 * LEAD_FLANK_CLEARANCE
FEMALE_CORE_R = F.THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
FEMALE_MAJOR_R = F.THREAD_MAJOR / 2.0 + LEAD_RADIAL_CLEARANCE

# The cartridge starts 15.8 mm behind the plate while the male thread starts
# 9.8 mm behind it.  The resulting 6.0 mm = 3*pitch phase offset is intentional.
# Generate the female master over the *same full 22.2 mm length* as the male,
# then crop the 14 mm cartridge window at that exact phase.  This keeps the
# OpenSCAD slice planes identical to the already-built male master and avoids
# false BRep intersections caused by separately tessellating a 14 mm helix.
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
        q = q.cut(
            F.cyl_y(
                SPINDLE_CLEAR_R,
                SPINDLE_CLEAR_Y1 - SPINDLE_CLEAR_Y0,
                sx,
                SPINDLE_CLEAR_Y0,
                F.SPINDLE_Z,
            )
        ).removeSplitter()
    C.require_single(q, 'full box-clamp spindle sweep clearance')
    return q


stage('derive phase-aligned cartridge female RH8x2 cutter from actual v60 male master')
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

# import_scad_shape already returns and validates one bounded solid.  Do not
# intersect it again with a nearly coincident cylinder: OCC can reduce that
# mesh-derived BRep to a valid non-solid even though the imported thread itself
# is fine.  Keep the full master untouched and use a simple planar box only for
# the axial phase crop below.
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

# Direct containment witness against the exact male master segment.  This is
# deliberately stronger than waiting for the assembled cartridge collision
# gate: at nominal phase every bit of male thread in the 14 mm engagement must
# already be inside the female cutter before coordinate transforms are applied.
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

stage('clear complete outboard spindle sweep from structural core')
_t = start_timer('box_prereq.clear_outboard_spindle_sweep_from_structural_core')
C.RIGHT = cut_full_spindle_sweep(C.RIGHT)
C.LEFT = C.mirror_x(C.RIGHT)
stop_timer('box_prereq.clear_outboard_spindle_sweep_from_structural_core', _t)

# apply_v60_front_final builds its cage as a separate solid and only then fuses
# it to C.RIGHT.  Clear the same complete spindle sweep from that one cage too.
# Restore the original helper immediately afterwards so this compatibility hook
# cannot affect later geometry stages.
_original_fuse_seq = C.fuse_seq


def _fuse_seq_with_box_clamp_clearance(shapes, label):
    q = _original_fuse_seq(shapes, label)
    if label == 'v60-v50-style-separate-nut-box-clamp-cage':
        _tc = start_timer('box_prereq.clear_outboard_spindle_sweep_from_final_cage')
        q = cut_full_spindle_sweep(q)
        C.fuse_seq = _original_fuse_seq
        stop_timer('box_prereq.clear_outboard_spindle_sweep_from_final_cage', _tc)
        stage('cleared complete outboard spindle sweep from final box-clamp cage')
    return q


C.fuse_seq = _fuse_seq_with_box_clamp_clearance

stage(
    'ready: phase-matched cartridge thread + outboard spindle axes '
    f'{SPINDLE_X} + full sweep Y={SPINDLE_CLEAR_Y0:.3f}..{SPINDLE_CLEAR_Y1:.3f} mm'
)
