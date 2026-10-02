# Eurobox carrier v110

V110 is a service-workaround release based on V100.

The existing V100 design is promoted unchanged, and one additional part is added:

- eurobox_v110_rack_nut_retainer_left_hand

This additional retainer is the exact X-mirror of the normal V100/V110 rack-nut retainer. Mirroring reverses the thread chirality while keeping the Z thread axis and insertion direction unchanged.

Use:
- current RIGHT base -> standard eurobox_v110_rack_nut_retainer
- current LEFT mirrored base -> eurobox_v110_rack_nut_retainer_left_hand

The left-hand service retainer tightens in the opposite rotational direction to the standard retainer.

This avoids reprinting the already-finished mirrored LEFT base. It is a compatibility workaround for the currently released mirrored female thread, not a reason to use opposite-handed threads in future base revisions.

All STL files are canonical binary STL. ASCII STL is rejected by the build/publish gate.
