$fn=128;

// V70 clamp plate derived from the final V60 plate.
// Local print orientation: plate broad face in XY, thickness in Z.
plate_w = 187.30;
plate_h = 30.00;
plate_t = 8.00;
hole_d = 8.60;

spindle_x = [15.00, 172.30];
spindle_y = 15.00;

// Existing lower box hook, transformed into local print coordinates.
hook_y0 = 9.55;
hook_h = 4.00;
hook_z0 = 7.80;
hook_depth = 4.40;

difference() {
    union() {
        cube([plate_w,plate_h,plate_t]);
        translate([0,hook_y0,hook_z0])
            cube([plate_w,hook_h,hook_depth]);
    }

    // The complete RH8x2 screw must pass through during assembly.
    for(x=spindle_x)
        translate([x,spindle_y,-0.5])
            cylinder(d=hole_d,h=plate_t+1.0);
}
