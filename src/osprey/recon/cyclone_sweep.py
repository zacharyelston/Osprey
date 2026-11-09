"""How many arms, and where A goes on them: the Cyclone re-sized for every combination of three to six arms,
A at the tip, three-quarters or half-way out, on every arm or every other, and what each does in every mode.

The arms are mode 4's wing as well as the rotor's blades (cyclone.layout): three fly as a dihedral wing and a
fin; four as an X; five as four lifting and a fin; six as four lifting, 30 degrees either side of level, with
a fin up and a fin down. The wing's area is the lifting arms', so with more arms each is narrower. A further
in goes round slower: its nacelles cost less to whirl, but it pushes harder for the same power, and it has
less leverage for mode 1's roll and pitch and mode 4's yaw.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor

from osprey.params import ns
from osprey.recon import cyclone

G = 9.81
ARMS = (3, 4, 5, 6)
STATIONS = (1.0, 0.75, 0.5)


def cases() -> list[tuple[int, float, int]]:
    return [(n, s, e) for n in ARMS for e in (1, 2) if n % e == 0 and n // e >= 3 for s in STATIONS]


def label(arms: int, station: float, every: int) -> str:
    where = {1.0: "at the tips", 0.75: "¾ out", 0.5: "half-way"}[station]
    return f"{arms} arms, A {where}" + ("" if every == 1 else ", every other arm")


def one(args) -> dict:
    """One combination re-sized for all seven jobs, and what it does."""
    from osprey.recon import cyclone_dynamics, cyclone_modes, cyclone_water
    from osprey.recon.params import load

    d, payload, (arms, station, every) = args
    cy = ns({**vars(cyclone.inputs()), "arms": arms, "a_station": station, "a_every": every})
    out = {"arms": arms, "a_station": station, "a_every": every, "label": label(arms, station, every),
           "layout": cyclone.layout(cy)}
    try:
        rs = cyclone.resize(d, payload, cy)
    except cyclone_modes.Refused as e:
        return out | {"ok": False, "why": f"the modes' manager refuses a move: {e}"}
    if rs is None:
        return out | {"ok": False, "why": "no battery closes all seven jobs"}
    p = load("sar-offshore", payload=payload)
    dc = rs["design"]
    m = cyclone.mass(p, dc, cy)
    g = cyclone.geometry(p, dc, cy)
    h = cyclone.rotor(p, dc, cy, m["mass_kg"])
    dy, md = cyclone_dynamics.inputs(), cyclone_modes.inputs()
    ab = cyclone.abilities(p, dc, cy, m, d)
    w = cyclone_dynamics.wind(p, dc, cy, m)
    sp = cyclone_dynamics.spin(p, dc, cy, m)
    au = cyclone_dynamics.authority(p, dc, cy, dy, m)
    fl = cyclone_water.afloat(p, dc, cy, cyclone_water.inputs(), m)
    mo = cyclone_modes.assess(p, dc, cy, md)["A"]
    # One A out in mode 1: the rest at the burst against the weight.
    rg = cyclone_dynamics.rings(p, dc, cy, m)
    r_a, n_a, p_a = rg[0]
    one_out = (n_a - 1) * cyclone_dynamics.a_max(cy, p_a, 0.0) / (m["mass_kg"] * G)
    f4 = au["four"]["search"]
    return out | {
        "ok": rs["ok"], "jobs": sum(r["ok"] for r in rs["jobs"].values()), "mass_kg": m["mass_kg"],
        "battery_kg": dc["battery_kg"], "chord_m": g["chord_m"], "R_m": g["R_m"], "a_r_m": r_a, "a_count": n_a,
        "arm_kg": g["arm_kg"], "motor_kg": m["motor_kg"], "rated_w": m["motor_peak_w"], "solidity": g["solidity"],
        "hover_w": h["p_shaft_w"], "rpm": h["rpm"], "prop_efficiency": h["prop_efficiency"],
        "nacelle_w": h["p_nacelle_w"], "figure_of_merit": h["figure_of_merit"],
        "wind2_ms": w["two_max_ms"], "wind2_limit": w["two_limit"], "wind1_ms": w["one_max_ms"],
        "build_s": sp["build"]["t_s"], "die_s": sp["die"]["t_s"], "inertia_kgm2": au["inertia_kgm2"],
        "off_wing_wh": cyclone.hover_j(p, dc, cy, m) / 3600,
        "tilt20_s": au["one"]["tilt20_s"], "yaw1_nm": au["one"]["yaw_nm"], "tilt2_dps": au["two"]["tilt_dps"],
        "one_out_tw": one_out,
        "lift_frac": cyclone.layout(cy)["lift_frac"], "span_m": cyclone._wing(p, dc, cy)["span_m"],
        "v_stall_ms": ab["flight"]["v_stall_ms"], "ld_max": ab["flight"]["ld_max"],
        "endurance_h": ab["flight"]["endurance_h"], "range_km": ab["flight"]["range_km"],
        "pitch4_nm": min(f4["pitch_up_nm"], f4["pitch_down_nm"]), "trim_below": f4["fin_share"],
        "yaw4_nm": f4["yaw_nm"], "roll4_dps": f4["roll_dps_5deg"], "bank30_s": f4["bank30_s"],
        "prop_height_m": fl["prop_height_m"], "camera_height_m": fl["camera_height_m"], "gm_m": fl["gm_m"],
        "draft_m": fl["draft_m"], "travel_range_km": mo["travel"]["range_km"], "h34_m": mo["h34_m"],
        "launch_s": mo["launch"]["time_s"], "recover_s": mo["recover"]["time_s"]}


def sweep(d: dict, payload: str, workers: int = 0) -> list[dict]:
    jobs = [(d, payload, c) for c in cases()]
    if workers == 1:
        return [one(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(one, jobs))


def report(rows: list[dict], payload: str) -> str:
    """The sweep's sheet: every combination, best first by the energy a sortie spends off the wing."""
    ok = [r for r in rows if r.get("ok")]
    base = next(r for r in rows if r["arms"] == 3 and r["a_station"] == 1.0 and r["a_every"] == 1)
    lines = [f"# The Cyclone's arms and A: {payload}", "",
             "Every combination of three to six arms and A at the tip, three-quarters or half-way out, on every arm or "
             "every other, each re-sized for all seven jobs (`recon/cyclone_sweep.py`). Mode 4's wing is the lifting "
             "arms (`cyclone.layout`): 3, a 30° dihedral wing and a fin; 4, an X; 5, four lifting and a fin; 6, four "
             "lifting 30° either side of level, a fin up and one down. The design today is the first row of the "
             "second table.", "",
             "## Every combination", "",
             "| | Mass | A rated | Spinning hover | Mode 2 wind | Mode 1 wind | Pitch-over from | Launch + recovery | "
             "Wing-borne range | L/D |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(ok, key=lambda r: r["off_wing_wh"]):
        lines.append(f"| {r['label']} | {r['mass_kg']:.2f} kg | {r['rated_w']:.0f} W | {r['hover_w']:.0f} W | "
                     f"{r['wind2_ms']:.2f} m/s | {r['wind1_ms']:.1f} m/s | {r['h34_m']:.0f} m | {r['off_wing_wh']:.1f} Wh | "
                     f"{r['range_km']:.0f} km | {r['ld_max']:.1f} |")
    for r in rows:
        if not r.get("ok"):
            lines.append(f"| {r['label']} | doesn't fly: {r['why']} | | | | | | | | |")
    lines += ["", "## Mode by mode", "",
              "| | Chord | A's radius | Spin builds, dies | Mode 1: 20° tilt, one A out | Mode 2: disc tilt | "
              "Mode 4: pitch, yaw, 30° bank | Afloat: props up, camera |", "|---|---|---|---|---|---|---|---|"]
    for r in [base] + sorted([r for r in ok if r is not base], key=lambda r: (r["arms"], r["a_every"], -r["a_station"])):
        lines.append(f"| {r['label']} | {r['chord_m'] * 100:.1f} cm | {r['a_r_m']:.2f} m | {r['build_s']:.2f} s, "
                     f"{r['die_s']:.2f} s | {r['tilt20_s']:.2f} s, {r['one_out_tw']:.2f} × weight | "
                     f"{r['tilt2_dps']:.0f}°/s | {r['pitch4_nm']:.2f} N m, {r['yaw4_nm']:.2f} N m, {r['bank30_s']:.2f} s | "
                     f"{r['prop_height_m'] * 100:.0f} cm, {r['camera_height_m'] * 100:+.0f} cm |")
    lines += ["", "A is rated for the larger of the spinning peak and its share of mode 1's. The pitch-over from 3 to "
              "4 runs A at its burst, tilted forward only as far as the height holds, so none loses height in it: "
              "each starts it from the safety height.", "", "Mode 2 wind: the strongest it holds station in spinning, until the retreating arm stalls, B's "
              "swing runs out, or A's rating. One A out in mode 1: the rest at their burst against the weight; above "
              "1 it can still climb. Mode 4 pitch: the least of the two ways A's thrust can be shifted between the "
              "motors above and below at the search speed, trim taken off.", ""]
    return "\n".join(lines) + "\n"
