import sys

sys.path.insert(0, 'scripts')
import build_v60 as C

_original_require_single = C.require_single

def traced_require_single(shape, label):
    print(f'V60_CHECKPOINT require_single START {label}', flush=True)
    print(f'V60_CHECKPOINT shape {label}: null={shape.isNull()} valid={shape.isValid()} solids={len(shape.Solids)}', flush=True)
    result = _original_require_single(shape, label)
    print(f'V60_CHECKPOINT require_single OK {label}', flush=True)
    return result

C.require_single = traced_require_single
print('V60_CHECKPOINT core import complete', flush=True)
import build_v60_full
print('V60_CHECKPOINT full module complete', flush=True)
