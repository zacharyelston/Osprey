"""The loiter craft: a larger bird for hours on station, where speed is not the
problem and time to observe is. Two layouts, side by side:

- liftbody: a blended lifting body, the battery inside its thick centre body,
  long outer panels and one pusher; it takes off from the water on a planing
  shoe and lands on it.
- tiltwing: a tandem tilt-wing, two high wings, the rear on a pylon, that turn
  up to hover, a prop a side on each, and nacelles whose tails behind the wing
  are floats; on the water it rests on its V-keel hull with the wings part way
  up and the front float tails dipped in as outriggers, lifts straight off,
  and turns the wings forward to fly.

Each is sized for each time on station and battery (design/recon/loiter.toml)
on the watch-passage job, an escort round the sailing boat, then flown through
it and checked on the water.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor

from osprey.params import _toml, ns
from osprey.recon.params import RECON

G = 9.81


def inputs():
    return ns(_toml(RECON / "loiter.toml"))


def load(airframe: str, hours: float, wh_per_kg: float | None = None, payload: str = "gimbal"):
    """The watch-passage job for hours on station, with the airframe and battery."""
    from osprey.recon.params import load as load_recon

    li = _toml(RECON / "loiter.toml")
    p = load_recon("escort-flanks", payload=payload, airframe=airframe, water=airframe == "liftbody")
    m = {**li["mission"], "escort_min": hours * 60.0, "task_time_max_s": hours * 3600.0 + 3600.0}
    p.mission = ns(m)
    sea = _toml(RECON.parent / "sea.toml")
    p.sea = ns({**sea["sea"][m["sea_state"]], "state": m["sea_state"]})
    if wh_per_kg:
        p.propulsion.battery_wh_per_kg = wh_per_kg
    return p


def label(airframe: str) -> str:
    return {"liftbody": "lifting body", "tiltwing": "tandem tilt-wing"}[airframe]


def one(args) -> dict:
    """One airframe sized for one time on station and battery, flown, and checked on the water."""
    import warnings

    from osprey.recon import flight, sizing, tailsitter, water

    warnings.filterwarnings("ignore")
    airframe, hours, wh = args
    p = load(airframe, hours, wh)
    out = {"airframe": airframe, "hours": hours, "wh_per_kg": wh, "label": label(airframe)}
    try:
        d, hist = sizing.size_and_fly(p)
    except Exception as e:                           # an infeasible case: say why and go on
        return out | {"ok": False, "why": f"{type(e).__name__}: {e}"}
    ac = flight.Aircraft.from_design(p, d)
    s = flight.summary(p, ac, flight.simulate(p, ac, t_max=hours * 3600 + 4 * 3600))
    out |= {"design": d, "history": hist, "flight": s,
            "ok": bool(d["converged"]) and s["outcome"] == "recovered" and bool(s["goal_met"])}
    m = d["mass_total_kg"]
    try:
        # The tilt-wing waits on the water on its keel, wings part way up, the float tails dipped in.
        out["afloat"] = water.afloat(p, {**d, "wing_tilt_deg": p.nacelle_floats.stance_tilt_deg}
                                     if tailsitter.vtol(p) else d, m)
    except Exception as e:                           # the design flies; say why it couldn't be floated
        out["afloat_why"] = f"{type(e).__name__}: {e}"
    if tailsitter.vtol(p):
        out["hover_w"] = tailsitter.hover_power(p, m * G)
        out["hover_wh"] = d["hover_energy_wh"]
    else:
        to = water.takeoff(p, d, m)
        out["takeoff"] = to
        out["impact_g"] = water.impact_factor(p, to["v_stall_ms"], m)
        out["sea_hs_m"], out["sea_state"] = water.sea_limit(p, water.hull_length(p, d))
    return out


def cases(li=None) -> list[tuple[str, float, float]]:
    sw = (li or inputs()).sweep
    return [(a, h, e) for a in sw.airframes for e in sw.battery_wh_per_kg for h in sw.hours]


def sweep(workers: int = 0) -> list[dict]:
    jobs = cases()
    if workers == 1:
        return [one(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(one, jobs))


def _unsettled(r: dict) -> bool:
    """Not a design that fails its constraints: OpenAeroStruct's coupled solve didn't settle on the way."""
    return any(k in r.get("why", "") for k in ("failed to converge", "solve_matrix"))


def _cell(r: dict) -> str:
    if not r.get("ok"):
        return "solver didn't settle" if _unsettled(r) else "doesn't close"
    d = r["design"]
    return f"{d['mass_total_kg']:.1f} kg, {_spans(d)}"


def _spans(d: dict) -> str:
    if "surfaces" in d:
        return " + ".join(f"{s['span_m']:.1f}" for s in d["surfaces"].values()) + " m"
    return f"{d['span_m']:.1f} m"


def _launch(r: dict) -> str:
    if "hover_w" in r:
        return f"lifts off on its props: {r['hover_w']:.0f} W to hover, {r['hover_wh']:.0f} Wh a sortie"
    to = r["takeoff"]
    run = f"{to['run_m']:.0f} m run" if to["gets_off"] else "doesn't get over the hump"
    return f"off the water, waves to {r['sea_hs_m'] * 100:.0f} cm ({r['sea_state']}): {run}; lands at {r['impact_g']:.1f} g"


def _afloat(r: dict) -> str:
    fl = r.get("afloat")
    if not fl:
        return r.get("afloat_why", "")
    prop = (f"props {fl['prop_clear_m'] * 100:.0f} cm clear" if fl["prop_clear_m"] >= 0
            else f"props {-fl['prop_clear_m'] * 100:.0f} cm in the water")
    if r["airframe"] == "tiltwing":                  # on its keel, wings part way up, the front float tails in
        prop = f"on its keel and front float tails, {prop}, the gimbal {fl['camera_clear_m'] * 100:.0f} cm clear"
    return f"{fl['reserve']:.1f}x reserve, trim {fl['trim_deg']:+.0f}°, {prop}"


def report(rows: list[dict]) -> str:
    """The sweep's sheet: what each airframe weighs for each time on station, and how each does it."""
    li = inputs()
    m = li.mission
    sw = li.sweep
    lines = ["# The loiter craft: hours on station", "",
             f"Speed is not the problem; time to observe is. The job: {m.label.lower()} ({m.escort_radius_m / 1e3:.0f} km "
             f"out, {m.escort_alt_m:.0f} m up, watching for a {m.watch_for}; the boat sails on at {m.boat_speed_kn:g} kn in "
             f"{m.wind_kn:g} kn of wind, {m.sea_state}). Each airframe is sized (OpenMDAO + OpenAeroStruct) for each time on "
             "station and battery, flown through it in the 3-DOF sim, and floated (`recon/loiter.py`). Both are moulded, "
             "carry the same gimbal, avionics and long-range link, and stow in panels to at most 4 m of span; a battery "
             f"of at most {li_battery_max():.0f} kg keeps the craft one or two people can handle from a boat.", "",
             "- **Lifting body** (`--airframe liftbody`): a blended wing body, the battery inside its thick centre body, "
             "one pusher; it takes off from the water on a planing shoe and lands on it.",
             "- **Tandem tilt-wing** (`--airframe tiltwing`): two high wings, the rear 1.2 m aft on a pylon 30 cm up, "
             "that turn up to hover; a prop a side on each, and nacelles whose tails behind the wing are floats. On the "
             "water it rests on its V-keel hull with the wings turned 55° up, the front float tails dipped in either "
             "side as outriggers; it lifts straight off and turns the wings forward to fly.", "",
             "## Take-off mass for each time on station", "",
             "| Hours on station | " + " | ".join(f"{label(a)}, {e:.0f} Wh/kg" for a in sw.airframes
                                                for e in sw.battery_wh_per_kg) + " |",
             "|---|" + "---|" * (len(sw.airframes) * len(sw.battery_wh_per_kg))]
    by = {(r["airframe"], r["hours"], r["wh_per_kg"]): r for r in rows}
    for h in sw.hours:
        lines.append(f"| {h:g} h | " + " | ".join(_cell(by[(a, h, e)]) for a in sw.airframes
                                                   for e in sw.battery_wh_per_kg) + " |")
    lines += ["", "\"Doesn't close\": no design meets every constraint with the battery inside its bounds. \"Solver didn't "
              "settle\": OpenAeroStruct's coupled wing-and-spar solve failed from every start, so the case is unknown, "
              "not infeasible.", ""]
    for e in sw.battery_wh_per_kg:
        lines += [f"## Each design, {e:.0f} Wh/kg", "",
                  "| | Mass | Battery | Spans | L/D | Loiter | Back aboard | Launch and recovery | Afloat |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for a in sw.airframes:
            for h in sw.hours:
                r = by[(a, h, e)]
                if not r.get("ok"):
                    continue
                d, s = r["design"], r["flight"]
                lines.append(f"| {label(a)}, {h:g} h | {d['mass_total_kg']:.1f} kg | {d['battery_kg']:.1f} kg "
                             f"({d['battery_kg'] / d['mass_total_kg'] * 100:.0f} %) | {_spans(d)} | {d['LD']:.1f} | "
                             f"{d['v_search_ms']:.1f} m/s, {d['power_w']:.0f} W | {s['energy_left_frac'] * 100:.0f} % left | "
                             f"{_launch(r)} | {_afloat(r)} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def li_battery_max() -> float:
    from osprey.recon.params import load as load_recon
    return load_recon("escort-flanks", airframe="tiltwing").propulsion.battery_bounds_kg[1]


def pair(rows: list[dict], wh: float) -> tuple[dict, dict] | None:
    """The longest time on station both airframes close at this battery: the pair to render side by side."""
    sw = inputs().sweep
    by = {(r["airframe"], r["hours"], r["wh_per_kg"]): r for r in rows}
    for h in sorted(sw.hours, reverse=True):
        rs = [by.get((a, h, wh)) for a in sw.airframes]
        if all(r and r.get("ok") for r in rs):
            return tuple(rs)
    return None


def stance(p, d: dict, mass_kg: float, tilt_deg: float = 3.0) -> dict:
    """Afloat on its keel, the wings at their stance tilt and the float tails dipped in either side: how far
    the wings' trailing edges, the props and the gimbal sit above the calm water, the share of the weight
    the hull carries, and the metacentric height each way, from the centre of buoyancy's shift when tipped."""
    import numpy as np

    from osprey.recon import geometry, tailsitter as ts, water

    dd = {**d, "wing_tilt_deg": p.nacelle_floats.stance_tilt_deg}
    parts = geometry.build(p, dd)
    sealed = [q for q in parts if q.kind in water.SEALED]
    cg = water.cg(p, dd)
    need = mass_kg / p.water.density_kgm3
    out = {}
    for axis, yaw in (("pitch", 0.0), ("roll", math.pi / 2)):
        R0 = ts._rot_z(yaw)
        ms0 = ts._posed(sealed, cg, R0)
        h0 = ts._level(ms0, need)
        x0 = water._below(ms0, h0)[1]
        t = math.radians(tilt_deg)
        ms1 = ts._posed(sealed, cg, ts._rot_y(t) @ R0)
        x1 = water._below(ms1, ts._level(ms1, need))[1]
        out[f"gm_{axis}_m"] = (x1 - x0) / math.sin(t)
        if axis == "pitch":
            h = h0
    low = lambda kinds: min(float((q.verts - cg)[:, 2].min()) for q in parts if q.kind in kinds) - h
    hull = [q for q in sealed if q.name == "pod"]
    hull_l = water._below(ts._posed(hull, cg, np.eye(3)), h)[0]
    return {**out, "draft_m": h - min(float((q.verts - cg)[:, 2].min()) for q in sealed),
            "hull_share": hull_l / need, "prop_clear_m": low(("disc",)),
            "wing_clear_m": low(("shell0", "shell1")), "camera_clear_m": low(water.CAMERAS)}


def one_floats(args) -> dict:
    """The tilt-wing re-sized with its float tails at one reserve and fineness, flown, and floated."""
    import warnings

    from osprey.recon import flight, sizing

    warnings.filterwarnings("ignore")
    reserve, fineness = args
    fl = inputs().floats
    p = load("tiltwing", fl.hours, fl.battery_wh_per_kg)
    p.nacelle_floats.reserve, p.nacelle_floats.fineness = reserve, fineness
    out = {"reserve": reserve, "fineness": fineness}
    try:
        d, _ = sizing.size_and_fly(p)
    except Exception as e:
        return out | {"ok": False, "why": f"{type(e).__name__}: {e}"}
    ac = flight.Aircraft.from_design(p, d)
    s = flight.summary(p, ac, flight.simulate(p, ac, t_max=fl.hours * 3600 + 4 * 3600))
    m = d["mass_total_kg"]
    return out | {"ok": bool(d["converged"]) and s["outcome"] == "recovered" and bool(s["goal_met"]),
                  "design": d, "flight": s, "floats": d["nacelle_floats"], "stance": stance(p, d, m)}


def float_sweep(workers: int = 0) -> list[dict]:
    fl = inputs().floats
    jobs = [(r, f) for f in fl.fineness for r in fl.reserve]
    if workers == 1:
        return [one_floats(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(one_floats, jobs))


def float_report(rows: list[dict]) -> str:
    fl = inputs().floats
    lines = ["# The tilt-wing's float tails: how small", "",
             f"The tandem tilt-wing re-sized for {fl.hours:g} h on station at {fl.battery_wh_per_kg:.0f} Wh/kg with its four "
             "float tails at each buoyancy reserve (all four's sealed volume over what the craft displaces) and "
             "fineness (length over diameter), flown, and floated in calm water on its keel with the wings at their "
             "stance tilt, the front float tails dipped in (`loiter.stance`). Keel: the share of the weight the hull "
             "carries. GM: the metacentric height, from the centre of buoyancy's shift when tipped 3°; positive is "
             "stable.", "",
             "| Reserve | Fineness | Float, each | Floats' mass, drag area | Mass | On station | Keel | Wings' trailing "
             "edges above the water | Props | Gimbal | GM pitch, roll |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["fineness"], r["reserve"])):
        if not r.get("ok"):
            lines.append(f"| {r['reserve']:g} | {r['fineness']:g} | doesn't close: {r.get('why', 'not recovered')} | | | | | | | | |")
            continue
        f, d, st = r["floats"], r["design"], r["stance"]
        lines.append(f"| {r['reserve']:g} | {r['fineness']:g} | {f['volume_l']:.1f} l, {f['length_m'] * 100:.0f} x "
                     f"{f['diameter_m'] * 100:.1f} cm | {f['kg']:.2f} kg, {f['cda_m2'] * 1e4:.0f} cm² | "
                     f"{d['mass_total_kg']:.2f} kg | {d['power_w']:.0f} W | {st['hull_share'] * 100:.0f} % | "
                     f"{st['wing_clear_m'] * 100:.0f} cm | {st['prop_clear_m'] * 100:.0f} cm | "
                     f"{st['camera_clear_m'] * 100:.0f} cm | "
                     f"{st['gm_pitch_m']:.2f}, {st['gm_roll_m']:.2f} m |")
    return "\n".join(lines) + "\n"
