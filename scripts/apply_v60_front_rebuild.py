"""Compatibility import for the canonical clean v60 front.

The former experimental rebuild was replaced wholesale.  Keep this module name
stable for build/assembly imports while the actual construction lives in the
from-scratch v2 builder.
"""

from apply_v60_front_rebuild_v2 import *  # noqa: F401,F403
