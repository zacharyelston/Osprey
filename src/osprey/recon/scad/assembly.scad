// The sailplane: the body, the whole truss-braced wing and its braces.
include <lib.scad>

show_upper_shell = true;
show_lower_shell = true;
show_structure = false;
show_wing = true;
show_panels = true;
show_braces = true;
show_fairing = true;
see_inside = false;      // the wing's skin clear, the brace fairings off

if (show_upper_shell) color("WhiteSmoke") upper_shell();
if (show_lower_shell) color("Gainsboro") lower_shell();
if (show_structure) color("DimGray") internal_structure();
if (show_wing) {
    color("WhiteSmoke", see_inside ? 0.3 : 1) center_skin();
    color("SteelBlue") { flap(1); flap(-1); }
    if (see_inside) {
        color("BurlyWood") { ribs(); end_rib(1); end_rib(-1); }
        color([0.12, 0.12, 0.12]) { spar(); rear_spar(); joiner(1); joiner(-1); }
    }
}
if (show_panels) color("WhiteSmoke", see_inside ? 0.3 : 1) { outer_panel(1); outer_panel(-1); }
if (show_braces) for (side = [-1, 1]) {
    color("OrangeRed") brace_fittings(side);
    color([0.12, 0.12, 0.12]) brace(side);
    if (!see_inside) color("Silver") brace_fairing(side);
}
if (show_fairing) color("SlateGray") root_fairing();
if (show_lower_shell) color("Goldenrod") camera_plate();
