// Installed-orientation preview for Eurobox v60.
// IMPORTANT: LEFT printable STL is an X-mirrored handed part. In the installed
// assembly it is additionally rotated 180 deg about Z, so its carriers project
// outward (-Y) while RIGHT projects outward (+Y).

$fn = 72;
rack_ctc = 110.67;
rack_r = 12.42 / 2;
right_y = rack_ctc / 2;
left_y = -rack_ctc / 2;

module rack_tube(y) {
    color([0.25, 0.25, 0.25, 1.0])
        translate([-220, y, 0])
            rotate([0, 90, 0])
                cylinder(h=440, r=rack_r);
}

module right_side() {
    color([0.92, 0.48, 0.12, 1.0])
        translate([0, right_y, 0])
            import("../build_v60/eurobox_v60_base_right.stl", convexity=20);
}

module left_side() {
    color([0.15, 0.55, 0.90, 1.0])
        translate([0, left_y, 0])
            rotate([0, 0, 180])
                import("../build_v60/eurobox_v60_base_left.stl", convexity=20);
}

// Transparent box footprint/rim reference. The two carrier sets must point
// away from the rack tubes toward the left/right outer box edges.
color([0.75, 0.75, 0.75, 0.16])
    translate([-200, -300, 39.54])
        cube([400, 600, 2.0]);

rack_tube(right_y);
rack_tube(left_y);
right_side();
left_side();
