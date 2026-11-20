// The braces' fittings, starboard, where they go: the fork under the wing, the root fork on the front main
// bulkhead, the jury strut's fork and collar, and the four tube ends.
// One part for the printer:  openscad -D part=\"tube_end\" -o tube_end.stl brace_fittings.scad
// parts: all, tube_end, jury_end, wing_fork, jury_fork, root_fork, jury_collar
include <lib.scad>

part = "all";
show_tubes = true;

if (part == "tube_end") tube_end(strut_od, strut_seat, pin_d);
else if (part == "jury_end") tube_end(jury_od, jury_seat, jury_pin_d);
else if (part == "wing_fork") spar_fork(spar_z_at(strut_wing[1]) - strut_wing[2], pin_d);
else if (part == "jury_fork") spar_fork(spar_z_at(jury_top[1]) - jury_top[2], jury_pin_d, 30);
else if (part == "root_fork") root_fork(1);
else if (part == "jury_collar") jury_collar(1);
else {
    brace_fittings(1);
    if (show_tubes) %union() { brace(1); spar(); }
}
