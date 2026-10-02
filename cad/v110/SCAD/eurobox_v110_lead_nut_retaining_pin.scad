$fn=48;

module cyl_x(d,l,x0) {
    translate([x0,0,0]) rotate([0,90,0]) cylinder(d=d,h=l);
}

// V80 lead-nut retaining pin.
// Recalculated from the actual frozen V60/V80 BASE service geometry:
// head pocket -14.35..-11.65, clip pocket +11.20..+13.20,
// service path -14.35..+15.05.
//
// Released geometry:
// head  -13.65..-11.65  Ø6.50
// shaft -11.65..+11.40  Ø3.00
// groove +11.40..+13.00 Ø2.40
// tip    +13.00..+14.50 Ø3.00
// total length = 28.15 mm
//
// Matching V80 clip:
// ID Ø2.10, opening 1.60, OD Ø7.00, thickness 1.30.

union() {
    cyl_x(6.50,2.00,-13.65);
    cyl_x(3.00,23.05,-11.65);
    cyl_x(2.40,1.60,11.40);
    cyl_x(3.00,1.50,13.00);
}
