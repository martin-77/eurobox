$fn=128;

// V70 clamp v4: recessed two-piece rotating bushings.
// X = full clamp width
// Y = installed vertical direction
// Z = depth toward box / lead-nut side
//
// Height geometry retained from v3:
// screw axis -> box underside = 15.00
// box underside -> start protrusion = 16.45
// box underside -> top protrusion = 33.57
// upper stabilising contact = 25.00
//
// Bearing redesign:
// screw-zone thickness = 12.00 mm (Z=-4..8)
// through bore Ø10.40
// flange pockets Ø18.40 x 1.20 mm from both sides
// each bushing half body = 4.925 mm from pocket floor toward centre
// total body stack = 9.85 vs 9.60 between pocket floors => 0.25 mm axial freedom

w = 187.30;
h = 88.57;
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
bearing_t = bearing_front-bearing_back;
bore_d = 10.40;
flange_pocket_d = 18.40;
flange_pocket_depth = 1.20;
rib_w = 22.00;

module clamp_solid() {
    union() {
        cube([w,h,backbone_t]);

        translate([0,0,bearing_back])
            cube([w,box_bottom_y,bearing_t]);

        for (x=spindle_x)
            translate([x-rib_w/2,box_bottom_y,bearing_back])
                cube([rib_w,h-box_bottom_y,4.00]);

        translate([0,box_bottom_y,backbone_t])
            cube([w,pocket_y0-box_bottom_y,primary_front-backbone_t]);

        translate([0,pocket_y1,backbone_t])
            cube([w,h-pocket_y1,upper_front-backbone_t]);
    }
}

difference() {
    clamp_solid();

    for (x=spindle_x) {
        translate([x,spindle_y,bearing_back-0.5])
            cylinder(d=bore_d,h=bearing_t+1.0);

        translate([x,spindle_y,bearing_back-0.01])
            cylinder(d=flange_pocket_d,h=flange_pocket_depth+0.02);

        translate([x,spindle_y,bearing_front-flange_pocket_depth-0.01])
            cylinder(d=flange_pocket_d,h=flange_pocket_depth+0.02);
    }
}
