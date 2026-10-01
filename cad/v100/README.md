# Eurobox carrier v100

V100 keeps the released V90 design and adds two local service changes.

Base/frame relief:
- rack tube: Ø12.42 mm
- reference rack-clamp width: 28 mm
- relief width: 56 mm = 2 × clamp width
- relief X: -28 .. +28 mm
- nearest relief edge is 52 mm from either ±80 mm rack-clamp centre (~1.86 clamp widths)
- relief is only on the +Y/front side
- the cut starts at the rack-tube centre plane Y=0
- the relief rises to the actual upper saddle/contact level Z=+6.31 mm
- the upper tube-support/contact surface itself remains unchanged

Rack Lower:
- the existing Ø5.0 mm M4 clearance bore at Y=+11 mm is opened toward +Y/front
- open slot width: 5.0 mm
- slot runs from Y=+11 to +19 mm, through the complete closure tongue
- the Lower can therefore swing up around a screw that remains threaded in the Upper
- final clamping/retention is provided by the hand knob

V100-native regenerated parts are base_left, base_right and rack_lower. Every other component is promoted byte-for-byte from V90.

All STL files are canonical binary STL. ASCII STL is rejected by the build/publish gate.
