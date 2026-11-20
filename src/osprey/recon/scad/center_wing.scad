// The centre wing: the section lofted over the frame, its ribs, the two flaps and the root fairing.
include <lib.scad>

show_skin = true;
show_ribs = true;
show_flaps = true;
show_fairing = true;
show_frame = true;
show_body = true;

if (show_skin) color("LightSteelBlue", 0.45) center_skin();
if (show_ribs) color("BurlyWood") ribs();
if (show_flaps) color("SteelBlue") { flap(1); flap(-1); }
if (show_fairing) color("SlateGray") root_fairing();
if (show_frame) color([0.12, 0.12, 0.12]) frame_tubes();
if (show_body) %body(0);
