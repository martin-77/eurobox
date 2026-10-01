# Eurobox carrier v100

V100 keeps the complete released V90 design and changes only the two handed bases.

A local relief is added between the two rack clamps where the bicycle-rack/frame pin crosses the rack tube.

Geometry:
- rack tube: Ø12.42 mm
- reference rack-clamp width: 28 mm
- relief width: 56 mm = 2 × clamp width
- relief X: -28 .. +28 mm
- nearest relief edge is 52 mm from either ±80 mm rack-clamp centre (~1.86 clamp widths)
- relief is only on the +Y/front side
- the cut starts exactly at the tube tangent Y=+6.21 mm
- the complete cylindrical upper saddle/contact surface remains unchanged
- height, tube support and all V90 clamp/guide geometry are unchanged

Only base_left and base_right are regenerated. Every other component is promoted byte-for-byte from V90.

All STL files are canonical binary STL. ASCII STL is rejected by the build/publish gate.
