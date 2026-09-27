$fn=128;

// V70 clamp v6 — support-free broad-face print.
//
// V5 had the screw zone down to Z=-4, while most of the rear face began
// at Z=0. Printed broad-face-down, that left the upper rear face suspended
// 4 mm above the bed.
//
// V6 fills that 4 mm rear layer continuously across the full clamp.
// This gives one planar print surface at Z=-4. Material saving is delegated
// to slicer infill (target: 30% gyroid, 7 bottom + 7 top layers at 0.20 mm).
//
// Box-contact and bearing geometry are unchanged from V5.

w = 187.30;
h = 80.02;
spindle_x = [15.00,172.30];
spindle_y = 15.00;

box_bottom_y = 30.00;
pocket_y0 = 46.20;
pocket_y1 = 63.82;

bearing_back = -4.00;
backbone_front = 8.00;
backbone_t = backbone_front-bearing_back; // 12.00 mm overall envelope

primary_front = 27.00;
upper_front = 26.50;

bore_d = 10.40;

seat_outer_d = 18.40;
seat_inner_d = 10.40;
seat_depth = 1.60;

module clamp_solid() {
    union() {
        // Continuous 12 mm backbone: support-free from one planar bed face.
        translate([0,0,bearing_back])
            cube([w,h,backbone_t]);

        // Lower PRIMARY contact: 16.20 mm high.
        translate([0,box_bottom_y,backbone_front])
            cube([w,pocket_y0-box_bottom_y,primary_front-backbone_front]);

        // Recess around box protrusion: Y=46.20..63.82.

        // Upper SECONDARY contact: also 16.20 mm high.
        translate([0,pocket_y1,backbone_front])
            cube([w,h-pocket_y1,upper_front-backbone_front]);
    }
}

difference() {
    clamp_solid();

    for (x=spindle_x) {
        translate([x,spindle_y,bearing_back-0.5])
            cylinder(d=bore_d,h=backbone_t+1.0);

        translate([x,spindle_y,bearing_back-0.01])
            cylinder(d1=seat_outer_d,d2=seat_inner_d,h=seat_depth+0.02);

        translate([x,spindle_y,backbone_front-seat_depth-0.01])
            cylinder(d1=seat_inner_d,d2=seat_outer_d,h=seat_depth+0.02);
    }
}
