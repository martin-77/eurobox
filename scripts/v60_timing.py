"""Lightweight runtime timing for the v60 CAD pipeline.

Every timed section prints one machine-readable log line and updates a JSON
report in build_v60/TIMING_v60.json.  The geometry code can therefore be
profiled on GitHub-hosted runners without adding a heavyweight profiler or
changing OCC behaviour.
"""

import json
import os
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_OUT = os.path.join(_ROOT, 'build_v60')
_REPORT = os.path.join(_OUT, 'TIMING_v60.json')
_PROCESS_T0 = time.perf_counter()
_RECORDS = []


def _write_report():
    os.makedirs(_OUT, exist_ok=True)
    payload = {
        'schema': 1,
        'process_elapsed_s': round(time.perf_counter() - _PROCESS_T0, 6),
        'records': _RECORDS,
    }
    tmp = _REPORT + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)
    os.replace(tmp, _REPORT)


def start_timer(label):
    """Start a section timer and emit a visible START marker."""
    print(f'V60_TIMING START {label}', flush=True)
    return time.perf_counter()


def stop_timer(label, started, **metadata):
    """Stop a section timer, persist it and return elapsed seconds."""
    elapsed = time.perf_counter() - started
    record = {
        'index': len(_RECORDS) + 1,
        'label': str(label),
        'seconds': round(elapsed, 6),
        'process_elapsed_s': round(time.perf_counter() - _PROCESS_T0, 6),
    }
    if metadata:
        record['metadata'] = metadata
    _RECORDS.append(record)
    print(
        f"V60_TIMING END {label} seconds={elapsed:.6f} "
        f"process_elapsed={record['process_elapsed_s']:.6f}",
        flush=True,
    )
    _write_report()
    return elapsed


def checkpoint(label, **metadata):
    """Record an instantaneous checkpoint in the same timing report."""
    record = {
        'index': len(_RECORDS) + 1,
        'label': str(label),
        'seconds': 0.0,
        'process_elapsed_s': round(time.perf_counter() - _PROCESS_T0, 6),
    }
    if metadata:
        record['metadata'] = metadata
    _RECORDS.append(record)
    print(
        f"V60_TIMING CHECKPOINT {label} "
        f"process_elapsed={record['process_elapsed_s']:.6f}",
        flush=True,
    )
    _write_report()
