import FreeCAD as App
import Part
import Mesh
import json
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build_v60')
if __name__ == '__main__':
    shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# Frozen measured datums
# ---------------------------------------------------------------------------
BOX_W = 600.0
BOX_L = 400.0
RIM_H = 16.45
RIM_Y = 16.45
RACK_D = 12.42
RACK_R = RACK_D / 2.0
RACK_CTC = 110.67
RACK_OUTER_W = 123.09
BOX_EDGE_Y = 244.665
BOX_RIM_INNER_Y = BOX_EDGE_Y - RIM_Y
BOX_SUPPORT_Z = 39.54

ARM_W = 32.0
ARM_H = 30.0
FLANGE_T = 4.5
WEB_T = 3.2
ARM_TOP_Z = BOX_SUPPORT_Z
ARM_BOTTOM_Z = ARM_TOP_Z - ARM_H
ARM_Y0 = 24.0
ARM_Y1 = 220.0
ARM_HEAD_FACE_Y = BOX_RIM_INNER_Y - 0.20
ARM_HEAD_CAP_T = WEB_T
ARM_HEAD_DROP_OVERLAP = 0.20
ARM_HEAD_DROP_Y0 = ARM_Y1 - ARM_HEAD_DROP_OVERLAP
ARM_HEAD_DROP_Y1 = ARM_HEAD_FACE_Y - ARM_HEAD_CAP_T + ARM_HEAD_DROP_OVERLAP

FRONT_CLAMP_X = -80.0
REAR_CLAMP_X = 80.0
CLAMP_X = (FRONT_CLAMP_X, REAR_CLAMP_X)
CLAMP_SPACING = REAR_CLAMP_X - FRONT_CLAMP_X
REAR_SUPPORT_X = 180.0

# Box-clamp layout is referenced to the two load-bearing holms, not to X=0.
# This uses the previously wasted span between the holms while keeping both
# screw stations equally clear of their nearest structural member.  The clamp
# plate follows the stations and therefore becomes wider without growing the
# printable BASE envelope.
BOX_CLAMP_BOSS_HALF_X = 11.35
BOX_CLAMP_HOLM_CLEAR_X = 12.0
BOX_CLAMP_EDGE_MARGIN_X = 15.0
FRONT_HOLM_INNER_X = FRONT_CLAMP_X + ARM_W/2.0
REAR_HOLM_INNER_X = REAR_SUPPORT_X - ARM_W/2.0
BOX_CLAMP_SPINDLE_X = (
    FRONT_HOLM_INNER_X + BOX_CLAMP_BOSS_HALF_X + BOX_CLAMP_HOLM_CLEAR_X,
    REAR_HOLM_INNER_X - BOX_CLAMP_BOSS_HALF_X - BOX_CLAMP_HOLM_CLEAR_X,
)
BOX_CLAMP_PLATE_X0 = BOX_CLAMP_SPINDLE_X[0] - BOX_CLAMP_EDGE_MARGIN_X
BOX_CLAMP_PLATE_X1 = BOX_CLAMP_SPINDLE_X[1] + BOX_CLAMP_EDGE_MARGIN_X

FIXED_STATION_HALF_X = 19.0
PHYSICAL_X_ORIGIN = 20.0 - (FRONT_CLAMP_X - FIXED_STATION_HALF_X)
FRONT_CLAMP_PHYS_X = FRONT_CLAMP_X + PHYSICAL_X_ORIGIN
REAR_CLAMP_PHYS_X = REAR_CLAMP_X + PHYSICAL_X_ORIGIN

BACKSTOP_X0 = REAR_CLAMP_X + 50.0
BACKSTOP_X1 = BACKSTOP_X0 + 50.0
BACKSTOP_W = BACKSTOP_X1 - BACKSTOP_X0
BACKSTOP_PHYS_X0 = BACKSTOP_X0 + PHYSICAL_X_ORIGIN
BACKSTOP_PHYS_X1 = BACKSTOP_X1 + PHYSICAL_X_ORIGIN
REAR_SUPPORT_PHYS_X = REAR_SUPPORT_X + PHYSICAL_X_ORIGIN

UPPER_SADDLE_R = 6.31
PIN_HOLE_D = 4.6
PIN_Y = -12.0
PIN_Z = -5.5
UPPER_PIVOT_W = 18.0
UPPER_PIVOT_R = 7.0
UPPER_BRIDGE_Y0 = -8.0
UPPER_BRIDGE_Y1 = 18.0
UPPER_BRIDGE_Z1 = 18.0
UPPER_GUSSET_LOWER_Y0 = PIN_Y - 5.5
UPPER_GUSSET_LOWER_Y1 = PIN_Y + 5.5
UPPER_GUSSET_LOWER_Z = PIN_Z + 3.0
UPPER_GUSSET_TOP_Y0 = UPPER_BRIDGE_Y0
UPPER_GUSSET_TOP_Y1 = 10.0
UPPER_GUSSET_TOP_Z = 13.0

RACK_CLOSURE_Y = 11.0
RACK_M4_BASE_CLEAR_D = 4.6
RACK_M4_NUT_AF = 7.4
RACK_M4_NUT_H = 3.6
RACK_M4_NUT_Z0 = 3.0

# Final box-clamp plate corridor.  The plate is now centred between the two
# load-bearing holm inner faces instead of around X=0.  It moves 5.5 mm toward
# -Y; 0.4 mm side/Z running clearance is kept.  Clearing exactly this envelope
# also removes the former one-sided massive crosshead region.
PLATE_SWEEP_X0 = BOX_CLAMP_PLATE_X0 - 0.4
PLATE_SWEEP_X1 = BOX_CLAMP_PLATE_X1 + 0.4
PLATE_SWEEP_Y0 = (BOX_RIM_INNER_Y - 8.0) - 5.5 - 0.4
PLATE_SWEEP_Y1 = (BOX_RIM_INNER_Y - 8.0) + 8.0 + 0.4
PLATE_SWEEP_Z0 = 16.0 - 0.4
PLATE_SWEEP_Z1 = 46.0 + 0.4

INDX_X_MAX = 298.0
INDX_Y_MAX = 275.0
V60_X_TARGET_MAX = 296.0

# Support-free reinforcement for the long front crosshead lip.  The old lower
# flange projected horizontally to ARM_HEAD_FACE_Y and therefore needed support
# in the installed print orientation.  Keep the full structural top surface,
# but carry its underside back to the existing crosshead web with a 45-degree
# DROP, matching the support strategy already used on the long side holms.
CROSSHEAD_FRONT_DROP_RUN = 8.0
CROSSHEAD_FRONT_DROP_RISE = 8.0


def box(x0, y0, z0, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x0, y0, z0))


def cyl_x(r, length, x=0.0, y=0.0, z=0.0):
    return Part.makeCylinder(r, length, App.Vector(x, y, z), App.Vector(1, 0, 0))


def hex_z(af, height, z0=0.0):
    import math
    rr = af / math.sqrt(3.0)
    pts = [App.Vector(rr*math.cos(math.radians(30+60*i)), rr*math.sin(math.radians(30+60*i)), z0) for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0,0,height))


def fuse_seq(shapes, label):
    if not shapes:
        raise RuntimeError(label + ': no shapes')
    out = shapes[0]
    for i, sh in enumerate(shapes[1:], 1):
        out = out.fuse(sh).removeSplitter()
        if not out.isValid():
            raise RuntimeError(f'{label}: invalid after fuse {i}')
    return out.removeSplitter()


def require_single(sh, label):
    if sh.isNull() or not sh.isValid() or len(sh.Solids) != 1:
        raise RuntimeError(f'{label}: expected one valid solid, got {len(sh.Solids)} solids')


def _smoothstep(t):
    return 3.0*t*t - 2.0*t*t*t


def _side_haunch(xc, y0, length, side, top):
    web_center = xc + side*8.0
    web_outer = web_center + side*(WEB_T/2.0)
    outer = xc + side*(ARM_W/2.0)
    span = abs(outer-web_outer)
    z_flange = (ARM_TOP_Z-FLANGE_T) if top else (ARM_BOTTOM_Z+FLANGE_T)
    z_tip = z_flange + (-10.0 if top else 10.0)
    curve = []
    for i in range(19):
        t = i/18.0
        z = z_tip + (z_flange-z_tip)*t
        x = web_outer + side*span*_smoothstep(t)
        curve.append(App.Vector(x, y0, z))
    pts = [App.Vector(web_outer,y0,z_flange), App.Vector(web_outer,y0,z_tip)] + curve[1:] + [App.Vector(web_outer,y0,z_flange)]
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0,length,0)).removeSplitter()


def make_i_beam_y(xc, y0, y1):
    length = y1-y0
    web_h = ARM_H - 2.0*FLANGE_T
    web_z = ARM_BOTTOM_Z + FLANGE_T
    parts = [
        box(xc-ARM_W/2.0,y0,ARM_TOP_Z-FLANGE_T,ARM_W,length,FLANGE_T),
        box(xc-ARM_W/2.0,y0,ARM_BOTTOM_Z,ARM_W,length,FLANGE_T),
        box(xc-8.0-WEB_T/2.0,y0,web_z,WEB_T,length,web_h),
        box(xc+8.0-WEB_T/2.0,y0,web_z,WEB_T,length,web_h),
    ]
    parts += [_side_haunch(xc,y0,length,side,top) for side in (-1,1) for top in (False,True)]
    return fuse_seq(parts, f'i-beam@{xc}')


def make_holm_head_closure(xc):
    cap = box(xc-ARM_W/2.0, ARM_HEAD_FACE_Y-ARM_HEAD_CAP_T, ARM_BOTTOM_Z, ARM_W, ARM_HEAD_CAP_T, ARM_H)
    drops = [
        box(xc-ARM_W/2.0, ARM_HEAD_DROP_Y0, ARM_BOTTOM_Z, WEB_T, ARM_HEAD_DROP_Y1-ARM_HEAD_DROP_Y0, ARM_H),
        box(xc+ARM_W/2.0-WEB_T, ARM_HEAD_DROP_Y0, ARM_BOTTOM_Z, WEB_T, ARM_HEAD_DROP_Y1-ARM_HEAD_DROP_Y0, ARM_H),
    ]
    return cap, drops


def make_long_support(xc, y0):
    holm = make_i_beam_y(xc, y0, ARM_Y1)
    cap, drops = make_holm_head_closure(xc)
    return fuse_seq([holm, cap] + drops, f'closed-long-support@{xc}')


def make_upper_station(xc):
    bridge = box(xc-19.0, UPPER_BRIDGE_Y0, 0.0, 38.0, UPPER_BRIDGE_Y1-UPPER_BRIDGE_Y0, UPPER_BRIDGE_Z1)
    root_beam = make_i_beam_y(xc, -8.0, 36.0)
    upper_pivot = cyl_x(UPPER_PIVOT_R, UPPER_PIVOT_W, xc-UPPER_PIVOT_W/2.0, PIN_Y, PIN_Z)
    gusset_pts = [
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_LOWER_Y0, UPPER_GUSSET_LOWER_Z),
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_LOWER_Y1, UPPER_GUSSET_LOWER_Z),
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_TOP_Y1, UPPER_GUSSET_TOP_Z),
        App.Vector(xc-UPPER_PIVOT_W/2.0, UPPER_GUSSET_TOP_Y0, UPPER_GUSSET_TOP_Z),
    ]
    upper_gusset = Part.Face(Part.makePolygon(gusset_pts+[gusset_pts[0]])).extrude(App.Vector(UPPER_PIVOT_W,0,0))
    pivot_web = box(xc-UPPER_PIVOT_W/2.0,-10.5,-5.5,UPPER_PIVOT_W,5.0,7.5)
    saddle_back = box(xc-UPPER_PIVOT_W/2.0,-8.0,-4.5,UPPER_PIVOT_W,2.5,6.5)
    q = fuse_seq([bridge,root_beam,upper_pivot,upper_gusset,pivot_web,saddle_back], f'upper-station@{xc}')
    q = q.cut(cyl_x(UPPER_SADDLE_R,40.0,xc-20.0,0.0,0.0)).removeSplitter()
    q = q.cut(cyl_x(PIN_HOLE_D/2.0,40.0,xc-20.0,PIN_Y,PIN_Z)).removeSplitter()
    q = q.cut(Part.makeCylinder(RACK_M4_BASE_CLEAR_D/2.0,9.0,App.Vector(xc,RACK_CLOSURE_Y,-1.0),App.Vector(0,0,1))).removeSplitter()
    nut = hex_z(RACK_M4_NUT_AF,RACK_M4_NUT_H,RACK_M4_NUT_Z0); nut.translate(App.Vector(xc,RACK_CLOSURE_Y,0.0))
    q = q.cut(nut).removeSplitter()
    if xc > 0:
        slot = box(xc+3.45,RACK_CLOSURE_Y-RACK_M4_NUT_AF/2.0,RACK_M4_NUT_Z0,15.75,RACK_M4_NUT_AF,RACK_M4_NUT_H)
    else:
        slot = box(xc-19.2,RACK_CLOSURE_Y-RACK_M4_NUT_AF/2.0,RACK_M4_NUT_Z0,15.75,RACK_M4_NUT_AF,RACK_M4_NUT_H)
    q = q.cut(slot).removeSplitter()
    require_single(q, f'upper-station@{xc}')
    return q


def make_clamp_frame_bridge():
    overlap = 0.30
    x0 = FRONT_CLAMP_X + 17.0 - overlap
    x1 = REAR_CLAMP_X - 17.0 + overlap
    top = box(x0,-8.0,BOX_SUPPORT_Z-6.0,x1-x0,16.0,6.0)
    raw = box(x0,-7.0,0.0,x1-x0,14.0,BOX_SUPPORT_Z-6.0)
    drop = raw.cut(cyl_x(UPPER_SADDLE_R,(x1-x0)+2.0,x0-1.0,0.0,0.0)).removeSplitter()
    q = fuse_seq([top,drop],'clamp-frame-bridge'); require_single(q,'clamp-frame-bridge'); return q


def make_crosshead_front_drop(x0, x1, y1):
    # Straight 45-degree self-supporting DROP under the front lower lip.
    # Root is 8 mm behind/below the free front edge, so the former horizontal
    # underside is fully supported without weakening the visible/front top edge.
    root_y = y1 - CROSSHEAD_FRONT_DROP_RUN
    root_z = ARM_BOTTOM_Z - CROSSHEAD_FRONT_DROP_RISE
    yz = [
        App.Vector(0.0, root_y, root_z),
        App.Vector(0.0, root_y, ARM_BOTTOM_Z),
        App.Vector(0.0, y1, ARM_BOTTOM_Z),
    ]
    face = Part.Face(Part.makePolygon(yz + [yz[0]]))
    q = face.extrude(App.Vector(x1-x0,0,0))
    q.translate(App.Vector(x0,0,0))
    require_single(q,'crosshead-front-drop')
    return q


def make_crosshead():
    x0 = FRONT_CLAMP_X - ARM_W/2.0
    x1 = REAR_SUPPORT_X + ARM_W/2.0
    y0 = 216.0
    y1 = ARM_HEAD_FACE_Y
    plate_x0 = PLATE_SWEEP_X0
    plate_x1 = PLATE_SWEEP_X1
    web_h = ARM_H-2.0*FLANGE_T
    return fuse_seq([
        box(x0,y0,ARM_BOTTOM_Z,x1-x0,y1-y0,FLANGE_T),
        box(x0,y0,ARM_TOP_Z-FLANGE_T,plate_x0-x0,y1-y0,FLANGE_T),
        box(plate_x1,y0,ARM_TOP_Z-FLANGE_T,x1-plate_x1,y1-y0,FLANGE_T),
        box(x0,y0,ARM_BOTTOM_Z+FLANGE_T,plate_x0-x0,4.5,web_h),
        box(plate_x1,y0,ARM_BOTTOM_Z+FLANGE_T,x1-plate_x1,4.5,web_h),
        make_crosshead_front_drop(x0,x1,y1),
    ],'crosshead')


def make_backstop():
    panel = box(BACKSTOP_X0,8.0,-42.0,BACKSTOP_W,4.0,50.0)
    root = box(BACKSTOP_X0,0.0,7.0,BACKSTOP_W,20.0,15.0)
    bridge = box(BACKSTOP_X0,0.0,18.0,BACKSTOP_W,20.0,20.75)
    q = fuse_seq([panel,root,bridge],'rear-backstop'); require_single(q,'rear-backstop'); return q


def make_plate_sweep_clearance():
    return box(PLATE_SWEEP_X0, PLATE_SWEEP_Y0, PLATE_SWEEP_Z0,
               PLATE_SWEEP_X1-PLATE_SWEEP_X0,
               PLATE_SWEEP_Y1-PLATE_SWEEP_Y0,
               PLATE_SWEEP_Z1-PLATE_SWEEP_Z0)


def make_right_core():
    front_support = make_long_support(FRONT_CLAMP_X, ARM_Y0)
    rear_support = make_long_support(REAR_SUPPORT_X, 0.0)
    core = fuse_seq([
        make_upper_station(FRONT_CLAMP_X), make_clamp_frame_bridge(), make_upper_station(REAR_CLAMP_X),
        front_support, make_crosshead(), rear_support, make_backstop(),
    ], 'RIGHT structural core before plate clearance')
    # Exact final v50 strategy: retain the full lower crosshead flange and outer
    # guide structures, but remove only the real moving plate envelope.  This
    # prevents the front holm head from intruding into the 160 mm plate after
    # the clamp spacing moved from 180 to 160 mm.
    core = core.cut(make_plate_sweep_clearance()).removeSplitter()
    require_single(core,'RIGHT structural core after plate clearance')
    return core


def mirror_x(sh):
    out=sh.copy(); out.mirror(App.Vector(0,0,0),App.Vector(1,0,0)); require_single(out,'mirrored LEFT structural core'); return out


def export_shape(name, sh):
    sh.exportStep(os.path.join(OUT,name+'.step'))
    doc=App.newDocument(name); obj=doc.addObject('Part::Feature',name); obj.Shape=sh
    doc.recompute(); doc.saveAs(os.path.join(OUT,name+'.FCStd')); Mesh.export([obj],os.path.join(OUT,name+'.stl')); App.closeDocument(doc.Name)


RIGHT=make_right_core(); LEFT=mirror_x(RIGHT)
failures=[]
if abs(CLAMP_SPACING-160.0)>1e-9: failures.append('Clamp centre spacing is not 160 mm')
if abs(FRONT_CLAMP_PHYS_X-39.0)>1e-9: failures.append('Front clamp physical centre is not 39 mm')
if abs(REAR_CLAMP_PHYS_X-199.0)>1e-9: failures.append('Rear clamp physical centre is not 199 mm')
if abs(BACKSTOP_PHYS_X0-249.0)>1e-9 or abs(BACKSTOP_PHYS_X1-299.0)>1e-9: failures.append('Backstop physical range is not 249..299 mm')
if abs(REAR_SUPPORT_PHYS_X-299.0)>1e-9: failures.append('Rear support physical centre is not 299 mm')
for side,sh in (('RIGHT',RIGHT),('LEFT',LEFT)):
    require_single(sh,side)
    if sh.BoundBox.XLength>INDX_X_MAX+1e-6: failures.append(f'{side} exceeds INDX X: {sh.BoundBox.XLength:.3f} mm')
    if sh.BoundBox.XLength>V60_X_TARGET_MAX+1e-6: failures.append(f'{side} exceeds v60 X reserve target: {sh.BoundBox.XLength:.3f} mm')
    if sh.BoundBox.YLength>INDX_Y_MAX+1e-6: failures.append(f'{side} exceeds INDX Y: {sh.BoundBox.YLength:.3f} mm')
left_back=mirror_x(LEFT); mirror_common=RIGHT.common(left_back).Volume
mirror_delta=abs(RIGHT.Volume+left_back.Volume-2.0*mirror_common)
if abs(RIGHT.Volume-LEFT.Volume)>1e-5: failures.append('LEFT/RIGHT volumes differ')
if mirror_delta>1e-4: failures.append(f'LEFT is not exact X mirror of RIGHT, delta={mirror_delta:.6f} mm3')
tube=cyl_x(RACK_R,400.0,-200.0,0.0,0.0); tube_common=RIGHT.common(tube).Volume
if tube_common>1e-4: failures.append(f'RIGHT structural core intersects real rack tube by {tube_common:.6f} mm3')
front_station=make_upper_station(FRONT_CLAMP_X); rear_station=make_upper_station(REAR_CLAMP_X); frame_bridge=make_clamp_frame_bridge()
if frame_bridge.common(front_station).Volume<1.0 or frame_bridge.common(rear_station).Volume<1.0: failures.append('Clamp-frame bridge is not fused into both fixed stations')
front_support=make_long_support(FRONT_CLAMP_X,ARM_Y0); rear_support=make_long_support(REAR_SUPPORT_X,0.0); backstop=make_backstop(); crosshead=make_crosshead()
if rear_support.common(backstop).Volume<500.0: failures.append('Moved rear support lacks substantial backstop overlap')
if rear_support.common(crosshead).Volume<300.0: failures.append('Moved rear support lacks substantial crosshead overlap')
if front_support.common(crosshead).Volume<300.0: failures.append('Front support is not continuously tied into crosshead')
panel_clearance=8.0-RACK_R
if panel_clearance<1.5: failures.append('Rear stop contact wall is not safely outboard of rack tube')
# The uncut support primitives must contain their cap and DROPs; the final core
# may then carry the intentional plate-sweep notch on the front support only.
drop_fractions=[]
for xc,support in ((FRONT_CLAMP_X,front_support),(REAR_SUPPORT_X,rear_support)):
    cap,drops=make_holm_head_closure(xc)
    drop_fractions.append({'x_mm':xc,'cap_fraction':round(support.common(cap).Volume/cap.Volume,6),'drop_fractions':[round(support.common(q).Volume/q.Volume,6) for q in drops]})
    if support.common(cap).Volume/cap.Volume<0.999: failures.append(f'Holm {xc} head cap missing')
    for i,q in enumerate(drops):
        if support.common(q).Volume/q.Volume<0.999: failures.append(f'Holm {xc} DROP {i} missing')
# The real final core must have the complete motion corridor free.
plate_sweep_common = RIGHT.common(make_plate_sweep_clearance()).Volume
if plate_sweep_common > 1e-4: failures.append(f'Final plate sweep corridor is blocked by {plate_sweep_common:.6f} mm3')
drop_probe=make_crosshead_front_drop(FRONT_CLAMP_X-ARM_W/2.0,REAR_SUPPORT_X+ARM_W/2.0,ARM_HEAD_FACE_Y)
drop_fraction=RIGHT.common(drop_probe).Volume/drop_probe.Volume
if drop_fraction<0.995: failures.append(f'Crosshead front DROP not fully incorporated: {drop_fraction:.6f}')
V={'version':'v60','stage':'clean_structural_core_v50_mechanics_restored','freecad_version':'.'.join(App.Version()[:3]),'architecture':'direct geometry; proven v50 rack joint/backstop/drop/plate-corridor solutions, no source rewriting','datums':{'rack_tube_diameter_mm':RACK_D,'rack_center_distance_mm':RACK_CTC,'clamp_centres_local_x_mm':list(CLAMP_X),'clamp_spacing_mm':CLAMP_SPACING,'front_clamp_physical_x_mm':FRONT_CLAMP_PHYS_X,'rear_clamp_physical_x_mm':REAR_CLAMP_PHYS_X,'backstop_local_x_mm':[BACKSTOP_X0,BACKSTOP_X1],'backstop_physical_x_mm':[BACKSTOP_PHYS_X0,BACKSTOP_PHYS_X1],'backstop_panel_y_mm':[8.0,12.0],'backstop_panel_clearance_from_tube_crown_mm':round(panel_clearance,3),'rear_support_local_x_mm':REAR_SUPPORT_X,'rear_support_physical_x_mm':REAR_SUPPORT_PHYS_X,'box_clamp_spindle_x_mm':[round(x,3) for x in BOX_CLAMP_SPINDLE_X],'box_clamp_plate_x_mm':[round(BOX_CLAMP_PLATE_X0,3),round(BOX_CLAMP_PLATE_X1,3)],'box_clamp_holm_clearance_mm':BOX_CLAMP_HOLM_CLEAR_X,'pivot_yz_mm':[PIN_Y,PIN_Z],'upper_pivot_width_mm':UPPER_PIVOT_W,'upper_pivot_diameter_mm':2.0*UPPER_PIVOT_R,'holm_head_face_y_mm':ARM_HEAD_FACE_Y,'holm_head_drop_y_mm':[ARM_HEAD_DROP_Y0,ARM_HEAD_DROP_Y1],'plate_sweep_xyz_mm':[[PLATE_SWEEP_X0,PLATE_SWEEP_X1],[PLATE_SWEEP_Y0,PLATE_SWEEP_Y1],[PLATE_SWEEP_Z0,PLATE_SWEEP_Z1]],'crosshead_front_drop_run_mm':CROSSHEAD_FRONT_DROP_RUN,'crosshead_front_drop_rise_mm':CROSSHEAD_FRONT_DROP_RISE,'crosshead_front_drop_angle_deg':45.0,'indx_build_xy_mm':[INDX_X_MAX,INDX_Y_MAX],'v60_x_target_max_mm':V60_X_TARGET_MAX},'geometry':{'right_bbox_mm':[round(RIGHT.BoundBox.XLength,3),round(RIGHT.BoundBox.YLength,3),round(RIGHT.BoundBox.ZLength,3)],'left_bbox_mm':[round(LEFT.BoundBox.XLength,3),round(LEFT.BoundBox.YLength,3),round(LEFT.BoundBox.ZLength,3)],'right_bounds_x_mm':[round(RIGHT.BoundBox.XMin,3),round(RIGHT.BoundBox.XMax,3)],'left_bounds_x_mm':[round(LEFT.BoundBox.XMin,3),round(LEFT.BoundBox.XMax,3)],'right_volume_mm3':round(RIGHT.Volume,3),'left_volume_mm3':round(LEFT.Volume,3),'mirror_delta_mm3':round(mirror_delta,9),'rack_tube_common_mm3':round(tube_common,9),'plate_sweep_common_mm3':round(plate_sweep_common,9),'front_support_crosshead_common_mm3':round(front_support.common(crosshead).Volume,3),'rear_support_backstop_common_mm3':round(rear_support.common(backstop).Volume,3),'rear_support_crosshead_common_mm3':round(rear_support.common(crosshead).Volume,3),'crosshead_front_drop_material_fraction':round(drop_fraction,6),'holm_head_closures':drop_fractions},'failures':failures}
with open(os.path.join(OUT,'VALIDATION_v60.json'),'w',encoding='utf-8') as f: json.dump(V,f,indent=2)
if failures:
    print(json.dumps(V,indent=2),flush=True); raise SystemExit('V60 HARD CHECKS FAILED: '+' | '.join(failures))
if __name__=='__main__':
    export_shape('eurobox_v60_base_right_core',RIGHT); export_shape('eurobox_v60_base_left_core',LEFT)
    with open(os.path.join(OUT,'README_BUILD_v60.txt'),'w',encoding='utf-8') as f:
        f.write('Eurobox v60 clean rebuild with proven v50 mechanics restored.\nBroad central Upper pivot + replaceable Lower fork; M4 positive closure.\nRear stop contact wall outboard of rack tube; long holms closed with caps and side DROPs.\nFinal moving plate corridor is cleared exactly as in the proven v50 width pass.\nDirect RIGHT structural construction; LEFT is exact X mirror.\n')
    print(json.dumps(V,indent=2),flush=True)
