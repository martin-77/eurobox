// v50 rack clamp M4 nut — standalone source of truth
// Printable M4x0.7 RH internal thread for PETG / 0.4 mm nozzle.
//
// Construction deliberately differs from the failed groove-cutter versions:
// 1) open the nut to the thread ROOT diameter (Ø4.40),
// 2) add the female THREAD TOOTH as a helical material ridge projecting inward.
// There is therefore no smaller smooth cylindrical wall that can hide the thread.

$fn=120;

pitch = 0.70;
nut_af = 7.00;
nut_h = 5.60;                 // 8 pitches
root_r = 2.20;                // Ø4.40 root/opening
crest_r = 1.75;               // Ø3.50 female crest
anchor_r = 2.24;              // 0.04 mm embed into nut body
crest_half_z = 0.15;          // 0.30 mm printable crest width
root_half_z = 0.22;           // 0.44 mm root width
phase_z = pitch/2;            // female tooth sits between matching male turns
ext = pitch;
total_h = nut_h + 2*ext;
turns = total_h/pitch;
steps = ceil(turns*64);
a0 = -360;
a1 = 360*(turns-1);

function ang(i) = a0 + (a1-a0)*i/steps;
function zc(i) = pitch*ang(i)/360 + phase_z;
function pt(r,a,z) = [r*cos(a), r*sin(a), z];

pts = [
  for (i=[0:steps])
    let(a=ang(i), z=zc(i))
      each [
        pt(anchor_r,a,z-root_half_z),
        pt(crest_r ,a,z-crest_half_z),
        pt(crest_r ,a,z+crest_half_z),
        pt(anchor_r,a,z+root_half_z)
      ]
];

sides = [
  for (i=[0:steps-1]) for (j=[0:3])
    [4*i+j, 4*(i+1)+j, 4*(i+1)+((j+1)%4), 4*i+((j+1)%4)]
];
start_face = [[0,1,2,3]];
e = 4*steps;
end_face = [[e+3,e+2,e+1,e]];

module female_thread_tooth() {
  polyhedron(points=pts,
             faces=concat(sides,start_face,end_face),
             convexity=100);
}

module hex_prism(af,h) {
  cylinder(r=af/sqrt(3), h=h, $fn=6);
}

module nut_body_with_root_bore() {
  difference() {
    hex_prism(nut_af,nut_h);
    translate([0,0,-0.2]) cylinder(r=root_r,h=nut_h+0.4,$fn=120);
  }
}

module rack_m4_nut() {
  // Clip the extended helix exactly to both nut faces.
  intersection() {
    union() {
      nut_body_with_root_bore();
      female_thread_tooth();
    }
    translate([-8,-8,0]) cube([16,16,nut_h]);
  }
}

render(convexity=120) rack_m4_nut();
