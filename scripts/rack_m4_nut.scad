$fn = 96;

// Printable M4 x 0.7 RH captive nut for the rack closure.
// Conventional female-thread construction: the smooth core bore and the
// helical groove are CUT OUT of the nut body. There is no inward-projecting
// ribbon or wall in front of the thread.
// CI trigger: revalidate after BASE printability/collision correction.
pitch = 0.7;
h = 5.6;
af = 7.0;

// Matched to the printed rack screw (major dia 3.90, core dia 3.10).
// Deliberately FDM-friendly clearances for a 0.4 mm nozzle / PETG.
bore_r = 1.72;          // Ø3.44 free core / female crest diameter
groove_inner_r = 1.62;  // overlaps bore by 0.10 mm: groove is physically open
groove_outer_r = 2.18;  // Ø4.36 female root diameter
inner_half_z = 0.18;    // 0.36 mm groove width at bore wall
outer_half_z = 0.07;    // 0.14 mm groove width at groove root
lead = 0.35;            // half-pitch entry chamfer at each end

// Extend the cutter by one full pitch beyond both faces. This prevents an
// unthreaded end wall from surviving at either end of the nut.
z_start = -pitch;
z_end = h + pitch;
turns_span = (z_end - z_start) / pitch;
steps = ceil(turns_span * 48);

function zc(i) = z_start + (z_end-z_start) * i / steps;
function ang(i) = 360 * zc(i) / pitch;
function pt(r,a,z) = [r*cos(a), r*sin(a), z];

pts = [for (i=[0:steps]) let(a=ang(i), z=zc(i))
    each [
        pt(groove_inner_r, a, z-inner_half_z),
        pt(groove_outer_r, a, z-outer_half_z),
        pt(groove_outer_r, a, z+outer_half_z),
        pt(groove_inner_r, a, z+inner_half_z)
    ]
];
side_faces = [for (i=[0:steps-1]) for (j=[0:3])
    [4*i+j, 4*(i+1)+j, 4*(i+1)+((j+1)%4), 4*i+((j+1)%4)]];
start_face = [[0,1,2,3]];
e = 4*steps;
end_face = [[e+3,e+2,e+1,e]];

module helical_groove() {
    polyhedron(points=pts, faces=concat(side_faces,start_face,end_face), convexity=80);
}

module female_thread_cutter() {
    union() {
        translate([0,0,-0.05]) cylinder(r=bore_r, h=h+0.10, $fn=96);
        helical_groove();
    }
}

module nut_body() {
    // For a regular hexagon: across-flats = sqrt(3) * circumradius.
    rotate([0,0,30]) cylinder(r=af/sqrt(3), h=h, $fn=6);
}

difference() {
    nut_body();
    female_thread_cutter();

    // Entry chamfers make screw pickup reliable without closing the core bore.
    translate([0,0,-0.01])
        cylinder(h=lead+0.02, r1=2.35, r2=bore_r, $fn=96);
    translate([0,0,h-lead-0.01])
        cylinder(h=lead+0.02, r1=bore_r, r2=2.35, $fn=96);
}
