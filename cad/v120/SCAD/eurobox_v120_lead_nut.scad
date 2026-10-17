$fn=128;

// V110 removable lead-nut carrier for TWO standard M8 nuts.
// External envelope and retaining-pin geometry reproduce the proven V60
// top-loaded cartridge so the existing BASE does not need to be reprinted.
//
// Measured nut: 12.79 mm AF x 6.20 mm high.
// Two nuts: 12.40 mm stack.
// Common pocket: 12.75 mm axial length -> 0.35 mm total phase/alignment freedom.
// The pocket is deliberately OPEN at the rear (Y=-14): after installation the
// existing BASE pocket closes that end and takes the high clamp thrust directly.
// A 1.25 mm printed front lip only retains the stack during clamp opening.

carrier_len = 14.00;
profile_r = 8.00;
body_z1 = 7.00;
cap_z0 = 10.80;
cap_z1 = 15.00;

nut_af = 13.15;
nut_pocket_len = 12.75;
front_lip = carrier_len - nut_pocket_len;
screw_clear_d = 8.80;

pin_y = -7.00;
pin_z = 10.00;
pin_hole_d = 3.40;
pin_drop_w = 3.80;

function semicircle_right(n=48) = [
    for(i=[0:n])
        let(z=-profile_r + profile_r*i/n,
            x=sqrt(max(0,profile_r*profile_r-z*z)))
        [x,z]
];

// OpenSCAD 2021.01 has no reverse() function. Generate the left side in
// descending index order instead. Skip i=0 because polygon closure returns to
// the one mathematical bottom point from semicircle_right().
function semicircle_left(n=48) = [
    for(i=[n:-1:1])
        let(z=-profile_r + profile_r*i/n,
            x=sqrt(max(0,profile_r*profile_r-z*z)))
        [-x,z]
];

function carrier_profile() = concat(
    semicircle_right(),
    [[profile_r,body_z1],[-profile_r,body_z1]],
    semicircle_left()
);

module prism_xz_neg_y(points,len,y_front=0) {
    translate([0,y_front,0])
        rotate([90,0,0])
            linear_extrude(height=len,convexity=10)
                polygon(points=points);
}

module hex_xz_neg_y(af,len,y_front) {
    h = af/sqrt(3);
    pts = [
        [ af/2, h/2], [0,h], [-af/2,h/2],
        [-af/2,-h/2], [0,-h], [af/2,-h/2]
    ];
    prism_xz_neg_y(pts,len,y_front);
}

module cyl_x(len,d,x0) {
    translate([x0,0,0]) rotate([0,90,0]) cylinder(h=len,d=d);
}

module carrier_outer() {
    union() {
        prism_xz_neg_y(carrier_profile(),carrier_len,0);
        translate([-6,-11,5]) cube([12,8,6]);
        translate([-8,-carrier_len,body_z1-0.10])
            cube([16,carrier_len,cap_z0-body_z1+0.20]);
        translate([-8,-carrier_len,cap_z0])
            cube([16,carrier_len,cap_z1-cap_z0]);
    }
}

difference() {
    carrier_outer();

    // Open rear end: the first steel nut bears directly against the existing
    // base pocket under high closing load instead of loading a thin printed wall.
    hex_xz_neg_y(nut_af,nut_pocket_len+0.10,-front_lip);

    // M8 running clearance through the front retaining lip.
    translate([0,0.20,0]) rotate([90,0,0])
        cylinder(h=carrier_len+0.40,d=screw_clear_d);

    // Existing V60 top-installed retaining-pin cradle and service throat.
    translate([0,pin_y,pin_z]) cyl_x(20,pin_hole_d,-10);
    translate([-10,pin_y-pin_drop_w/2,pin_z])
        cube([20,pin_drop_w,cap_z1-pin_z+0.50]);
}
