// An outer panel's receptacle, at y = +/-800: the starboard one, where the frame puts it.
// The port one:  openscad -D side=-1 -o joiner_box_port.stl joiner_box.scad
include <lib.scad>

side = 1;
show_frame = true;

joiner_box(side);
if (show_frame) %union() { frame_tubes(); all_lugs(); }
