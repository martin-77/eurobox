$fn=128;

// V70 clamp v2 prototype: full-width stepped clamp.
// X = width, Y = installed height, Z = depth toward box.
//
// Height chain:
// clamp bottom -> screw axis          = 15.00 mm
// screw axis -> box underside        = 15.00 mm
// box underside -> top of protrusion = 33.57 mm
// extra press height above protrusion= 25.00 mm
// total                              = 88.57 mm
//
// Measured press-plane offset between protrusion and wall above ≈ 18.50 mm.

w = 187.30;
lower_h = 63.57;
upper_h = 25.00;
lower_t = 8.00;
upper_front = 26.50; // 8.0 + 18.5
hole_d = 8.80;
spindle_x = [15.00,172.30];
spindle_y = 15.00;

difference() {
    union() {
        cube([w,lower_h,lower_t]);
        translate([0,lower_h,0])
            cube([w,upper_h,upper_front]);
    }

    for(x=spindle_x)
        translate([x,spindle_y,-0.5])
            cylinder(d=hole_d,h=lower_t+1.0);
}
