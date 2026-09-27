$fn=96;

// Eurobox V70 clamp v3 prototype.
// X = full clamp width, Y = installed vertical direction, Z = depth toward box.
// Fixed/measured:
// screw axis -> box underside = 15.00 mm
// box underside -> start protrusion = 16.45 mm
// box underside -> top protrusion = 33.57 mm
// protrusion depth ~= 18.50 mm
// upper stabilising contact = 25.00 mm

w = 187.30;
h = 88.57;
spindle_x = [15.00,172.30];
spindle_y = 15.00;

box_bottom_y = 30.00;
pocket_y0 = 46.20; // 0.25 mm below nominal protrusion start
pocket_y1 = 63.82; // 0.25 mm above nominal protrusion top

backbone_t = 8.00;
primary_front = 27.00; // lower primary contact +0.50 vs upper
upper_front = 26.50;

bearing_back = -2.00;
bearing_front = 8.00;
bearing_t = bearing_front-bearing_back; // 10.00 mm
bushing_bore_d = 10.40;
rib_w = 20.00;

module clamp_solid() {
    union() {
        cube([w,h,backbone_t]);

        // Full-width 10 mm screw-zone spine.
        translate([0,0,bearing_back])
            cube([w,box_bottom_y,bearing_t]);

        // Rear ribs above each screw station.
        for (x=spindle_x)
            translate([x-rib_w/2,box_bottom_y,bearing_back])
                cube([rib_w,h-box_bottom_y,2.00]);

        // Primary lower contact.
        translate([0,box_bottom_y,backbone_t])
            cube([w,pocket_y0-box_bottom_y,primary_front-backbone_t]);

        // Y=46.20..63.82 remains recessed to Z=8 for the box protrusion.

        // Upper secondary/stabilising contact.
        translate([0,pocket_y1,backbone_t])
            cube([w,h-pocket_y1,upper_front-backbone_t]);
    }
}

difference() {
    clamp_solid();
    for (x=spindle_x)
        translate([x,spindle_y,bearing_back-0.5])
            cylinder(d=bushing_bore_d,h=bearing_t+1.0);
}
