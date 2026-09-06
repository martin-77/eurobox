// v50 final printable mesh generator
// Use:
//   openscad -D 'part="spindle"' -o <output.stl> final_print_meshes.scad
//   openscad -D 'part="rack_m4_nut"' -o <output.stl> final_print_meshes.scad
//
// The editable FreeCAD model remains the dimensional BRep/STEP authority.
// Selected helical printable meshes are emitted directly by OpenSCAD/CGAL
// because converting the helical mesh to BRep and tessellating it again can
// create open STL seams despite a valid OCC solid.

$fn=96;
part="spindle";

pitch=2.0;
core_r=3.25;
major_r=4.0;
root_w=0.58;
crest_w=0.24;

module rh_thread_z(length) {
  union() {
    cylinder(r=core_r,h=length,$fn=96);
    linear_extrude(height=length,
                   twist=360*length/pitch,
                   slices=ceil(length/pitch*28),
                   convexity=30)
      polygon(points=[
        [core_r-0.08,-root_w/2],
        [major_r,-crest_w/2],
        [major_r, crest_w/2],
        [core_r-0.08, root_w/2]
      ]);
  }
}

module hex_prism_z(af,h) {
  cylinder(r=af/sqrt(3),h=h,$fn=6);
}

module spindle_z() {
  union() {
    cylinder(r=3.0,h=0.42);
    translate([0,0,0.38]) cylinder(r=2.5,h=1.44);
    translate([0,0,1.78]) cylinder(r=3.0,h=6.24);
    translate([0,0,7.98]) cylinder(r=5.5,h=1.84);
    translate([0,0,9.78]) cylinder(r=core_r,h=23.04);
    translate([0,0,9.8])
      linear_extrude(height=23.0,
                     twist=360*23.0/pitch,
                     slices=ceil(23.0/pitch*28),
                     convexity=30)
        polygon(points=[
          [core_r-0.08,-root_w/2],
          [major_r,-crest_w/2],
          [major_r, crest_w/2],
          [core_r-0.08, root_w/2]
        ]);
    translate([0,0,32.78]) hex_prism_z(10.0,4.54);
    translate([0,0,37.28]) cylinder(r=core_r,h=7.02);
    translate([0,0,37.30])
      linear_extrude(height=7.0,
                     twist=360*7.0/pitch,
                     slices=ceil(7.0/pitch*28),
                     convexity=30)
        polygon(points=[
          [core_r-0.08,-root_w/2],
          [major_r,-crest_w/2],
          [major_r, crest_w/2],
          [core_r-0.08, root_w/2]
        ]);
  }
}

// Canonical printable rack nut: M4x0.7 RH, eight full turns over 5.6 mm.
// The helical thread forms the actual bore wall. The old Ø3.44 smooth core
// hid the thread behind a cylindrical wall; this is corrected to Ø3.32.
rack_m4_pitch=0.7;
rack_m4_nut_af=7.0;
rack_m4_nut_h=5.6;
rack_m4_crest_r=1.66;
rack_m4_groove_major_r=2.20;
rack_m4_minor_width=0.40;
rack_m4_major_width=0.30;
rack_m4_thread_len=rack_m4_nut_h+2*rack_m4_pitch;

module rack_m4_female_cutter() {
  translate([0,0,-rack_m4_pitch])
    union() {
      // Only open the bore to the female thread crest diameter. The helix then
      // cuts outward from this wall, so the remaining crest is exposed inside
      // the hole instead of sitting behind a larger smooth cylinder.
      cylinder(r=rack_m4_crest_r,h=rack_m4_thread_len,$fn=96);
      linear_extrude(height=rack_m4_thread_len,
                     twist=360*rack_m4_thread_len/rack_m4_pitch,
                     slices=ceil(rack_m4_thread_len/rack_m4_pitch*40),
                     convexity=40)
        polygon(points=[
          [rack_m4_crest_r-0.08,-rack_m4_minor_width/2],
          [rack_m4_groove_major_r,-rack_m4_major_width/2],
          [rack_m4_groove_major_r, rack_m4_major_width/2],
          [rack_m4_crest_r-0.08, rack_m4_minor_width/2]
        ]);
    }
}

module rack_m4_nut_z() {
  difference() {
    hex_prism_z(rack_m4_nut_af,rack_m4_nut_h);
    rack_m4_female_cutter();
  }
}

if (part == "spindle")
  rotate([-90,0,0]) render(convexity=40) spindle_z();
else if (part == "rack_m4_nut")
  render(convexity=50) rack_m4_nut_z();
