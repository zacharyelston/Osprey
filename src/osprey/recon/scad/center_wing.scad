// The centre wing: the section lofted over its two spars, the ribs, the two flaps and the root fairing.
include <lib.scad>

show_skin = true;
show_ribs = true;
show_flaps = true;
show_fairing = true;
show_spars = true;

if (show_skin) color("LightSteelBlue", 0.45) center_skin();
if (show_ribs) color("BurlyWood") { ribs(); end_rib(1); end_rib(-1); }
if (show_flaps) color("SteelBlue") { flap(1); flap(-1); }
if (show_fairing) color("SlateGray") root_fairing();
if (show_spars) color([0.12, 0.12, 0.12]) { spar(); rear_spar(); }
