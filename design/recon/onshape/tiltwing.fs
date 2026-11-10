FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

// Osprey Recon's loiter tilt-wing as one Onshape feature: two wings, the rear `stagger` behind the front
// and `gap` above it, each turning about its shaft at `pivot` of the chord by `tilt` (0 in cruise, 90 to
// hover or stand in the water); a prop a side on each at `propStation` of the span; each nacelle runs
// inline from the prop through the wing and on behind the trailing edge as a float. The rear floats are
// longer by the gap, so standing, all four reach the same water. Defaults are the 4 h design from
// `osprey recon-loiter` (design/recon/airframes/tiltwing.toml). Frame: x aft from the front wing's
// leading edge, y to port, z up; metres.

const SPAN = { (meter) : [0.2, 3.184, 10] } as LengthBoundSpec;
const SPAN_R = { (meter) : [0.2, 2.957, 10] } as LengthBoundSpec;
const CHORD_FR = { (meter) : [0.02, 0.195, 2] } as LengthBoundSpec;
const CHORD_FT = { (meter) : [0.02, 0.195, 2] } as LengthBoundSpec;
const CHORD_RR = { (meter) : [0.02, 0.243, 2] } as LengthBoundSpec;
const CHORD_RT = { (meter) : [0.02, 0.195, 2] } as LengthBoundSpec;
const STAGGER = { (meter) : [0.1, 1.2, 10] } as LengthBoundSpec;
const GAP = { (meter) : [0.0, 0.15, 2] } as LengthBoundSpec;
const PROP = { (meter) : [0.05, 0.5, 3] } as LengthBoundSpec;
const FLOAT_D = { (meter) : [0.01, 0.094, 1] } as LengthBoundSpec;
const FLOAT_L = { (meter) : [0.05, 0.661, 3] } as LengthBoundSpec;
const POD_L = { (meter) : [0.2, 1.7, 5] } as LengthBoundSpec;
const POD_D = { (meter) : [0.02, 0.2, 1] } as LengthBoundSpec;
const POD_NOSE = { (meter) : [0, 0.35, 2] } as LengthBoundSpec;
const POD_Z = { (meter) : [-0.5, 0.06, 0.5] } as LengthBoundSpec;
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
        annotation { "Name" : "Pod length" }
        isLength(definition.podL, POD_L);
        annotation { "Name" : "Pod diameter" }
        isLength(definition.podD, POD_D);
        annotation { "Name" : "Pod nose ahead of the front wing" }
        isLength(definition.podNose, POD_NOSE);
        annotation { "Name" : "Pod axis above the front wing" }
        isLength(definition.podZ, POD_Z);
    }
    {
        const foil = airfoil(0.02, 0.4, definition.tc, 24);
        const wings = [
                { "name" : "front", "x" : 0 * meter, "z" : 0 * meter, "span" : definition.frontSpan,
                  "root" : definition.frontRoot, "tip" : definition.frontTip, "extra" : 0 * meter },
                { "name" : "rear", "x" : definition.stagger, "z" : definition.gap, "span" : definition.rearSpan,
                  "root" : definition.rearRoot, "tip" : definition.rearTip, "extra" : definition.gap }];
        for (var w in wings)
        {
            const wid = id + w.name;
            const half = w.span / 2;
            // Each half: a loft from the root section to the tip section.
            for (var side in [1, -1])
            {
                const sid = wid + (side > 0 ? "L" : "R");
                section(context, sid + "root", 0 * meter, w.x, w.root, w.z, foil);
                section(context, sid + "tip", side * half, w.x + (w.root - w.tip) * definition.pivot, w.tip, w.z, foil);
                opLoft(context, sid + "loft", {
                            "profileSubqueries" : [qSketchRegion(sid + "root"), qSketchRegion(sid + "tip")],
                            "bodyType" : ToolBodyType.SOLID });
                opDeleteBodies(context, sid + "sketches", { "entities" : qUnion([qCreatedBy(sid + "root", EntityType.BODY),
                                    qCreatedBy(sid + "tip", EntityType.BODY)]) });
                // The nacelle, prop and float at the prop station.
                const yp = side * definition.propStation * w.span;
                const cp = w.root + (w.tip - w.root) * abs(yp) / half;
                const xle = w.x + (w.root - cp) * definition.pivot;
                const r = definition.floatD / 2;
                revolved(context, sid + "nacelle", xle - 0.12 * meter, xle + 0.5 * cp, yp, w.z, 0.035 * meter);
                revolved(context, sid + "float", xle + 0.5 * cp, xle + cp + definition.floatL + w.extra, yp, w.z, r);
                fCylinder(context, sid + "prop", {
                            "topCenter" : vector(xle - 0.13 * meter, yp, w.z),
                            "bottomCenter" : vector(xle - 0.125 * meter, yp, w.z),
                            "radius" : definition.prop / 2 });
            }
            // The tilt shaft, and the wing turned about it.
            const xp = w.x + definition.pivot * w.root;
            fCylinder(context, wid + "shaft", {
                        "topCenter" : vector(xp, 0.45 * definition.podD, w.z),
                        "bottomCenter" : vector(xp, -0.45 * definition.podD, w.z),
                        "radius" : 0.012 * meter });
            if (definition.tilt > 0.01 * degree)
            {
                opTransform(context, wid + "tilt", {
                            "bodies" : qUnion([qCreatedBy(wid + "L", EntityType.BODY), qCreatedBy(wid + "R", EntityType.BODY)]),
                            "transform" : rotationAround(line(vector(xp, 0 * meter, w.z), vector(0, 1, 0)), definition.tilt) });
            }
        }
        // The pod, the fin to the rear wing, and the gimbal.
        revolved(context, id + "pod", -definition.podNose, definition.podL - definition.podNose, 0 * meter, definition.podZ,
            definition.podD / 2);
        const xr = definition.stagger + definition.pivot * definition.rearRoot;
        fCylinder(context, id + "fin", {
                    "topCenter" : vector(xr, 0 * meter, definition.gap),
                    "bottomCenter" : vector(xr, 0 * meter, definition.podZ),
                    "radius" : 0.02 * meter });
        opSphere(context, id + "gimbal", {                       // fSphere wants a vertex query; opSphere a vector
                    "center" : vector(0.55 * meter, 0 * meter, definition.podZ - definition.podD / 2 - 0.027 * meter),
                    "radius" : 0.045 * meter });
    }, {
        "tilt" : 0 * degree, "frontSpan" : 3.184 * meter, "frontRoot" : 0.195 * meter, "frontTip" : 0.195 * meter,
        "rearSpan" : 2.957 * meter, "rearRoot" : 0.243 * meter, "rearTip" : 0.195 * meter, "stagger" : 1.2 * meter,
        "gap" : 0.15 * meter, "tc" : 0.12, "pivot" : 0.25, "prop" : 0.5 * meter, "propStation" : 0.26,
        "floatD" : 0.094 * meter, "floatL" : 0.661 * meter, "podL" : 1.7 * meter, "podD" : 0.2 * meter,
        "podNose" : 0.35 * meter, "podZ" : 0.06 * meter });

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

/** A streamlined body of revolution along x, from x0 to x1, at (y, z), of greatest radius r. */
function revolved(context is Context, id is Id, x0 is ValueWithUnits, x1 is ValueWithUnits, y is ValueWithUnits,
    z is ValueWithUnits, r is ValueWithUnits)
{
    const sk = newSketchOnPlane(context, id + "sketch", {
                "sketchPlane" : plane(vector(0 * meter, y, 0 * meter), vector(0, -1, 0), vector(1, 0, 0)) });
    var pts = [];
    const n = 16;
    for (var i = 0; i <= n; i += 1)
    {
        const s = i / n;
        var k = 0;
        if (s < 0.35)
            k = sqrt(max(1 - ((0.35 - s) / 0.35) ^ 2, 0));
        else
            k = max(1 - ((s - 0.35) / 0.65) ^ 2, 0);
        pts = append(pts, vector(x0 + s * (x1 - x0), z + max(k, 0.02) * r));
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
