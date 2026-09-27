$fn=128;

// One rotating flanged bushing; print two per clamp.
// Body is 0.25 mm longer than the 10.00 mm clamp bearing section so
// tightening screw shoulder <-> knob cannot pinch the stationary clamp.
body_od = 10.00;
body_id = 8.35;
body_len = 10.25;
flange_od = 14.00;
flange_h = 2.00;

difference() {
    union() {
        cylinder(d=body_od,h=body_len);
        translate([0,0,-flange_h])
            cylinder(d=flange_od,h=flange_h);
    }
    translate([0,0,-flange_h-0.5])
        cylinder(d=body_id,h=body_len+flange_h+1.0);
}
