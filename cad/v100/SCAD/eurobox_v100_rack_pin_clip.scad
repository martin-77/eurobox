$fn=24;

module clip(od,id,t,ow){
  difference(){
    difference(){
      cylinder(d=od,h=t);
      translate([0,0,-0.1]) cylinder(d=id,h=t+0.2);
    }
    translate([-ow/2,0,-0.2]) cube([ow,od/2+1,t+0.4]);
  }
}

// V70 v4 rack-pin clip.
// Reference topology: V50 plate-retainer clip.
// Target groove Ø3.10; relaxed ID Ø2.80; opening 2.15.
// Outer diameter widened to Ø7.50 for stronger arms.
clip(7.50,2.80,1.30,2.15);
