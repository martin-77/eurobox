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

// V70 v4 lead-nut retaining-pin clip.
// Reference topology: V50 plate-retainer clip.
// Target groove Ø2.40; relaxed ID Ø2.10; opening 1.60.
// Outer diameter widened to Ø7.00 for stronger arms.
clip(7.00,2.10,1.30,1.60);
