$fn=48;

module tight_c_clip(outer_d, inner_d, t, throat_w, entry_w) {
    outer_r=outer_d/2;
    inner_r=inner_d/2;
    difference() {
        difference() {
            cylinder(r=outer_r,h=t);
            translate([0,0,-0.1]) cylinder(r=inner_r,h=t+0.2);
        }
        linear_extrude(height=t+0.4)
            polygon(points=[
                [-throat_w/2,-0.2],
                [ throat_w/2,-0.2],
                [ entry_w/2,outer_r+0.4],
                [-entry_w/2,outer_r+0.4]
            ]);
    }
}

// V3: tightened for direct sideways snap onto the Ø2.40 groove.
tight_c_clip(outer_d=6.40,inner_d=2.10,t=1.30,throat_w=2.00,entry_w=2.60);
