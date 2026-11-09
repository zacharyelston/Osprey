"""The loiter craft: a larger bird for hours on station, where speed is not the
problem and time to observe is. Two layouts, side by side:

- liftbody: a blended lifting body, the battery inside its thick centre body,
  long outer panels and one pusher; it takes off from the water on a planing
  shoe and lands on it.
- tandem: a tandem tilt-body after the Opener BlackFly, a jellybean hull and
  a front and a rear wing with four props on each; it lifts off on its props
  and lands on its belly.

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
    return {"liftbody": "lifting body", "tandem": "tandem tilt-body"}[airframe]


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
        out["afloat"] = water.afloat(p, d, m)
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


def _cell(r: dict) -> str:
    if not r.get("ok"):
        return "doesn't close"
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
             "- **Tandem tilt-body** (`--airframe tandem`): flown like the Opener BlackFly. Staggered wings, the front low "
             "and the rear high and 1 m aft, four props on each, a slim pod between; it lifts off by pitching up onto "
             "its props and lands on eight nacelle floats.", "",
             "## Take-off mass for each time on station", "",
             "| Hours on station | " + " | ".join(f"{label(a)}, {e:.0f} Wh/kg" for a in sw.airframes
                                                for e in sw.battery_wh_per_kg) + " |",
             "|---|" + "---|" * (len(sw.airframes) * len(sw.battery_wh_per_kg))]
    by = {(r["airframe"], r["hours"], r["wh_per_kg"]): r for r in rows}
    for h in sw.hours:
        lines.append(f"| {h:g} h | " + " | ".join(_cell(by[(a, h, e)]) for a in sw.airframes
                                                   for e in sw.battery_wh_per_kg) + " |")
    lines += ["", "\"Doesn't close\": no design meets every constraint with the battery inside its bounds.", ""]
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
    return load_recon("escort-flanks", airframe="tandem").propulsion.battery_bounds_kg[1]


def pair(rows: list[dict], wh: float) -> tuple[dict, dict] | None:
    """The longest time on station both airframes close at this battery: the pair to render side by side."""
    sw = inputs().sweep
    by = {(r["airframe"], r["hours"], r["wh_per_kg"]): r for r in rows}
    for h in sorted(sw.hours, reverse=True):
        rs = [by.get((a, h, wh)) for a in sw.airframes]
        if all(r and r.get("ok") for r in rs):
            return tuple(rs)
    return None
