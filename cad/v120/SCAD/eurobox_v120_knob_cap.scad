$fn=128;

// V120 positive-retention cap for the M8 steel-spindle knob.
// Four flexible snap tabs retain the cap mechanically. The cap remains
// non-structural: screw torque and axial load are carried by the hex pocket.

cap_d = 15.80;
cap_h = 1.30;
chamfer = 0.25;

// Four tabs sit beside flats of the captured M8 hex head. The distal barb
// flexes inward while being inserted and expands into matching pockets in
// eurobox_v120_knob.scad.
tab_angles = [30, 90, 210, 270];
tab_r0 = 6.85;
tab_t = 0.80;
tab_w = 2.35;
tab_z0 = cap_h - 0.25;
tab_len = 3.50;
hook_out = 0.50;
hook_body_h = 0.55;
hook_ramp_h = 0.45;

module snap_tab(a) {
    rotate([0,0,a])
        translate([tab_r0,-tab_w/2,tab_z0])
            union() {
                // Flexible axial cantilever.
                cube([tab_t,tab_w,tab_len]);

                // Positive barb: square withdrawal shoulder on the cap side,
                // then a tapered lead-in toward the insertion tip.
                translate([tab_t-0.01,0,tab_len-hook_body_h-hook_ramp_h])
                    cube([hook_out+0.01,tab_w,hook_body_h]);

                hull() {
                    translate([tab_t+hook_out-0.02,0,tab_len-hook_ramp_h])
                        cube([0.02,tab_w,0.02]);
                    translate([tab_t-0.02,0,tab_len-0.02])
                        cube([0.02,tab_w,0.02]);
                }
            }
}

union() {
    cylinder(d1=cap_d-2*chamfer,d2=cap_d,h=chamfer);
    translate([0,0,chamfer]) cylinder(d=cap_d,h=cap_h-chamfer);

    for(a=tab_angles)
        snap_tab(a);
}
