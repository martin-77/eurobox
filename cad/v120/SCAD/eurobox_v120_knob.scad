$fn=128;

// V120 hand knob for captured M8 hex-head steel screw.
// Measured head: 12.90 mm AF x 5.50 mm high.
// The knob is deliberately enlarged to 40 mm for leverage and grip.
// A four-leg positive snap cap retains the screw head mechanically; torque
// and axial thrust remain carried by the hex pocket and knob body.

knob_h = 12.00;
knob_r = 20.00;
scallop_r = 4.35;
scallop_c = 21.70;

head_af = 13.18;
head_h = 5.70;
cap_recess_d = 19.45;
cap_recess_h = 1.80;
shank_d = 8.70;

nose_d = 16.00;
nose_h = 0.80;

// Four evenly distributed insertion channels for the cap legs. The channels
// are intentionally wider than the legs so retention comes from the positive
// undercut, not friction. They sit outside the M8 head envelope.
tab_angles = [45, 135, 225, 315];
tab_slot_r0 = 8.15;
tab_slot_r1 = 9.55;
tab_slot_w = 2.95;
tab_slot_z0 = cap_recess_h - 0.20;
tab_slot_h = 5.65;

// Deep local pockets receive the outward-facing barbs. The square upper wall
// is the withdrawal shoulder; vibration cannot simply walk the cap outward.
latch_r0 = 8.85;
latch_r1 = 10.15;
latch_w = 3.25;
latch_z0 = 5.45;
latch_h = 1.10;

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

    // Four long insertion channels and positive latch pockets. The cap legs
    // flex inward during insertion, then spring into the deeper pockets.
    for(a=tab_angles) {
        radial_box(a,tab_slot_r0,tab_slot_r1,tab_slot_w,tab_slot_z0,tab_slot_h);
        radial_box(a,latch_r0,latch_r1,latch_w,latch_z0,latch_h);
    }

    // Two shallow service notches allow a small flat tool to lift the cap if
    // deliberate disassembly is ever required; they do not intersect latches.
    for(a=[0,180])
        radial_box(a,9.20,10.20,2.20,-0.05,0.85);
}
