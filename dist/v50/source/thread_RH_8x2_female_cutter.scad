$fn=48;
module thread_solid(){
  union(){
    cylinder(r=3.42,h=14.0);
    linear_extrude(height=14.0,twist=360*14.0/2.0,slices=ceil(14.0/2.0*18),convexity=30)
      polygon(points=[[3.42-0.08,-0.76/2],[4.22,-0.4/2],[4.22,0.4/2],[3.42-0.08,0.76/2]]);
  }
}
thread_solid();
