// The sailplane's shared geometry: the body, the frame, the lugs, the joiner box, the wing and the belly flat.
// Definitions only; the part files beside this one draw them. Every number comes from params.scad, which
// `osprey recon-sailplane` writes from design/recon/sailplane.toml.
// mm. Origin at the nose tip; +x aft, +y starboard, +z up.

include <params.scad>

$fn = 72;
half = center_span / 2;
tail_len = L - nose_len - mid_len;
hinge_u = chord * (1 - flap_frac);            // the flap hinge line, from the leading edge

// ---- the body: a Myring body of revolution ----------------------------------------------------------------

function myring_r(x) =
    (x <= 0) ? 0 :
    (x < nose_len) ? R * pow(1 - pow((x - nose_len) / nose_len, 2), 1 / nose_exp) :
    (x <= nose_len + mid_len) ? R :
    let(dx = x - nose_len - mid_len, t = tan(tail_angle), c = tail_len)
        max(R - (3 * R / (c * c) - t / c) * dx * dx + (2 * R / (c * c * c) - t / (c * c)) * dx * dx * dx, r_spinner);

module body(inset = 0, step = 10) {
    pts = [
        for (x = [0 : step : x_max - 0.01]) [max(0, myring_r(x) - inset), x],
        [max(0, myring_r(x_max) - inset), x_max],
        [0, x_max]
    ];
    rotate([0, 90, 0]) rotate_extrude() polygon(pts);
}

// A 2-D shape drawn in (y, z) becomes a slab from x on aft.
module at_station(x, t) { translate([x, 0, 0]) rotate([90, 0, 90]) linear_extrude(t) children(); }

// ---- the belly flat: the body cut by one plane ------------------------------------------------------------

// In here x runs aft along the flat from its forward reference, y is across, z is the flat's inward normal.
module flat_frame() { translate([nadir_xa, 0, nadir_za]) rotate([0, nadir_tilt, 0]) children(); }

module above_flat(lift = 0) { flat_frame() translate([-2 * L, -2 * R, lift]) cube([4 * L, 4 * R, 4 * R]); }

module hull_solid() { intersection() { body(0); above_flat(0); } }

module hull_cavity() { intersection() { translate([shell_t, 0, 0]) body(shell_t); above_flat(nadir_floor); } }

pane_u = nadir_margin;                                   // where the pane starts along the flat
mount_c = [pane_u + nadir_pane / 2, 0];                  // the window's centre on the flat

module nadir_cuts() flat_frame() {
    // the recess the pane sits in, flush with the outside
    translate([pane_u, -nadir_pane / 2, -0.01]) cube([nadir_pane, nadir_pane, nadir_pane_t + 0.01]);
    // the clear opening
    translate([mount_c[0] - nadir_window / 2, -nadir_window / 2, -1]) cube([nadir_window, nadir_window, nadir_floor + 2]);
    // the camera plate's bosses, tapped
    for (sx = [-1, 1], sy = [-1, 1])
        translate([mount_c[0] + sx * nadir_mount[0] / 2, sy * nadir_mount[1] / 2, nadir_pane_t + 1])
            cylinder(d = nadir_m3, h = nadir_floor + nadir_boss[1], $fn = 16);
}

module nadir_bosses() intersection() {
    flat_frame() for (sx = [-1, 1], sy = [-1, 1])
        translate([mount_c[0] + sx * nadir_mount[0] / 2, sy * nadir_mount[1] / 2, 0])
            cylinder(d = nadir_boss[0], h = nadir_floor + nadir_boss[1], $fn = 24);
    hull_solid();
}

// The interchangeable camera plate: it bolts to the four bosses, the camera to it.
module camera_plate(t = 3, lens = 40) flat_frame() translate([mount_c[0], 0, nadir_floor + nadir_boss[1]]) difference() {
    translate([-nadir_mount[0] / 2 - 7, -nadir_mount[1] / 2 - 7, 0]) cube([nadir_mount[0] + 14, nadir_mount[1] + 14, t]);
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * nadir_mount[0] / 2, sy * nadir_mount[1] / 2, -1]) cylinder(d = 3.2, h = t + 2, $fn = 16);
    translate([0, 0, -1]) cylinder(d = lens, h = t + 2);
}

module lower_shell() difference() {
    union() {
        difference() {
            intersection() { hull_solid(); translate([-1, -2 * R, -2 * R]) cube([L + 2, 4 * R, 2 * R]); }
            hull_cavity();
        }
        nadir_bosses();
    }
    nadir_cuts();
}

module upper_shell() difference() {
    intersection() { hull_solid(); translate([-1, -2 * R, 0]) cube([L + 2, 4 * R, 2 * R]); }
    hull_cavity();
    translate([hatch_x[0], -hatch_half_w, hatch_z]) cube([hatch_x[1] - hatch_x[0], 2 * hatch_half_w, 2 * R]);
}

// ---- bulkheads and rails ----------------------------------------------------------------------------------

module ring_bulkhead(x, t, web, relief = 22) {
    r_out = myring_r(x) - shell_t;
    r_in = max(10, r_out - web);
    intersection() {
        at_station(x - t / 2, t) difference() {
            circle(r = r_out);
            circle(r = r_in);
            translate([-r_out, -r_out]) square([2 * r_out, relief]);      // open at the bottom, for the cables and the camera
        }
        above_flat(nadir_floor);
    }
}

module internal_structure() {
    for (b = bulkheads) ring_bulkhead(b[0], b[1], b[2]);
    for (sy = [-1, 1]) translate([rail_x[0], sy * rail_y - rail_s / 2, rail_z]) cube([rail_x[1] - rail_x[0], rail_s, rail_s]);
}

// ---- the frame --------------------------------------------------------------------------------------------

module along(v) { l = norm(v); rotate([0, acos(v[2] / l), atan2(v[1], v[0])]) children(); }

module strut(p1, p2, d) { v = p2 - p1; translate(p1) along(v) cylinder(h = norm(v), d = d, $fn = 24); }

module frame_tubes(grow = 0, only_struts = false) {
    for (m = members) if (!only_struts || m[2] < od_chord) strut(m[0], m[1], m[2] + grow);
}

// ---- the node lugs ----------------------------------------------------------------------------------------
// An arm is [direction, tube OD, seat, kind]: kind 0 a socket whose tube stops `seat` short of the node,
// 1 a chord passing through, 2 a chord ending in a capped socket.

function arm_z0(a) = (a[3] == 1) ? -socket : (a[3] == 2) ? -a[2] : a[2];
function arm_len(a) = (a[3] == 1) ? 2 * socket : (a[3] == 2) ? a[2] + socket : socket;

module lug_arm_solid(a) {
    od = a[1] + 2 * bond_gap + 2 * lug_wall;
    along(a[0]) {
        if (a[3] == 0) cylinder(d = od, h = a[2] + socket, $fn = 36);
        else translate([0, 0, arm_z0(a) - (a[3] == 2 ? lug_wall : 0)]) cylinder(d = od, h = arm_len(a) + (a[3] == 2 ? lug_wall : 0), $fn = 36);
    }
}

module lug_arm_bore(a) {
    bd = a[1] + 2 * bond_gap;
    od = bd + 2 * lug_wall;
    z0 = arm_z0(a);
    ln = arm_len(a);
    along(a[0]) {
        translate([0, 0, z0 - (a[3] == 1 ? 1 : 0)]) cylinder(d = bd, h = ln + 2, $fn = 36);
        // adhesive relief grooves
        for (g = [1 : grooves]) translate([0, 0, z0 + ln * g / (grooves + 1) - groove[0] / 2]) cylinder(d = bd + 2 * groove[1], h = groove[0], $fn = 36);
        // a port to inject the epoxy through
        translate([0, 0, z0 + ln / 2]) rotate([0, 90, 0]) cylinder(d = port_d, h = od, $fn = 12);
    }
}

module lug(i) {
    arms = lugs[i][2];
    difference() {
        union() {
            for (a = arms) lug_arm_solid(a);
            sphere(d = od_chord + 2 * bond_gap + 2 * lug_wall, $fn = 36);
        }
        for (a = arms) lug_arm_bore(a);
    }
}

module all_lugs() { for (i = [0 : len(lugs) - 1]) translate(lugs[i][1]) lug(i); }

// ---- the joiner box: an outer panel's receptacle ----------------------------------------------------------
// Two plates thread onto the four chords and carry the joiner's couple into them; a square sleeve between
// them takes the joiner, tilted to the dihedral; a block on the outer plate holds the two connectors.

joiner_so = joiner_size + 2 * joiner_gap + 2 * joiner_wall;
joiner_yc = half - joiner_engage / 2;
slot_d = od_strut + 2 * bond_gap + 2 * lug_wall + 1;     // room for a strut in its lug's arm

module joiner_plate(y) {
    x0 = truss_x[0] - joiner_margin;
    z0 = truss_z[0] - joiner_margin;
    translate([x0, y - joiner_plate_t / 2, z0])
        cube([truss_x[1] - truss_x[0] + 2 * joiner_margin, joiner_plate_t, truss_z[1] - truss_z[0] + 2 * joiner_margin]);
}

module joiner_tilt(side) { translate([joiner_x, side * joiner_yc, joiner_z]) rotate([side * dihedral, 0, 0]) children(); }

module connector_pocket(x, body) {
    // the body's pocket, open to the mating face, and a slot behind it for the wires, smaller by the shoulder
    translate([x - body[0] / 2, half - body[2], joiner_z - body[1] / 2]) cube([body[0], body[2] + 1, body[1]]);
    translate([x - body[0] / 2 + shoulder, half - 60, joiner_z - body[1] / 2 + shoulder]) cube([body[0] - 2 * shoulder, 61, body[1] - 2 * shoulder]);
}

module joiner_box(side = 1) {
    yo = joiner_plate_y[0];
    yi = joiner_plate_y[1];
    block_w = mpx[0] + xt30[0] + 18;
    mirror([0, side < 0 ? 1 : 0, 0]) difference() {
        intersection() {
            union() {
                joiner_plate(yo);
                joiner_plate(yi);
                joiner_tilt(1) cube([joiner_so, joiner_engage + 10, joiner_so], center = true);
                translate([connector_x - block_w / 2, yo, joiner_z - max(mpx[1], xt30[1]) / 2 - 4])
                    cube([block_w, half - yo, max(mpx[1], xt30[1]) + 8]);
            }
            translate([0, yi - joiner_plate_t / 2, 0]) cube([L, half - yi + joiner_plate_t / 2, 2 * R]);     // flush at the mouth
        }
        // the joiner's socket, closed at its inboard end
        joiner_tilt(1) translate([0, joiner_wall + 10, 0]) cube([joiner_size + 2 * joiner_gap, joiner_engage + 10, joiner_size + 2 * joiner_gap], center = true);
        // the chords, bonded; every other tube and its lug arm passes through a slot
        for (x = truss_x, z = truss_z) translate([x, half - joiner_engage, z]) rotate([90, 0, 0]) cylinder(d = od_chord + 2 * bond_gap, h = 4 * joiner_engage, center = true, $fn = 36);
        frame_tubes(slot_d - od_strut, only_struts = true);
        connector_pocket(connector_x - block_w / 2 + 5 + mpx[0] / 2, mpx);
        connector_pocket(connector_x + block_w / 2 - 5 - xt30[0] / 2, xt30);
    }
}

// ---- the centre wing: skin, ribs, flaps and the root fairing ----------------------------------------------

module section2d(inset = 0) { offset(delta = -inset) polygon([for (p = airfoil_pts) [p[0] * chord, p[1] * chord]]); }

module aft_of(u) { translate([u, -chord]) square([2 * chord, 2 * chord]); }

// A 2-D section drawn in (chordwise, up) becomes the wing between span stations y0 and y1.
module span_extrude(y0, y1) { translate([le_x, y1, chord_z]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children(); }

module skin2d() difference() {                        // the skin ahead of the hinge line, closed by a wall there
    difference() { section2d(); aft_of(hinge_u - flap_gap / 2); }
    difference() { section2d(skin_t); aft_of(hinge_u - flap_gap / 2 - skin_t); }
}

module flap2d() intersection() { section2d(); aft_of(hinge_u + flap_gap / 2); }

function flap_y1() = half - flap_end_gap;
function hinge_ys() = [for (k = [0 : hinges_per_flap - 1]) flap_y0 + (k + 0.5) / hinges_per_flap * (flap_y1() - flap_y0)];

module hinge_pockets() {                              // in the lower surface, across the hinge line, both sides
    for (side = [-1, 1], y = hinge_ys())
        translate([le_x + hinge_u - hinge_pocket[1] / 2, side * y - hinge_pocket[0] / 2, hinge_z - 1])
            cube([hinge_pocket[1], hinge_pocket[0], hinge_pocket[2] + 1]);
}

module center_skin() difference() {
    union() {
        span_extrude(-half, half) skin2d();
        // over the body the trailing edge is fixed: a flap there would swing into the crown
        span_extrude(-flap_y0 + flap_end_gap, flap_y0 - flap_end_gap) intersection() { section2d(); aft_of(hinge_u - flap_gap / 2 - 0.01); }
    }
    hinge_pockets();
}

module flap(side = 1) difference() {
    mirror([0, side < 0 ? 1 : 0, 0]) span_extrude(flap_y0, flap_y1()) flap2d();
    hinge_pockets();
}

function rib_ys() = concat([for (i = [0 : len(station_y) - 2]) (station_y[i] + station_y[i + 1]) / 2], [-flap_y0, flap_y0]);

module rib(y) difference() {
    span_extrude(y - rib_t / 2, y + rib_t / 2) difference() { section2d(skin_t); aft_of(hinge_u - flap_gap / 2 - skin_t); }
    frame_tubes(1);
}

module ribs() { for (y = rib_ys()) rib(y); }

// The root fairing, lofted in slices: at each station the body's circle, a web up to the wing's underside
// and the wing itself are joined and their inside corners filled to the fillet radius.
function wing_lower_z(x) = chord_z + chord * lookup((x - le_x) / chord, lower_tab);
function fair_w(x) = let(u = 2 * (x - le_x) / chord - 1) fair_half_w * sqrt(max(0, 1 - pow(abs(u), 6)));

module fairing_section(x) {
    r = myring_r(x);
    w = fair_w(x);
    f = min(fair_fillet, w / 2);
    zl = wing_lower_z(x);
    if (w > 2) difference() {
        offset(r = -f) offset(delta = f) union() {
            circle(r = r, $fn = 96);
            translate([-w, 0]) square([2 * w, zl + 1]);
            translate([-w - 3 * f, zl]) square([2 * w + 6 * f, 4 * f]);
        }
        circle(r = r - 0.01, $fn = 96);
        translate([-2 * R, zl]) square([4 * R, 4 * R]);
    }
}

module root_fairing() {
    for (x = [le_x + fair_step / 2 : fair_step : le_x + chord - fair_step / 2])
        at_station(x - fair_step / 2, fair_step) fairing_section(x);
}
