import importlib.util
import os
import sys
import traceback

sys.path.insert(0, 'scripts')

import build_v60 as C

# FreeCADCmd is entering this driver a second time while the first invocation is
# still inside the box-clamp hard checks.  A second execution is destructive
# because the OCC source objects are intentionally mutated in-place.  Keep the
# driver idempotent and print the complete Python stack on any nested execution
# so the caller remains visible in the Actions log without corrupting geometry.
if getattr(C, '_V60_CONTINUOUS_CI_ACTIVE', False):
    print('V60_CONTINUOUS_CI REENTRY SUPPRESSED', flush=True)
    print(''.join(traceback.format_stack()), flush=True)
else:
    C._V60_CONTINUOUS_CI_ACTIVE = True

    import build_v60_continuous_carrier  # mutates C.RIGHT/C.LEFT to canonical clean core

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
    _spec.loader.exec_module(_full_ci)
    print('V60_CONTINUOUS_CI full-CI module completed once', flush=True)

    import check_v60_rack_closure_exports  # revalidates final handed meshes and published report

    C._V60_CONTINUOUS_CI_ACTIVE = False
    print('V60_CONTINUOUS_CI complete', flush=True)
