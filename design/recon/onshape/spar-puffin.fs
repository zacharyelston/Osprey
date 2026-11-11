FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

// Osprey's spar Puffin: a UAS-sized take on NASA's Puffin electric tailsitter (Moore, 2010) that floats tail-down
// and always bobs back upright. Drawn standing on its tail, as it floats and lifts off: z up from the tail.
// The hull is a spar: a slender boom at the tail that carries the battery and ballast (the keel), flaring to the
// full girth at the waterline, then a round nose that carries the camera. Displacement is the dial: the girth and
// where it sits set where it floats and how hard it comes back. The wings and nacelles are free-flooding, so
// lying flat they don't hold it there. Two props at the wingtips; four strakes on the boom, an X, are the
// tail in flight and the legs on deck.
// Three layouts, as `osprey recon-puffin` compares them (design/recon/puffin.toml):
//   Puffin as drawn: the slender streamlined hull, the battery mid-hull; it settles lying flat.
//   Spar, fixed ballast: the battery and 1 kg of ballast in the boom, the CG behind the wing (a lifting tail).
//   Spar, battery on a screw: the battery down the boom afloat, up at the wing in flight; no ballast.
// Each component is its own named part, ready for an assembly. The water surface, a thin disc, sits where the
// model floats each layout (for the dials as they are; change them and run the model again).
// Frame: z up from the tail along the hull's axis, the wing's span along y, x toward the belly; metres.

export enum PuffinLayout
{
    annotation { "Name" : "Puffin as drawn" }
    AS_DRAWN,
    annotation { "Name" : "Spar, fixed ballast" }
    FIXED_BALLAST,
    annotation { "Name" : "Spar, battery on a screw" }
    SCREW
}

const LEN = { (meter) : [0.3, 1.3, 5] } as LengthBoundSpec;
const GIRTH = { (meter) : [0.05, 0.40, 2] } as LengthBoundSpec;
const BOOM_R = { (meter) : [0.01, 0.055, 0.5] } as LengthBoundSpec;
const FRAC_BOOM = { (unitless) : [0.0, 0.30, 0.9] } as RealBoundSpec;
const FRAC_FLARE = { (unitless) : [0.0, 0.45, 0.95] } as RealBoundSpec;
const FRAC_FULL = { (unitless) : [0.0, 0.75, 0.98] } as RealBoundSpec;
const SPAN = { (meter) : [0.2, 1.6, 10] } as LengthBoundSpec;
const CHORD = { (meter) : [0.02, 0.26, 2] } as LengthBoundSpec;
const TC = { (unitless) : [0.04, 0.14, 0.3] } as RealBoundSpec;
const PROP = { (meter) : [0.05, 0.76, 3] } as LengthBoundSpec;
const NAC_R = { (meter) : [0.01, 0.04, 0.3] } as LengthBoundSpec;
const STRAKE_L = { (meter) : [0.02, 0.35, 2] } as LengthBoundSpec;
const STRAKE_S = { (meter) : [0.02, 0.30, 2] } as LengthBoundSpec;

annotation { "Feature Type Name" : "Osprey spar Puffin" }
export const ospreySparPuffin = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Layout" }
        definition.layout is PuffinLayout;
        annotation { "Name" : "Battery in flight position (screw layout)" }
        definition.flying is boolean;
        annotation { "Name" : "Show the water surface" }
        definition.showWater is boolean;
        annotation { "Name" : "Hull length" }
        isLength(definition.length, LEN);
        annotation { "Name" : "Girth (hull diameter)" }
        isLength(definition.girth, GIRTH);
        annotation { "Name" : "Boom radius" }
        isLength(definition.boomR, BOOM_R);
        annotation { "Name" : "Boom to, of the length" }
        isReal(definition.boomTo, FRAC_BOOM);
        annotation { "Name" : "Full girth from, of the length" }
        isReal(definition.girthFrom, FRAC_FLARE);
        annotation { "Name" : "Full girth to, of the length" }
        isReal(definition.girthTo, FRAC_FULL);
        annotation { "Name" : "Wing span" }
        isLength(definition.span, SPAN);
        annotation { "Name" : "Wing chord" }
        isLength(definition.chord, CHORD);
        annotation { "Name" : "Wing thickness / chord" }
        isReal(definition.tc, TC);
        annotation { "Name" : "Prop diameter" }
        isLength(definition.prop, PROP);
        annotation { "Name" : "Nacelle radius" }
        isLength(definition.nacR, NAC_R);
        annotation { "Name" : "Strake length" }
        isLength(definition.strakeL, STRAKE_L);
        annotation { "Name" : "Strake span" }
        isLength(definition.strakeS, STRAKE_S);
    }
    {
        // Each layout's stations, from the righting model: the wing, the battery, ballast, and where it floats.
        const drawn = definition.layout == PuffinLayout.AS_DRAWN;
        const presets = {
                PuffinLayout.AS_DRAWN : { "wingLE" : 0.726, "battery" : 0.60, "ballast" : false, "water" : 0.479 },
                PuffinLayout.FIXED_BALLAST : { "wingLE" : 0.679, "battery" : 0.10, "ballast" : true, "water" : 0.526 },
                PuffinLayout.SCREW : { "wingLE" : 0.70, "battery" : definition.flying ? 0.618 : 0.10, "ballast" : false,
                    "water" : 0.514 } };
        const pre = presets[definition.layout];
        const wingLE = pre.wingLE * meter;

        // The hull: a profile r(z) revolved about the z axis.
        const L = definition.length;
        const R = drawn ? 0.10 * meter : definition.girth / 2;
        const rb = definition.boomR;
        const sk = newSketchOnPlane(context, id + "hullSketch", {
                    "sketchPlane" : plane(vector(0, 0, 0) * meter, vector(0, -1, 0), vector(1, 0, 0)) });
        var pts = [vector(0 * meter, 0 * meter)];
        const n = 40;
        for (var i = 1; i < n; i += 1)
        {
            const q = i / n;
            var r = R;
            if (drawn)
            {
                // The Puffin's: a round nose over the top 15 %, full to half way, then tapering to the tail.
                const s = 1 - q;
                var k = 1;
                if (s < 0.15)
                    k = sqrt(max(1 - ((0.15 - s) / 0.15) ^ 2, 0));
                else if (s > 0.5)
                    k = max(1 - ((s - 0.5) / 0.5) ^ 2, 0) ^ 0.8;
                r = max(k, 0.03) * R;
            }
            else if (q < 0.03)
                r = rb * sqrt(max(1 - ((0.03 - q) / 0.03) ^ 2, 0.01));
            else if (q < definition.boomTo)
                r = rb;
            else if (q < definition.girthFrom)
                r = rb + (R - rb) * (1 - cos(PI * (q - definition.boomTo) / (definition.girthFrom - definition.boomTo) * radian)) / 2;
            else if (q > definition.girthTo)
                r = R * sqrt(max(1 - ((q - definition.girthTo) / (1 - definition.girthTo)) ^ 2, 0.0004));
            pts = append(pts, vector(r, q * L));
        }
        pts = append(pts, vector(0 * meter, L));
        skFitSpline(sk, "profile", { "points" : pts });
        skLineSegment(sk, "axis", { "start" : vector(0 * meter, 0 * meter), "end" : vector(0 * meter, L) });
        skSolve(sk);
        opRevolve(context, id + "hull", {
                    "entities" : qSketchRegion(id + "hullSketch"),
                    "axis" : line(vector(0, 0, 0) * meter, vector(0, 0, 1)),
                    "angleForward" : 360 * degree });
        opDeleteBodies(context, id + "hullClean", { "entities" : qCreatedBy(id + "hullSketch", EntityType.BODY) });
        name(context, id + "hull", "Hull");

        // The wing: its chord along z, the leading edge up (forward in flight), the span along y.
        const foil = airfoil(0.02, 0.4, definition.tc, 24);
        const c = definition.chord;
        const half = definition.span / 2;
        const y0 = R * 0.6;
        for (var side in [1, -1])
        {
            const wid = id + (side > 0 ? "wingL" : "wingR");
            section(context, wid + "root", side * y0, wingLE, c, foil);
            section(context, wid + "tip", side * half, wingLE, c, foil);
            opLoft(context, wid + "loft", {
                        "profileSubqueries" : [qSketchRegion(wid + "root"), qSketchRegion(wid + "tip")],
                        "bodyType" : ToolBodyType.SOLID });
            opDeleteBodies(context, wid + "sketches", { "entities" : qUnion([qCreatedBy(wid + "root", EntityType.BODY),
                                qCreatedBy(wid + "tip", EntityType.BODY)]) });
            name(context, wid + "loft", side > 0 ? "Wing, port" : "Wing, starboard");
            // The nacelle at the tip, along z, and a two-bladed prop at its top.
            const yt = side * half;
            const top = wingLE + 0.12 * meter;
            nacelle(context, wid + "nacelle", yt, top, wingLE - c - 0.10 * meter, definition.nacR);
            name(context, wid + "nacelle", side > 0 ? "Nacelle and motor, port" : "Nacelle and motor, starboard");
            for (var k in [0, 1])
            {
                const a = (0.6 + k * PI) * radian;
                fCylinder(context, wid + ("blade" ~ k), {
                            "topCenter" : vector(cos(a) * definition.prop / 2, yt + sin(a) * definition.prop / 2, top - 0.03 * meter),
                            "bottomCenter" : vector(0 * meter, yt, top - 0.03 * meter), "radius" : 0.010 * meter });
            }
            opBoolean(context, wid + "prop", { "tools" : qUnion([qCreatedBy(wid + "blade0", EntityType.BODY),
                                qCreatedBy(wid + "blade1", EntityType.BODY)]), "operationType" : BooleanOperationType.UNION });
            name(context, wid + "blade0", side > 0 ? "Prop, port" : "Prop, starboard");
        }

        // Four strakes on the boom, an X: a symmetric section, its chord along z from the tail up, thickness across.
        const sym = airfoil(0, 0.4, 0.10, 16);
        for (var k = 0; k < 4; k += 1)
        {
            const th = (45 + 90 * k) * degree;
            const sid = id + ("strake" ~ k);
            for (var lvl in [["in", rb * 0.5], ["out", rb + definition.strakeS]])
            {
                const o = vector(cos(th), sin(th), 0);
                const sks = newSketchOnPlane(context, sid + lvl[0], {
                            "sketchPlane" : plane(o * lvl[1], o, vector(-sin(th), cos(th), 0)) });
                for (var part in ["upper", "lower"])
                {
                    var sp = [];
                    for (var p in sym[part])
                        sp = append(sp, vector(p[1] * definition.strakeL, definition.strakeL - p[0] * definition.strakeL));
                    skFitSpline(sks, part, { "points" : sp });
                }
                skSolve(sks);
            }
            opLoft(context, sid + "loft", {
                        "profileSubqueries" : [qSketchRegion(sid + "in"), qSketchRegion(sid + "out")],
                        "bodyType" : ToolBodyType.SOLID });
            opDeleteBodies(context, sid + "sketches", { "entities" : qUnion([qCreatedBy(sid + "in", EntityType.BODY),
                                qCreatedBy(sid + "out", EntityType.BODY)]) });
            name(context, sid + "loft", "Strake " ~ (k + 1));
        }

        // The battery, on its screw along the axis, and the ballast at the foot of the boom.
        const bz = pre.battery * meter;
        fCylinder(context, id + "battery", { "topCenter" : vector(0 * meter, 0 * meter, bz + 0.09 * meter),
                    "bottomCenter" : vector(0 * meter, 0 * meter, bz - 0.09 * meter), "radius" : 0.045 * meter });
        name(context, id + "battery", definition.layout == PuffinLayout.SCREW ?
                (definition.flying ? "Battery (on its screw, in flight)" : "Battery (on its screw, afloat)") : "Battery");
        if (pre.ballast)
        {
            fCylinder(context, id + "ballast", { "topCenter" : vector(0 * meter, 0 * meter, 0.06 * meter),
                        "bottomCenter" : vector(0 * meter, 0 * meter, 0.01 * meter), "radius" : 0.045 * meter });
            name(context, id + "ballast", "Ballast, 1 kg");
        }
        if (definition.showWater)
        {
            const zw = pre.water * meter;
            fCylinder(context, id + "water", { "topCenter" : vector(0 * meter, 0 * meter, zw),
                        "bottomCenter" : vector(0 * meter, 0 * meter, zw - 0.002 * meter), "radius" : 1.2 * meter });
            name(context, id + "water", "Water surface (afloat)");
        }

        // The dome's gimbal camera: a ball in the nose.
        opSphere(context, id + "gimbal", { "center" : vector(0 * meter, 0 * meter, L - 0.06 * meter), "radius" : 0.045 * meter });
        name(context, id + "gimbal", "Gimbal camera (dome)");
    }, {
        "layout" : PuffinLayout.SCREW, "flying" : false, "showWater" : true, "length" : 1.3 * meter,
        "girth" : 0.40 * meter, "boomR" : 0.055 * meter, "boomTo" : 0.30, "girthFrom" : 0.45, "girthTo" : 0.75,
        "span" : 1.6 * meter, "chord" : 0.26 * meter, "tc" : 0.14, "prop" : 0.76 * meter, "nacR" : 0.04 * meter, "strakeL" : 0.35 * meter, "strakeS" : 0.30 * meter });

/** A NACA 4-digit section, (u, z) in chord units: the upper surface from the trailing edge to the leading edge,
 * and the lower from the leading edge back, sharing both end points. */
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
        if (m > 0 && x < pos)
        {
            yc = m / pos ^ 2 * (2 * pos * x - x ^ 2);
            dy = 2 * m / pos ^ 2 * (pos - x);
        }
        else if (m > 0)
        {
            yc = m / (1 - pos) ^ 2 * (1 - 2 * pos + 2 * pos * x - x ^ 2);
            dy = 2 * m / (1 - pos) ^ 2 * (pos - x);
        }
        const th = atan(dy);
        if (i == 0 || i == n)
        {
            up = append(up, [x, yc]);
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

/** A wing section in the plane y = const, the chord running down z from the leading edge at le, the camber toward -x
 * (the back, in flight the top); sketch coordinates are (x, z). */
function section(context is Context, id is Id, y is ValueWithUnits, le is ValueWithUnits, c is ValueWithUnits, foil is map)
{
    const sk = newSketchOnPlane(context, id, {
                "sketchPlane" : plane(vector(0 * meter, y, 0 * meter), vector(0, -1, 0), vector(1, 0, 0)) });
    for (var side in ["upper", "lower"])
    {
        var pts = [];
        for (var p in foil[side])
            pts = append(pts, vector(-p[1] * c, le - p[0] * c));
        skFitSpline(sk, side, { "points" : pts });
    }
    skSolve(sk);
}

/** A streamlined nacelle along z at (0, y), from z0 at the top down to z1: a round top, full, then tapering. */
function nacelle(context is Context, id is Id, y is ValueWithUnits, z0 is ValueWithUnits, z1 is ValueWithUnits, r is ValueWithUnits)
{
    const sk = newSketchOnPlane(context, id + "sketch", {
                "sketchPlane" : plane(vector(0 * meter, y, 0 * meter), vector(0, -1, 0), vector(1, 0, 0)) });
    var pts = [];
    const n = 16;
    for (var i = 0; i <= n; i += 1)
    {
        const s = i / n;
        var k = 1;
        if (s < 0.2)
            k = sqrt(max(1 - ((0.2 - s) / 0.2) ^ 2, 0));
        else if (s > 0.5)
            k = max(1 - ((s - 0.5) / 0.5) ^ 2, 0) ^ 0.8;
        pts = append(pts, vector(max(k, 0.03) * r, z0 + s * (z1 - z0)));
    }
    pts[0] = vector(0 * meter, z0);
    pts[n] = vector(0 * meter, z1);
    skFitSpline(sk, "profile", { "points" : pts });
    skLineSegment(sk, "axis", { "start" : vector(0 * meter, z0), "end" : vector(0 * meter, z1) });
    skSolve(sk);
    opRevolve(context, id, {
                "entities" : qSketchRegion(id + "sketch"),
                "axis" : line(vector(0 * meter, y, 0 * meter), vector(0, 0, 1)),
                "angleForward" : 360 * degree });
    opDeleteBodies(context, id + "clean", { "entities" : qCreatedBy(id + "sketch", EntityType.BODY) });
}

/** Name the bodies an operation created, so each shows as its own part. */
function name(context is Context, opId is Id, value is string)
{
    setProperty(context, { "entities" : qCreatedBy(opId, EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : value });
}
