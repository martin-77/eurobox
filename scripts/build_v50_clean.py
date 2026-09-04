import FreeCAD as App
import Part, Mesh
import os, json, math, shutil, subprocess

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'build_v50')
shutil.rmtree(OUT,ignore_errors=True); os.makedirs(OUT)
D=json.load(open(os.path.join(ROOT,'docs','V50_DIMENSIONS.json')))
M=D['measured_hard_datums_user']; P=D['v50_design_parameters']

# ---------- helpers ----------
def box(x,y,z,dx,dy,dz): return Part.makeBox(dx,dy,dz,App.Vector(x,y,z))
def cyl(r,l,x,y,z,axis=(0,0,1)): return Part.makeCylinder(r,l,App.Vector(x,y,z),App.Vector(*axis))
def fuse(items):
    s=items[0]
    for q in items[1:]: s=s.fuse(q)
    return s.removeSplitter()
def prism_x(points_yz,x0,length):
    pts=[App.Vector(x0,y,z) for y,z in points_yz]; pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(length,0,0))
def hex_z(af,h,z0=0):
    r=af/math.sqrt(3.0)
    pts=[App.Vector(r*math.cos(math.radians(30+60*i)),r*math.sin(math.radians(30+60*i)),z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,h))
def z_to_y(shape,x=0,y=0,z=0):
    q=shape.copy(); q.rotate(App.Vector(),App.Vector(1,0,0),-90); q.translate(App.Vector(x,y,z)); return q

def thread_stl_solid(name,length,major_d,core_d,pitch,profile_scale=1.0):
    # Real continuous helical solid. Tooth overlaps the core by 0.30 mm so OpenSCAD produces a manifold union.
    depth=(major_d-core_d)/2.0
    halfroot=pitch*0.24*profile_scale; halfcrest=pitch*0.105*profile_scale
    slices=max(48,int(math.ceil(length/pitch*18)))
    scad=os.path.join(OUT,name+'.scad'); stl=os.path.join(OUT,name+'_source.stl')
    txt=f'''$fn=64; major={major_d}; core={core_d}; pitch={pitch}; length={length}; depth=(major-core)/2;
union() {{
 cylinder(h=length,d=core);
 linear_extrude(height=length,twist=360*length/pitch,slices={slices},convexity=20)
  translate([core/2,0,0]) polygon(points=[[-0.30,-{halfroot}],[depth,-{halfcrest}],[depth,{halfcrest}],[-0.30,{halfroot}]]);
}}
'''
    open(scad,'w').write(txt)
    subprocess.run(['openscad','-o',stl,scad],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    m=Mesh.Mesh(stl); sh=Part.Shape(); sh.makeShapeFromMesh(m.Topology,0.04)
    if sh.ShapeType=='Shell': sh=Part.makeSolid(sh)
    elif sh.ShapeType=='Compound' and len(sh.Shells)==1: sh=Part.makeSolid(sh.Shells[0])
    sh=sh.removeSplitter()
    if sh.isNull() or not sh.isValid() or len(sh.Solids)!=1: raise RuntimeError('invalid helical solid '+name)
    return sh

def export_part(name,shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1: raise RuntimeError(name+' invalid before export')
    step=os.path.join(OUT,name+'.step'); stl=os.path.join(OUT,name+'.stl'); fcstd=os.path.join(OUT,name+'.FCStd')
    shape.exportStep(step)
    d=App.newDocument('exp_'+name); o=d.addObject('Part::Feature',name); o.Shape=shape; d.recompute(); d.saveAs(fcstd); Mesh.export([o],stl); App.closeDocument(d.Name)
    rt=Part.Shape(); rt.read(step)
    if not rt.isValid() or len(rt.Solids)!=1: raise RuntimeError(name+' STEP roundtrip failed')
    return {'bbox_mm':[round(rt.BoundBox.XLength,3),round(rt.BoundBox.YLength,3),round(rt.BoundBox.ZLength,3)],'volume_mm3':round(rt.Volume,3),'step_volume_delta_mm3':round(abs(rt.Volume-shape.Volume),6)}

print('STAGE thread masters')
PITCH=P['prototype_lead_thread_pitch_mm']; MAJOR=P['prototype_lead_thread_nominal_mm']; CORE=P['prototype_lead_thread_core_mm']; CLEAR=P['lead_nut_radial_clearance_mm']
MALE=thread_stl_solid('thread_RH_D8x2_male_master',24.0,MAJOR,CORE,PITCH,1.0)
FEMALE=thread_stl_solid('thread_RH_D8x2_female_cutter',16.0,MAJOR+2*CLEAR,CORE+2*CLEAR,PITCH,1.05)

# ---------- double-web I arms ----------
print('STAGE base')
def beam(cx):
    w=P['arm_outer_width_x_mm']; h=P['arm_outer_height_z_mm']; tf=P['arm_flange_thickness_mm']; tw=P['arm_web_thickness_mm']; off=P['arm_web_centers_x_offset_mm']; z0=P['arm_bottom_z_mm']; y0=P['arm_start_y_mm']; L=P['arm_end_y_mm']-y0
    return fuse([box(cx-w/2,y0,z0,w,L,tf),box(cx-w/2,y0,z0+h-tf,w,L,tf),box(cx-off-tw/2,y0,z0+tf,tw,L,h-2*tf),box(cx+off-tw/2,y0,z0+tf,tw,L,h-2*tf)])

HINGE_Y=P['rack_hinge_axis_y_mm']; LATCH_Y=P['rack_latch_axis_y_mm']; PIN_Z=P['rack_pin_axis_z_mm']
def upper_clamp(cx):
    # rigid saddle Ø12.54: 0.06 mm radial clearance to actual Ø12.42 tube
    body=box(cx-17,-19,0,34,38,19).cut(cyl(P['rack_upper_saddle_diameter_mm']/2,36,cx-18,0,0,(1,0,0)))
    body=body.fuse(box(cx-16,12,P['arm_bottom_z_mm'],32,18,P['arm_outer_height_z_mm']))
    # ears are outside the 32 mm rack-lower body; two aligned pins = permanent hinge + removable latch
    for yy in (HINGE_Y,LATCH_Y):
        body=body.fuse(box(cx-23,yy-6,-17,6,12,19)).fuse(box(cx+17,yy-6,-17,6,12,19))
        body=body.cut(cyl(P['rack_pin_hole_diameter_mm']/2,48,cx-24,yy,PIN_Z,(1,0,0)))
    return body.removeSplitter()

base=fuse([beam(-90),beam(90),upper_clamp(-90),upper_clamp(90)])
# broad box-side crosshead and deep load paths; no decorative holes near clamp roots
base=base.fuse(box(-106,216,34.54,212,28.665,5.0))
for cx in (-90,90): base=base.fuse(box(cx-16,216,18,32,28.665,16.54))
base=base.fuse(box(-106,240,13.0,42,36,26.54)).fuse(box(64,240,13.0,42,36,26.54))
base=base.fuse(box(-68,240,9.54,136,36,4.2))
# two separate lead-nut posts + top/bottom ties. Moving plate remains free between them.
for sx in P['spindle_centers_x_mm']:
    base=base.fuse(box(sx-13,258.0,18,26,17.5,31))
base=base.fuse(box(-67,258.0,13,134,6,5)).fuse(box(-67,258.0,49,134,6,5))
# top-loading keyed nut pockets and screw passages
NUT_Y=258.665
for sx in P['spindle_centers_x_mm']:
    base=base.cut(box(sx-9.8,NUT_Y-0.3,22.5,19.6,14.6,32.0))
    base=base.cut(cyl(4.6,22,sx,253.0,P['spindle_axis_z_mm'],(0,1,0)))
# guide rails: plate tongues move +Y by 4.5 mm with 0.4 mm side/vertical clearance
for sign in (-1,1):
    xo=65.4 if sign>0 else -68.0
    base=base.fuse(box(xo,251.8,35.0,2.6,14.4,12.0))
    xi=58.4 if sign>0 else -65.4
    base=base.fuse(box(xi,251.8,34.0,7.0,14.4,2.6)).fuse(box(xi,251.8,45.4,7.0,14.4,2.6))
base=base.removeSplitter()
if not base.isValid() or len(base.Solids)!=1: raise RuntimeError('base not one valid solid')

# ---------- contoured rack-lower ----------
print('STAGE rack lower')
w=P['rack_lower_body_width_x_mm']
ring=cyl(9.8,w,-w/2,0,0,(1,0,0)).cut(cyl(P['rack_lower_saddle_diameter_mm']/2,w+2,-w/2-1,0,0,(1,0,0))).common(box(-w/2,-11,-11,w,22,11.0))
left_web=prism_x([(HINGE_Y,-15),( -8,-8.5),(-6.5,-4),(HINGE_Y,-5)],-w/2,w)
right_web=prism_x([(LATCH_Y,-15),(8,-8.5),(6.5,-4),(LATCH_Y,-5)],-w/2,w)
lower=fuse([ring,cyl(5.0,w,-w/2,HINGE_Y,PIN_Z,(1,0,0)),cyl(5.0,w,-w/2,LATCH_Y,PIN_Z,(1,0,0)),left_web,right_web])
for yy in (HINGE_Y,LATCH_Y): lower=lower.cut(cyl(P['rack_pin_hole_diameter_mm']/2,w+2,-w/2-1,yy,PIN_Z,(1,0,0)))
lower=lower.removeSplitter()
if not lower.isValid() or len(lower.Solids)!=1: raise RuntimeError('rack lower invalid')

# ---------- clamp plate ----------
print('STAGE clamp plate')
PLATE_Y=M['rack_tube_to_box_edge_local_y_mm']; PLATE_Z0=P['box_clamp_plate_z_min_mm']; PLATE_H=P['box_clamp_plate_z_max_mm']-PLATE_Z0
plate=fuse([box(-59,PLATE_Y,PLATE_Z0,118,8,PLATE_H),box(-59,PLATE_Y-P['box_clamp_underhook_depth_mm'],18.8,118,P['box_clamp_underhook_depth_mm'],P['box_clamp_underhook_thickness_mm'])])
# true holes, strong outside bosses, recessed inside nut pockets
for sx in P['spindle_centers_x_mm']:
    plate=plate.fuse(cyl(8.0,4.0,sx,PLATE_Y+8,P['spindle_axis_z_mm'],(0,1,0)))
    plate=plate.cut(cyl(P['plate_hole_diameter_mm']/2,14,sx,PLATE_Y-1,P['spindle_axis_z_mm'],(0,1,0)))
    plate=plate.cut(cyl(7.4,3.7,sx,PLATE_Y,P['spindle_axis_z_mm'],(0,1,0)))
# additive guide tongues, not weakening slots
for gx in (-62,62): plate=plate.fuse(box(gx-3,PLATE_Y+8,37,6,8,8))
plate=plate.removeSplitter()
if not plate.isValid() or len(plate.Solids)!=1: raise RuntimeError('plate invalid')

# ---------- replaceable lead nut + cap ----------
print('STAGE lead nut')
lead_nut=fuse([box(-8,-7,0,16,14,14),box(-9.5,-8,11,19,16,3)])
fc=FEMALE.copy(); fc.translate(App.Vector(0,0,-1)); lead_nut=lead_nut.cut(fc).removeSplitter()
lead_nut_cap=fuse([box(-11,-9,0,22,18,2.4),box(-9.6,-8.1,-2.4,19.2,16.2,2.4)])
if not lead_nut.isValid() or len(lead_nut.Solids)!=1: raise RuntimeError('lead nut invalid')

# ---------- separated spindle, plate retainer nut, knob, knob retainer ----------
print('STAGE spindle and knob')
def thread_segment(length): return MALE.common(cyl(4.05,length,0,0,0)).removeSplitter()
inner=thread_segment(4.0)
journal=cyl(P['plate_journal_nominal_diameter_mm']/2,4.665,0,0,4.0)
shoulder=cyl(P['thrust_shoulder_diameter_mm']/2,2.0,0,0,8.665)
main=thread_segment(20.0); main.translate(App.Vector(0,0,10.665))
hexdrive=hex_z(P['knob_hex_af_spindle_mm'],7.0,30.665)
outer=thread_segment(6.0); outer.translate(App.Vector(0,0,37.665))
spindle=fuse([inner,journal,shoulder,main,hexdrive,outer])

def female_hex_nut(name,af,thickness):
    cutter=thread_stl_solid(name+'_cutter',thickness+2,MAJOR+2*CLEAR,CORE+2*CLEAR,PITCH,1.05); cutter.translate(App.Vector(0,0,-1))
    return hex_z(af,thickness).cut(cutter).removeSplitter()
plate_retainer=female_hex_nut('plate_retainer',14.0,P['plate_retainer_nut_thickness_mm'])
knob_retainer=female_hex_nut('knob_retainer',14.0,3.0)
knob=cyl(P['knob_diameter_mm']/2,P['knob_thickness_mm'],0,0,0)
knob=knob.cut(hex_z(P['knob_hex_af_socket_mm'],7.4,-0.1)).cut(cyl(4.4,P['knob_thickness_mm']+1,0,0,-0.5)).removeSplitter()
for s,n in ((spindle,'spindle'),(plate_retainer,'plate retainer'),(knob,'knob'),(knob_retainer,'knob retainer')):
    if not s.isValid() or len(s.Solids)!=1: raise RuntimeError(n+' invalid')

# ---------- rack pins + clip ----------
print('STAGE pins')
pin=fuse([cyl(2.0,50,-25,0,0,(1,0,0)),cyl(4.0,2.5,-25,0,0,(1,0,0))])
pin=pin.cut(cyl(1.65,1.8,21.5,0,0,(1,0,0))).removeSplitter()
pin_clip=cyl(4.4,1.6,0,0,0).cut(cyl(1.72,1.8,0,0,-0.1)).cut(box(0,-5,-0.1,5,10,1.8)).removeSplitter()

# ---------- adjustable Focus diagonal-stay anti-flop saddle ----------
print('STAGE stay saddle')
stay=box(-16,-12,0,32,24,16)
# 90 degree V, deliberately not a fake exact tube diameter
vcut=prism_x([(-7,16),(0,9),(7,16)],-17,34); stay=stay.cut(vcut)
for xx in (-8,8): stay=stay.cut(box(xx-2.1,-6,-0.5,4.2,12,17))
# offset vertical adjuster so the stay remains in the V
stay=stay.fuse(cyl(8,12,0,9,8))
stay_fc=FEMALE.copy(); stay_fc.translate(App.Vector(0,9,7)); stay=stay.cut(stay_fc).removeSplitter()
stay_screw=thread_segment(18).fuse(cyl(9,3,0,0,18)).removeSplitter()
if not stay.isValid() or len(stay.Solids)!=1: raise RuntimeError('stay saddle invalid')

# ---------- validations ----------
print('STAGE validation')
R=M['rack_tube_diameter_mm']/2; report={'version':'v50','freecad_version':'.'.join(App.Version()[:3]),'parts':{},'checks':{}}
# hard global box-edge arithmetic
right=M['rack_tube_centers_global_y_mm'][1]+M['rack_tube_to_box_edge_local_y_mm']; left=M['rack_tube_centers_global_y_mm'][0]-M['rack_tube_to_box_edge_local_y_mm']
if abs(right-300)>1e-6 or abs(left+300)>1e-6: raise RuntimeError('box global edges wrong')
report['checks']['global_box_edges_y_mm']=[left,right]
# rigid base vs real pipe; lower preload
for cx in M['clamp_station_x_mm']:
    tube=cyl(R,34,cx-17,0,0,(1,0,0)); cv=base.common(tube).Volume
    if cv>1e-4: raise RuntimeError('rigid base/tube collision '+str(cx))
    lo=lower.copy(); lo.translate(App.Vector(cx,0,0)); bc=base.common(lo).Volume; preload=tube.common(lo).Volume
    if bc>1e-4 or preload<=0: raise RuntimeError('rack lower closed check failed '+str(cx))
    report['checks']['rack_'+str(cx)]={'base_tube_common_mm3':round(cv,6),'base_lower_common_mm3':round(bc,6),'lower_tube_preload_mm3':round(preload,6)}
# hinge motion and real-tube release
swing=[]
for deg in (0,-10,-15,-20,-30,-45,-60,-75):
    lo=lower.copy(); lo.rotate(App.Vector(0,HINGE_Y,PIN_Z),App.Vector(1,0,0),deg); lo.translate(App.Vector(-90,0,0))
    bc=base.common(lo).Volume; tube=cyl(R,34,-107,0,0,(1,0,0)); tc=tube.common(lo).Volume
    if bc>1e-4: raise RuntimeError('rack lower swing collision '+str(deg))
    swing.append({'deg':deg,'base_common_mm3':round(bc,6),'tube_common_mm3':round(tc,6)})
if swing[4]['tube_common_mm3']>1e-4: raise RuntimeError('tube not released by -30 deg')
report['checks']['rack_lower_swing']=swing
# pin axes actually align: Ø4 probe must pass lower and base holes
for yy in (HINGE_Y,LATCH_Y):
    probe=cyl(P['rack_pin_nominal_diameter_mm']/2,50,-25,yy,PIN_Z,(1,0,0))
    if lower.common(probe).Volume>1e-4: raise RuntimeError('pin does not clear rack lower')
    q=probe.copy(); q.translate(App.Vector(-90,0,0))
    if base.common(q).Volume>1e-4: raise RuntimeError('pin does not clear base ears')
report['checks']['pin_axes']={'hinge_y_mm':HINGE_Y,'latch_y_mm':LATCH_Y,'z_mm':PIN_Z,'pin_d_mm':P['rack_pin_nominal_diameter_mm'],'hole_d_mm':P['rack_pin_hole_diameter_mm']}
# plate travel 0..4.5
motion=[]
for d in (0,1,2,3,4,4.5):
    q=plate.copy(); q.translate(App.Vector(0,d,0)); cv=base.common(q).Volume
    if cv>1e-4: raise RuntimeError('plate/base collision '+str(d))
    motion.append({'open_mm':d,'base_common_mm3':round(cv,6)})
report['checks']['plate_motion']=motion
# actual real holes: Ø8.0 journal probe must pass; shoulder must be larger than hole
for sx in P['spindle_centers_x_mm']:
    probe=cyl(P['plate_journal_nominal_diameter_mm']/2,12,sx,PLATE_Y-1,P['spindle_axis_z_mm'],(0,1,0))
    if plate.common(probe).Volume>1e-4: raise RuntimeError('plate hole not through at '+str(sx))
if P['thrust_shoulder_diameter_mm']<=P['plate_hole_diameter_mm']: raise RuntimeError('shoulder cannot retain plate')
report['checks']['plate_spindle_interface']={'journal_d_mm':P['plate_journal_nominal_diameter_mm'],'hole_d_mm':P['plate_hole_diameter_mm'],'shoulder_d_mm':P['thrust_shoulder_diameter_mm'],'retainer_recess_depth_mm':3.7}
# conservative box-rim solid: plate must not penetrate; underhook clears after +4.5
rim=box(-70,PLATE_Y-M['eurobox_lower_rim_horizontal_mm'],M['box_support_z_mm']-M['eurobox_lower_rim_vertical_mm'],140,M['eurobox_lower_rim_horizontal_mm'],M['eurobox_lower_rim_vertical_mm'])
if plate.common(rim).Volume>1e-4: raise RuntimeError('plate penetrates box rim closed')
po=plate.copy(); po.translate(App.Vector(0,P['box_clamp_plate_open_travel_mm'],0))
if po.common(rim).Volume>1e-4: raise RuntimeError('plate penetrates box rim open')
hook_open=PLATE_Y-P['box_clamp_underhook_depth_mm']+P['box_clamp_plate_open_travel_mm']
if hook_open<=PLATE_Y: raise RuntimeError('underhook does not clear box edge')
report['checks']['box_underhook']={'closed_inner_y_mm':PLATE_Y-P['box_clamp_underhook_depth_mm'],'open_inner_y_mm':hook_open,'box_edge_y_mm':PLATE_Y}
# real helical nut/spindle phase. Nut start chosen exactly two pitches after main-thread start.
nut=lead_nut.copy(); nut=z_to_y(nut,-42,NUT_Y,31)
SPINDLE_Y=244.0
kin=[]
for d in (0,0.5,1.0,2.0,4.0):
    q=spindle.copy(); q.rotate(App.Vector(),App.Vector(0,0,1),-360*d/PITCH); q=z_to_y(q,-42,SPINDLE_Y+d,31)
    cv=q.common(nut).Volume
    if cv>0.02: raise RuntimeError('correct thread phase collision '+str(d)+' '+str(cv))
    kin.append({'open_mm':d,'rotation_deg':-360*d/PITCH,'nut_common_mm3':round(cv,6)})
wrong=spindle.copy(); wrong.rotate(App.Vector(),App.Vector(0,0,1),90); wrong=z_to_y(wrong,-42,SPINDLE_Y+0.5,31); wrong_cv=wrong.common(nut).Volume
if wrong_cv<0.1: raise RuntimeError('thread is not phase-sensitive')
report['checks']['thread_kinematics']=kin; report['checks']['wrong_phase_at_0_5mm_common_mm3']=round(wrong_cv,6)
# retainer/knob mounting dimensions
if P['knob_hex_af_socket_mm']<=P['knob_hex_af_spindle_mm']: raise RuntimeError('knob hex has no FDM clearance')
report['checks']['knob_interface']={'spindle_hex_AF_mm':P['knob_hex_af_spindle_mm'],'knob_socket_AF_mm':P['knob_hex_af_socket_mm'],'separate_parts':True}
# beam sanity check
b=P['arm_outer_width_x_mm']; h=P['arm_outer_height_z_mm']; tf=P['arm_flange_thickness_mm']; tw=P['arm_web_thickness_mm']; hw=h-2*tf
A=2*b*tf+2*tw*hw; I=2*(b*tf**3/12+b*tf*(h/2-tf/2)**2)+2*(tw*hw**3/12)
F=P['design_payload_limit_kg']*9.81/4; L=P['arm_end_y_mm']-P['arm_start_y_mm']; E=P['petg_E_MPa_sanity']; c=h/2
report['beam_sanity']={'area_mm2':round(A,3),'Ix_mm4':round(I,3),'free_length_mm':L,'static_force_per_arm_N':round(F,3),'static_stress_MPa':round(F*L*c/I,3),'static_tip_deflection_mm':round(F*L**3/(3*E*I),3),'dynamic_3x_stress_MPa':round(3*F*L*c/I,3),'dynamic_3x_tip_deflection_mm':round(3*F*L**3/(3*E*I),3),'E_MPa_assumed':E}
# width estimate incl separated knob/nut
module_max_y=SPINDLE_Y+43.665
full_width=2*(M['rack_tube_centers_global_y_mm'][1]+module_max_y)
report['checks']['estimated_full_system_width_closed_mm']=round(full_width,3)

# ---------- export ----------
print('STAGE export')
parts={'eurobox_v50_base':base,'eurobox_v50_clamp_plate':plate,'eurobox_v50_rack_lower':lower,'eurobox_v50_lead_nut_print':lead_nut,'eurobox_v50_lead_nut_cap':lead_nut_cap,'eurobox_v50_lead_spindle_print':spindle,'eurobox_v50_plate_retainer_nut':plate_retainer,'eurobox_v50_knob':knob,'eurobox_v50_knob_retainer_nut':knob_retainer,'eurobox_v50_rack_pin':pin,'eurobox_v50_pin_clip':pin_clip,'eurobox_v50_stay_saddle':stay,'eurobox_v50_stay_support_screw':stay_screw}
for name,shape in parts.items(): report['parts'][name]=export_part(name,shape)

# one-side assembly with real pipe, both lower clamps and screw mechanism
ad=App.newDocument('Eurobox_v50_Assembly')
def add(name,shape): o=ad.addObject('Part::Feature',name); o.Shape=shape
add('Base',base); add('ClampPlate',plate); add('REF_RackTube',cyl(R,220,-110,0,0,(1,0,0)))
for cx in (-90,90):
    q=lower.copy(); q.translate(App.Vector(cx,0,0)); add('RackLower_'+str(cx).replace('-','m'),q)
for sx in P['spindle_centers_x_mm']:
    q=spindle.copy(); q=z_to_y(q,sx,SPINDLE_Y,31); add('Spindle_'+str(sx).replace('-','m'),q)
    q=lead_nut.copy(); q=z_to_y(q,sx,NUT_Y,31); add('LeadNut_'+str(sx).replace('-','m'),q)
    # inner retainer nut spans y245.2..248.0, fully recessed
    q=plate_retainer.copy(); q=z_to_y(q,sx,245.2,31); add('PlateRetainer_'+str(sx).replace('-','m'),q)
    # knob sits on AF12 drive, separate outer retainer after it
    q=knob.copy(); q=z_to_y(q,sx,274.5,31); add('Knob_'+str(sx).replace('-','m'),q)
ad.recompute(); ad.saveAs(os.path.join(OUT,'eurobox_v50_assembly.FCStd')); App.closeDocument(ad.Name)

with open(os.path.join(OUT,'VALIDATION_v50.json'),'w') as f: json.dump(report,f,indent=2,sort_keys=True)
with open(os.path.join(OUT,'README_BUILD.txt'),'w') as f:
    f.write('Eurobox v50 clean-sheet build for FOCUS THRON2 6.8 EQP 2023\n')
    f.write('All hard datums and design values: docs/V50_DIMENSIONS.json\n')
    f.write('Concept/rationale: docs/V50_DESIGN.md\n')
    f.write('This is a 16 kg rack-limit design; 3x is only an adapter sanity check, not a higher payload approval.\n')
print(json.dumps(report,indent=2,sort_keys=True)); print('BUILD_OK')
