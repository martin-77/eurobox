$fn=128;

pitch = 2.0;
male_core_r = 3.25;
male_major_r = 4.0;
male_root_w = 1.20;
male_crest_w = 0.60;

female_core_r = 3.50;
female_major_r = 4.25;
female_root_w = 1.50;
female_crest_w = 0.90;

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

module male_thread(len,z0=0) {
    union() {
        translate([0,0,z0-0.25]) cylinder(r=male_core_r,h=len+0.5);
        ridge_rh(male_core_r,male_major_r,pitch,len,male_root_w,male_crest_w,z0,ceil(len/pitch*40));
    }
}

module female_thread_cutter(len,z0=0,overrun=2.0) {
    union() {
        translate([0,0,z0-overrun]) cylinder(r=female_core_r,h=len+2*overrun);
        ridge_rh(
            female_core_r,female_major_r,pitch,
            len+2*overrun,female_root_w,female_crest_w,
            z0-overrun,ceil((len+2*overrun)/pitch*40)
        );
    }
}

module scalloped_knob(h=7.0) {
    difference() {
        cylinder(r=15,h=h);
        for(a=[0:45:315])
            translate([16.2*cos(a),16.2*sin(a),-0.2])
                cylinder(r=3.4,h=h+0.4);
    }
}

knob_h = 7.0;
flange_h = 2.0;
flange_r = 6.5;
journal_r = 4.0;
journal_h = 7.35;
stop_h = 0.80;
stop_r = 4.20;
thread_len = 22.2;

z_flange = knob_h;
z_journal = z_flange + flange_h;
z_stop = z_journal + journal_h;
z_thread = z_stop + stop_h;

union() {
    scalloped_knob(knob_h);

    translate([0,0,z_flange])
        cylinder(r=flange_r,h=flange_h);

    translate([0,0,z_journal])
        cylinder(r=journal_r,h=journal_h+0.20);

    // Ø8.4 hard stop passes through the Ø8.8 clamp bore but the
    // RH8x2 female retainer cannot pass over it.
    translate([0,0,z_stop])
        cylinder(r=stop_r,h=stop_h);

    // Proven RH8x2 working thread, unchanged from the fitting pair.
    male_thread(thread_len,z_thread);
}
