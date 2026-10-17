$fn=128;

// Non-structural press cap for the V110 M8 knob.
// The screw head carries torque/axial load in the knob pocket; this cap only
// prevents the head from falling out during handling.
cap_d = 16.06;
cap_h = 1.30;
chamfer = 0.25;

union() {
    cylinder(d1=cap_d-2*chamfer,d2=cap_d,h=chamfer);
    translate([0,0,chamfer]) cylinder(d=cap_d,h=cap_h-chamfer);
}
