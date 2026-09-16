import sys

sys.path.insert(0, 'scripts')

import build_v60 as C
import build_v60_continuous_carrier  # mutates C.RIGHT/C.LEFT to canonical clean core
import run_v60_full_ci  # imports canonical build_v60_full; current rack closure is built there
import check_v60_rack_closure_exports  # revalidates final handed meshes and published report
