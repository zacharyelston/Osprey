// The printed node lugs. As it stands: every lug laid out on a plate.
// One lug for the printer:  openscad -D lug_index=7 -o lug_07.stl lugs.scad
// lugs[i][0] is its node's name: F or R the front or rear plane, B or T bottom or top, then y.
include <lib.scad>

lug_index = -1;

if (lug_index >= 0) {
    echo(lug = lugs[lug_index][0]);
    lug(lug_index);
} else {
    for (i = [0 : len(lugs) - 1]) translate([(i % 6) * 130, floor(i / 6) * 230, 0]) lug(i);
}
