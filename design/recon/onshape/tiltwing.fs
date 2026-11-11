FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

// Osprey Recon's loiter tilt-wing as one Onshape feature: two high wings, each turning on its shaft at
// `pivot` of the chord by `tilt` (0 in cruise, 90 to hover, 55 afloat). The front wing's halves start at
// the hull's sides just over its beam; the rear sits `stagger` behind and `gap` above on a pylon over the
// tail, which is the fin too, its shaft through the pylon's head. A two-bladed prop a side on each wing at
// `propStation` of the span; each nacelle is one streamlined body, spinner and motor ahead of the wing,
// full through it, then tapering behind the trailing edge as a float: afloat, the front two dip in as
// outriggers. The hull is a teardrop point down, a round top over a V keel `keel` x the half-beam deep,
// and floats on it; the gimbal sits in a nose turret over the waterline.
// Defaults are the 4 h design from `osprey recon-loiter` (design/recon/airframes/tiltwing.toml).
// Frame: x aft from the front wing's leading edge, y to port, z up; metres.

const SPAN = { (meter) : [0.2, 2.961, 10] } as LengthBoundSpec;
const SPAN_R = { (meter) : [0.2, 3.467, 10] } as LengthBoundSpec;
const CHORD_FR = { (meter) : [0.02, 0.193, 2] } as LengthBoundSpec;
const CHORD_FT = { (meter) : [0.02, 0.193, 2] } as LengthBoundSpec;
const CHORD_RR = { (meter) : [0.02, 0.250, 2] } as LengthBoundSpec;
const CHORD_RT = { (meter) : [0.02, 0.193, 2] } as LengthBoundSpec;
const STAGGER = { (meter) : [0.1, 1.2, 10] } as LengthBoundSpec;
const GAP = { (meter) : [0.0, 0.30, 2] } as LengthBoundSpec;
const PROP = { (meter) : [0.05, 0.5, 3] } as LengthBoundSpec;
const FLOAT_D = { (meter) : [0.01, 0.068, 1] } as LengthBoundSpec;
const FLOAT_L = { (meter) : [0.05, 0.409, 3] } as LengthBoundSpec;
const POD_L = { (meter) : [0.2, 1.85, 5] } as LengthBoundSpec;
const POD_D = { (meter) : [0.02, 0.22, 1] } as LengthBoundSpec;
const POD_NOSE = { (meter) : [0, 0.30, 2] } as LengthBoundSpec;
const POD_Z = { (meter) : [-0.5, -0.03, 0.5] } as LengthBoundSpec;
const KEEL = { (unitless) : [0.5, 1.5, 3] } as RealBoundSpec;
const TC = { (unitless) : [0.04, 0.12, 0.3] } as RealBoundSpec;
const FRAC_PIVOT = { (unitless) : [0, 0.25, 1] } as RealBoundSpec;
const FRAC_PROP = { (unitless) : [0.05, 0.26, 0.5] } as RealBoundSpec;
const TILT = { (degree) : [0, 0, 90] } as AngleBoundSpec;

annotation { "Feature Type Name" : "Osprey loiter tilt-wing" }
export const ospreyTiltWing = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Wing tilt" }
        isAngle(definition.tilt, TILT);
        annotation { "Name" : "Front span" }
        isLength(definition.frontSpan, SPAN);
        annotation { "Name" : "Front root chord" }
        isLength(definition.frontRoot, CHORD_FR);
        annotation { "Name" : "Front tip chord" }
        isLength(definition.frontTip, CHORD_FT);
        annotation { "Name" : "Rear span" }
        isLength(definition.rearSpan, SPAN_R);
        annotation { "Name" : "Rear root chord" }
        isLength(definition.rearRoot, CHORD_RR);
        annotation { "Name" : "Rear tip chord" }
        isLength(definition.rearTip, CHORD_RT);
        annotation { "Name" : "Stagger" }
        isLength(definition.stagger, STAGGER);
        annotation { "Name" : "Gap" }
        isLength(definition.gap, GAP);
        annotation { "Name" : "Thickness / chord" }
        isReal(definition.tc, TC);
        annotation { "Name" : "Pivot, of the chord" }
        isReal(definition.pivot, FRAC_PIVOT);
        annotation { "Name" : "Prop diameter" }
        isLength(definition.prop, PROP);
        annotation { "Name" : "Prop station, of the span" }
        isReal(definition.propStation, FRAC_PROP);
        annotation { "Name" : "Float diameter" }
        isLength(definition.floatD, FLOAT_D);
        annotation { "Name" : "Float length behind the wing" }
        isLength(definition.floatL, FLOAT_L);
        annotation { "Name" : "Hull length" }
        isLength(definition.podL, POD_L);
        annotation { "Name" : "Hull beam" }
        isLength(definition.podD, POD_D);
        annotation { "Name" : "Hull nose ahead of the front wing" }
        isLength(definition.podNose, POD_NOSE);
        annotation { "Name" : "Hull beam above the front wing" }
        isLength(definition.podZ, POD_Z);
        annotation { "Name" : "Keel depth, of the half-beam" }
        isReal(definition.keel, KEEL);
    }
    {
        const foil = airfoil(0.02, 0.4, definition.tc, 24);
        const headR = 0.035 * meter;                                // the rear shaft's housing on the pylon
        const wings = [
                { "name" : "front", "x" : 0 * meter, "z" : 0 * meter, "span" : definition.frontSpan,
                  "root" : definition.frontRoot, "tip" : definition.frontTip, "y0" : definition.podD / 2 + 0.01 * meter },
                { "name" : "rear", "x" : definition.stagger, "z" : definition.gap, "span" : definition.rearSpan,
                  "root" : definition.rearRoot, "tip" : definition.rearTip, "y0" : headR + 0.01 * meter }];
        for (var w in wings)
        {
            const wid = id + w.name;
            const half = w.span / 2;
            const y0 = w.y0;                                        // the hull's side, or the pylon head's
            const c0 = w.root + (w.tip - w.root) * y0 / half;
            for (var side in [1, -1])
            {
                const sid = wid + (side > 0 ? "L" : "R");
                section(context, sid + "root", side * y0, w.x + (w.root - c0) * definition.pivot, c0, w.z, foil);
                section(context, sid + "tip", side * half, w.x + (w.root - w.tip) * definition.pivot, w.tip, w.z, foil);
                opLoft(context, sid + "loft", {
                            "profileSubqueries" : [qSketchRegion(sid + "root"), qSketchRegion(sid + "tip")],
                            "bodyType" : ToolBodyType.SOLID });
                opDeleteBodies(context, sid + "sketches", { "entities" : qUnion([qCreatedBy(sid + "root", EntityType.BODY),
                                    qCreatedBy(sid + "tip", EntityType.BODY)]) });
                // The nacelle: one body from the spinner to the float's tail, full through the wing.
                const yp = side * definition.propStation * w.span;
                const cp = w.root + (w.tip - w.root) * abs(yp) / half;
                const xle = w.x + (w.root - cp) * definition.pivot;
                const r = max(definition.floatD / 2, 0.6 * definition.tc * cp);
                const xn = xle - 0.16 * meter;
                const xt = xle + cp + definition.floatL;
                streamlined(context, sid + "nacelle", xn, xt, yp, w.z, r, 0.12, (0.16 * meter + cp) / (xt - xn));
                // A two-bladed prop just behind the spinner's tip.
                const hub = vector(xn + 0.03 * meter, yp, w.z);
                for (var k in [0, 1])
                {
                    const a = (0.6 + k * PI) * radian;
                    fCylinder(context, sid + ("blade" ~ k), {
                                "topCenter" : hub + vector(0 * meter, cos(a) * definition.prop / 2, sin(a) * definition.prop / 2),
                                "bottomCenter" : hub, "radius" : 0.012 * meter });
                }
            }
            // The tilt shaft, through the hull or the pylon's head, and the wing turned about it.
            const xp = w.x + definition.pivot * w.root;
            fCylinder(context, wid + "shaft", {
                        "topCenter" : vector(xp, y0 + 0.01 * meter, w.z),
                        "bottomCenter" : vector(xp, -y0 - 0.01 * meter, w.z),
                        "radius" : 0.012 * meter });
            if (w.name == "rear")
            {
                streamlined(context, wid + "head", xp - 0.10 * meter, xp + 0.22 * meter, 0 * meter, w.z, headR, 0.3, 0.5);
                // The pylon: a symmetric 15 % section, its chord 0.9 of the rear root's, from inside the hull up into the head.
                const cy = 0.9 * w.root;
                const sym = airfoil(0, 0.4, 0.15, 16);
                for (var lvl in [["lo", definition.podZ], ["hi", w.z]])
                {
                    const sk = newSketchOnPlane(context, wid + ("pylon" ~ lvl[0]), {
                                "sketchPlane" : plane(vector(0 * meter, 0 * meter, lvl[1]), vector(0, 0, 1), vector(1, 0, 0)) });
                    for (var side in ["upper", "lower"])
                    {
                        var pts = [];
                        for (var q in sym[side])
                            pts = append(pts, vector(xp - 0.3 * cy + q[0] * cy, q[1] * cy));
                        skFitSpline(sk, side, { "points" : pts });
                    }
                    skSolve(sk);
                }
                opLoft(context, wid + "pylon", {
                            "profileSubqueries" : [qSketchRegion(wid + "pylonlo"), qSketchRegion(wid + "pylonhi")],
                            "bodyType" : ToolBodyType.SOLID });
                opDeleteBodies(context, wid + "pylonsketches", { "entities" : qUnion([qCreatedBy(wid + "pylonlo", EntityType.BODY),
                                    qCreatedBy(wid + "pylonhi", EntityType.BODY)]) });
            }
            if (definition.tilt > 0.01 * degree)
            {
                opTransform(context, wid + "tilt", {
                            "bodies" : qUnion([qCreatedBy(wid + "L", EntityType.BODY), qCreatedBy(wid + "R", EntityType.BODY)]),
                            "transform" : rotationAround(line(vector(xp, 0 * meter, w.z), vector(0, 1, 0)), definition.tilt) });
            }
        }
        // The hull, full past the front shaft, a V keel under a round top; the gimbal in its nose turret.
        hull(context, id + "hull", -definition.podNose, definition.podL - definition.podNose, definition.podZ,
            definition.podD / 2, definition.keel, 0.15, 0.70);
        opSphere(context, id + "gimbal", {                       // fSphere wants a vertex query; opSphere a vector
                    "center" : vector(-definition.podNose + 0.0495 * meter, 0 * meter, definition.podZ + 0.45 * definition.podD / 2),
                    "radius" : 0.045 * meter });
    }, {
        "tilt" : 0 * degree, "frontSpan" : 2.961 * meter, "frontRoot" : 0.193 * meter, "frontTip" : 0.193 * meter,
        "rearSpan" : 3.467 * meter, "rearRoot" : 0.250 * meter, "rearTip" : 0.193 * meter, "stagger" : 1.2 * meter,
        "gap" : 0.30 * meter, "tc" : 0.12, "pivot" : 0.25, "prop" : 0.5 * meter, "propStation" : 0.26,
        "floatD" : 0.068 * meter, "floatL" : 0.409 * meter, "podL" : 1.85 * meter, "podD" : 0.22 * meter,
        "podNose" : 0.30 * meter, "podZ" : -0.03 * meter, "keel" : 1.5 });

/** A NACA 4-digit section, (u, z) in chord units: the upper surface from the trailing edge to the leading edge,
 * and the lower from the leading edge back, sharing both end points (a sharp trailing edge on the camber line). */
function airfoil(m is number, pos is number, t is number, n is number) returns map
{
    var up = [];
    var lo = [];
    for (var i = 0; i <= n; i += 1)
    {
        const x = (1 - cos(PI * i / n * radian)) / 2;
        const yt = 5 * t * (0.2969 * sqrt(x) - 0.1260 * x - 0.3516 * x ^ 2 + 0.2843 * x ^ 3 - 0.1036 * x ^ 4);
        var yc = 0;
        var dy = 0;
        if (x < pos)
        {
            yc = m / pos ^ 2 * (2 * pos * x - x ^ 2);
            dy = 2 * m / pos ^ 2 * (pos - x);
        }
        else
        {
            yc = m / (1 - pos) ^ 2 * (1 - 2 * pos + 2 * pos * x - x ^ 2);
            dy = 2 * m / (1 - pos) ^ 2 * (pos - x);
        }
        const th = atan(dy);
        if (i == 0 || i == n)
        {
            up = append(up, [x, yc]);                 // the leading and trailing edges: on the camber line
            lo = append(lo, [x, yc]);
        }
        else
        {
            up = append(up, [x - yt * sin(th), yc + yt * cos(th)]);
            lo = append(lo, [x + yt * sin(th), yc - yt * cos(th)]);
        }
    }
    return { "upper" : reverse(up), "lower" : lo };
}

/** A closed section sketch in the plane y = const: sketch coordinates are (x aft, z up). Two splines, upper and
 * lower, meeting at the leading and trailing edges: one closed spline made a cusp at the trailing edge the loft
 * couldn't follow. */
function section(context is Context, id is Id, y is ValueWithUnits, le is ValueWithUnits, c is ValueWithUnits,
    z is ValueWithUnits, foil is map)
{
    const sk = newSketchOnPlane(context, id, {
                "sketchPlane" : plane(vector(0 * meter, y, 0 * meter), vector(0, -1, 0), vector(1, 0, 0)) });
    for (var side in ["upper", "lower"])
    {
        var pts = [];
        for (var p in foil[side])
            pts = append(pts, vector(le + p[0] * c, z + p[1] * c));
        skFitSpline(sk, side, { "points" : pts });
    }
    skSolve(sk);
}

/** A streamlined body of revolution along x, from x0 back to x1, at (y, z): a round nose over the first `nose` of
 * its length, the full radius r to `full`, then tapering to a point. */
function streamlined(context is Context, id is Id, x0 is ValueWithUnits, x1 is ValueWithUnits, y is ValueWithUnits,
    z is ValueWithUnits, r is ValueWithUnits, nose is number, full is number)
{
    const sk = newSketchOnPlane(context, id + "sketch", {
                "sketchPlane" : plane(vector(0 * meter, y, 0 * meter), vector(0, -1, 0), vector(1, 0, 0)) });
    var pts = [];
    const n = 20;
    for (var i = 0; i <= n; i += 1)
    {
        const s = i / n;
        var k = 1;
        if (s < nose)
            k = sqrt(max(1 - ((nose - s) / nose) ^ 2, 0));
        else if (s > full)
            k = max(1 - ((s - full) / (1 - full)) ^ 2, 0) ^ 0.8;
        pts = append(pts, vector(x0 + s * (x1 - x0), z + max(k, 0.03) * r));
    }
    pts[0] = vector(x0, z);
    pts[n] = vector(x1, z);
    skFitSpline(sk, "profile", { "points" : pts });
    skLineSegment(sk, "axis", { "start" : vector(x0, z), "end" : vector(x1, z) });
    skSolve(sk);
    opRevolve(context, id, {
                "entities" : qSketchRegion(id + "sketch"),
                "axis" : line(vector(x0, y, z), vector(1, 0, 0)),
                "angleForward" : 360 * degree });
    opDeleteBodies(context, id + "clean", { "entities" : qCreatedBy(id + "sketch", EntityType.BODY) });
}

/** The hull from x0 back to x1, its sections a teardrop point down: a round top of radius r over the beam at height z,
 * the sides falling straight from the beam and closing to a V keel keel x r below it. Side on, a round nose over the
 * first `nose` of its length, full to `full`, then tapering. Each section is two splines, port and starboard, meeting
 * at the crown and the keel; the hull is lofted through them. */
function hull(context is Context, id is Id, x0 is ValueWithUnits, x1 is ValueWithUnits, z is ValueWithUnits,
    r is ValueWithUnits, keel is number, nose is number, full is number)
{
    const stations = [0.02, 0.05, 0.1, 0.15, 0.4, 0.7, 0.8, 0.9, 0.97];
    var regions = [];
    var sketches = [];
    for (var i = 0; i < size(stations); i += 1)
    {
        const s = stations[i];
        var k = 1;
        if (s < nose)
            k = sqrt(max(1 - ((nose - s) / nose) ^ 2, 0));
        else if (s > full)
            k = max(1 - ((s - full) / (1 - full)) ^ 2, 0) ^ 0.8;
        k = max(k, 0.03);
        const sid = id + ("s" ~ i);
        const sk = newSketchOnPlane(context, sid, {
                    "sketchPlane" : plane(vector(x0 + s * (x1 - x0), 0 * meter, 0 * meter), vector(1, 0, 0), vector(0, 1, 0)) });
        for (var side in [1, -1])
        {
            var pts = [];
            const n = 12;
            for (var j = 0; j <= n; j += 1)
            {
                const a = (-90 + 180 * j / n) * degree;            // keel to crown, round the side
                if (a < 0 * degree)
                    pts = append(pts, vector(side * k * r * cos(a) ^ 2, z + k * r * keel * sin(a)));
                else
                    pts = append(pts, vector(side * k * r * cos(a), z + k * r * sin(a)));
            }
            pts[0] = vector(0 * meter, z - k * r * keel);
            pts[n] = vector(0 * meter, z + k * r);
            skFitSpline(sk, side > 0 ? "port" : "stbd", { "points" : pts });
        }
        skSolve(sk);
        regions = append(regions, qSketchRegion(sid));
        sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
    }
    opLoft(context, id + "loft", { "profileSubqueries" : regions, "bodyType" : ToolBodyType.SOLID });
    opDeleteBodies(context, id + "sketches", { "entities" : qUnion(sketches) });
}
