import importlib.util
import os
import sys

sys.path.insert(0, 'scripts')

import build_v60 as C
import build_v60_continuous_carrier  # mutates C.RIGHT/C.LEFT to canonical clean core

# FreeCADCmd has re-entered run_v60_full_ci while the canonical front was still
# being built.  That applied the plate/spindle corridor cuts a second time to an
# already-mutated OCC shape and produced an invalid BRep.  Load the full CI
# explicitly and register it under both names before executing any of its code.
# Any nested import therefore resolves to this same in-progress module instead
# of executing the builder a second time.
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
