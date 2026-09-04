$fn=48;
module ridge(core_r, major_r, pitch, length, root_w, crest_w){
  linear_extrude(height=length,twist=360*length/pitch,slices=ceil(length/pitch*18),convexity=40)
    polygon(points=[[core_r-0.08,-root_w/2],[major_r,-crest_w/2],[major_r,crest_w/2],[core_r-0.08,root_w/2]]);
}
module male_thread(length){
  union(){
    translate([0,0,-0.10]) cylinder(r=3.25,h=length+0.20);
    ridge(3.25,4.0,2.0,length,0.58,0.24);
  }
}
union(){
  cylinder(r=3.0,h=0.5);
  translate([0,0,0.35]) cylinder(r=2.5,h=1.55);
  translate([0,0,1.75]) cylinder(r=3.0,h=6.35);
  translate([0,0,7.9]) cylinder(r=5.5,h=2.0);
  translate([0,0,9.8]) male_thread(22.2);
  translate([0,0,31.9])
    rotate([0,0,30]) cylinder(r=5.773502691896258,h=4.7,$fn=6);
  translate([0,0,36.5]) male_thread(4.5);
}
