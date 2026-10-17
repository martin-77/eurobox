$fn=128;

// V110 27.7 mm clamp-to-base support for M8 steel spindle.
// Retains the proven 30x30 pads and Ø20 body.
// Clamp-side stepped relief clears both the Ø18 bushing collar and the
// captured M8 stop nut while the broad pad still bears on the clamp.

sleeve_len = 27.70;
run_bore_d = 8.90;
body_d = 20.00;
pad_xy = 30.00;
pad_t = 4.00;
transition_len = 3.00;

bushing_relief_d = 18.50;
bushing_relief_depth = 1.10;
stop_nut_relief_d = 15.40;
stop_nut_relief_depth = 7.55; // 0.85 collar + 6.20 nut + 0.50 axial freedom

module cylindrical_x(len,d) {
    rotate([0,90,0]) cylinder(h=len,d=d,center=false);
}

module outer_support() {
    union() {
        translate([0,-pad_xy/2,-pad_xy/2]) cube([pad_t,pad_xy,pad_xy]);
        translate([sleeve_len-pad_t,-pad_xy/2,-pad_xy/2]) cube([pad_t,pad_xy,pad_xy]);
        cylindrical_x(sleeve_len,body_d);
        hull() {
            translate([pad_t-transition_len,0,0]) cylindrical_x(0.01,body_d);
            translate([pad_t,-body_d/2,-body_d/2]) cube([0.01,body_d,body_d]);
        }
        hull() {
            translate([sleeve_len-pad_t,-body_d/2,-body_d/2]) cube([0.01,body_d,body_d]);
            translate([sleeve_len-pad_t+transition_len,0,0]) cylindrical_x(0.01,body_d);
        }
    }
}

difference() {
    outer_support();
    translate([-0.10,0,0]) cylindrical_x(sleeve_len+0.20,run_bore_d);
    translate([-0.10,0,0]) cylindrical_x(bushing_relief_depth+0.10,bushing_relief_d);
    translate([bushing_relief_depth-0.05,0,0])
        cylindrical_x(stop_nut_relief_depth-bushing_relief_depth+0.10,stop_nut_relief_d);
}
