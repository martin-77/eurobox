// v50 final printable mesh generator
// Use: openscad -D 'part="spindle"' -o <output.stl> final_print_meshes.scad
//
// The editable FreeCAD model remains the dimensional BRep/STEP authority.
// The coarse RH 8x2 prototype thread is emitted directly by OpenSCAD/CGAL
// because converting the helical mesh to BRep and tessellating it again can
// create open STL seams despite a valid OCC solid.

$fn=72;
part="spindle";

pitch=2.0;
core_r=3.25;
major_r=4.0;
root_w=0.58;
crest_w=0.24;

module rh_thread_z(length) {
  union() {
    cylinder(r=core_r,h=length,$fn=72);
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
    translate([0,0,9.78]) cylinder(r=core_r,h=22.24);
    translate([0,0,9.8])
      linear_extrude(height=22.2,
                     twist=360*22.2/pitch,
                     slices=ceil(22.2/pitch*28),
                     convexity=30)
        polygon(points=[
          [core_r-0.08,-root_w/2],
          [major_r,-crest_w/2],
          [major_r, crest_w/2],
          [core_r-0.08, root_w/2]
        ]);

    // Separate knob is driven by AF10 hex.
    translate([0,0,31.98]) hex_prism_z(10.0,4.54);

    // Outer retainer stud, same RH 8x2 profile.
    translate([0,0,36.48]) cylinder(r=core_r,h=4.52);
    translate([0,0,36.5])
      linear_extrude(height=4.5,
                     twist=360*4.5/pitch,
                     slices=ceil(4.5/pitch*28),
                     convexity=30)
        polygon(points=[
          [core_r-0.08,-root_w/2],
          [major_r,-crest_w/2],
          [major_r, crest_w/2],
          [core_r-0.08, root_w/2]
        ]);
  }
}

if (part == "spindle")
  // FreeCAD assembly convention: spindle axis +Y.
  rotate([-90,0,0]) render(convexity=40) spindle_z();
