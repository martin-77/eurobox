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
- `lead_nut_retaining_pin` = recalculated V70 retaining pin v2 geometry

Their SCAD and validated binary STL blobs are copied/reused without ASCII STL conversion.

## Lead-nut retaining pin / clip validation

The lead-nut retaining pin was recalculated against the frozen V60/V80 service geometry rather than against the rejected short pin:

- head pocket: X = -14.35 .. -11.65 mm, Ø6.70 mm
- two retaining walls: X = -11.35 .. -8.20 mm and +8.20 .. +11.35 mm
- clip pocket: X = +11.20 .. +13.20 mm, Ø7.10 mm
- complete service path: X = -14.35 .. +15.05 mm, Ø3.40 mm shaft cradle

Released pin geometry:

- head: X = -13.65 .. -11.65 mm, Ø6.50 mm
- shaft: X = -11.65 .. +11.40 mm, Ø3.00 mm
- groove: X = +11.40 .. +13.00 mm, Ø2.40 mm
- tip: X = +13.00 .. +14.50 mm, Ø3.00 mm
- total length: 28.15 mm

Fit margins:

- head pocket diametral clearance: 0.20 mm
- shaft cradle diametral clearance: 0.40 mm
- pin end to service-path end: 0.55 mm
- clip groove width: 1.60 mm
- clip thickness: 1.30 mm -> 0.30 mm total axial clearance
- clip relaxed ID: Ø2.10 mm on Ø2.40 mm groove
- clip OD: Ø7.00 mm in Ø7.10 mm pocket
- clip opening: 1.60 mm

The clip keeps the approved V50-style closed-ring topology. The previously rejected short pin and the earlier mismatched clip variants are not used.

## Clamp hardware quantities

Per clamp plate / side module:

- 1 × clamp
- 2 × lead screw
- 2 × knob
- 4 × bushing half (two halves per screw)

Per complete side/base assembly, retain the V60 quantity of lead-nut retaining hardware required by the two lead-nut cartridges.

## Provenance

V80 was created from repository HEAD:

`1a2beba6e2ab7973f8d8ca41061bbaabc297c9c4`

No V60/V70 source geometry was regenerated during the initial consolidation. Binary parts are referenced by their existing Git blobs so copied files remain byte-identical to the selected source versions.

Clip promotion source: `826498f8c1946e2297675bba36959e4a0468d5f9`.

Lead-nut retaining pin source: `91df19c673b58b4f080d4ed262167e199e63f9a0`.
