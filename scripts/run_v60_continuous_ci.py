import importlib.util
import os
import sys
import traceback

sys.path.insert(0, 'scripts')

import build_v60 as C
from v60_timing import start_timer, stop_timer

# Keep the driver idempotent. A second execution in the same OCC process would
# mutate the canonical geometry twice and invalidate timing as well as checks.
if getattr(C, '_V60_CONTINUOUS_CI_ACTIVE', False):
    print('V60_CONTINUOUS_CI REENTRY SUPPRESSED', flush=True)
    print(''.join(traceback.format_stack()), flush=True)
else:
    C._V60_CONTINUOUS_CI_ACTIVE = True
    _t_all = start_timer('ci.total_freecad_pipeline')

    _t = start_timer('ci.build_continuous_carrier_core')
    import build_v60_continuous_carrier  # mutates C.RIGHT/C.LEFT to canonical clean core
    stop_timer('ci.build_continuous_carrier_core', _t)

    # Register the full-CI module before executing it as an additional guard
    # against imports through either the flat scripts path or package-like name.
    _full_ci_path = os.path.join(os.path.dirname(__file__), 'run_v60_full_ci.py')
    _spec = importlib.util.spec_from_file_location('run_v60_full_ci', _full_ci_path)
    if _spec is None or _spec.loader is None:
        raise RuntimeError('Could not create import spec for run_v60_full_ci.py')
    _full_ci = importlib.util.module_from_spec(_spec)
    sys.modules['run_v60_full_ci'] = _full_ci
    sys.modules['scripts.run_v60_full_ci'] = _full_ci
    print('V60_CONTINUOUS_CI registered single full-CI module before execution', flush=True)

    _t = start_timer('ci.full_mechanism_build_and_hard_checks')
    _spec.loader.exec_module(_full_ci)
    stop_timer('ci.full_mechanism_build_and_hard_checks', _t)
    print('V60_CONTINUOUS_CI full-CI module completed once', flush=True)

    _t = start_timer('ci.postvalidate_rack_closure_exports')
    import check_v60_rack_closure_exports  # revalidates final handed meshes and published report
    stop_timer('ci.postvalidate_rack_closure_exports', _t)

    C._V60_CONTINUOUS_CI_ACTIVE = False
    stop_timer('ci.total_freecad_pipeline', _t_all)
    print('V60_CONTINUOUS_CI complete', flush=True)
