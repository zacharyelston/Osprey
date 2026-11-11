"""The Trident: a crewed tailsitter built from three identical modules round a foam-walled core (design/trident.toml).

Each module is an arm and wing panel, a motor pod with a big slow prop, and a leg ending in a foam float-foot. The
core is sized round a 4x8 ft sheet and carries a person and their mission load (or cargo) in a padded, buoyant
container. The power cells sit in a bay a metre long under it: the keel afloat, the tail in flight. It lifts off
standing on its tail, tips over and flies on the three wings in a Y, and lands back on its float-feet.

- Sizing: momentum theory over the three discs for the hover, a drag polar for the wing-borne cruise, weight
  fractions and part weights from the geometry, the battery sized for one trip and a reserve; the weight closed by
  iterating. The cargo case flies the crewed airframe and battery with no one aboard.
- Afloat: the sealed envelope (bay, core and nose), the float-feet and the wing panels as closed meshes, floated at
  the weight and knocked over by every angle to 180 degrees, toward a module, between two and halfway. GZ, the
  righting arm, is the horizontal distance from the centre of gravity to the centre of buoyancy; above zero all the
  way round, it always comes back upright.

Body frame: z up the axis from the tail (the bottom of the bay), forward in flight; the modules at 0, 120 and 240
degrees round it; metres. Every number is a REF stand-in: these are first-look numbers to dial, not a design.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from osprey.beet import revolve
from osprey.params import DESIGN, _toml
from osprey.recon import geometry as g
from osprey.recon import water
from osprey.recon.puffin import _level, rot_y, rot_z

G = 9.81
ANGLES = (0.0, 2 * math.pi / 3, 4 * math.pi / 3)
CREW_ONLY = ("person", "mission load", "container", "seat", "hatch", "safety")


def inputs() -> dict:
    return _toml(DESIGN / "trident.toml")


def params(layout_name: str = "found", li: dict | None = None, **over) -> dict:
    """The crewed case's parameters: [core], [module], [power], [aero], [mission], the case, the layout, then any
    overrides. `feet=(r, l)` sets the float-feet's radius and length (0, 0 for none: legs with pads)."""
    li = li or inputs()
    lo = {k: v for k, v in li["layouts"][layout_name].items() if k != "label"}
    c = {**li["core"], **li["module"], **li["power"], **li["aero"], **li["mission"], **li["cases"]["crewed"], **lo}
    c["layout"] = layout_name
    feet = over.pop("feet", None)
    if feet is not None:
        c["foot_r_m"], c["foot_l_m"] = feet
    c.update(over)
    c["skin_kgm2"] = li["skins"][c["skin"]]["kgm2"]
    return c


def layout(c: dict) -> dict:
    """Where everything goes. The props' plane is where the case puts it (the core's top unless it is balanced
    lower); the arm puts each tip just clear of the core; the wing's leading edge is just behind the props."""
    r_core = c["interior_w_m"] / 2 + c["wall_m"]
    core_l = c["interior_l_m"] + 2 * c["wall_m"]
    d = c["prop_d_m"]
    arm = r_core + c["prop_gap_m"] + d / 2
    z_top = c["bay_m"] + core_l
    r_tip = arm + c["wing_tip_ext"] * d / 2
    foot_top = c["foot_bottom_m"] + c["foot_l_m"]
    zp = c.get("z_prop", z_top) if c["prop_z_m"] == "balance" else float(c["prop_z_m"])
    return {"r_core": r_core, "core_l": core_l, "z_floor": c["bay_m"], "z_top": z_top, "z_nose": z_top + c["nose_m"],
            "arm": arm, "tip_gap": math.sqrt(3) * arm - d, "z_prop": zp, "r_tip": r_tip,
            "panel_span": r_tip - r_core, "z_wing_le": zp - 0.20, "foot_top": foot_top,
            "leg_l": max(zp - 0.3 - (foot_top if c["foot_l_m"] else c["foot_bottom_m"]), 0.0),
            "across_m": 2 * (arm + d / 2), "span_m": 2 * r_tip}


def envelope(c: dict, n: int = 32) -> tuple[np.ndarray, np.ndarray]:
    """The sealed envelope as one revolved mesh."""
    return revolve(outline(c), n)


def outline(c: dict) -> list[tuple[float, float]]:
    """The envelope's outline (radius, height) from the tail up: the bay's rounded tail, the bay, a short flare to
    the core, the core, and the aeroshell's nose."""
    lay = layout(c)
    rb, rc, tf = c["bay_r_m"], lay["r_core"], c["tail_fair_m"]
    pts = [(0.0, 0.0)]
    for t in np.linspace(0, math.pi / 2, 6):
        pts.append((rb * (0.55 + 0.45 * math.sin(t)), tf * (1 - math.cos(t))))
    pts += [(rb, c["bay_m"] - 0.10), (rc, c["bay_m"] + 0.05), (rc, lay["z_top"])]
    for t in np.linspace(0, math.pi / 2, 9)[1:]:
        pts.append((rc * math.cos(t) if t < math.pi / 2 - 1e-9 else 0.0, lay["z_top"] + c["nose_m"] * math.sin(t)))
    return pts


def foot(c: dict, theta: float, n: int = 20) -> tuple[np.ndarray, np.ndarray]:
    """One float-foot: a vertical cylinder with rounded ends under its module's pod."""
    lay = layout(c)
    rf, lf, fb = c["foot_r_m"], c["foot_l_m"], c["foot_bottom_m"]
    e = min(rf, lf / 4)
    pts = [(0.0, fb)] + [(rf * math.sin(t), fb + e * (1 - math.cos(t))) for t in np.linspace(0, math.pi / 2, 5)[1:]]
    pts += [(rf * math.cos(t), fb + lf - e + e * math.sin(t)) for t in np.linspace(0, math.pi / 2, 5)[:-1]] + [(0.0, fb + lf)]
    v, f = revolve(pts, n)
    return v + np.array([lay["arm"] * math.cos(theta), lay["arm"] * math.sin(theta), 0.0]), f


def panel(c: dict, theta: float) -> tuple[np.ndarray, np.ndarray]:
    """One wing panel, from the core's side out under its prop, the chord along the axis."""
    lay = layout(c)
    u, zf = g.naca4(0.0, 0.4, c["wing_t_over_c"], 14)
    er = np.array([math.cos(theta), math.sin(theta), 0.0])
    et = np.array([-math.sin(theta), math.cos(theta), 0.0])
    ch = c["wing_chord_m"]
    rings = [r * er + np.outer(lay["z_wing_le"] - u * ch, [0, 0, 1]) + np.outer(zf * ch, et)
             for r in np.linspace(lay["r_core"], lay["r_tip"], 5)]
    return g.loft(rings)


def meshes(c: dict) -> list[tuple[str, tuple[np.ndarray, np.ndarray]]]:
    """Every sealed body: the envelope, the float-feet, and the wing panels unless they free-flood."""
    out = [("envelope", envelope(c))]
    if c["foot_r_m"] > 0 and c["foot_l_m"] > 0:
        out += [(f"foot {k + 1}", foot(c, th)) for k, th in enumerate(ANGLES)]
    if not c["wings_flood"]:
        out += [(f"wing {k + 1}", panel(c, th)) for k, th in enumerate(ANGLES)]
    return out


def hover_kw(c: dict, mass_kg: float) -> float:
    """Electrical power to hover out of ground effect: ideal induced power over the three discs, the figure of
    merit, the motors and controllers."""
    area = 3 * math.pi * c["prop_d_m"] ** 2 / 4
    t = mass_kg * G
    return t**1.5 / math.sqrt(2 * c["air_density_kgm3"] * area) / c["figure_of_merit"] / c["drive_eta"] / 1e3


def wing(c: dict) -> dict:
    """The Y's lifting area and span: two panels at the dihedral carry the lift (projected), the third is the fin."""
    lay = layout(c)
    k = math.cos(math.radians(c["y_dihedral_deg"]))
    a_panel = lay["panel_span"] * c["wing_chord_m"]
    return {"panel_m2": a_panel, "lift_m2": 2 * (a_panel + lay["r_core"] * c["wing_chord_m"]) * k,
            "span_m": 2 * lay["r_tip"] * k, "planform_m2": 3 * a_panel}


def cda(c: dict) -> float:
    """Parasite drag area in cruise, nose first: the core in its aeroshell, the panels, pods, legs and feet."""
    lay, w = layout(c), wing(c)
    feet = 3 * c["foot_cd"] * math.pi * c["foot_r_m"] ** 2
    return (c["body_cd"] * math.pi * lay["r_core"] ** 2 + c["wing_cd0"] * w["planform_m2"] + 3 * c["pod_cda_m2"]
            + 3 * c["leg_cd"] * lay["leg_l"] * c["leg_chord_m"] + feet)


def cruise(c: dict, mass_kg: float) -> dict:
    """Wing-borne cruise: the speed with the most distance per joule, but not under the stall margin; electrical
    power through the props' cruise efficiency and the drive."""
    w, rho, k = wing(c), c["air_density_kgm3"], cda(c)
    weight = mass_kg * G
    v_stall = math.sqrt(2 * weight / (rho * w["lift_m2"] * c["cl_max"]))

    def power(v: float) -> float:
        q = 0.5 * rho * v * v
        drag = q * k + weight**2 / (q * math.pi * c["oswald_e"] * w["span_m"] ** 2)
        return drag * v / c["prop_cruise_eta"] / c["drive_eta"] / 1e3

    vs = np.linspace(c["cruise_over_stall"] * v_stall, 4 * v_stall, 200)
    v = float(vs[np.argmin([power(x) / x for x in vs])])
    return {"v_stall_ms": v_stall, "v_ms": v, "kw": power(v), "cda_m2": k, "lift_m2": w["lift_m2"],
            "span_m": w["span_m"], "wing_loading_kgm2": mass_kg / w["lift_m2"],
            "ld": mass_kg * G / (power(v) * 1e3 * c["prop_cruise_eta"] * c["drive_eta"] / v)}


def trip_kwh(c: dict, p_hover: float, cr: dict, range_km: float | None = None) -> float:
    """Energy out of the pack for one trip and its reserve."""
    d = (c["range_km"] if range_km is None else range_km) * 1e3
    return p_hover * c["hover_min"] / 60 + cr["kw"] * (d / cr["v_ms"] + c["reserve_min"] * 60) / 3600


def parts(c: dict, mass_kg: float, batt_kg: float, p_peak: float) -> dict:
    """Every part's weight (kg) at a gross weight, a battery and an installed peak power (kW)."""
    lay, w = layout(c), wing(c)
    rc, L = lay["r_core"], lay["core_l"]
    r_mid = rc - c["wall_m"] / 2
    wall_a = 2 * math.pi * r_mid * L + 2 * math.pi * r_mid**2
    nose_a = math.pi * rc * math.hypot(rc, c["nose_m"])
    bay_a = 2 * math.pi * c["bay_r_m"] * c["bay_m"] + math.pi * c["bay_r_m"] ** 2
    rf, lf = c["foot_r_m"], c["foot_l_m"]
    feet = 3 * (math.pi * rf**2 * lf * c["foot_kgm3"] + 2 * math.pi * rf * lf * c["foot_skin_kgm2"]) if rf else 0.0
    return {
        "person": c["person_kg"], "mission load": c["mission_kg"], "container": c["container_kg"],
        "seat": c["seat_kg"], "hatch": c["hatch_kg"], "safety": c["safety_kg"],
        "core walls": wall_a * (c["wall_m"] * c["foam_kgm3"] + c["skin_kgm2"]),
        "core frame": c["frame_kg"],
        "nose": nose_a * c["nose_kgm2"],
        "bay": bay_a * c["bay_kgm2"],
        "battery": batt_kg,
        "motors": p_peak / c["motor_kw_kg"],
        "props": 3 * c["prop_ref_kg"] * (c["prop_d_m"] / c["prop_ref_m"]) ** 2,
        "pods": 3 * c["pod_kg"],
        "wings": w["planform_m2"] * c["wing_kgm2"],
        "legs": 3 * lay["leg_l"] * c["leg_kgm"],
        "float-feet": feet,
        "avionics": c["avionics_kg"] + c["avionics_frac"] * mass_kg,
    }


def heights(c: dict) -> dict:
    """Each part's height (z) up the axis."""
    lay = layout(c)
    zf, zt = lay["z_floor"], lay["z_top"]
    mid = zf + lay["core_l"] / 2
    pay = zf + c["wall_m"] + c["payload_z_m"]
    return {"person": pay, "mission load": pay, "container": pay, "seat": pay - 0.2, "hatch": mid + 0.3,
            "safety": pay, "core walls": mid, "core frame": zf + 0.4, "nose": zt + c["nose_m"] / 3,
            "bay": c["bay_m"] / 2, "battery": 0.45 * c["bay_m"], "motors": lay["z_prop"] - 0.15,
            "props": lay["z_prop"], "pods": lay["z_prop"] - 0.3, "wings": lay["z_wing_le"] - 0.42 * c["wing_chord_m"],
            "legs": lay["foot_top"] + lay["leg_l"] / 2, "float-feet": c["foot_bottom_m"] + c["foot_l_m"] / 2,
            "avionics": zf + 0.3}


# The parts carried by the three modules sit out on the arms; everything else is on the axis.
RADIAL = {"motors": "arm", "props": "arm", "pods": "arm", "legs": "arm", "float-feet": "arm", "wings": "wing"}


def neutral_point(c: dict) -> float:
    """The wing's aerodynamic centre up the axis (its quarter chord): taken as the neutral point. The core ahead of
    it and the legs and feet behind it are left out."""
    return layout(c)["z_wing_le"] - 0.25 * c["wing_chord_m"]


def balance(c: dict, ps: dict, mass_kg: float) -> float:
    """With prop_z_m = "balance", slide the module ring (props, wings, pods) up or down the core until the CG sits
    the static margin ahead of the wing's neutral point: what flight needs. Returns how far it moved."""
    if c["prop_z_m"] != "balance":
        return 0.0
    lay = layout(c)
    zg = sum(ps[k] * heights(c)[k] for k in ps) / mass_kg
    z = zg - c["static_margin"] * c["wing_chord_m"] + 0.25 * c["wing_chord_m"] + 0.20
    z = min(max(z, lay["z_floor"] + 0.5), lay["z_top"])
    moved = abs(z - lay["z_prop"])
    c["z_prop"] = lay["z_prop"] + 0.5 * (z - lay["z_prop"])
    return moved


def size(layout_name: str = "found", range_km: float | None = None, li: dict | None = None, **over) -> dict:
    """Close the crewed Trident's weight with its battery sized for the trip."""
    c = params(layout_name, li, **({"range_km": range_km} if range_km is not None else {}), **over)
    w, ok, ps = 600.0, False, {}
    for _ in range(300):
        p_h = hover_kw(c, w)
        p_peak = c["thrust_to_weight"] ** 1.5 * p_h
        cr = cruise(c, w)
        e = trip_kwh(c, p_h, cr)
        batt = max(e / c["usable"] * 1e3 / c["pack_wh_kg"], p_peak / c["pack_kw_kg"])
        ps = parts(c, w, batt, p_peak)
        w_new = sum(ps.values())
        moved = balance(c, ps, w_new)
        if w_new > 5000:
            break
        if abs(w_new - w) < 1e-4 and moved < 1e-5:
            ok = True
            break
        w = 0.5 * w + 0.5 * w_new
    return _result(c, w, ps, ok, "crewed")


def _result(c: dict, w: float, ps: dict, ok: bool, case: str) -> dict:
    lay = layout(c)
    p_h = hover_kw(c, w)
    cr = cruise(c, w)
    z = heights(c)
    zg = sum(ps[k] * z[k] for k in ps) / w
    batt = ps["battery"]
    return {"case": case, "ok": ok, "mass_kg": w, "parts": ps, "z": z, "zg_m": zg, "params": c, "layout": lay,
            "static_margin": (zg - neutral_point(c)) / c["wing_chord_m"],
            "hover_kw": p_h, "peak_kw": c["thrust_to_weight"] ** 1.5 * p_h, "cruise": cr,
            "disc_loading_kgm2": w / (3 * math.pi * c["prop_d_m"] ** 2 / 4),
            "downwash_ms": math.sqrt(w / (3 * math.pi * c["prop_d_m"] ** 2 / 4) * G / (2 * c["air_density_kgm3"])),
            "battery_kwh": batt * c["pack_wh_kg"] / 1e3, "trip_kwh": trip_kwh(c, p_h, cr),
            "bay_full": batt * c["pack_wh_kg"] / c["pack_wh_l"] / 1e3 / (math.pi * c["bay_r_m"] ** 2 * c["bay_m"]),
            "payload_kg": sum(ps[k] for k in ("person", "mission load")),
            "range_km": c["range_km"], "useful_kg": ps["person"] + ps["mission load"]}


def cargo(crewed: dict, range_km: float | None = None) -> dict:
    """The crewed airframe at the same gross weight with no one aboard: everything the person needed comes out and
    cargo goes in its place. At a shorter range, part of the battery's weight goes to cargo too."""
    c = dict(crewed["params"])
    w = crewed["mass_kg"]
    ps = {k: v for k, v in crewed["parts"].items() if k not in CREW_ONLY}
    rng = c["range_km"] if range_km is None else range_km
    if rng != c["range_km"]:
        c["range_km"] = rng
        p_h = hover_kw(c, w)
        e = trip_kwh(c, p_h, cruise(c, w))
        ps["battery"] = max(e / c["usable"] * 1e3 / c["pack_wh_kg"], c["thrust_to_weight"] ** 1.5 * p_h / c["pack_kw_kg"])
    cargo_kg = w - sum(ps.values())
    r = _result(c, w, {**{k: 0.0 for k in CREW_ONLY}, **ps}, cargo_kg > 0, "cargo")
    r["parts"]["cargo"] = cargo_kg
    r["z"]["cargo"] = r["z"]["container"]
    r["zg_m"] = sum(r["parts"][k] * r["z"][k] for k in r["parts"]) / w
    r["static_margin"] = (r["zg_m"] - neutral_point(c)) / c["wing_chord_m"]
    r["useful_kg"] = r["payload_kg"] = cargo_kg
    r["range_km"] = rng
    return r


def _cg(r: dict) -> np.ndarray:
    return np.array([0.0, 0.0, r["zg_m"]])


def gz(ms: list, cg: np.ndarray, need: float, phi: float, psi: float = 0.0) -> float:
    """The righting arm (m), knocked over by phi in a direction psi round the axis from a module (0 is onto a
    module, 60 degrees between two). Positive pushes it back toward upright."""
    R = rot_y(phi) @ rot_z(-psi)
    posed = [((v - cg) @ R.T, f) for v, f in ms]
    h = _level(posed, need)
    return math.nan if h is None else water._below(posed, h)[1]


def afloat(r: dict, step_deg: float = 10.0, fall_deg: tuple = (0.0, 30.0, 60.0)) -> dict:
    """Upright afloat (the waterline, the feet's share, the stiffness) and the righting curves to 180 degrees."""
    c = r["params"]
    named = meshes(c)
    ms = [m for _, m in named]
    cg = _cg(r)
    need = r["mass_kg"] / c["water_density_kgm3"]
    posed = [(v - cg, f) for v, f in ms]
    h = _level(posed, need)
    feet = [(v - cg, f) for n, (v, f) in named if n.startswith("foot")]
    share = water._below(feet, h)[0] / need if feet else 0.0
    gm = gz(ms, cg, need, math.radians(2)) / math.sin(math.radians(2))
    phis = np.arange(0, 180 + 1e-9, step_deg)
    curves = {float(p): [gz(ms, cg, need, math.radians(a), math.radians(p)) for a in phis] for p in fall_deg}
    inner = {p: [a for ph, a in zip(phis, arms) if 0 < ph < 180] for p, arms in curves.items()}
    rights = all(not math.isnan(a) and a > 0 for v in inner.values() for a in v)
    least = min(min(v) for v in inner.values())
    worst = min(curves, key=lambda p: min(inner[p]))
    vanish = next((float(a) for a, x in zip(phis[1:], curves[worst][1:]) if x <= 0), 180.0)
    return {"waterline_m": h + r["zg_m"], "sealed_m3": water._below(ms, 1e3)[0], "displaced_m3": need,
            "feet_share": share, "gm_m": gm, "phi_deg": phis.tolist(), "gz_m": {str(k): v for k, v in curves.items()},
            "rights": rights, "least_gz_m": least, "worst_fall_deg": worst, "vanishes_deg": vanish,
            "floor_dry_m": r["layout"]["z_floor"] - (h + r["zg_m"]),
            "props_clear_m": r["layout"]["z_prop"] - (h + r["zg_m"])}


def one(args) -> dict:
    kind, name, over, float_it = args
    over = dict(over)
    rng = over.pop("cargo_range_km", None)
    r = size(name, **over)
    if kind == "cargo":
        r = cargo(r, rng)
    if float_it and r["ok"]:
        r.update(afloat(r, 5.0, (0.0, 15.0, 30.0, 45.0, 60.0)) if float_it == "fine" else afloat(r))
    r["layout_name"] = name
    r["over"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in over.items()}
    if rng is not None:
        r["over"]["cargo_range_km"] = rng
    del r["params"]
    return r


def _map(jobs, workers: int):
    if workers == 1:
        return [one(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(one, jobs))


def run(workers: int = 0) -> dict:
    """The three layouts, crewed, floated; the found layout as cargo; and sweeps on the found layout: the props, the
    core's walls, the range, the feet and wings afloat, the wing's size and the crew's crouch."""
    li = inputs()
    sw = li["sweep"]
    jobs = [("crewed", n, {}, "fine") for n in li["layouts"]] + [("cargo", "found", {}, "fine")]
    n = len(jobs)
    jobs += [("crewed", "found", {"prop_d_m": d}, False) for d in sw["prop_d_m"]]
    jobs += [("crewed", "found", {"skin": s, "wall_m": t}, False) for s in sw["skin"] for t in sw["wall_m"]]
    jobs += [("crewed", "found", {"range_km": x}, False) for x in sw["range_km"]]
    jobs += [("cargo", "found", {"cargo_range_km": x}, False) for x in sw["range_km"]]
    jobs += [("crewed", "found", {"feet": tuple(f), "wings_flood": wf}, True) for f in sw["feet"] for wf in sw["wings_flood"]]
    jobs += [("crewed", "found", {"wing_tip_ext": e, "wing_chord_m": c}, True) for e in sw["wing_tip_ext"]
             for c in sw["wing_chord_m"]]
    jobs += [("crewed", "found", {"payload_z_m": z}, True) for z in sw["payload_z_m"]]
    rows = _map(jobs, workers)
    return {"layouts": rows[:n - 1], "cargo": rows[n - 1], "sweeps": rows[n:]}


def _sweep(res: dict, *keys: str, case: str = "crewed") -> list[dict]:
    return [r for r in res["sweeps"] if sorted(r["over"]) == sorted(keys) and r["case"] == case]


def _rights(r: dict) -> str:
    return "yes" if r["rights"] else f"no: past {r['vanishes_deg']:.0f}° ({r['worst_fall_deg']:.0f}° round)"


def _feet(f) -> str:
    return "legs with pads" if not f[0] else f"{f[0] * 100:.0f} x {f[1] * 100:.0f} cm"


def report(res: dict) -> str:
    li = inputs()
    mi, mo = li["mission"], li["module"]
    cr, ca = next(r for r in res["layouts"] if r["layout_name"] == "found"), res["cargo"]
    lay = cr["layout"]
    lines = ["# The Trident: a three-module tailsitter, by the numbers", "",
             "Three identical modules (an arm and wing panel, a motor pod and a big slow prop, a leg and its foot) round "
             "a foam-walled core sized to a 4x8 ft sheet, the power cells in a bay a metre long under it. It lifts off "
             "on its tail, flies on the three wings in a Y and lands back on its feet (`src/osprey/trident.py`, inputs "
             "in `design/trident.toml`, every number a REF stand-in).", "",
             f"Each is sized for one trip: {mi['hover_min']:g} min of hover (two lift-offs and landings), "
             f"{mi['range_km']:g} km of cruise, and {mi['reserve_min']:g} min of cruise in reserve. Knocked over by every "
             "angle to 180°, toward a module, between two and halfway; heights are up the axis from the bay's tail.", "",
             "## Three layouts", "",
             "| Layout | Max weight | CG | Props' plane | Static margin | Hover | Cruise | Waterline | GM | Props clear "
             "the water | Rights itself | Least GZ |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["layouts"]:
        lines.append(f"| {li['layouts'][r['layout_name']]['label']} | {r['mass_kg']:.0f} kg | {r['zg_m']:.2f} m | "
                     f"{r['layout']['z_prop']:.2f} m | {r['static_margin']:+.2f} | {r['hover_kw']:.0f} kW | "
                     f"{r['cruise']['kw']:.0f} kW at {r['cruise']['v_ms']:.0f} m/s | {r['waterline_m']:.2f} m | "
                     f"{r['gm_m']:.1f} m | {r['props_clear_m']:.2f} m | {_rights(r)} | {r['least_gz_m'] * 100:+.0f} cm |")
    lines += ["", "Static margin is in wing chords, the CG ahead of the wing's quarter chord; it must be positive to fly.", "",
              "## The found layout, crewed and as cargo", "",
              "| | Crewed | Cargo |", "|---|---|---|",
              f"| What it carries | {cr['useful_kg']:.0f} kg: a person and 100 kg | {ca['useful_kg']:.0f} kg of cargo |",
              f"| Max weight | {cr['mass_kg']:.0f} kg | {ca['mass_kg']:.0f} kg |",
              f"| Battery | {cr['battery_kwh']:.0f} kWh, {cr['parts']['battery']:.0f} kg, "
              f"{cr['bay_full'] * 100:.0f} % of the bay | same |",
              f"| Hover / installed | {cr['hover_kw']:.0f} / {cr['peak_kw']:.0f} kW | same |",
              f"| Disc loading, downwash | {cr['disc_loading_kgm2']:.0f} kg/m², {cr['downwash_ms']:.1f} m/s | same |",
              f"| Cruise | {cr['cruise']['v_ms']:.0f} m/s on {cr['cruise']['kw']:.0f} kW, L/D {cr['cruise']['ld']:.1f} "
              f"(stall {cr['cruise']['v_stall_ms']:.0f} m/s) | same |",
              f"| Static margin | {cr['static_margin']:+.2f} | {ca['static_margin']:+.2f} |",
              f"| Afloat: waterline, the core's floor above it | {cr['waterline_m']:.2f} m, {cr['floor_dry_m'] * 100:.0f} cm | "
              f"{ca['waterline_m']:.2f} m, {ca['floor_dry_m'] * 100:.0f} cm |",
              f"| GM, props clear the water | {cr['gm_m']:.1f} m, {cr['props_clear_m']:.2f} m | {ca['gm_m']:.1f} m, "
              f"{ca['props_clear_m']:.2f} m |",
              f"| Rights itself, least GZ | {_rights(cr)}, {cr['least_gz_m'] * 100:+.0f} cm | {_rights(ca)}, "
              f"{ca['least_gz_m'] * 100:+.0f} cm |", "",
              f"Across the prop tips it is {lay['across_m']:.1f} m; the wing tips are {lay['span_m']:.1f} m apart in plan; "
              f"it stands {lay['z_nose'] - mo['foot_bottom_m']:.1f} m tall on its feet. Each prop's tip clears the core "
              f"by {mo['prop_gap_m'] * 100:.0f} cm and the next tip by {lay['tip_gap']:.2f} m.", "",
              "## Where the weight goes", "", "| Part | Crewed | Cargo | Up the axis |", "|---|---|---|---|"]
    for k in cr["parts"]:
        lines.append(f"| {k} | {cr['parts'][k]:.0f} kg | {ca['parts'].get(k, 0):.0f} kg | {cr['z'][k]:.2f} m |")
    lines += [f"| cargo | | {ca['parts']['cargo']:.0f} kg | {ca['z']['cargo']:.2f} m |",
              f"| **total** | **{cr['mass_kg']:.0f} kg** | **{ca['mass_kg']:.0f} kg** | CG {cr['zg_m']:.2f} / "
              f"{ca['zg_m']:.2f} m |", "",
              "## The props", "", "| Prop | Across the tips | Max weight | Hover | Disc loading | Downwash | Cruise |",
              "|---|---|---|---|---|---|---|"]
    for r in _sweep(res, "prop_d_m"):
        lines.append(f"| {r['over']['prop_d_m']:.2f} m | {r['layout']['across_m']:.1f} m | {r['mass_kg']:.0f} kg | "
                     f"{r['hover_kw']:.0f} kW | {r['disc_loading_kgm2']:.0f} kg/m² | {r['downwash_ms']:.1f} m/s | "
                     f"{r['cruise']['kw']:.0f} kW at {r['cruise']['v_ms']:.0f} m/s |")
    lines += ["", "## The core's walls", "", "| Skin | Walls | Core walls weigh | Max weight | Battery |",
              "|---|---|---|---|---|"]
    for r in _sweep(res, "skin", "wall_m"):
        lines.append(f"| {li['skins'][r['over']['skin']]['label']} | {r['over']['wall_m'] * 100:.0f} cm | "
                     f"{r['parts']['core walls']:.0f} kg | {r['mass_kg']:.0f} kg | {r['battery_kwh']:.0f} kWh |")
    lines += ["", "## Range", "", "Crewed, sized for each range; and the crewed airframe (sized for "
              f"{mi['range_km']:g} km) flying cargo at each range, the battery it doesn't need going to cargo.", "",
              "| Range | Crewed: max weight | Battery | Cargo on the crewed airframe |", "|---|---|---|---|"]
    cargo_by = {r["over"]["cargo_range_km"]: r for r in _sweep(res, "cargo_range_km", case="cargo")}
    for r in _sweep(res, "range_km"):
        x = r["over"]["range_km"]
        k = cargo_by.get(x)
        lines.append(f"| {x:.0f} km | " + (f"{r['mass_kg']:.0f} kg | {r['battery_kwh']:.0f} kWh |" if r["ok"]
                                           else "doesn't close | |")
                     + (f" {k['useful_kg']:.0f} kg |" if k and k["ok"] else " doesn't fit |"))
    lines += ["", "## Afloat: the feet and the wings", "",
              "The found layout with each kind of foot, its wing panels buoyant (foam-cored) or free-flooding.", "",
              "| Feet (radius x length) | Wings | Max weight | Waterline | Feet carry | GM | Rights itself | Least GZ |",
              "|---|---|---|---|---|---|---|---|"]
    for r in _sweep(res, "feet", "wings_flood"):
        lines.append(f"| {_feet(r['over']['feet'])} | {'flooding' if r['over']['wings_flood'] else 'buoyant'} | "
                     f"{r['mass_kg']:.0f} kg | {r['waterline_m']:.2f} m | {r['feet_share'] * 100:.0f} % | "
                     f"{r['gm_m']:.1f} m | {_rights(r)} | {r['least_gz_m'] * 100:+.0f} cm |")
    lines += ["", "## The wing's size", "",
              "Tip extension is how far the panel runs past the motor pod, in prop radii.", "",
              "| Tip extension | Chord | Max weight | Cruise | Stall | Props' plane | GM | Rights itself | Least GZ |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in _sweep(res, "wing_tip_ext", "wing_chord_m"):
        o = r["over"]
        lines.append(f"| {o['wing_tip_ext']:.1f} | {o['wing_chord_m']:.1f} m | {r['mass_kg']:.0f} kg | "
                     f"{r['cruise']['kw']:.0f} kW at {r['cruise']['v_ms']:.0f} m/s | {r['cruise']['v_stall_ms']:.0f} m/s | "
                     f"{r['layout']['z_prop']:.2f} m | {r['gm_m']:.1f} m | {_rights(r)} | {r['least_gz_m'] * 100:+.0f} cm |")
    lines += ["", "## Crouching", "", "The container's centre above the core's floor: the person crouched low, or sitting "
              "up.", "", "| Container | CG | Props' plane | GM | Rights itself | Least GZ |", "|---|---|---|---|---|---|"]
    for r in _sweep(res, "payload_z_m"):
        lines.append(f"| {r['over']['payload_z_m']:.2f} m | {r['zg_m']:.2f} m | {r['layout']['z_prop']:.2f} m | "
                     f"{r['gm_m']:.1f} m | {_rights(r)} | {r['least_gz_m'] * 100:+.0f} cm |")
    return "\n".join(lines) + "\n"
