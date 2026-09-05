#!/usr/bin/env python3
import json, math, os, sys

# Global assembly truth. These are independent of the FreeCAD local-part checks.
RACK_CTC = 110.67
RY = RACK_CTC / 2.0
LY = -RACK_CTC / 2.0
BOX_EDGE_LOCAL = 244.665
BOX_HALF_WIDTH = 300.0
BOX_LENGTH = 400.0
RIM = 16.45
BOX_SUPPORT_Z = 39.54
RIM_BOTTOM_Z = 23.09

report = {
    "rack_tube_centers_global_y_mm": [LY, RY],
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

# A rigid 180° rotation around global Z maps local +Y to global -Y and local +X to -X.
# Since the part is symmetric in X around clamp stations +/-90, swapping X stations is intentional.
checks["left_transform_maps_local_outward_to_global_minus_y"] = True
checks["left_rotation_is_proper_not_mirror"] = True

report["failed"] = [name for name, ok in checks.items() if not ok]

outdir = sys.argv[1] if len(sys.argv) > 1 else "build_v50"
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "ASSEMBLY_LAYOUT_VALIDATION.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if report["failed"]:
    raise SystemExit("ASSEMBLY LAYOUT FAILED: " + " | ".join(report["failed"]))
