"""Prepare the canonical v60 front for the restored v50 box-clamp mechanism.

This module fixes two prerequisites before ``apply_v60_front_final`` runs:

1. The removable RH8x2 lead-nut cartridge gets a female cutter derived from
   the *actual* v60 spindle profile using the proven v50 print clearances.
   The previous v60 female profile was an independently tuned legacy profile
   and collided with the male spindle even at the nominal phase.
2. The smooth spindle corridor is cleared for the complete 43.5 mm spindle
   length plus the full 5.5 mm opening travel.  The previous corridor started
   at CAGE_Y0 and therefore cut only the front part of the spindle sweep.

The production hard checks in ``apply_v60_front_final`` remain authoritative;
this module deliberately does not relax any validation thresholds.
"""

import os

import Part

import build_v60_full_baseline as F

C = F.C

SPINDLE_X = (-65.0, 65.0)
LEAD_RADIAL_CLEARANCE = 0.18
LEAD_FLANK_CLEARANCE = 0.12

# These are the actual male profile values used by build_v60_full_baseline.
MALE_ROOT_W = 0.58
MALE_CREST_W = 0.24
FEMALE_ROOT_W = MALE_ROOT_W + 2.0 * LEAD_FLANK_CLEARANCE
FEMALE_CREST_W = MALE_CREST_W + 2.0 * LEAD_FLANK_CLEARANCE
FEMALE_CORE_R = F.THREAD_CORE_R + LEAD_RADIAL_CLEARANCE
FEMALE_MAJOR_R = F.THREAD_MAJOR / 2.0 + LEAD_RADIAL_CLEARANCE

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


stage('derive cartridge female RH8x2 cutter from actual v60 male profile')
female_scad = os.path.join(C.OUT, 'v60_box_clamp_matched_female_RH8x2.scad')
F.write_thread_scad(
    female_scad,
    FEMALE_CORE_R,
    FEMALE_MAJOR_R,
    F.THREAD_PITCH,
    F.NUT_THREAD_LEN,
    FEMALE_ROOT_W,
    FEMALE_CREST_W,
)
female_z = F.import_scad_shape(female_scad).common(
    Part.makeCylinder(FEMALE_MAJOR_R + 0.06, F.NUT_THREAD_LEN)
).removeSplitter()
C.require_single(female_z, 'matched cartridge female RH8x2 cutter')
F.FEMALE_NEGY = F.rotate_z180(F.z_to_y(female_z))
C.require_single(F.FEMALE_NEGY, 'matched cartridge female RH8x2 cutter -Y')

stage('clear complete spindle sweep from structural core')
C.RIGHT = cut_full_spindle_sweep(C.RIGHT)
C.LEFT = C.mirror_x(C.RIGHT)

# apply_v60_front_final builds its cage as a separate solid and only then fuses
# it to C.RIGHT.  Clear the same complete spindle sweep from that one cage too.
# Restore the original helper immediately afterwards so this compatibility hook
# cannot affect later geometry stages.
_original_fuse_seq = C.fuse_seq


def _fuse_seq_with_box_clamp_clearance(shapes, label):
    q = _original_fuse_seq(shapes, label)
    if label == 'v60-v50-style-separate-nut-box-clamp-cage':
        q = cut_full_spindle_sweep(q)
        C.fuse_seq = _original_fuse_seq
        stage('cleared complete spindle sweep from final box-clamp cage')
    return q


C.fuse_seq = _fuse_seq_with_box_clamp_clearance

stage(
    'ready: matched cartridge thread + full spindle sweep '
    f'Y={SPINDLE_CLEAR_Y0:.3f}..{SPINDLE_CLEAR_Y1:.3f} mm'
)
