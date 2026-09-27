# V70 retaining hardware v2 — physical-fit candidates

These parts stay in V70 until they have been physically accepted. Do not copy
them into V80 yet.

## Corrected lead-nut retaining pin

The rejected short pin used the lead-nut lug width instead of the complete
frozen BASE service geometry.

Frozen BASE interface:
- head pocket: X = -14.35 .. -11.65 mm
- clip pocket: X = +11.20 .. +13.20 mm
- service path: X = -14.35 .. +15.05 mm

Corrected candidate:
- head: Ø6.50 x 2.00 mm, X = -13.65 .. -11.65
- shaft: Ø3.00 mm, X = -11.65 .. +11.40
- retaining groove: Ø2.40 x 1.60 mm, X = +11.40 .. +13.00
- end tip: Ø3.00 x 1.50 mm, X = +13.00 .. +14.50
- total length: **28.15 mm**

The groove is centred in the existing 2.00 mm clip pocket, leaving 0.20 mm
pocket clearance at each axial side. The tip ends 0.55 mm before the frozen
service-path end.

## Tight clip rule

The clip is installed sideways directly into the reduced groove. It never has
to open over the larger shaft.

For the two clips still used by the current carrier:
- relaxed ID = groove diameter - 0.20 mm
- throat = relaxed ID - 0.10 mm
- flared entry = groove diameter + 0.20 mm
- thickness = 1.30 mm
- compact original C-clip form retained

Lead-nut pin clip:
- groove Ø2.40
- relaxed ID Ø2.20
- throat 2.10
- entry 2.60
- OD 6.40
- t 1.30
- groove width 1.60 => 0.15 mm axial clearance each side

Rack-pin clip:
- groove Ø3.10
- relaxed ID Ø2.90
- throat 2.80
- entry 3.30
- OD 6.40
- t 1.30

The old V60 plate-retainer clip is obsolete with the current two-piece bushing
+ lead-screw + knob clamp mechanism and is deliberately not rebuilt.

All three STL files in this test set are true binary STL Git blobs.
