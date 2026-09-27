$fn=128;

// V70 clamp v5.
// Changes from v4:
// - upper stabilising contact reduced to same actual height as lower primary
//   contact: 16.20 mm
// - two-piece bushing seats are conical instead of cylindrical
// - no direct screw-to-clamp seat: screw/knob centre on the rotating bushings

w = 187.30;
h = 80.02;
spindle_x = [15.00,172.30];
spindle_y = 15.00;

box_bottom_y = 30.00;
pocket_y0 = 46.20;
pocket_y1 = 63.82;

backbone_t = 8.00;
primary_front = 27.00;
upper_front = 26.50;

bearing_back = -4.00;
bearing_front = 8.00;
bearing_t = bearing_front-bearing_back; // 12.00

bore_d = 10.40;

// Conical bushing seat: Ø18.4 at outside surface -> Ø10.4 at inner end.
seat_outer_d = 18.40;
seat_inner_d = 10.40;
seat_depth = 1.60;

rib_w = 22.00;

module clamp_solid() {
    union() {
        cube([w,h,backbone_t]);

        translate([0,0,bearing_back])
            cube([w,box_bottom_y,bearing_t]);

        for (x=spindle_x)
            translate([x-rib_w/2,box_bottom_y,bearing_back])
                cube([rib_w,h-box_bottom_y,4.00]);

        // Lower PRIMARY contact: 16.20 mm high.
        translate([0,box_bottom_y,backbone_t])
            cube([w,pocket_y0-box_bottom_y,primary_front-backbone_t]);

        // Recess around the box protrusion remains Y=46.20..63.82.

        // Upper SECONDARY contact: same 16.20 mm height as lower primary.
        translate([0,pocket_y1,backbone_t])
            cube([w,h-pocket_y1,upper_front-backbone_t]);
    }
}

difference() {
    clamp_solid();

    for (x=spindle_x) {
        translate([x,spindle_y,bearing_back-0.5])
            cylinder(d=bore_d,h=bearing_t+1.0);

        // Knob-side conical bushing seat.
        translate([x,spindle_y,bearing_back-0.01])
            cylinder(d1=seat_outer_d,d2=seat_inner_d,h=seat_depth+0.02);

        // Lead-nut-side conical bushing seat.
        translate([x,spindle_y,bearing_front-seat_depth-0.01])
            cylinder(d1=seat_inner_d,d2=seat_outer_d,h=seat_depth+0.02);
    }
}