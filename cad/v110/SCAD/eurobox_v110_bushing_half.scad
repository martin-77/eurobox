$fn=128;

// V70 v5 rotating bushing HALF.
// Print FOUR per clamp: two halves per spindle.
//
// Clamp seat is a matching cone:
// outside Ø18.4 -> inside Ø10.4 over 1.60 mm.
// Bushing seat:
// outside Ø18.0 -> inside Ø10.0 over 1.60 mm.
//
// A short outer collar remains outside the clamp.
// The OUTER face also has a conical female centering recess for the
// screw shoulder or knob nose.

body_od = 10.00;
body_id = 8.35;

// Clamp: 12.00 mm total thickness, 1.60 mm cone each side.
// Distance between cone inner ends = 8.80 mm.
// Two bodies total 9.05 mm => 0.25 mm axial freedom.
body_len = 4.525;

collar_od = 18.00;
collar_h = 0.85;
seat_h = 1.60;

// Outer centering recess for screw shoulder / knob nose.
centre_outer_d = 11.60;
centre_inner_d = 8.60;
centre_depth = 0.70;

difference() {
    union() {
        // outer collar
        cylinder(d=collar_od,h=collar_h);

        // self-centering conical clamp seat
        translate([0,0,collar_h])
            cylinder(d1=collar_od,d2=body_od,h=seat_h);

        // cylindrical radial guide to clamp centre
        translate([0,0,collar_h+seat_h])
            cylinder(d=body_od,h=body_len);
    }

    // screw journal bore
    translate([0,0,-0.5])
        cylinder(d=body_id,h=collar_h+seat_h+body_len+1.0);

    // shallow female cone on the OUTER face.
    // Wide outside, narrower toward the body.
    translate([0,0,-0.01])
        cylinder(d1=centre_outer_d,d2=centre_inner_d,h=centre_depth+0.02);
}