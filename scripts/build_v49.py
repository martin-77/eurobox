import FreeCAD as App, Part, Mesh, importCSG, os, math, json, shutil, zipfile
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')); INPUT=os.path.join(ROOT,'inputs_decoded'); OUT=os.path.join(ROOT,'build'); shutil.rmtree(OUT,ignore_errors=True); os.makedirs(OUT)

def load_shape(p): s=Part.Shape(); s.read(p); return s

def hexp(af,h,z0=0):
    R=af/math.sqrt(3); pts=[App.Vector(R*math.cos(math.radians(30+60*i)),R*math.sin(math.radians(30+60*i)),z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,h))

def z2y(sh,x,y,z):
    a=sh.copy(); a.rotate(App.Vector(),App.Vector(1,0,0),-90); a.translate(App.Vector(x,y,z)); return a

def write_thread_scad(path, core, major, pitch, length, root_w, crest_w):
    txt=f'''$fn=64;\nmodule thread_solid(){{union(){{cylinder(r={core},h={length}); linear_extrude(height={length},twist=360*{length}/{pitch},slices=ceil({length}/{pitch}*20),convexity=20) polygon(points=[[{core}-0.10,-{root_w}/2],[{major},-{crest_w}/2],[{major},{crest_w}/2],[{core}-0.10,{root_w}/2]]);}}}}\nthread_solid();\n'''
    open(path,'w').write(txt)

def import_scad_shape(path):
    d=importCSG.open(path); d.recompute()
    candidates=[]
    for o in d.Objects:
        if hasattr(o,'Shape') and not o.Shape.isNull() and len(o.Shape.Solids)>0 and o.Shape.isValid(): candidates.append((abs(o.Shape.Volume),o.Shape.copy()))
    if not candidates: raise RuntimeError('no valid solid from '+path)
    sh=max(candidates,key=lambda x:x[0])[1]
    App.closeDocument(d.Name)
    return sh

male_scad=OUT+'/prototype_thread_male_8x2.scad'; female_scad=OUT+'/prototype_thread_female_cutter_8x2.scad'
write_thread_scad(male_scad,3.25,4.00,2.0,24.0,0.55,0.22)
write_thread_scad(female_scad,3.42,4.22,2.0,18.0,0.72,0.38)
male24=import_scad_shape(male_scad)
female18=import_scad_shape(female_scad)
male24=male24.common(Part.makeCylinder(4.05,24.0)).removeSplitter()
female18=female18.common(Part.makeCylinder(4.30,18.0)).removeSplitter()

base=load_shape(INPUT+'/v47_base.brep'); plate=load_shape(INPUT+'/v47_clamp_plate.brep'); lower=load_shape(INPUT+'/v47_rack_lower.brep'); stay=load_shape(INPUT+'/v47_rack_stay_support.brep'); pin=load_shape(INPUT+'/v45_pin.brep'); clip=load_shape(INPUT+'/v45_retaining_clip.brep')

for sx in (-42,42): base=base.fuse(Part.makeCylinder(4.8,15.2,App.Vector(sx,259.3,31),App.Vector(0,1,0)))
for x0 in (-104,76): base=base.fuse(Part.makeBox(28,32,11.74,App.Vector(x0,8,19.8)))
for sx in (-42,42):
    base=base.cut(z2y(female18,sx,261.165,31))
    base=base.cut(Part.makeCylinder(4.45,11.2,App.Vector(sx,250.0,31),App.Vector(0,1,0)))
    base=base.cut(Part.makeCylinder(5.75,11.25,App.Vector(sx,250.0,31),App.Vector(0,1,0)))
base=base.removeSplitter()

for sx in (-42,42):
    plate=plate.fuse(Part.makeCylinder(5.8,6.2,App.Vector(sx,244.465,31),App.Vector(0,1,0)))
    plate=plate.cut(Part.makeCylinder(3.2,8.0,App.Vector(sx,244.0,31),App.Vector(0,1,0)))
    plate=plate.cut(Part.makeCylinder(5.2,2.5,App.Vector(sx,244.665,31),App.Vector(0,1,0)))
plate=plate.removeSplitter()

sp=Part.makeCylinder(3,0.7).fuse(Part.makeCylinder(2.05,1.8,App.Vector(0,0,.7))).fuse(Part.makeCylinder(3,3.5,App.Vector(0,0,2.5)))
sp=sp.fuse(Part.makeCylinder(5.5,2.5,App.Vector(0,0,6.0)))
lead=male24.copy(); lead.translate(App.Vector(0,0,8.5)); sp=sp.fuse(lead)
sp=sp.fuse(hexp(10,6,32.5))
stud=male24.common(Part.makeCylinder(4.05,7.0)); stud.translate(App.Vector(0,0,38.5)); sp=sp.fuse(stud).removeSplitter()

knob=Part.makeCylinder(16,8)
for a in range(0,360,45):
    rr=17.6; knob=knob.cut(Part.makeCylinder(3.8,8.2,App.Vector(rr*math.cos(math.radians(a)),rr*math.sin(math.radians(a)),-.1)))
knob=knob.cut(Part.makeCylinder(4.35,8.2,App.Vector(0,0,-.1))).cut(hexp(10.35,6.2,-.1)).removeSplitter()
fem5=female18.common(Part.makeCylinder(4.30,5.0))
nut=hexp(13,4.5).cut(fem5).removeSplitter()

parts={'eurobox_v49_base':base,'eurobox_v49_clamp_plate':plate,'eurobox_v49_lead_spindle_RH_8x2':sp,'eurobox_v49_knob':knob,'eurobox_v49_knob_retainer_nut_8x2':nut,'eurobox_v49_spindle_retaining_clip':clip,'eurobox_v49_rack_lower':lower,'eurobox_v49_pin':pin,'eurobox_v49_pin_retaining_clip':clip,'eurobox_v49_rack_stay_support':stay}

ck={'freecad_version':'.'.join(App.Version()[:3]),'prototype_thread':{'type':'right-hand helical CSG lead thread','nominal_major_dia_mm':8.0,'pitch_mm':2.0,'male_bbox_major_dia_mm':round(max(male24.BoundBox.XLength,male24.BoundBox.YLength),3),'plate_hole_dia_mm':6.4,'plate_lug_thickness_mm':6.2,'plate_travel_mm':4.0},'valid':{k:v.isValid() for k,v in parts.items()},'solids':{k:len(v.Solids) for k,v in parts.items()}}
ck['plate_hole_probe_common_mm3']=[]
for sx in (-42,42): ck['plate_hole_probe_common_mm3'].append(round(plate.common(Part.makeCylinder(3.1,8,App.Vector(sx,244,31),App.Vector(0,1,0))).Volume,6))
ck['plate_motion']=[]
for d in [0,1,2,3,4]:
 p=plate.copy(); p.translate(App.Vector(0,d,0)); ck['plate_motion'].append({'open_mm':d,'base_common_mm3':round(base.common(p).Volume,6)})
sc=z2y(sp,-42,244.665,31); ck['spindle_plate_common_mm3']=round(sc.common(plate).Volume,6)
c=clip.copy(); c.rotate(App.Vector(),App.Vector(1,0,0),90); c.translate(App.Vector(-42,247.065,31)); ck['clip_spindle_common_mm3']=round(c.common(sc).Volume,6); ck['clip_plate_common_mm3']=round(c.common(plate).Volume,6)
ck['thread_kinematics']=[]
for d in [0,.5,1,2,3,4]:
 q=sp.copy(); q.rotate(App.Vector(),App.Vector(0,0,1),-360*d/2); q=z2y(q,-42,244.665+d,31); ck['thread_kinematics'].append({'open_mm':d,'rotation_deg':-360*d/2,'base_common_mm3':round(base.common(q).Volume,6)})
wrong=sp.copy(); wrong.rotate(App.Vector(),App.Vector(0,0,1),90); wrong=z2y(wrong,-42,245.165,31); ck['wrong_rotation_at_0_5mm_common_mm3']=round(base.common(wrong).Volume,6)
kb=knob.copy(); kb.translate(App.Vector(0,0,32.5)); nt=nut.copy(); nt.translate(App.Vector(0,0,40.5)); ck['knob_interface']={'spindle_knob_common_mm3':round(sp.common(kb).Volume,6),'spindle_nut_common_mm3':round(sp.common(nt).Volume,6),'knob_nut_common_mm3':round(kb.common(nt).Volume,6),'spindle_knob_distance_mm':round(sp.distToShape(kb)[0],6),'spindle_nut_distance_mm':round(sp.distToShape(nt)[0],6)}
tube=Part.makeCylinder(6.21,220,App.Vector(-110,0,0),App.Vector(1,0,0)); ck['tube_base_common_mm3']=round(base.common(tube).Volume,6); ck['rack_lower']=[]
for x in (-90,90):
 l=lower.copy(); l.translate(App.Vector(x,0,0)); ck['rack_lower'].append({'x':x,'base_common_mm3':round(base.common(l).Volume,6),'tube_preload_common_mm3':round(tube.common(l).Volume,6)})
ck['rack_lower_swing']=[]
for deg in [0,-15,-30,-45,-60,-75]:
 l=lower.copy(); l.rotate(App.Vector(0,-12,-5.5),App.Vector(1,0,0),deg); l.translate(App.Vector(-90,0,0)); ck['rack_lower_swing'].append({'deg':deg,'base_common_mm3':round(base.common(l).Volume,6)})

for n,s in parts.items():
    s.exportBrep(OUT+'/'+n+'.brep')
    s.exportStep(OUT+'/'+n+'.step')
    td=App.newDocument('mesh_'+n); to=td.addObject('Part::Feature','P'); to.Shape=s; td.recompute(); Mesh.export([to],OUT+'/'+n+'.stl'); App.closeDocument(td.Name)
    rt=Part.Shape(); rt.read(OUT+'/'+n+'.step')
    ck.setdefault('step_roundtrip',{})[n]={'valid':rt.isValid(),'solids':len(rt.Solids),'volume_delta_mm3':round(abs(rt.Volume-s.Volume),6)}

doc=App.newDocument('Eurobox_v49')
for n,s in parts.items(): o=doc.addObject('Part::Feature',n); o.Shape=s
for n,s in [('ASM_base',base),('ASM_plate',plate)]: o=doc.addObject('Part::Feature',n); o.Shape=s
for x in (-90,90): l=lower.copy(); l.translate(App.Vector(x,0,0)); o=doc.addObject('Part::Feature','ASM_rack_lower_'+str(x).replace('-','m')); o.Shape=l
for sx in (-42,42):
 q=z2y(sp,sx,244.665,31); o=doc.addObject('Part::Feature','ASM_spindle_'+str(sx).replace('-','m')); o.Shape=q
 k=kb.copy(); k=z2y(k,sx,244.665,31); o=doc.addObject('Part::Feature','ASM_knob_'+str(sx).replace('-','m')); o.Shape=k
 n=nt.copy(); n=z2y(n,sx,244.665,31); o=doc.addObject('Part::Feature','ASM_nut_'+str(sx).replace('-','m')); o.Shape=n
 cc=clip.copy(); cc.rotate(App.Vector(),App.Vector(1,0,0),90); cc.translate(App.Vector(sx,247.065,31)); o=doc.addObject('Part::Feature','ASM_spindle_clip_'+str(sx).replace('-','m')); o.Shape=cc
info=doc.addObject('App::FeaturePython','DesignParameters')
for prop,val in [('BoxSupportZ',39.54),('BoxEdgeY',244.665),('RackTubeDiameter',12.42),('LeadThreadDiameter',8.0),('LeadThreadPitch',2.0),('PlateOpenTravel',4.0),('PlateHoleDiameter',6.4)]: info.addProperty('App::PropertyLength',prop); setattr(info,prop,val)
doc.recompute(); doc.saveAs(OUT+'/eurobox_v49_assembly.FCStd')
with open(OUT+'/VALIDATION_v49_source.json','w') as f: json.dump(ck,f,indent=2)
print(json.dumps(ck,indent=2))
