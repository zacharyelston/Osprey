// The sailplane's shared geometry: the body, the wing and its spars, the braces and their fittings, the belly flat.
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

// ---- tubes and the spars ---------------------------------------------------------------------------------

module along(v) { l = norm(v); rotate([0, acos(v[2] / l), atan2(v[1], v[0])]) children(); }

module strut(p1, p2, d) { v = p2 - p1; translate(p1) along(v) cylinder(h = norm(v), d = d, $fn = 24); }

function flip(p, side) = [p[0], side * p[1], p[2]];
function unit(v) = v / norm(v);

// The centre section's spar: a square tube from joint to joint; the joiners slide into its ends.
module spar(grow = 0, hollow = true) translate([spar_x, 0, spar_z]) difference() {
    cube([spar_od + grow, center_span, spar_od + grow], center = true);
    if (hollow) cube([spar_od - 2 * spar_wall, center_span + 2, spar_od - 2 * spar_wall], center = true);
}

module rear_spar(grow = 0) translate([rear_x, 0, rear_z]) rotate([90, 0, 0]) cylinder(d = rear_od + grow, h = center_span, center = true, $fn = 24);

module joiner(side = 1) translate([spar_x, side * half, spar_z]) cube([joiner_size, 2 * joiner_engage, joiner_size], center = true);

// ---- the braces -------------------------------------------------------------------------------------------
// One a side, from a pin low on the body to a pin under the wing; a jury strut from mid-brace up to the wing.

function spar_z_at(y) = spar_z + (abs(y) > half ? (abs(y) - half) * tan(dihedral) : 0);
jury_top = [spar_x, strut_jury[1], spar_z_at(strut_jury[1]) - spar_od / 2 - skin_t - wing_drop];

// The brace's aerofoil fairing over its tube: chord along the flight direction.
module brace_fairing(side = 1) {
    a = flip(strut_root, side);
    b = flip(strut_wing, side);
    v = b - a;
    inset = strut_seat + fit_socket;
    translate(a) along(v) translate([0, 0, inset]) linear_extrude(norm(v) - 2 * inset)
        rotate([0, 0, side > 0 ? -90 : 90]) translate([-0.3 * strut_chord, 0]) polygon([for (p = brace_pts) [p[0] * strut_chord, side * p[1] * strut_chord]]);
}

module brace_tube(side = 1) {
    a = flip(strut_root, side);
    b = flip(strut_wing, side);
    u = unit(b - a);
    strut(a + strut_seat * u, b - strut_seat * u, strut_od);
}

// A tube's end fitting: a bonded socket and a tang with the pin's hole. Drawn with the pin at the origin,
// the tube leaving along +z and the pin along y.
module tube_end(od, seat, pin) {
    bd = od + 2 * bond_gap;
    sd = bd + 2 * fit_wall;
    difference() {
        union() {
            translate([0, 0, seat - fit_wall]) cylinder(d = sd, h = fit_socket + fit_wall, $fn = 36);
            hull() {
                translate([0, 0, seat - fit_wall]) cylinder(d = sd, h = 0.5, $fn = 36);
                rotate([90, 0, 0]) cylinder(d = 3 * pin, h = tang_t, center = true, $fn = 36);
            }
        }
        translate([0, 0, seat]) cylinder(d = bd, h = fit_socket + 1, $fn = 36);
        for (g = [1 : grooves]) translate([0, 0, seat + fit_socket * g / (grooves + 1) - groove[0] / 2]) cylinder(d = bd + 2 * groove[1], h = groove[0], $fn = 36);
        rotate([90, 0, 0]) cylinder(d = pin + 0.2, h = sd + 2, center = true, $fn = 24);
    }
}

// The same fitting where it goes: its pin at p, its tube leaving toward q.
module tube_end_at(p, q, od, seat, pin) { translate(p) along(q - p) tube_end(od, seat, pin); }

// A fork for a tang, hung under a square spar: a cradle bonded round the spar's lower half, two cheeks down
// to the pin. Drawn with the spar's centre line through the origin along y and the pin at [0, 0, -drop].
module spar_fork(drop, pin, len = 46) {
    w = spar_od + 2 * bond_gap;
    difference() {
        union() {
            translate([-w / 2 - fit_wall, -len / 2, -w / 2 - fit_wall]) cube([w + 2 * fit_wall, len, w / 2 + fit_wall]);
            for (sx = [-1, 1]) hull() {
                translate([sx * (tang_t / 2 + 0.2 + cheek_t / 2), 0, -drop]) rotate([0, 90, 0]) cylinder(d = 3 * pin, h = cheek_t, center = true, $fn = 36);
                translate([sx * (tang_t / 2 + 0.2 + cheek_t / 2) - cheek_t / 2, -len / 2, -w / 2 - fit_wall]) cube([cheek_t, len, 1]);
            }
        }
        translate([-w / 2, -len / 2 - 1, -w / 2]) cube([w, len + 2, w]);
        translate([0, 0, -drop]) rotate([0, 90, 0]) cylinder(d = pin + 0.2, h = w + 2 * fit_wall + 2, center = true, $fn = 24);
    }
}

module wing_fork(side = 1) { p = flip(strut_wing, side); translate([spar_x, p[1], spar_z_at(p[1])]) spar_fork(spar_z_at(p[1]) - p[2], pin_d); }

module jury_fork(side = 1) { p = flip(jury_top, side); translate([spar_x, p[1], spar_z_at(p[1])]) spar_fork(spar_z_at(p[1]) - p[2], jury_pin_d, 30); }

// The brace's root on the front main bulkhead: a fork outside the hull on a foot that bolts to the bulkhead.
module root_fork(side = 1) {
    p = flip(strut_root, side);
    foot = [16, 34, 34];
    inward = side * (strut_root[1] - 26);
    difference() {
        union() {
            for (sx = [-1, 1]) hull() {
                translate(p + [sx * (tang_t / 2 + 0.2 + cheek_t / 2), 0, 0]) rotate([0, 90, 0]) cylinder(d = 3 * pin_d, h = cheek_t, center = true, $fn = 36);
                translate([p[0] + sx * (tang_t / 2 + 0.2 + cheek_t / 2), inward, p[2]]) cube([cheek_t, 8, foot[2]], center = true);
            }
            translate([p[0], inward - side * 4, p[2]]) cube(foot, center = true);
        }
        translate(p) rotate([0, 90, 0]) cylinder(d = pin_d + 0.2, h = 40, center = true, $fn = 24);
        for (dz = [-10, 10]) translate([p[0], inward - side * 4, p[2] + dz]) rotate([0, 90, 0]) cylinder(d = 4.3, h = 40, center = true, $fn = 20);
    }
}

// A collar bonded on the brace's tube where the jury strut leaves it, with an ear for the jury's tang.
module jury_collar(side = 1) {
    a = flip(strut_root, side);
    b = flip(strut_wing, side);
    j = flip(strut_jury, side);
    up = unit(flip(jury_top, side) - j);
    bd = strut_od + 2 * bond_gap;
    difference() {
        union() {
            translate(j) along(b - a) cylinder(d = bd + 2 * fit_wall, h = 22, center = true, $fn = 36);
            hull() {
                translate(j) along(b - a) cylinder(d = bd + 2 * fit_wall, h = 10, center = true, $fn = 36);
                translate(j + (bd / 2 + fit_wall + 2 * jury_pin_d) * up) rotate([0, 90, 0]) cylinder(d = 3 * jury_pin_d, h = tang_t, center = true, $fn = 30);
            }
        }
        translate(j) along(b - a) cylinder(d = bd, h = 60, center = true, $fn = 36);
        translate(j + (bd / 2 + fit_wall + 2 * jury_pin_d) * up) rotate([0, 90, 0]) cylinder(d = jury_pin_d + 0.2, h = 30, center = true, $fn = 20);
    }
}

jury_pin_low = strut_jury + (strut_od / 2 + bond_gap + fit_wall + 2 * jury_pin_d) * unit(jury_top - strut_jury);

module brace_fittings(side = 1) {
    wing_fork(side);
    jury_fork(side);
    root_fork(side);
    jury_collar(side);
    tube_end_at(flip(strut_root, side), flip(strut_wing, side), strut_od, strut_seat, pin_d);
    tube_end_at(flip(strut_wing, side), flip(strut_root, side), strut_od, strut_seat, pin_d);
    tube_end_at(flip(jury_top, side), flip(jury_pin_low, side), jury_od, jury_seat, jury_pin_d);
    tube_end_at(flip(jury_pin_low, side), flip(jury_top, side), jury_od, jury_seat, jury_pin_d);
}

module brace(side = 1) {
    brace_tube(side);
    a = flip(jury_pin_low, side);
    b = flip(jury_top, side);
    strut(a + jury_seat * unit(b - a), b - jury_seat * unit(b - a), jury_od);
}

// ---- the centre section's end rib: it closes the section at the joint and carries the two connectors ------

module connector_pocket(x, body) {
    // the body's pocket, open to the mating face, and a slot behind it for the wires, smaller by the shoulder
    translate([x - body[0] / 2, half - body[2], spar_z - body[1] / 2]) cube([body[0], body[2] + 1, body[1]]);
    translate([x - body[0] / 2 + shoulder, half - 40, spar_z - body[1] / 2 + shoulder]) cube([body[0] - 2 * shoulder, 41, body[1] - 2 * shoulder]);
}

module end_rib(side = 1) {
    block_w = mpx[0] + xt30[0] + 18;
    block_d = max(mpx[2], xt30[2]) + 3;
    mirror([0, side < 0 ? 1 : 0, 0]) difference() {
        union() {
            span_extrude(half - end_rib_t, half) difference() { section2d(skin_t); aft_of(hinge_u - flap_gap / 2 - skin_t); }
            translate([connector_x - block_w / 2, half - block_d, spar_z - max(mpx[1], xt30[1]) / 2 - 4]) cube([block_w, block_d, max(mpx[1], xt30[1]) + 8]);
        }
        spar(2 * bond_gap, hollow = false);
        rear_spar(2 * bond_gap);
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

function rib_ys() = concat([for (y = rib_y) each [-y, y]], [-flap_y0, flap_y0]);

module rib(y) difference() {
    span_extrude(y - rib_t / 2, y + rib_t / 2) difference() { section2d(skin_t); aft_of(hinge_u - flap_gap / 2 - skin_t); }
    spar(2 * bond_gap, hollow = false);
    rear_spar(2 * bond_gap);
}

module ribs() { for (y = rib_ys()) rib(y); }

// An outer panel, for the look of the whole wing: tapered, its spar line straight, tilted up by the dihedral.
module outer_panel(side = 1) {
    panel = span / 2 - half;
    mirror([0, side < 0 ? 1 : 0, 0]) translate([0, half, chord_z]) rotate([dihedral, 0, 0]) translate([0, -half, -chord_z]) hull() {
        span_extrude(half, half + 1) section2d();
        translate([le_x + spar_frac * (chord - tip_chord), half + panel, chord_z]) rotate([90, 0, 0]) linear_extrude(1) scale(tip_chord / chord) section2d();
    }
}

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
        intersection() {
            offset(r = -f) offset(delta = f) union() {
                circle(r = r, $fn = 96);
                translate([-w, 0]) square([2 * w, zl + 1]);
                translate([-w - 3 * f, zl]) square([2 * w + 6 * f, 4 * f]);
            }
            translate([-w - 3 * f, 0]) square([2 * w + 6 * f, zl]);       // only the web and its fillets
        }
        circle(r = r, $fn = 96);
    }
}

module root_fairing() {
    for (x = [le_x + fair_step / 2 : fair_step : le_x + chord - fair_step / 2])
        at_station(x - fair_step / 2, fair_step) fairing_section(x);
}
