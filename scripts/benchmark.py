import FreeCAD as App, Part, importCSG, os, time, json
root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
out=os.path.join(root,'benchmark_out'); os.makedirs(out,exist_ok=True)
t0=time.time()
# Representative FreeCAD geometry: two long PETG arms, rack clamps, front clamp wall
base=Part.makeBox(28,220,8,App.Vector(-104,0,31.54)).fuse(Part.makeBox(28,220,8,App.Vector(76,0,31.54)))
base=base.fuse(Part.makeBox(212,54,20,App.Vector(-106,220,20)))
for x in (-90,90):
    tube=Part.makeCylinder(6.26,34,App.Vector(x-17,0,0),App.Vector(1,0,0))
    shell=Part.makeCylinder(12,34,App.Vector(x-17,0,0),App.Vector(1,0,0)).cut(tube)
    base=base.fuse(shell)
# Representative Ø8x2 RH CSG thread
scad=os.path.join(out,'thread.scad')
open(scad,'w').write('''$fn=64; union(){ cylinder(r=3.25,h=24); linear_extrude(height=24,twist=4320,slices=240,convexity=20) polygon(points=[[3.15,-0.275],[4,-0.11],[4,0.11],[3.15,0.275]]); }''')
d=importCSG.open(scad); d.recompute(); candidates=[o.Shape.copy() for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull() and len(o.Shape.Solids)>0]; thread=max(candidates,key=lambda s:s.Volume); App.closeDocument(d.Name)
# Repeated booleans/kinematic checks similar to assembly validation
checks=[]
for i in range(60):
    q=thread.copy(); shift=(i%9)*0.5; q.rotate(App.Vector(),App.Vector(0,0,1),-90*(i%9)); q.translate(App.Vector(0,0,shift))
    block=Part.makeCylinder(5.5,28)
    checks.append(round(block.common(q).Volume,6))
# STEP roundtrip
step=os.path.join(out,'benchmark.step'); base.exportStep(step); rt=Part.Shape(); rt.read(step)
result={'freecad_version':'.'.join(App.Version()[:3]),'elapsed_seconds':round(time.time()-t0,3),'base_valid':base.isValid(),'roundtrip_valid':rt.isValid(),'thread_valid':thread.isValid(),'boolean_checks':len(checks),'base_volume_mm3':round(base.Volume,3)}
open(os.path.join(out,'benchmark.json'),'w').write(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
