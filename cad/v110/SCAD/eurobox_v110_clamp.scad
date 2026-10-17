$fn=96;
w=187.30; h=80.02;
bearing_back=-4.00;
backbone_front=8.00;
bearing_t=backbone_front-bearing_back;
bearing_d=10.40;
seat_outer_d=18.40;
seat_depth=1.60;
pocket_lo=46.20; pocket_hi=63.82;
lower_z2=27.00; upper_z2=26.50;
x_positions=[15.00,172.30];

module stepped_body() {
    union() {
        translate([0,0,bearing_back]) cube([w,h,bearing_t]);
        translate([0,0,backbone_front]) cube([w,pocket_lo,20]);
        translate([0,pocket_hi,backbone_front]) cube([w,h-pocket_hi,18.5]);
        for (x=x_positions)
            translate([x-11,0,backbone_front]) cube([22,h,8]);
    }
}
module spindle_cut(x) {
    translate([x,15,bearing_back-0.1])
        cylinder(h=bearing_t+0.2,d=bearing_d);
    translate([x,15,bearing_back-0.1])
        cylinder(h=seat_depth+0.1,d1=seat_outer_d,d2=bearing_d);
    translate([x,15,backbone_front-seat_depth])
        cylinder(h=seat_depth+0.1,d1=bearing_d,d2=seat_outer_d);
}
difference() {
    stepped_body();
    for (x=x_positions) spindle_cut(x);
}
