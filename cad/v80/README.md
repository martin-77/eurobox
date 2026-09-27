# Eurobox carrier V80

V80 is the consolidated working set. It gathers the currently selected parts in one version folder instead of requiring a mix of V60 and V70 directories.

## Included from V60

The geometry is copied unchanged; only the V80 filenames/path are new:

- `base_left`
- `base_right`
- `lead_nut`
- `rack_lower`
- `rack_nut_retainer`
- `rack_hand_knob`
- `rack_pin`

Where present in V60, matching FCStd, STEP and STL files are copied into V80 byte-for-byte.

## Included from V70

Current clamp mechanism:

- `clamp` = V70 clamp v6
- `bushing_half` = V70 bushing half v5
- `lead_screw` = V70 lead screw v5
- `knob` = V70 knob v5
- `lead_nut_pin_clip` = V70 lead-nut pin clip v4
- `rack_pin_clip` = V70 rack-pin clip v4

Their SCAD and validated binary STL blobs are copied byte-for-byte into V80.

## Intentionally NOT included

The corrected lead-nut retaining pin itself is still not promoted into V80 yet.

The two approved V70 v4 clips are now included in V80. They retain the V50 plate-retainer clip topology (closed circular ring with a narrow rectangular side opening) and their validated binary STL blobs are reused unchanged.

The open correction is documented in:

`cad/v70/LEAD_NUT_PIN_CORRECTION.md`

## Clamp hardware quantities

Per clamp plate / side module:

- 1 × clamp
- 2 × lead screw
- 2 × knob
- 4 × bushing half (two halves per screw)

Frozen/reused base-side quantities should follow the V60 assembly until the V80 assembly drawing is regenerated.

## Provenance

V80 was created from repository HEAD:

`1a2beba6e2ab7973f8d8ca41061bbaabc297c9c4`

No V60/V70 source geometry was regenerated during consolidation. Binary parts are referenced by their existing Git blobs so copied files remain byte-identical to the selected source versions.

Clip promotion commit source: `826498f8c1946e2297675bba36959e4a0468d5f9`.
