$fn=128;

// Print FOUR identical halves per clamp (two per spindle).

body_od = 10.00;
body_id = 8.35;
body_len = 4.925;

flange_od = 18.00;
flange_h = 2.20;

difference() {
    union() {
        cylinder(d=flange_od,h=flange_h);
        translate([0,0,flange_h])
            cylinder(d=body_od,h=body_len);
    }

    translate([0,0,-0.5])
        cylinder(d=body_id,h=flange_h+body_len+1.0);
}
