// Eurobox v50 automated preview
// Generated from the actual STL outputs produced by GitHub Actions.
// Coordinates: X riding direction, Y transverse/outward to box, Z up.

$fn = 72;

module tube_x(x0=-120, len=240, y=0, z=0, d=12.42) {
  translate([x0,y,z]) rotate([0,90,0]) cylinder(d=d,h=len);
}

module assembly() {
  // Structural base, already contains both rack-clamp stations and both arms.
  color([0.72,0.72,0.76]) import("../build_v50/eurobox_v50_base.stl", convexity=10);

  // Two moving rack lower jaws in closed position.
  color([0.20,0.42,0.78]) {
    translate([-90,0,0]) import("../build_v50/eurobox_v50_rack_lower.stl", convexity=10);
    translate([ 90,0,0]) import("../build_v50/eurobox_v50_rack_lower.stl", convexity=10);
  }

  // Clamp plate, closed.
  color([0.85,0.45,0.18]) import("../build_v50/eurobox_v50_clamp_plate.stl", convexity=10);

  // Real rack tube surrogate at the measured Ø12.42 interface.
  color([0.18,0.18,0.18]) tube_x();

  // Eurobox lower rim surrogate: inner face Y=228.215, outer edge Y=244.665,
  // bottom Z=23.09, top/support Z=39.54.
  %color([0.2,0.7,0.35,0.28])
    translate([-200,228.215,23.09]) cube([400,16.45,16.45]);
}

assembly();
