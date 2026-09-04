# Eurobox bicycle mount v50

Target bicycle: **FOCUS THRON² EQP, model year 2023**.

This document is the single source of truth for geometry, design intent and validation criteria of v50. Values are classified as **MEASURED**, **FOCUS/MY23 SOURCE**, or **DESIGN** so that later measurements can be changed without silently mixing them with assumptions.

## 1. Goal

Tool-less removable PETG carrier adapter for a 600 x 400 mm Eurobox mounted transversely on the original FOCUS THRON² EQP rear rack. The holder clamps to the original rack tubes, supports the bottom edge of the Eurobox and clamps the lower Eurobox rim without drilling the box.

Primary priorities, in order:

1. no collision with the 2023 THRON² EQP rack/fender/suspension movement;
2. mechanically credible load paths rather than thin cantilever plates;
3. printable on a Prusa CORE One L with 0.4 mm nozzle and little/no support;
4. tool-less mounting/removal;
5. no left/right-specific printed part unless unavoidable;
6. printed prototype fastener now, later convertible to metal M4/heat-set hardware without redesigning the Base;
7. all critical dimensions live in one parameter block in `scripts/build_v50.py`.

## 2. Bicycle context

### FOCUS / MY23 source data

FOCUS archive: THRON² EQP 2022-2024 Bosch, including a dedicated MY23 EQP exploded drawing and MY23 6.7/6.8 EQP datasheets.

Relevant chassis/equipment facts:

- 29 inch rear wheel.
- full-suspension F.O.L.D. chassis, 130 mm rear travel.
- 148 x 12 mm rear thru axle.
- original EQP rear carrier: Massload 3-leg.
- original fender: aluminium, about 60 mm nominal width in MY23 listings.
- system weight limit: 150 kg.
- rack rating conflict in published material: MY23 dealer/spec listings commonly state **25 kg**, while the current FOCUS archive FAQ for this generation states **16 kg (8 kg per side)**. v50 uses **16 kg as the conservative design ceiling** until the exact label/part on the user's bike is confirmed.

Sources used during v50 design:

- FOCUS archive: https://www.focus-bikes.com/int/archive/e-bikes/thron/pdp-thron-eqp-2022-2024-bosch
- FOCUS THRON² 2022-2024 archive/FAQ: https://www.focus-bikes.com/de_de/archive/e-bikes/thron/pdp-thron-2022-2024-bosch
- MY23 dealer spec example: https://www.bikes.de/shop/e-bikes/marke.focus/focus-thron2-6-8-eqp-2023/

The carrier is part of the sprung rear structure of this full-suspension bike. Therefore v50 mounts only to the existing rack, not between sprung and unsprung frame members.

## 3. Coordinate system

All CAD uses the following local convention for one holder:

- **X** = direction of travel / rack-tube axis.
- **Y** = transverse, positive from rack tube toward the Eurobox outside edge.
- **Z** = upward.
- local rack tube centre = **Y 0 / Z 0**.
- rack tube axis = X.

The same holder is mirrored by placement for the opposite side; geometry itself remains universal.

## 4. Hard dimensions

### Eurobox — MEASURED

| Parameter | Value |
|---|---:|
| box width transverse | 600.00 mm |
| box length longitudinal | 400.00 mm |
| lower rim horizontal projection | 16.45 mm |
| lower rim vertical projection | 16.45 mm |
| lower rim wall material | approx. 2-3 mm |

Box edges in the complete-bike coordinate system are Y = +/-300 mm and X = +/-200 mm.

### Original rack — MEASURED

| Parameter | Value |
|---|---:|
| rack outside width | 123.09 mm |
| actual rack tube diameter | **12.42 mm** |
| tube centre-to-centre transverse | 110.67 mm |
| tube centres in complete-bike coordinates | Y = +/-55.335 mm |
| usable straight tube length | approx. 220-240 mm |
| clamp station spacing along X | **180.00 mm** |
| clamp station centres | X = +/-90.00 mm |
| tube-centre to box-edge transverse distance | **244.665 mm** |
| tube outer surface to box edge | 238.455 mm |

### Vertical clearances — MEASURED / DERIVED

| Parameter | Value |
|---|---:|
| rack tube centre Z | 0.00 mm |
| rack tube top | +6.21 mm |
| fender top | +34.54 mm |
| Eurobox support plane | **+39.54 mm** |
| nominal residual fender clearance | **5.00 mm** |

The 5 mm fender clearance is a hard keep-out target, not available structure volume.

## 5. v50 architecture

### 5.1 Base

The Base is rebuilt from primitives; no v45/v47 BREP is used.

It consists of:

- two rack clamp towers at X +/-90 mm;
- two long outboard support beams from the tube zone to the Eurobox rim;
- cross ties near the tube and near the clamp screw bracket;
- local solid gussets above the pivot zone;
- an outer screw bridge carrying two replaceable nut cartridges at X +/-42 mm;
- a flat support surface at Z = 39.54 mm.

The long beams are not simple 8 mm plates. They use an **open-bottom U section** so the upper support surface remains flat while bending stiffness comes primarily from vertical side webs.

Nominal beam section:

- beam width X: 28 mm;
- top skin: 5.0 mm;
- side web thickness: 3.2 mm;
- web depth below top skin: 17.5 mm;
- lower web edge Z: 17.04 mm;
- support top Z: 39.54 mm.

This gives a much larger second moment of area than the old 28 x 8 mm slab while remaining support-friendly in the intended print orientation.

### 5.2 Rack clamp

The rigid upper saddle and flexible lower jaw form a two-piece clamp around the original 12.42 mm tube.

- rigid Base saddle diameter: **12.52 mm** = 0.05 mm radial clearance;
- flexible lower-jaw nominal saddle diameter: **12.30 mm** = intentional printed preload;
- pivot axis: X;
- pivot centre relative to tube centre: Y = -12.0 mm, Z = -5.5 mm;
- pin shaft: 4.0 mm;
- printed pivot holes: 4.6 mm;
- pin diametral clearance: 0.6 mm.

The lower jaw opens toward negative rotation around X. The required checked range is 0 to -75 degrees; the tube should be released by approximately -45 degrees.

### 5.3 Eurobox clamp plate

One broad plate spans the two screw axes.

- screw axes: X = +/-42 mm, Z = 31.0 mm;
- clamp travel: 0-4.0 mm;
- spindle journal hole: 6.4 mm;
- spindle journal: 6.0 mm;
- radial journal clearance: 0.20 mm;
- plate must have real through-holes, not open bottom slots;
- no long T-slot or undercut weakening the plate;
- lower hook overlaps the 16.45 mm Eurobox rim by nominally 4 mm when closed;
- at 4 mm opening the hook must clear the rim for tool-less removal.

### 5.4 Lead screw and replaceable nut cartridge

The prototype drive uses a coarse printable right-hand lead thread:

- nominal major diameter: 8.0 mm;
- pitch: 2.0 mm;
- right hand;
- two screws per holder.

The female thread is **not permanently tied to the Base geometry**. Each screw bridge receives a replaceable anti-rotation nut cartridge.

Prototype cartridge: printed Tr8x2-like thread.

Future cartridge: same outer cartridge interface but with an M4 heat-set insert or captive metal M4 nut. This lets the Base survive the transition from prototype to metal hardware.

Normal tightening logic:

- user turns knob clockwise from the outside;
- screw advances inward toward the Eurobox;
- thrust shoulder pushes the clamp plate inward;
- on loosening, an inner retaining clip pulls the plate back outward;
- the plate itself does not rotate and contains no drive thread.

### 5.5 Spindle / plate capture

The plate capture follows a standard shoulder-journal-retainer arrangement:

- smooth journal through plate;
- thrust shoulder on the outside of the plate;
- shallow annular retaining groove on the inside;
- separate printed horseshoe retaining clip in the groove.

The clip carries only the plate-retraction load. Clamp force is carried by the solid thrust shoulder.

### 5.6 Knob

Knob and spindle are separate printable parts.

- knob nominal OD: 32 mm;
- spindle torque interface: 10 mm across-flats hex;
- knob socket: 10.3 mm AF nominal;
- central clearance around the retaining stud;
- separate retaining nut holds the knob axially;
- torque is transmitted by the hex, not by the retaining thread.

The retaining thread is not used as a substitute for the main lead screw and does not reverse the lead-screw hand.

### 5.7 Anti-flop stay support

The THRON² EQP rack uses diagonal stays down toward the rear axle. A small secondary printed support may brace the Eurobox holder against one of these stays so the holder does not rotate downward while the box is being installed.

The exact stay diameter and angle are currently **unknown**. Therefore v50 deliberately uses a universal V-groove + zip-tie-slot support, not a fake form-fitting clamp. It is marked as an optional calibration part until the stay is measured.

## 6. Conservative load target

Published rack ratings conflict between 16 and 25 kg. v50 therefore uses:

- **design ceiling for the complete rack system: 16 kg** until the specific MY23 rack label is checked;
- prototype proof-load calculations/checks must not be presented as a certification;
- printed PETG parts are not allowed to redefine the bicycle manufacturer's rating.

The Eurobox is 600 mm wide, so load should be centred and kept as low as practical. The holder must not transfer load into the fender.

## 7. Printing assumptions

Target printer/material:

- Prusa CORE One L;
- 0.4 mm nozzle;
- PETG first prototype;
- 0.20 mm layer height preferred;
- 3 perimeters minimum for structural prototypes;
- support minimised by flat upper surfaces and open-bottom beam sections.

Thread clearances are prototype values and may need one calibration print for the actual PETG/printer combination.

## 8. Mandatory automated validation

A v50 build is not considered printable until CI checks at least:

1. every exported BREP/STEP is valid and a single solid where expected;
2. STEP re-import succeeds;
3. STL is watertight, winding-consistent and one connected component;
4. rigid Base vs 12.42 mm rack tube = no collision;
5. flexible lower jaw vs tube = intentional limited preload;
6. lower-jaw sweep 0, -15, -30, -45, -60, -75 degrees has no Base collision;
7. plate vs Base is collision-free at 0,1,2,3,4 mm travel;
8. both 6.4 mm plate holes are actually through-open;
9. lead-screw correct screw-motion phase is collision-free and wrong handed motion collides;
10. spindle/plate shoulder and retainer do not create unintended solid intersections;
11. fender keep-out volume remains clear below Z 34.54 mm in the fender zone;
12. overall box/rack width remains within the intended 600 mm box envelope except the accessible knobs, whose protrusion is reported explicitly.

## 9. Measurements still worth taking

These are not blockers for v50 prototype, but replacing assumptions with measurements will improve the next revision:

- exact diameter of the diagonal 3-leg rack stay;
- stay angle in Y/Z and its position relative to each rack tube;
- exact transverse fender profile, not only its top height;
- exact lower Eurobox rim wall thickness on the specific box;
- label/part number and load rating printed on the actual MY23 Massload rack.

## 10. Version rule

v50 is the first version whose source geometry is generated from documented parameters rather than inheriting opaque BREP geometry from an earlier version. Any future dimensional change must update both this document and the parameter block in `scripts/build_v50.py`.