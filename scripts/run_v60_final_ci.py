import sys

sys.path.insert(0, 'scripts')

# Importing this module mutates the canonical build_v60 module's RIGHT/LEFT
# solids to the final closed-root geometry. run_v60_full_ci then imports the
# same already-loaded build_v60 module and performs the normal full hard checks,
# STL mirror proof, installed-orientation checks and exports.
import build_v60_core_final  # noqa: F401

exec(compile(open('scripts/run_v60_full_ci.py', 'r', encoding='utf-8').read(),
             'scripts/run_v60_full_ci.py', 'exec'))
