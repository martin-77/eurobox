$fn=128;

// V110 hand knob for captured M8 hex-head steel screw.
// Measured head: 12.90 mm AF x 5.50 mm high.
// Head is inserted from the visible outer face and retained by a press cap.

knob_h = 9.50;
knob_r = 15.00;
scallop_r = 3.40;
scallop_c = 16.20;

head_af = 13.18;
head_h = 5.70;
cap_recess_d = 16.00;
cap_recess_h = 1.35;
shank_d = 8.70;

nose_d = 16.00;
nose_h = 0.80;

module scalloped_knob(h=knob_h) {
    difference() {
        cylinder(r=knob_r,h=h);
        for(a=[0:45:315])
            translate([scallop_c*cos(a),scallop_c*sin(a),-0.2])
                cylinder(r=scallop_r,h=h+0.4);
    }
}

module hex_socket(af,h) {
    cylinder(r=af/sqrt(3),h=h,$fn=6);
}

difference() {
    union() {
        scalloped_knob();
        // Narrow thrust nose reaches only the rotating bushing collar and
        // stays clear of the stationary Ø18.4 clamp seat.
        translate([0,0,knob_h]) cylinder(d=nose_d,h=nose_h);
    }

    translate([0,0,-0.02]) cylinder(d=cap_recess_d,h=cap_recess_h+0.04);
    translate([0,0,cap_recess_h-0.01])
        hex_socket(head_af,head_h+0.02);
    translate([0,0,cap_recess_h+head_h-0.02])
        cylinder(d=shank_d,h=knob_h+nose_h-(cap_recess_h+head_h)+0.20);
}
