import sys

sys.path.insert(0, 'scripts')

import build_v60 as C
import build_v60_continuous_carrier  # mutates C.RIGHT/C.LEFT to canonical clean core
import run_v60_full_ci  # executes full mechanism build, mesh gates and exports
import apply_v60_rack_closure  # rebuilds canonical rack closure and re-exports revised parts
import check_v60_rack_closure_exports  # revalidates final handed meshes and published report
