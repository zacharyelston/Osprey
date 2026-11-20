// The centre section's end rib at y = +/-800: it closes the section round the spar, where the outer panel's
// joiner goes in, and holds the MPX and XT30 connectors in the mating face. Starboard as drawn.
// The port one:  openscad -D side=-1 -o end_rib_port.stl end_rib.scad
include <lib.scad>

side = 1;

end_rib(side);
