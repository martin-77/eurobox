$fn = 128;

// V70 emergency spindle support sleeve
// Slides over the Ø8 RH8x2 working screw and bridges the measured 60 mm gap
// between base and clamp. The broad end pads spread lateral load into both parts.

length = 60.00;
bore_d = 8.60;          // 0.30 mm radial running clearance over Ø8 screw
pad_xy = 30.00;         // largest symmetric square around spindle at x/y = 15 mm on clamp
pad_r = 3.00;
pad_t = 5.00;
tube_d = 20.00;
transition_h = 8.00;

module rounded_square_2d(size, r) {
    offset(r=r)
        square([size-2*r, size-2*r], center=true);
}

module pad(h) {
    linear_extrude(height=h)
        rounded_square_2d(pad_xy, pad_r);
}

module end_transition(z0, flip=false) {
    // Smooth, heavily gusseted transition from the 30x30 bearing pad to Ø20 tube.
    if (!flip) {
        hull() {
            translate([0,0,z0])
                linear_extrude(height=0.8)
                    rounded_square_2d(pad_xy, pad_r);
            translate([0,0,z0+transition_h])
                cylinder(d=tube_d,h=0.8);
        }
    } else {
        hull() {
            translate([0,0,z0])
                cylinder(d=tube_d,h=0.8);
            translate([0,0,z0+transition_h])
                linear_extrude(height=0.8)
                    rounded_square_2d(pad_xy, pad_r);
        }
    }
}

difference() {
    union() {
        // Base-side bearing pad.
        pad(pad_t);

        // Broad load transition.
        end_transition(pad_t-0.01, false);

        // Central stiff guide body.
        translate([0,0,pad_t+transition_h-0.01])
            cylinder(d=tube_d,
                     h=length-2*(pad_t+transition_h)+0.02);

        // Clamp-side transition and bearing pad.
        end_transition(length-pad_t-transition_h-0.79, true);
        translate([0,0,length-pad_t])
            pad(pad_t);
    }

    // Continuous screw clearance bore.
    translate([0,0,-0.5])
        cylinder(d=bore_d,h=length+1.0);
}
