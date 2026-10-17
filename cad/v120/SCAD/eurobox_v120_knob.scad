$fn=128;

// V120 hand knob for captured M8 hex-head steel screw.
// Measured head: 12.90 mm AF x 5.50 mm high.
// Head is inserted from the visible outer face and retained by a four-lug
// snap cap. The cap is only a retainer; torque and thrust stay in the knob.

knob_h = 9.50;
knob_r = 15.00;
scallop_r = 3.40;
scallop_c = 16.20;

head_af = 13.18;
head_h = 5.70;
cap_recess_d = 16.10;
cap_recess_h = 1.35;
shank_d = 8.70;

nose_d = 16.00;
nose_h = 0.80;

// Four positive snap receivers. Angles align the tabs beside hex-head flats,
// leaving clearance to the screw head while keeping the wall around the cap.
tab_angles = [30, 90, 210, 270];
tab_slot_r0 = 6.72;
tab_slot_r1 = 8.03;
tab_slot_w = 2.75;
tab_slot_z0 = cap_recess_h - 0.15;
tab_slot_h = 3.55;

// Local undercut into which each cap barb expands after insertion.
latch_r0 = 7.55;
latch_r1 = 8.40;
latch_w = 3.05;
latch_z0 = 3.45;
latch_h = 0.90;

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

module radial_box(a,r0,r1,w,z0,h) {
    rotate([0,0,a])
        translate([r0,-w/2,z0])
            cube([r1-r0,w,h]);
}

difference() {
    union() {
        scalloped_knob();
        // Narrow thrust nose reaches only the rotating bushing collar and
        // stays clear of the stationary Ø18.4 clamp seat.
        translate([0,0,knob_h]) cylinder(d=nose_d,h=nose_h);
    }

    // Cap seat and M8 screw-head pocket.
    translate([0,0,-0.02]) cylinder(d=cap_recess_d,h=cap_recess_h+0.04);
    translate([0,0,cap_recess_h-0.01])
        hex_socket(head_af,head_h+0.02);
    translate([0,0,cap_recess_h+head_h-0.02])
        cylinder(d=shank_d,h=knob_h+nose_h-(cap_recess_h+head_h)+0.20);

    // Four insertion channels plus deeper latch pockets. During insertion the
    // cap barbs flex radially inward through the narrow channels and then snap
    // outward into these undercuts. This gives a real click-fit instead of a
    // simple press plug.
    for(a=tab_angles) {
        radial_box(a,tab_slot_r0,tab_slot_r1,tab_slot_w,tab_slot_z0,tab_slot_h);
        radial_box(a,latch_r0,latch_r1,latch_w,latch_z0,latch_h);
    }
}
