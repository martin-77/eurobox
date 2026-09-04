$fn=48;
module thread_solid(){
  union(){
    cylinder(r=3.25,h=22.2);
    linear_extrude(height=22.2,twist=360*22.2/2.0,slices=ceil(22.2/2.0*18),convexity=30)
      polygon(points=[[3.25-0.08,-0.58/2],[4.0,-0.24/2],[4.0,0.24/2],[3.25-0.08,0.58/2]]);
  }
}
thread_solid();
