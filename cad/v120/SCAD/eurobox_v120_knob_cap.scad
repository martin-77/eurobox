$fn=128;

// V120 positive-retention cap for the enlarged M8 steel-spindle knob.
// Four long flexible snap legs retain the cap mechanically. The cap is not
// structural: screw torque and axial load are carried by the knob's hex pocket.

cap_d = 19.20;
cap_h = 1.70;
chamfer = 0.30;

// Four evenly distributed flexible legs. The distal barb flexes inward through
// the knob channel and expands into a deeper undercut. The square shoulder on
// the cap side resists vibration-driven withdrawal; the lower face is ramped
// for insertion.
tab_angles = [45, 135, 225, 315];
tab_r0 = 8.25;
tab_t = 0.90;
tab_w = 2.45;
tab_z0 = cap_h - 0.25;
tab_len = 5.20;
hook_out = 0.75;
hook_body_h = 0.70;
hook_ramp_h = 0.60;

module snap_tab(a) {
    rotate([0,0,a])
        translate([tab_r0,-tab_w/2,tab_z0])
            union() {
                // Long axial cantilever gives enough compliance for PETG
                // without relying on a loose press fit at the cap rim.
                cube([tab_t,tab_w,tab_len]);

                // Positive outward barb with a square withdrawal shoulder.
                translate([tab_t-0.01,0,tab_len-hook_body_h-hook_ramp_h])
                    cube([hook_out+0.01,tab_w,hook_body_h]);

                // Tapered insertion ramp toward the leg tip.
                hull() {
                    translate([tab_t+hook_out-0.02,0,tab_len-hook_ramp_h])
                        cube([0.02,tab_w,0.02]);
                    translate([tab_t-0.02,0,tab_len-0.02])
                        cube([0.02,tab_w,0.02]);
                }
            }
}

union() {
    // Visible cap disc: small radial clearance to the knob recess, so the
    // four snap legs — not friction or glue — provide retention.
    cylinder(d1=cap_d-2*chamfer,d2=cap_d,h=chamfer);
    translate([0,0,chamfer]) cylinder(d=cap_d,h=cap_h-chamfer);

    for(a=tab_angles)
        snap_tab(a);
}
