// The sailplane's body and centre wing, assembled.
include <lib.scad>

show_upper_shell = true;
show_lower_shell = true;
show_structure = true;
show_frame = true;
show_lugs = true;
show_joiners = true;
show_wing = true;
show_fairing = true;

if (show_upper_shell) %upper_shell();
if (show_lower_shell) color("Khaki", 0.6) lower_shell();
if (show_structure) color("DimGray") internal_structure();
if (show_frame) color([0.12, 0.12, 0.12]) frame_tubes();
if (show_lugs) color("OrangeRed") all_lugs();
if (show_joiners) color("Orange") { joiner_box(1); joiner_box(-1); }
if (show_wing) {
    color("LightSteelBlue", 0.35) center_skin();
    color("BurlyWood") ribs();
    color("SteelBlue") { flap(1); flap(-1); }
}
if (show_fairing) color("SlateGray") root_fairing();
if (show_lower_shell) color("Goldenrod") camera_plate();
