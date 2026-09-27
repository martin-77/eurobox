$fn=64;

pitch = 2.0;
male_core_r = 3.25;
male_major_r = 4.0;
male_root_w = 1.20;
male_crest_w = 0.60;

module ridge_rh(core_r, major_r, pitch, len, root_w, crest_w, z0=0, steps=480) {
    inner_r = core_r - 0.12;
    root_half = root_w/2;
    crest_half = crest_w/2;
    a1 = 360*len/pitch;
    function ang(i)=a1*i/steps;
    function zc(i)=pitch*ang(i)/360;
    function pt(r,a,z)=[r*cos(a),r*sin(a),z];
    pts=[for(i=[0:steps]) let(a=ang(i),z=zc(i))
        each [
            pt(inner_r,a,z-root_half),
            pt(major_r,a,z-crest_half),
            pt(major_r,a,z+crest_half),
            pt(inner_r,a,z+root_half)
        ]];
    side_faces=[for(i=[0:steps-1]) for(j=[0:3]) each [
        [4*(i+1)+((j+1)%4),4*(i+1)+j,4*i+j],
        [4*i+((j+1)%4),4*(i+1)+((j+1)%4),4*i+j]
    ]];
    start_face=[[2,1,0],[3,2,0]];
    e=4*steps;
    end_face=[[e+1,e+2,e+3],[e,e+1,e+3]];
    translate([0,0,z0])
        polyhedron(points=pts,faces=concat(side_faces,start_face,end_face),convexity=100);
}

module male_thread(len,z0=0,steps_per_pitch=8) {
    union() {
        translate([0,0,z0-0.25]) cylinder(r=male_core_r,h=len+0.5);
        ridge_rh(male_core_r,male_major_r,pitch,len,male_root_w,male_crest_w,z0,ceil(len/pitch*steps_per_pitch));
    }
}

// knob side (z=0) -> bicycle / lead nut (+z)
knob_thread_len = 8.50;
journal_len = 10.25;
shoulder_h = 2.00;
shoulder_d = 10.80; // 0.50 mm radial clearance in frozen Ø11.8 corridor
main_thread_len = 74.00; // old 24 mm + 50 mm permanent engagement reserve

z_journal = knob_thread_len;
z_shoulder = z_journal + journal_len;
z_main = z_shoulder + shoulder_h;

union() {
    // Separate screw-on knob; same RH8x2 fit geometry.
    male_thread(knob_thread_len,0,12);

    // Smooth rotating journal through bushing.
    translate([0,0,z_journal])
        cylinder(d=8.00,h=journal_len+0.10);

    // Stable counterface against inner end of bushing.
    translate([0,0,z_shoulder])
        cylinder(d=shoulder_d,h=shoulder_h);

    // Long working thread remains engaged in frozen lead nut.
    male_thread(main_thread_len,z_main,8);
}
