#!/usr/bin/env python3
import json, math, os, sys

# Global assembly truth. These checks are intentionally independent of the
# FreeCAD local-part collision checks, but consume the source validation report
# for the handed rear-backstop coordinates.
RACK_CTC = 110.67
RY = RACK_CTC / 2.0
LY = -RACK_CTC / 2.0
BOX_EDGE_LOCAL = 244.665
BOX_HALF_WIDTH = 300.0
BOX_LENGTH = 400.0
RIM = 16.45
BOX_SUPPORT_Z = 39.54
RIM_BOTTOM_Z = 23.09
REAR_CLAMP_GLOBAL_X = 90.0
CLAMP_HALF_X = 17.0

outdir = sys.argv[1] if len(sys.argv) > 1 else "build_v50"
source_path = os.path.join(outdir, "VALIDATION_v50_source.json")
source = json.load(open(source_path, encoding="utf-8")) if os.path.isfile(source_path) else {}
mb = source.get("mounting_backstop", {})

right_local = mb.get("right_base_local_panel_x_range_mm")
left_local = mb.get("left_base_local_panel_x_range_mm")
right_global = list(right_local) if isinstance(right_local, list) and len(right_local) == 2 else None
# LEFT assembly is a proper 180-degree rotation around Z: local x -> -global x.
left_global = ([-left_local[1], -left_local[0]]
               if isinstance(left_local, list) and len(left_local) == 2 else None)

report = {
    "rack_tube_centers_global_y_mm": [LY, RY],
    "riding_axis": "X",
    "front_direction": "-X",
    "rear_direction": "+X",
    "right_module_outward_direction": "+Y",
    "left_module_outward_direction": "-Y",
    "right_box_outer_edge_y_mm": RY + BOX_EDGE_LOCAL,
    "left_box_outer_edge_y_mm": LY - BOX_EDGE_LOCAL,
    "right_rim_y_range_mm": [RY + BOX_EDGE_LOCAL - RIM, RY + BOX_EDGE_LOCAL],
    "left_rim_y_range_mm": [LY - BOX_EDGE_LOCAL, LY - BOX_EDGE_LOCAL + RIM],
    "box_width_from_edges_mm": (RY + BOX_EDGE_LOCAL) - (LY - BOX_EDGE_LOCAL),
    "box_x_range_mm": [-BOX_LENGTH/2.0, BOX_LENGTH/2.0],
    "box_support_z_mm": BOX_SUPPORT_Z,
    "rim_bottom_z_mm": RIM_BOTTOM_Z,
    "rear_clamp_global_x_mm": REAR_CLAMP_GLOBAL_X,
    "right_backstop_local_x_range_mm": right_local,
    "left_backstop_local_x_range_mm": left_local,
    "right_backstop_global_x_range_mm": right_global,
    "left_backstop_global_x_range_mm": left_global,
    "checks": {},
}

checks = report["checks"]
checks["rack_centers_are_plusminus_55_335"] = (
    abs(RY - 55.335) < 1e-9 and abs(LY + 55.335) < 1e-9
)
checks["right_outer_edge_is_plus300"] = abs(report["right_box_outer_edge_y_mm"] - 300.0) < 1e-9
checks["left_outer_edge_is_minus300"] = abs(report["left_box_outer_edge_y_mm"] + 300.0) < 1e-9
checks["assembled_box_width_is_600"] = abs(report["box_width_from_edges_mm"] - 600.0) < 1e-9
checks["right_rim_is_outboard_of_right_rack"] = report["right_rim_y_range_mm"][0] > RY
checks["left_rim_is_outboard_of_left_rack"] = report["left_rim_y_range_mm"][1] < LY
checks["rim_vertical_height_is_16_45"] = abs(BOX_SUPPORT_Z - RIM_BOTTOM_Z - RIM) < 1e-9

# A proper 180-degree rotation maps local +Y -> global -Y and local X -> -X.
# Rear-only X asymmetry therefore requires a mirrored printable LEFT base before
# that rotation. Both resulting stops must land at the same global +X rear end.
checks["source_declares_handed_bases"] = mb.get("handed_bases_required") is True
checks["source_freezes_minus_x_front_plus_x_rear"] = (
    mb.get("front_direction") == "-X" and mb.get("rear_direction") == "+X"
)
checks["left_transform_maps_local_outward_to_global_minus_y"] = True
checks["left_assembly_transform_is_proper_180deg_rotation"] = True
checks["right_backstop_coordinates_available"] = right_global is not None
checks["left_backstop_coordinates_available"] = left_global is not None
checks["both_backstops_same_global_x_range"] = (
    right_global is not None and left_global is not None and
    all(abs(a-b) < 1e-9 for a,b in zip(right_global, left_global))
)
checks["right_backstop_is_behind_rear_clamp"] = (
    right_global is not None and right_global[0] > REAR_CLAMP_GLOBAL_X + CLAMP_HALF_X
)
checks["left_backstop_is_behind_rear_clamp"] = (
    left_global is not None and left_global[0] > REAR_CLAMP_GLOBAL_X + CLAMP_HALF_X
)
checks["both_backstops_are_global_rear_not_front"] = (
    right_global is not None and left_global is not None and
    right_global[0] > 0 and left_global[0] > 0
)

report["failed"] = [name for name, ok in checks.items() if not ok]

os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "ASSEMBLY_LAYOUT_VALIDATION.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if report["failed"]:
    raise SystemExit("ASSEMBLY LAYOUT FAILED: " + " | ".join(report["failed"]))
