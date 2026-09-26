$fn=128;

pitch = 2.0;
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

nut_h = 5.4;
nose_h = 2.0;
tip_r = 5.00;
body_r = 5.50;
flat_half = 5.30;

difference() {
    union() {
        // Ø10 tip gives 0.6 mm radial capture around the Ø8.8 clamp bore.
        cylinder(r1=tip_r,r2=body_r,h=nose_h);

        // Max Ø11.0 preserves 0.40 mm radial clearance in the frozen
        // Ø11.8 BASE spindle corridor. Two flats allow tightening.
        translate([0,0,nose_h])
            intersection() {
                cylinder(r=body_r,h=nut_h-nose_h);
                translate([-flat_half,-body_r-0.2,0])
                    cube([2*flat_half,2*body_r+0.4,nut_h-nose_h]);
            }
    }

    // Same female RH8x2 geometry as the proven lead nut.
    female_thread_cutter(nut_h,0,2.0);
}
