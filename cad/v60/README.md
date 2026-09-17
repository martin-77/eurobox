# Eurobox carrier v60

Canonical clean rebuild generated and hard-validated by `scripts/build_v60.py`, `scripts/build_v60_continuous_carrier.py` and `scripts/build_v60_full.py`.

Structural principle: one continuous rack-side carrier. The two rack clamps and the rear stop hang from this carrier; the long box-support holms fuse into the same load path.

- `FCStd/` — individual editable FreeCAD parts
- `STEP/` — neutral CAD exports
- `STL/` — printable handed meshes and removable clamp hardware
- `assembly/` — installed-orientation PNG
- `validation/` — machine-readable hard-check and timing reports
- workflow artifact `eurobox-v60-complete` — complete generated FreeCAD assembly and all proof outputs

The box clamp keeps a 160 mm central clamp face. Its front assembly position is validated separately by the production front-position stage. The working RH8x2 lead nut is a replaceable cartridge; its spindle, 30 mm hand knob and open-ended RH8x2 knob retainer have explicit full-travel service-access checks. The rack closure retains its explicit matched 12x2 service-retainer thread pair with a hard top-access/unscrew audit. No printed working thread is accepted behind a closed wall.

`validation/TIMING_v60.json` records measured stage/operation durations from the GitHub runner so expensive OCC operations can be optimized from data rather than guesswork.
