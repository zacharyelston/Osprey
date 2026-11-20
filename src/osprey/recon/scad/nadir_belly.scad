// The belly shell with the flat for the camera's window, the pane's recess and the camera plate's bosses.
include <lib.scad>

show_plate = true;
nose_only = true;      // the shell back to the front main bulkhead; false for the whole lower shell

intersection() {
    lower_shell();
    if (nose_only) translate([-1, -2 * R, -2 * R]) cube([bulkheads[2][0] + 1, 4 * R, 4 * R]);
}
if (show_plate) color("Goldenrod") camera_plate();
