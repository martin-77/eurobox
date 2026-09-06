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
  // For a regular hexagon, circumradius = AF/sqrt(3).
  cylinder(r=af/sqrt(3),h=h,$fn=6);
}

module spindle_z() {
  union() {
    // Plate journal + retaining groove.
    cylinder(r=3.0,h=0.42);
    translate([0,0,0.38]) cylinder(r=2.5,h=1.44);
    translate([0,0,1.78]) cylinder(r=3.0,h=6.24);

    // Axial thrust shoulder.
    translate([0,0,7.98]) cylinder(r=5.5,h=1.84);

    // Main RH 8x2 lead thread. Core overlaps shoulder by 0.02 mm only;
    // outer helical phase still begins at the nominal 9.8 mm datum.
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

    // Integral AF10 DRIVE BOSS for eurobox_v50_knob.stl. This is deliberately
    // part of the screw and is not a nut; the separate threaded retainer nut
    // sits on the outer RH 8x2 stud after the knob is fitted.
    translate([0,0,32.78]) hex_prism_z(10.0,4.54);

    // Outer retainer stud, extended to 7 mm so the separate retainer nut gets
    // useful thread engagement after the 7 mm knob.
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

// Canonical printable rack nut. These values intentionally mirror the final
// FreeCAD source fixup and are the FDM-printability authority for the STL:
// M4x0.7 RH, female minor Ø3.44, groove major Ø4.40, radial depth 0.48,
// 0.40 mm cutter width at the minor radius and 0.30 mm at the major radius.
rack_m4_pitch=0.7;
rack_m4_nut_af=7.0;
rack_m4_nut_h=3.2;
rack_m4_minor_r=1.72;
rack_m4_groove_major_r=2.20;
rack_m4_minor_width=0.40;
rack_m4_major_width=0.30;
rack_m4_thread_len=rack_m4_nut_h+2*rack_m4_pitch;

module rack_m4_female_cutter() {
  // Extend one complete pitch beyond each end so the helical cut reaches both
  // faces as a true open internal thread rather than terminating in a skin.
  translate([0,0,-rack_m4_pitch])
    union() {
      cylinder(r=rack_m4_minor_r,h=rack_m4_thread_len,$fn=96);
      linear_extrude(height=rack_m4_thread_len,
                     twist=360*rack_m4_thread_len/rack_m4_pitch,
                     slices=ceil(rack_m4_thread_len/rack_m4_pitch*40),
                     convexity=40)
        polygon(points=[
          [rack_m4_minor_r-0.08,-rack_m4_minor_width/2],
          [rack_m4_groove_major_r,-rack_m4_major_width/2],
          [rack_m4_groove_major_r, rack_m4_major_width/2],
          [rack_m4_minor_r-0.08, rack_m4_minor_width/2]
        ]);
    }
}

module rack_m4_nut_z() {
  difference() {
    hex_prism_z(rack_m4_nut_af,rack_m4_nut_h);
    rack_m4_female_cutter();
    // Symmetric entry chamfers, matching the validated BRep dimensions.
    translate([0,0,-0.01])
      cylinder(h=0.55,r1=2.18,r2=1.72,$fn=96);
    translate([0,0,2.66])
      cylinder(h=0.55,r1=1.72,r2=2.18,$fn=96);
  }
}

if (part == "spindle")
  // FreeCAD assembly convention: spindle axis +Y.
  rotate([-90,0,0]) render(convexity=40) spindle_z();
else if (part == "rack_m4_nut")
  render(convexity=50) rack_m4_nut_z();
