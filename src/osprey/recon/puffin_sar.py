"""The spar Puffin's search-and-rescue build: the flight and mission budget behind docs/puffin/build-spec.md.

The SAR layout ([layouts.sar] in design/recon/puffin.toml) is the battery-on-a-screw spar carrying the SAR kit: an
EO/IR gimbal and an AIS-MOB beacon in the dome, a rescue tube slung under the wing. puffin.py floats it and knocks
it over, with the tube aboard and after it is dropped. This module adds first-order flight numbers:

- hover: momentum theory over the two props' discs with a figure of merit;
- cruise: a drag polar (the hull on its frontal area, the wing's profile drag, booms, strakes and nacelles, induced
  drag over the span), through the props' cruise efficiency and the motors';
- the missions: launch from the boat, fly to the datum, search for the mission's task time, then either land beside
  the person to mark them or fly back the same distance. Marking, it floats on what is left of the battery.

These are estimates to build from, not results: the hover rig and the first flights replace them.
"""

from __future__ import annotations

import math

from concurrent.futures import ProcessPoolExecutor

from osprey.params import _toml
from osprey.recon import puffin
from osprey.recon.params import RECON

G = 9.81


def inputs() -> dict:
    return puffin.inputs()["sar"]


def budget() -> dict:
    """The SAR build's mass, hover and cruise numbers, and the missions."""
    li = puffin.inputs()
    s = li["sar"]
    c = puffin.layout(s["layout"], li)
    _, masses, m, _ = puffin.build(c, c["float_x_m"])
    parts = {}
    for name, kg, _ in masses:
        parts[name] = parts.get(name, 0.0) + kg
    parts["drop pack"] = s["drop_pack_kg"]
    parts["wing"] -= s["drop_pack_kg"]
    rho = s["air_density_kgm3"]
    disc = 2 * math.pi * c["prop_diameter_m"] ** 2 / 4
    w = m * G
    hover_shaft = w**1.5 / math.sqrt(2 * rho * disc) / s["figure_of_merit"]
    hover_w = hover_shaft / s["motor_eta"]
    wing_area = c["span_m"] * c["chord_m"]
    v_stall = math.sqrt(2 * w / (rho * wing_area * s["cl_max"]))
    cda = (s["hull_cd"] * math.pi * c["diameter_m"] ** 2 / 4 + s["wing_cd0"] * wing_area
           + s["boom_strakes_cda_m2"] + s["nacelles_cda_m2"])

    def cruise_w(v: float, mass: float = m) -> float:
        q = 0.5 * rho * v * v
        drag = q * cda + (mass * G) ** 2 / (q * math.pi * s["oswald_e"] * c["span_m"] ** 2)
        return drag * v / s["prop_cruise_eta"] / s["motor_eta"]

    v = s["cruise_over_stall"] * v_stall
    p_cruise = cruise_w(v)
    pack_wh = c["battery_kg"] * s["cell_wh_kg"]
    usable = pack_wh * s["usable"]
    e_vtol = hover_w * (s["launch_s"] + s["landing_s"]) / 3600
    missions = []
    for name in s["missions"]:
        mi = _toml(RECON / "missions" / f"{name}.toml")["mission"]
        out_s = mi["datum_range_m"] / v
        search_s = mi["task_time_max_s"]
        e_mark = e_vtol + p_cruise * (out_s + search_s) / 3600
        e_back = e_mark + p_cruise * out_s / 3600
        left = usable - e_mark
        can_mark = (usable - e_vtol) / p_cruise * 3600 - out_s          # search it can afford, then marking
        can_back = (usable - e_vtol) / p_cruise * 3600 - 2 * out_s      # or flying back
        missions.append({"mission": name, "label": mi["label"], "range_km": mi["datum_range_m"] / 1e3,
                         "out_min": out_s / 60, "search_min": search_s / 60, "mark_wh": e_mark, "back_wh": e_back,
                         "left_wh": left, "afloat_h": max(left, 0) / s["afloat_w"],
                         "can_search_mark_min": can_mark / 60, "can_search_back_min": can_back / 60,
                         "mark_ok": e_mark <= usable, "back_ok": e_back <= usable})
    return {"layout": s["layout"], "mass_kg": m, "after_drop_kg": m - s["drop_pack_kg"], "parts": parts,
            "disc_loading_kgm2": m / disc, "hover_w": hover_w, "hover_per_motor_w": hover_w / 2,
            "motor_peak_w": s["thrust_to_weight"] ** 1.5 * hover_w / 2,
            "wing_loading_kgm2": m / wing_area, "v_stall_ms": v_stall, "v_cruise_ms": v, "cda_m2": cda,
            "cruise_w": p_cruise, "cruise_curve": [(vv, cruise_w(vv)) for vv in (v_stall * 1.1, v, v * 1.15, v * 1.3)],
            "pack_wh": pack_wh, "usable_wh": usable, "vtol_wh": e_vtol,
            "cruise_min": (usable - e_vtol) / p_cruise * 60, "range_km": (usable - e_vtol) / p_cruise * v * 3.6,
            "afloat_full_h": usable / s["afloat_w"], "missions": missions}


def floated() -> dict:
    """The SAR layout floated and knocked over with the drop pack aboard, and again after it is dropped."""
    s = inputs()
    li = puffin.inputs()
    wing = li["layouts"][s["layout"]]["wing_kg"]
    return {"aboard": puffin.one(s["layout"], li), "dropped": puffin.one(s["layout"], li, wing_kg=wing - s["drop_pack_kg"])}


def hover_w(mass_kg: float, prop_d_m: float, s: dict | None = None) -> float:
    s = s or inputs()
    disc = 2 * math.pi * prop_d_m**2 / 4
    return (mass_kg * G) ** 1.5 / math.sqrt(2 * s["air_density_kgm3"] * disc) / s["figure_of_merit"] / s["motor_eta"]


def _sweep_job(sweep_deg: float) -> dict:
    li = puffin.inputs()
    s, fs = li["sar"], li["sar"]["forward_sweep"]
    c = puffin.layout(s["layout"], li, sweep_deg=sweep_deg)
    shift = puffin.tip_shift(c)
    root = fs["mean_le_m"] - shift / 2                  # the mean chord stays put
    plane = root + shift + 0.12                         # the props' plane, up from the tail
    q = plane / c["length_m"]
    r_hull = puffin.spar_radius(c, q) if 0 <= q <= 1 else 0.0
    d_max = min(c["span_m"] - fs["prop_gap_m"], 2 * (c["span_m"] / 2 - r_hull - fs["prop_gap_m"]))
    d = min(d_max, fs["prop_max_m"])
    prop_kg = fs["prop_ref_kg"] * (d / fs["prop_ref_m"]) ** 2
    r = puffin.one(s["layout"], li, sweep_deg=sweep_deg, wing_le_m=root, prop_diameter_m=d, prop_kg=prop_kg)
    r.update(sweep_deg=sweep_deg, root_le_m=root, tip_shift_m=shift, prop_plane_m=plane, hull_r_at_props_m=r_hull,
             prop_d_m=d, prop_d_max_m=d_max, hover_w=hover_w(r["mass_kg"], d, s),
             hover_same_props_w=hover_w(r["mass_kg"], fs["prop_ref_m"], s),
             disc_loading_kgm2=r["mass_kg"] / (2 * math.pi * d * d / 4),
             props_clear_15_m=r["props_clear_m"] - d / 2 * math.sin(math.radians(15)))
    return r


def forward_sweep(workers: int = 0) -> list[dict]:
    """The SAR build with its wing swept forward, the mean chord fixed: the battery's travel, the props' clearance
    and size, and the righting."""
    degs = inputs()["forward_sweep"]["sweep_deg"]
    if workers == 1:
        return [_sweep_job(d) for d in degs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(_sweep_job, degs))


def fall(b: dict, sweep_rows: list[dict]) -> list[dict]:
    """Total power lost in flight: the speed it meets the water at, tail-first, for each way of slowing it."""
    li = puffin.inputs()
    s, f = li["sar"], li["sar"]["fall"]
    c = puffin.layout(s["layout"], li)
    rho, m = s["air_density_kgm3"], b["mass_kg"]
    big = max(sweep_rows, key=lambda r: r["prop_d_m"]) if sweep_rows else None

    def v_term(cda: float, mass: float = m) -> float:
        return math.sqrt(2 * mass * G / (rho * cda))

    body = f["hull_cd_tail_first"] * math.pi * c["diameter_m"] ** 2 / 4 + f["edge_cda_m2"]
    rows = [{"how": "nothing: it falls boom first", "v": v_term(body), "adds_kg": 0.0}]
    for label, d in (("the props windmilling", c["prop_diameter_m"]),
                     *((("the longest props windmilling", big["prop_d_m"]),) if big else ())):
        disc = 2 * math.pi * d * d / 4
        rows.append({"how": f"{label} ({d:.2f} m)", "v": v_term(body + f["windmill_cd"] * disc), "adds_kg": 0.0})
    for label, d in (("autorotating, collective pitch", c["prop_diameter_m"]),
                     *((("autorotating, the longest props", big["prop_d_m"]),) if big else ())):
        disc = 2 * math.pi * d * d / 4
        v_h = math.sqrt(m * G / (2 * rho * disc))
        omega = f["tip_speed_ms"] / (d / 2)
        fs = s["forward_sweep"]
        ke = 2 * 0.5 * (fs["prop_ref_kg"] * (d / fs["prop_ref_m"]) ** 2 * (d / 2) ** 2 / 3) * omega**2
        v = f["autorotation_vh"] * v_h
        v_flare = math.sqrt(max(v * v - 2 * ke / m, 0.0))
        rows.append({"how": f"{label} ({d:.2f} m), then a flare", "v": v, "v_flare": v_flare, "adds_kg": 0.0,
                     "note": "variable-pitch hubs on both props"})
    area = math.pi * f["chute_d_m"] ** 2 / 4
    rows.append({"how": f"a {f['chute_d_m']:g} m parachute", "v": v_term(body + f["chute_cd"] * area, m + f["chute_kg"]),
                 "adds_kg": f["chute_kg"]})
    for r in rows:
        r["drop_m"] = r["v"] ** 2 / (2 * G)
        if "v_flare" in r:
            r["drop_flare_m"] = r["v_flare"] ** 2 / (2 * G)
    return rows


def report(b: dict, f: dict, sw: list[dict] | None = None, fl: list[dict] | None = None) -> str:
    s = inputs()
    a, d = f["aboard"], f["dropped"]
    lines = ["# The spar Puffin, SAR build: mass, power and missions", "",
             "First-order numbers for the SAR layout (`recon/puffin_sar.py`, inputs in `design/recon/puffin.toml` "
             "[layouts.sar] and [sar]). Estimates to build from; the hover rig and first flights replace them.", "",
             "## Mass", "", "| Part | kg |", "|---|---|"]
    for k, v in b["parts"].items():
        lines.append(f"| {k} | {v:.2f} |")
    lines += [f"| **total** | **{b['mass_kg']:.2f}** |", "",
              "## Afloat and knocked over", "",
              "| | Mass | Under water | Props clear | Dome above water | Battery travel | GZ at 15° | Least GZ | GZ at 90° | Rights itself |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in (("drop pack aboard", a), ("after the drop", d)):
        lines.append(f"| {name} | {r['mass_kg']:.2f} kg | {r['waterline_m'] * 100:.0f} cm | {r['props_clear_m'] * 100:.0f} cm | "
                     f"{r['dome_above_m'] * 100:.0f} cm | {r['travel_m'] * 100:.0f} cm | {r['gz15_m'] * 100:+.1f} cm | "
                     f"{min(r['least_gz_belly_m'], r['least_gz_wingtip_m']) * 100:+.1f} cm | "
                     f"{r['gz_belly_m'][len(r['phi_deg']) // 2] * 100:+.0f} cm | {'yes' if r['rights'] else 'no'} |")
    lines += ["", "## Hover and cruise", "",
              f"- Disc loading {b['disc_loading_kgm2']:.1f} kg/m² on the two props; hover {b['hover_w']:.0f} W "
              f"electric, {b['hover_per_motor_w']:.0f} W a motor; at {s['thrust_to_weight']:g}× thrust to weight each "
              f"motor peaks near {b['motor_peak_w']:.0f} W.",
              f"- Wing loading {b['wing_loading_kgm2']:.1f} kg/m²: stalls at {b['v_stall_ms']:.1f} m/s, cruises at "
              f"{b['v_cruise_ms']:.1f} m/s ({b['v_cruise_ms'] * 1.944:.0f} kn) on {b['cruise_w']:.0f} W; drag area "
              f"{b['cda_m2'] * 1e4:.0f} cm².",
              f"- Pack {b['pack_wh']:.0f} Wh, {b['usable_wh']:.0f} Wh usable. Launch and landing in hover "
              f"{b['vtol_wh']:.0f} Wh. Then {b['cruise_min']:.0f} min of cruise, {b['range_km']:.0f} km.",
              f"- Afloat on a full pack, marking at {s['afloat_w']:g} W: {b['afloat_full_h']:.0f} h.", "",
              "| Airspeed | Electric power |", "|---|---|"]
    lines += [f"| {vv:.1f} m/s | {pp:.0f} W |" for vv, pp in b["cruise_curve"]]
    lines += ["", "## The missions", "",
              "Launch, fly to the datum and search, then land beside the person to mark them, or fly back the same "
              "way. Search time is what the usable pack affords after the hover and the transit; afloat is what is "
              "left for marking if it searches for the mission's whole task time.", "",
              "| Mission | Out | Task time | Search it affords, then marking | Then afloat | Search it affords, then flying back |",
              "|---|---|---|---|---|---|"]
    for mm in b["missions"]:
        lines.append(f"| {mm['label']} | {mm['range_km']:.0f} km, {mm['out_min']:.0f} min | {mm['search_min']:.0f} min | "
                     f"{mm['can_search_mark_min']:.0f} min | "
                     + (f"{mm['afloat_h']:.0f} h |" if mm["mark_ok"] else "none: the search runs the pack down |")
                     + f" {mm['can_search_back_min']:.0f} min |")
    if sw:
        lines += ["", "## Forward sweep", "",
                  "The wing swept forward with its mean chord where the SAR layout has it, so the neutral point stays "
                  "put: the tips and props go up the hull, the root down. Up the hull the props sit beside the narrowing "
                  "dome, so they can be longer (to the hull with a gap, or tip to tip, or the cap). Hover power with "
                  "those props, and with the original 0.76 m props for comparison. The SAR build itself flies 25° "
                  "and 1.0 m props, a little short of the longest.", "",
                  "| Sweep | Root LE | Props' plane | Longest props | Disc loading | Hover | Hover, 0.76 m props | Mass | "
                  "Battery travel | Props clear | Clear, rolled 15° | GZ at 15° | Least GZ | Rights itself |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in sw:
            lines.append(f"| {r['sweep_deg']:.0f}° | {r['root_le_m'] * 100:.0f} cm | {r['prop_plane_m'] * 100:.0f} cm | "
                         f"{r['prop_d_m']:.2f} m | {r['disc_loading_kgm2']:.1f} kg/m² | {r['hover_w']:.0f} W | "
                         f"{r['hover_same_props_w']:.0f} W | {r['mass_kg']:.2f} kg | {r['travel_m'] * 100:.0f} cm | "
                         f"{r['props_clear_m'] * 100:.0f} cm | {r['props_clear_15_m'] * 100:.0f} cm | "
                         f"{r['gz15_m'] * 100:+.1f} cm | {min(r['least_gz_belly_m'], r['least_gz_wingtip_m']) * 100:+.1f} cm | "
                         f"{'yes' if r['rights'] else 'no'} |")
    if fl:
        lines += ["", "## Power lost in flight", "",
                  "With the screw unpowered the battery runs down the boom and the craft pitches up to tail-first. With "
                  "the motors still running that is only its hover attitude, and it lands. With all power gone it falls "
                  "boom first: the speed it meets the water at, and the drop height that equals.", "",
                  "| Slowed by | Hits the water at | Like a drop of | Adds |", "|---|---|---|---|"]
        for r in fl:
            v = f"{r['v']:.1f} m/s" + (f", {r['v_flare']:.1f} m/s after the flare" if "v_flare" in r else "")
            h = f"{r['drop_m']:.1f} m" + (f", {r['drop_flare_m']:.1f} m" if "drop_flare_m" in r else "")
            add = r.get("note") or (f"{r['adds_kg']:.1f} kg" if r["adds_kg"] else "nothing")
            lines.append(f"| {r['how']} | {v} | {h} | {add} |")
    return "\n".join(lines) + "\n"
