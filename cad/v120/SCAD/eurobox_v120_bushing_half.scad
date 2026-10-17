$fn=128;

// V110 rotating bushing half for an M8 full-thread steel spindle.
// Two halves per spindle, four per clamp.
// Keeps the proven V70/V5 clamp-seat geometry, but replaces the old
// centering recess with a flat thrust face and increases the running bore.

body_od = 10.00;
body_id = 8.80;
body_len = 4.525;
collar_od = 18.00;
collar_h = 0.85;
seat_h = 1.60;

difference() {
    union() {
        cylinder(d=collar_od,h=collar_h);
        translate([0,0,collar_h])
            cylinder(d1=collar_od,d2=body_od,h=seat_h);
        translate([0,0,collar_h+seat_h])
            cylinder(d=body_od,h=body_len);
    }
    translate([0,0,-0.5])
        cylinder(d=body_id,h=collar_h+seat_h+body_len+1.0);
}
