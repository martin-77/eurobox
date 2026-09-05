// Eurobox v50 automated preview
// Generated from the actual STL outputs produced by GitHub Actions.
// Coordinates: X riding direction, Y transverse, Z up.
// Global truth: rack tube centres Y = +/-55.335 mm; Eurobox outer edges Y = +/-300 mm.

$fn = 72;
RACK_CTC = 110.67;
RY = RACK_CTC/2;
LY = -RACK_CTC/2;
BOX_EDGE_LOCAL = 244.665;
BOX_EDGE_R = RY + BOX_EDGE_LOCAL;   // +300.000
BOX_EDGE_L = LY - BOX_EDGE_LOCAL;   // -300.000
RIM = 16.45;
RIM_BOTTOM_Z = 23.09;
BOX_SUPPORT_Z = 39.54;

module tube_x(y=0, x0=-120, len=240, z=0, d=12.42) {
  translate([x0,y,z]) rotate([0,90,0]) cylinder(d=d,h=len);
}

module right_module() {
  translate([0,RY,0]) {
    color([0.72,0.72,0.76]) import("../build_v50/eurobox_v50_base.stl", convexity=10);
    color([0.20,0.42,0.78]) {
      translate([-90,0,0]) import("../build_v50/eurobox_v50_rack_lower.stl", convexity=10);
      translate([ 90,0,0]) import("../build_v50/eurobox_v50_rack_lower.stl", convexity=10);
    }
    color([0.85,0.45,0.18]) import("../build_v50/eurobox_v50_clamp_plate.stl", convexity=10);
  }
}

module left_module() {
  // Same printable parts; whole local module is rotated 180 degrees around Z,
  // then placed on the left rack tube. This makes local +Y point outward (-global Y).
  translate([0,LY,0]) rotate([0,0,180]) {
    color([0.72,0.72,0.76]) import("../build_v50/eurobox_v50_base.stl", convexity=10);
    color([0.20,0.42,0.78]) {
      translate([-90,0,0]) import("../build_v50/eurobox_v50_rack_lower.stl", convexity=10);
      translate([ 90,0,0]) import("../build_v50/eurobox_v50_rack_lower.stl", convexity=10);
    }
    color([0.85,0.45,0.18]) import("../build_v50/eurobox_v50_clamp_plate.stl", convexity=10);
  }
}

module box_reference() {
  // Only the two lower side-rim strips are shown solid-translucent.
  // Their OUTER faces are exactly Y = +/-300 mm.
  %color([0.20,0.70,0.35,0.32]) {
    translate([-200, BOX_EDGE_R-RIM, RIM_BOTTOM_Z]) cube([400,RIM,RIM]);
    translate([-200, BOX_EDGE_L,     RIM_BOTTOM_Z]) cube([400,RIM,RIM]);
  }
  // Very faint 600 x 400 underside plane at support height.
  %color([0.20,0.70,0.35,0.10]) translate([-200,-300,BOX_SUPPORT_Z]) cube([400,600,0.6]);
}

module arrow_y(y0, y1, z=56, x=0) {
  len = abs(y1-y0)-8;
  dir = y1 > y0 ? 1 : -1;
  color([0.75,0.10,0.10]) {
    translate([x,y0,z]) rotate([dir>0?-90:90,0,0]) cylinder(d=3,h=max(len,1));
    translate([x,y1,z]) rotate([dir>0?-90:90,0,0]) cylinder(r1=6,r2=0,h=12);
  }
}

module label(txt, x, y, z=58, size=12) {
  color([0.08,0.08,0.08]) translate([x,y,z]) rotate([0,0,90])
    linear_extrude(height=0.8) text(txt,size=size,halign="center",valign="center");
}

right_module();
left_module();
color([0.18,0.18,0.18]) {
  tube_x(RY);
  tube_x(LY);
}
box_reference();

// Orientation markers: arrows always point from rack centre toward the Eurobox side.
arrow_y(RY+20, BOX_EDGE_R-28, 58, 0);
arrow_y(LY-20, BOX_EDGE_L+28, 58, 0);
label("RIGHT / +Y OUTBOARD", 0, 178, 60, 11);
label("LEFT / -Y OUTBOARD", 0, -178, 60, 11);
label("BOX EDGE +300", 155, 292, 60, 9);
label("BOX EDGE -300", -155, -292, 60, 9);
