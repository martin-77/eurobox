$fn=48;
module thread_solid(){
  union(){
    cylinder(r=3.25,h=4.5);
    linear_extrude(height=4.5,twist=360*4.5/2.0,slices=ceil(4.5/2.0*18),convexity=30)
      polygon(points=[[3.25-0.08,-0.58/2],[4.0,-0.24/2],[4.0,0.24/2],[3.25-0.08,0.58/2]]);
  }
}
thread_solid();
