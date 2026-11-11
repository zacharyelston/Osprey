"""The spar Puffin: a UAS-sized take on NASA's Puffin electric tailsitter (Moore, NASA Langley, 2010) that floats
tail-down, the attitude it lifts off from, and always bobs back upright when a wave knocks it over.

A tailsitter that capsizes at sea and lies flat can't take off again. So the question for each layout is its
righting curve: knocked over by any angle, onto its belly or back or onto a wingtip, does the water push it back
toward upright? GZ, the righting arm, is the horizontal distance from the centre of gravity to the centre of
buoyancy; above zero all the way from 0 to 180 degrees, it always comes back.

Three layouts (design/recon/puffin.toml):

- as drawn: the Puffin's slender streamlined hull, the battery mid-hull and the wing at the CG. Upright it is
  top-heavy on a narrow waterline, and it settles lying flat.
- ballast: a spar. A slender boom at the tail carries the battery and 1 kg of ballast, the keel; the hull flares to
  its girth at the waterline. It always rights itself, but the CG sits behind the wing, so the tail must lift.
- screw: the same spar with the battery on a screw. It runs down the boom to float and up to the wing to fly, so a
  normal tail balances it and it needs no ballast. The sweep finds how far it must travel, and what a heavier
  payload in the dome does to the righting.

Body frame: x up the hull's axis from the tail (forward in flight), y along the span, z across; metres.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from osprey.params import _toml
from osprey.recon import geometry as g
from osprey.recon import water
from osprey.recon.params import RECON


def inputs() -> dict:
    return _toml(RECON / "puffin.toml")


def layout(name: str, li: dict | None = None, **over) -> dict:
    """One layout's parameters: [craft], its [layouts.<name>] on top, then any overrides."""
    li = li or inputs()
    c = {**li["craft"], **li["layouts"].get(name, {}), **over}
    if c["hull"].get("kind", "spar") == "spar":
        c["hull"] = {**li["craft"]["hull"], **c["hull"]}
    c.setdefault("wing_le_m", 0.70)
    c.setdefault("sweep_deg", 0.0)
    c["float_x_m"] = li["screw"]["float_x_m"]
    return c


def rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


UPRIGHT = rot_y(-math.pi / 2)            # body x (the nose) to world z (up): floating tail-down


def hull_kg(c: dict) -> float:
    return c["hull_ref_kg"] * (c["diameter_m"] / c["hull_ref_diameter_m"]) ** c["hull_girth_exponent"] * \
        c["length_m"] / c["hull_ref_length_m"]


def spar_radius(c: dict, q: float) -> float:
    """The spar hull's radius a fraction q of its length up from the tail: a round tail cap, the boom, a cosine flare
    to the full girth, full, then a round nose."""
    h, R, rb = c["hull"], c["diameter_m"] / 2, c["hull"]["boom_r_m"]
    if q < 0.03:
        return rb * math.sqrt(max(1 - ((0.03 - q) / 0.03) ** 2, 0.01))
    if q < h["boom_to"]:
        return rb
    if q < h["girth_from"]:
        t = (q - h["boom_to"]) / (h["girth_from"] - h["boom_to"])
        return rb + (R - rb) * (1 - math.cos(math.pi * t)) / 2
    if q < h["girth_to"]:
        return R
    t = (q - h["girth_to"]) / (1 - h["girth_to"])
    return R * math.sqrt(max(1 - t**2, 0.0004))


def tip_shift(c: dict) -> float:
    """How far forward (up the hull) the wingtip's leading edge sits of the root's: forward sweep is positive. The
    wing is taken from the hull's side (its girth) to the tip."""
    return (c["span_m"] / 2 - c["diameter_m"] / 2) * math.tan(math.radians(c.get("sweep_deg", 0.0)))


def build(c: dict, battery_x: float) -> tuple[list, list, float, np.ndarray]:
    """Sealed meshes [(name, (verts, faces))], point masses [(name, kg, xyz)], the total mass and the CG, with the
    battery at battery_x up from the tail."""
    L, R = c["length_m"], c["diameter_m"] / 2
    span, ch, tc = c["span_m"], c["chord_m"], c["t_over_c"]
    meshes, masses = [], []
    if c["hull"]["kind"] == "spar":
        a = np.linspace(0, 2 * math.pi, 24, endpoint=False)
        meshes.append(("hull", g.loft([np.stack([np.full_like(a, q * L), spar_radius(c, q) * np.cos(a),
                                                 spar_radius(c, q) * np.sin(a)], 1) for q in np.linspace(0, 1, 40)])))
    else:                                # the Puffin's: a round nose, tapering to the tail
        meshes.append(("hull", g._streamlined(L, 0.0, 0.0, 0.0, R, nose=0.15, full=0.5)))
    masses += [("hull", hull_kg(c), [0.5 * L, 0, 0]), ("battery", c["battery_kg"], [battery_x, 0, 0]),
               ("payload", c["payload_kg"], [L - c["payload_from_nose_m"], 0, 0]),
               ("avionics", c["avionics_kg"], [c["avionics_x_m"], 0, 0]), ("fins", c["fins_kg"], [0.12, 0, 0])]
    if c["ballast_kg"]:
        masses.append(("ballast", c["ballast_kg"], [c["ballast_x_m"], 0, 0]))
    xw = c["wing_le_m"]
    u, zf = g.naca4(0.02, 0.4, tc, 24)
    if not c["wings_flood"]:
        for sgn in (1, -1):
            sweep = math.tan(math.radians(c.get("sweep_deg", 0.0)))
            meshes.append((f"wing{sgn}", g.loft([g._section(u, zf, -(xw + max(y - R, 0.0) * sweep), ch, sgn * y, 0.0, 0.0)
                                                 for y in np.linspace(R * 0.6, span / 2, 6)])))
    shift = tip_shift(c)
    masses.append(("wing", c["wing_kg"], [xw + shift / 2 - 0.42 * ch, 0, 0]))
    for sgn in (1, -1):
        yt = sgn * span / 2
        if not c["wings_flood"]:
            meshes.append((f"nacelle{sgn}", g._streamlined(xw + shift + 0.12, xw + shift - ch - c["nacelle_tail_m"], yt, 0.0,
                                                           c["nacelle_r_m"], nose=0.2, full=0.5)))
        masses += [("motor", c["motor_kg"], [xw + shift + 0.06, yt, 0]), ("prop", c["prop_kg"], [xw + shift + 0.12, yt, 0])]
    m = sum(k for _, k, _ in masses)
    cg = sum(k * np.array(p, float) for _, k, p in masses) / m
    return meshes, masses, m, cg


def flight_cg_target(c: dict) -> float:
    """Where the CG must sit in flight: the static margin ahead of the neutral point, taken as the quarter chord of
    the mean chord, which forward sweep carries forward by half the tip's shift."""
    return c["wing_le_m"] + tip_shift(c) / 2 - (0.25 + c["static_margin"]) * c["chord_m"]


def balance_wing(c: dict, battery_x: float) -> dict:
    """A fixed layout: slide the wing (and its motors) until the CG sits where flight needs it."""
    c = dict(c)
    for _ in range(40):
        c["wing_le_m"] += build(c, battery_x)[3][0] - flight_cg_target(c)
    return c


def flight_station(c: dict) -> float:
    """The screw layout: the battery station that balances the craft on its wing in flight. Only the battery's
    moment moves, so it is one step."""
    _, _, m, cg = build(c, 0.0)
    return (flight_cg_target(c) - cg[0]) * m / c["battery_kg"]


def _posed(meshes, cg, R):
    return [((v - cg) @ R.T, f) for _, (v, f) in meshes]


def _level(ms, need: float) -> float | None:
    """The waterline under which the sealed volume displaces `need` m³, or None if it all would not."""
    lo = min(float(v[:, 2].min()) for v, _ in ms)
    hi = max(float(v[:, 2].max()) for v, _ in ms)
    if water._below(ms, hi)[0] < need:
        return None
    for _ in range(45):
        h = (lo + hi) / 2
        if water._below(ms, h)[0] < need:
            lo = h
        else:
            hi = h
    return (lo + hi) / 2


def gz(meshes, cg, need: float, axis: str, phi: float) -> float:
    """The righting arm (m), knocked over from upright by phi about world y ("belly": it falls onto its belly or
    back, the wings flat) or about world x ("wingtip"). Positive pushes it back toward upright."""
    R = (rot_y(phi) if axis == "belly" else rot_x(phi)) @ UPRIGHT
    if axis == "wingtip":
        R = rot_z(-math.pi / 2) @ R                 # world y onto x, so the waterline's x-centroid is the arm
    ms = _posed(meshes, cg, R)
    h = _level(ms, need)
    if h is None:
        return math.nan
    cb = water._below(ms, h)[1]
    return cb if axis == "belly" else -cb


def righting(c: dict, battery_x: float, step_deg: float = 5.0) -> dict:
    """Upright afloat (where the water comes to, the props' and wing's clearance) and both righting curves."""
    meshes, masses, m, cg = build(c, battery_x)
    need = m / c["water_density_kgm3"]
    sealed = water._below(_posed(meshes, cg, np.eye(3)), 1e3)[0]
    h = _level(_posed(meshes, cg, UPRIGHT), need)
    out = {"mass_kg": m, "cg_x_m": float(cg[0]), "battery_x_m": battery_x, "wing_le_m": c["wing_le_m"],
           "sealed_l": sealed * 1e3, "displaced_l": need * 1e3}
    water_x = h + cg[0]                                  # the waterline, up from the tail
    out.update(waterline_m=water_x, props_clear_m=c["wing_le_m"] + tip_shift(c) + 0.12 - water_x,
               wing_te_clear_m=c["wing_le_m"] - c["chord_m"] - water_x, dome_above_m=c["length_m"] - water_x)
    phis = np.arange(0, 180 + 1e-9, step_deg)
    out["phi_deg"] = phis.tolist()
    for axis in ("belly", "wingtip"):
        arms = [gz(meshes, cg, need, axis, math.radians(p)) for p in phis]
        inner = [a for p, a in zip(phis, arms) if 0 < p < 180]
        out[f"gz_{axis}_m"] = arms
        out[f"least_gz_{axis}_m"] = min(inner)
        out[f"rights_{axis}"] = all(a > 0 for a in inner)
    out["rights"] = out["rights_belly"] and out["rights_wingtip"]
    out["gz15_m"] = min(out["gz_belly_m"][int(15 / step_deg)], out["gz_wingtip_m"][int(15 / step_deg)])
    return out


def one(name: str, li: dict | None = None, **over) -> dict:
    """One layout floated: a fixed battery (the wing balanced to the CG), or the screw (the battery down the boom
    afloat, the wing where the layout puts it, the flight station found)."""
    c = layout(name, li, **over)
    if c["battery"] == "screw":
        fly = flight_station(c)
        r = righting(c, c["float_x_m"])
        r.update(flight_battery_x_m=fly, travel_m=fly - r["battery_x_m"])
    else:
        c = balance_wing(c, c["battery"])
        r = righting(c, c["battery"])
    return {"layout": name, "label": c.get("label", name), "payload_kg": c["payload_kg"], "ballast_kg": c["ballast_kg"],
            **r}


def _sweep_job(args) -> dict:
    wing, payload, ballast = args
    return one("screw", wing_le_m=wing, payload_kg=payload, ballast_kg=ballast)


def sweep(workers: int = 0) -> list[dict]:
    sw = inputs()["sweep"]
    jobs = [(w, p, b) for w in sw["wing_le_m"] for p in sw["payload_kg"] for b in sw["ballast_kg"]]
    if workers == 1:
        return [_sweep_job(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(_sweep_job, jobs))


def _yes(r: dict) -> str:
    if r["rights"]:
        return "yes"
    worst = "belly" if r["least_gz_belly_m"] < r["least_gz_wingtip_m"] else "wingtip"
    phis, arms = r["phi_deg"], r[f"gz_{worst}_m"]
    settle = next((p for p, a in zip(phis[1:], arms[1:]) if a < 0), None)
    return f"no: falls from {settle:.0f}° onto its {'belly or back' if worst == 'belly' else 'wingtip'}"


def report(rows: list[dict], sweep_rows: list[dict]) -> str:
    li = inputs()
    lines = ["# The spar Puffin: will it always bob back tail-down?", "",
             "A UAS-sized Puffin (NASA's electric tailsitter, Moore 2010), floated tail-down and knocked over by every "
             "angle to 180°, onto its belly or back and onto a wingtip. GZ is the righting arm: above zero it pushes it "
             "back upright. It always rights itself if GZ stays above zero all the way round (`recon/puffin.py`, "
             "inputs in `design/recon/puffin.toml`).", "",
             "## The layouts", "",
             "| Layout | Mass | Battery afloat | Under water | Props clear | Dome above water | Rights itself | "
             "GZ at 15°, least | GZ at 90° |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['label']} | {r['mass_kg']:.2f} kg | {r['battery_x_m'] * 100:.0f} cm up | "
                     f"{r['waterline_m'] * 100:.0f} cm | {r['props_clear_m'] * 100:.0f} cm | {r['dome_above_m'] * 100:.0f} cm | "
                     f"{_yes(r)} | {r['gz15_m'] * 100:+.1f}, {min(r['least_gz_belly_m'], r['least_gz_wingtip_m']) * 100:+.1f} cm | "
                     f"{r['gz_belly_m'][len(r['phi_deg']) // 2] * 100:+.0f} cm |")
    lines += ["", "## The battery on a screw", "",
              f"The screw layout with the wing's leading edge at each station, each payload in the dome and with or without "
              f"ballast in the boom. Afloat the battery sits {li['screw']['float_x_m'] * 100:.0f} cm up from the tail; in "
              f"flight it runs up to balance the craft on the wing with a {li['craft']['static_margin'] * 100:.0f} % static "
              f"margin. Travel: how far the screw runs between the two.", "",
              "| Wing LE | Dome payload | Ballast | Mass | Battery in flight | Travel | Props clear | Rights itself | GZ at 15°, least |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(sweep_rows, key=lambda r: (r["wing_le_m"], r["payload_kg"], r["ballast_kg"])):
        lines.append(f"| {r['wing_le_m']:.2f} m | {r['payload_kg']:.1f} kg | {r['ballast_kg']:.1f} kg | {r['mass_kg']:.2f} kg | "
                     f"{r['flight_battery_x_m'] * 100:.0f} cm up | {r['travel_m'] * 100:.0f} cm | {r['props_clear_m'] * 100:.0f} cm | "
                     f"{_yes(r)} | {r['gz15_m'] * 100:+.1f}, {min(r['least_gz_belly_m'], r['least_gz_wingtip_m']) * 100:+.1f} cm |")
    return "\n".join(lines) + "\n"
