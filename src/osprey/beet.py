"""The Beet: a flying buoy. A circular RIB with a 360-degree glass observation cabin, its mass low, and a coaxial
rotor on a mast at the top. It is a boat first: it floats, and makes powered hops to height before landing back on
the water. The question here is what the numbers look like (design/beet.toml).

- Sizing: momentum theory for the coaxial rotor (checked against an R44), weight fractions, and one hop (climb to
  150 m, look for five minutes, come down), closed by iterating the weight. Four ways to power it: a battery that
  flies the hop with a small genset recharging it afloat; a piston or turbine genset that carries the hover with
  the battery for peaks and a landing; and a plain turboshaft, the conventional baseline.
- Afloat: the hull, cabin, mast and any keel pod revolved into one sealed mesh, floated at its weight and knocked
  over by every angle to 180 degrees. GZ, the righting arm, is the horizontal distance from the centre of gravity to
  the centre of buoyancy; above zero all the way round, it always comes back upright.

Body frame: z up the axis from the keel (the bottom of the hull, not the keel pod), x and y across; metres.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from osprey.params import DESIGN, _toml
from osprey.recon import water
from osprey.recon.puffin import _level, rot_y

G = 9.81


def inputs() -> dict:
    return _toml(DESIGN / "beet.toml")


def case(name: str, li: dict | None = None, **over) -> dict:
    """One case's parameters: [craft], [geometry], [hop], the case on top, then any overrides."""
    li = li or inputs()
    c = {**li["craft"], **li["geometry"], **li["hop"], "crewed": True, **li["cases"][name], **over}
    c["name"] = name
    return c


def cabin(c: dict) -> dict:
    """The cabin's radii at floor and roof, the roof's height and the hull's radius. Crewed, the seats face out
    round a central column and the glass leans in to the roof: a cone frustum."""
    if "cabin" in c:
        cab = dict(c["cabin"])
        return {"r_base": cab["r_base"], "r_top": cab["r_top"], "roof": cab["roof"], "r_hull": c["hull_r_m"]}
    r_seat = max(c["seat_ring_min_m"], c["people"] * c["seat_pitch_m"] / (2 * math.pi))
    r_base = r_seat + c["legroom_m"]
    return {"r_base": r_base, "r_top": max(c["cabin_top_min_m"], c["cabin_top_ratio"] * r_base), "roof": c["roof_m"],
            "r_hull": r_base + c["tube_d_m"] + 0.10}


def hover_kw(c: dict, mass_kg: float) -> float:
    """Shaft power to hover out of ground effect: ideal induced power over the disc, the coaxial factor, the
    figure of merit."""
    area = mass_kg / c["disc_loading_kgm2"]
    t = mass_kg * G
    return c["k_coax"] * t**1.5 / math.sqrt(2 * c["air_density_kgm3"] * area) / c["figure_of_merit"] / 1e3


def r44(li: dict | None = None) -> dict:
    """The model's hover power for an R44 at max weight, single rotor plus its tail rotor, against its ratings."""
    li = li or inputs()
    r, c = li["r44"], li["craft"]
    area = math.pi * r["rotor_m"] ** 2 / 4
    t = r["mass_kg"] * G
    p = t**1.5 / math.sqrt(2 * c["air_density_kgm3"] * area) / c["figure_of_merit"] / 1e3 * r["tail_rotor"] / 0.97
    return {"hover_kw": p, "mcp_kw": r["mcp_kw"], "takeoff_kw": r["takeoff_kw"]}


def hop(c: dict, mass_kg: float, p_hover: float) -> tuple[float, float]:
    """Energy (kWh, at the hover power's point in the chain) for one hop, and its length (s)."""
    t_up, t_down = c["height_m"] / c["climb_ms"], c["height_m"] / c["descend_ms"]
    p_climb = p_hover + mass_kg * G * c["climb_ms"] / 2 / 1e3     # half the climb power: the induced flow eases
    t_view = c["view_min"] * 60 + c["on_water_s"]
    e = (p_climb * t_up + p_hover * t_view + c["descent_power"] * p_hover * t_down) / 3600
    return e, t_up + t_down + t_view


def size(name: str, power: str, li: dict | None = None, **over) -> dict:
    """Close the weight for one case and one way of powering it."""
    li = li or inputs()
    pw = {**li["power"][power], **{k: v for k, v in over.items() if k in li["power"][power]}}
    c = case(name, li, **{k: v for k, v in over.items() if k not in pw})
    cab = cabin(c)
    payload = c.get("payload_kg", c["people"] * c["person_kg"])
    a_plan = math.pi * cab["r_hull"] ** 2
    h = cab["roof"] - c["floor_m"]
    slant = math.hypot(h, cab["r_base"] - cab["r_top"])
    a_dome = math.pi * (cab["r_base"] + cab["r_top"]) * slant + math.pi * cab["r_top"] ** 2
    if not c["crewed"]:
        a_dome *= 0.4                                  # a sensor fairing, not glazing
    w, ok, parts = 3.0 * payload + 300.0, False, {}
    for _ in range(400):
        p_shaft = hover_kw(c, w)
        e_hop_shaft, t_hop = hop(c, w, p_shaft)
        gen = batt_kwh = m_batt = 0.0
        if power == "turbine":
            p_h = p_shaft / pw["eta_drive"]            # at the engine
            p_inst = c["power_margin"] * p_h
            fuel = p_h * pw["hover_fuel_min"] / 60 * pw["sfc_kg_kwh"]
            e_hop = e_hop_shaft / pw["eta_drive"]
            m_drive = p_inst / pw["drive_kw_per_kg"]
        else:
            p_h = p_shaft / pw["eta_drive"]            # electric, at the bus
            p_inst = c["power_margin"] * p_h
            e_hop = e_hop_shaft / pw["eta_drive"]
            gen = pw["genset_of_hover"] * p_h
            if pw["genset_of_hover"] < 1:              # the battery flies the hop
                batt_kwh = e_hop * pw["reserve"] / pw["batt_eta"]
                p_batt = p_inst
                fuel = pw["recharges"] * batt_kwh / pw["batt_eta"] * pw["sfc_kg_kwh"]
            else:                                      # the genset carries the hover
                p_batt = p_inst - gen
                batt_kwh = ((p_inst - gen) * pw["peak_min"] / 60 + p_h * pw["land_s"] / 3600) \
                    * pw["reserve"] / pw["batt_eta"]
                fuel = gen * pw["hover_fuel_min"] / 60 * pw["sfc_kg_kwh"]
            m_batt = max(batt_kwh * 1e3 / pw["batt_wh_kg"], p_batt / pw["batt_kw_kg"])
            m_drive = p_inst / pw["drive_kw_per_kg"]
        parts = {
            "payload": payload,
            "rotors": c["rotor_frac"] * w,
            "mast and controls": c["mast_frac"] * w,
            "drive": m_drive,
            "hull": c["hull_kgm2"] * a_plan,
            "cabin glass": c["dome_kgm2"] * a_dome,
            "interior": c["seat_kg"] * c["people"] + c["interior_kg"] if c["crewed"] else 5.0,
            "systems": c["systems_kg"] + c["systems_frac"] * w,
            "boat drive": c["boat_drive_kg"] if c["crewed"] else 5.0,
            "safety": c["safety_kg"] if c["crewed"] else 0.0,
            "genset": gen / pw["gen_kw_per_kg"] if gen else 0.0,
            "fuel": fuel * 1.10,                       # and its tank
            "battery": m_batt,
        }
        w_new = sum(parts.values())
        if w_new > 25 * payload + 5000:                # each kilogram of battery needs more battery to lift it
            break
        if abs(w_new - w) < 1e-3:
            ok = True
            break
        w = 0.5 * w + 0.5 * w_new
    d_rotor = math.sqrt(4 * w / c["disc_loading_kgm2"] / math.pi)
    z_rot = cab["roof"] + max(c["rotor_gap_min_m"], c["rotor_gap_frac"] * d_rotor)
    pod = c["keel_pod_m"]
    low = -pod / 2 if pod else None
    z = {"payload": c["floor_m"] + 0.55 if c["crewed"] else cab["roof"],
         "rotors": z_rot + c["coax_spacing_frac"] * d_rotor / 2,
         "mast and controls": (cab["roof"] + z_rot) / 2 + 0.3,
         "drive": cab["roof"] + 0.2 if power == "turbine" else z_rot - 0.2,
         "hull": 0.15, "cabin glass": c["floor_m"] + 0.45 * (cab["roof"] - c["floor_m"]),
         "interior": c["floor_m"] + 0.3, "systems": 0.4, "boat drive": 0.05, "safety": 0.4,
         "genset": low if low is not None else 0.20, "fuel": low if low is not None else 0.12,
         "battery": low if low is not None else 0.10}
    zg = sum(parts[k] * z[k] for k in parts) / w
    return {"case": name, "label": c["label"], "power": power, "power_label": pw["label"], "ok": ok,
            "people": c["people"], "mass_kg": w, "parts": parts, "z": z, "zg_m": zg,
            "rotor_m": d_rotor, "rotor_z_m": z_rot, "top_m": z_rot + c["coax_spacing_frac"] * d_rotor + 0.15,
            "hover_kw": p_shaft, "installed_kw": c["power_margin"] * p_shaft, "genset_kw": gen,
            "battery_kwh": batt_kwh, "hop_kwh": e_hop, "hop_min": t_hop / 60, "fuel_kg": fuel,
            "downwash_ms": math.sqrt(c["disc_loading_kgm2"] * G / (2 * c["air_density_kgm3"])),
            "disc_loading_kgm2": c["disc_loading_kgm2"], "view_min": c["view_min"],
            "hull_m": 2 * cab["r_hull"], "cabin": cab, "keel_pod_m": pod,
            "geometry": {k: c[k] for k in ("floor_m", "tube_d_m", "tube_bottom_m", "mast_r_m", "keel_pod_m",
                                            "keel_pod_r_m", "cabin_top_ratio")},
            "water_density_kgm3": c["water_density_kgm3"]}


def profile(r: dict) -> list[tuple[float, float]]:
    """The sealed body's outline (radius, height), from the bottom of the axis round the outside to the top: keel
    pod, flat bottom, the RIB tube, the deck, the cabin's glass, the roof and the mast to the lower rotor."""
    g, cab = r["geometry"], r["cabin"]
    tr = g["tube_d_m"] / 2
    c_r = cab["r_hull"] - tr
    zb = g["tube_bottom_m"]
    pts = []
    if g["keel_pod_m"]:
        pr = g["keel_pod_r_m"]
        pts += [(0.0, -g["keel_pod_m"]), (pr, -g["keel_pod_m"]), (pr, 0.0)]
    else:
        pts.append((0.0, 0.0))
    pts.append((max(c_r - tr, (g["keel_pod_r_m"] if g["keel_pod_m"] else 0.0) + 0.02), 0.0))
    for th in np.linspace(-math.pi / 2, math.pi / 2, 13):
        pts.append((c_r + tr * math.cos(th), zb + tr + tr * math.sin(th)))
    deck = zb + 2 * tr
    pts += [(cab["r_base"], deck + 1e-3), (cab["r_top"], cab["roof"]), (g["mast_r_m"], cab["roof"] + 1e-3),
            (g["mast_r_m"], r["rotor_z_m"] - 0.1), (0.0, r["rotor_z_m"] - 0.1)]
    return pts


def revolve(pts: list[tuple[float, float]], n: int = 48) -> tuple[np.ndarray, np.ndarray]:
    """Revolve an outline about z into a closed mesh, every face wound outward: walking up the outline, outward is
    to its right."""
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    v = np.concatenate([np.stack([rr * np.cos(th), rr * np.sin(th), np.full(n, zz)], 1) for rr, zz in pts])
    f = []
    for i in range(len(pts) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            k = (j + 1) % n
            f += [(a + j, a + k, b + k), (a + j, b + k, b + j)]
    return v, np.array(f, int)


def gz(mesh, cg: np.ndarray, need: float, phi: float) -> float:
    """The righting arm (m), heeled by phi from upright. Positive pushes it back toward upright."""
    v, f = mesh
    ms = [((v - cg) @ rot_y(phi).T, f)]
    h = _level(ms, need)
    return math.nan if h is None else water._below(ms, h)[1]


def afloat(r: dict, step_deg: float = 10.0) -> dict:
    """Upright afloat (the waterline, the stiffness, the roll period) and the righting curve to 180 degrees."""
    mesh = revolve(profile(r))
    cg = np.array([0.0, 0.0, r["zg_m"]])
    need = r["mass_kg"] / r["water_density_kgm3"]
    v, f = mesh
    h = _level([(v - cg, f)], need)
    gm = gz(mesh, cg, need, math.radians(2)) / math.sin(math.radians(2))
    phis = np.arange(0, 180 + 1e-9, step_deg)
    arms = [gz(mesh, cg, need, math.radians(p)) for p in phis]
    inner = [a for p, a in zip(phis, arms) if 0 < p < 180]
    vanish = next((float(p) for p, a in zip(phis[1:], arms[1:]) if a <= 0), 180.0)
    k = 0.35 * r["hull_m"]                             # roll radius of gyration, a rough third of the beam
    return {"waterline_m": h + r["zg_m"], "sealed_m3": water._below([mesh], 1e3)[0], "gm_m": gm,
            "roll_s": 2 * math.pi * k / math.sqrt(G * gm) if gm > 0 else math.nan,
            "phi_deg": phis.tolist(), "gz_m": arms, "rights": all(a > 0 for a in inner),
            "vanishes_deg": vanish, "least_gz_m": min(inner)}


def one(args) -> dict:
    name, power, over, floated = args
    r = size(name, power, **over)
    if floated and r["ok"]:
        r.update(afloat(r))
    r["over"] = over
    return r


def _map(jobs, workers: int):
    if workers == 1:
        return [one(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers or None) as ex:
        return list(ex.map(one, jobs))


def run(workers: int = 0) -> dict:
    """Every case with every power, floated; and the sweeps on the Beet-4."""
    li = inputs()
    sw = li["sweep"]
    jobs = [(n, p, {}, True) for n in li["cases"] for p in li["power"]]
    jobs += [("beet-4", p, {"disc_loading_kgm2": d}, False) for p in ("gen-hover", "battery-hop")
             for d in sw["disc_loading_kgm2"]]
    jobs += [("beet-4", p, {"view_min": t}, False) for p in ("gen-hover", "battery-hop", "turbine")
             for t in sw["view_min"]]
    jobs += [("beet-4", "battery-hop", {"batt_kw_kg": k}, False) for k in sw["batt_kw_kg"]]
    jobs += [("beet-4", "gen-hover", {"cabin_top_ratio": t, "keel_pod_m": d}, True)
             for t in sw["cabin_top_ratio"] for d in sw["keel_pod_m"]]
    rows = _map(jobs, workers)
    n = len(li["cases"]) * len(li["power"])
    return {"r44": r44(li), "cases": rows[:n], "sweeps": rows[n:]}


def _sweep(res: dict, key: str, power: str | None = None) -> list[dict]:
    return [r for r in res["sweeps"] if list(r["over"]) == [key] and (power is None or r["power"] == power)]


def report(res: dict) -> str:
    li = inputs()
    hop_ = li["hop"]
    k = res["r44"]
    lines = ["# The Beet: a flying buoy, by the numbers", "",
             "A circular RIB with a 360° glass observation cabin, its mass low and a coaxial rotor on a mast at the top. "
             f"Each is sized for one hop: climb to {hop_['height_m']:.0f} m at {hop_['climb_ms']:g} m/s, look for "
             f"{hop_['view_min']:g} min, come down at {hop_['descend_ms']:g} m/s and land on the water "
             f"(`src/osprey/beet.py`, inputs in `design/beet.toml`, every number a REF stand-in).", "",
             f"Calibration: the model puts an R44 at {k['hover_kw']:.0f} kW to hover at its max weight; it is rated "
             f"{k['mcp_kw']:.0f} kW continuous and {k['takeoff_kw']:.0f} kW for take-off.", "",
             "## Every case, every way of powering it", "",
             "| Case | Power | Max weight | Rotor | Hover | Installed | Genset | Battery | Fuel | Hull | Top of mast | "
             "Waterline | GM | Roll | Rights itself |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["cases"]:
        if not r["ok"]:
            lines.append(f"| {r['label'].split(':')[0]} | {r['power']} | doesn't close | | | | | | | | | | | | |")
            continue
        lines.append(
            f"| {r['label'].split(':')[0]} | {r['power']} | {r['mass_kg']:.0f} kg | {r['rotor_m']:.1f} m | "
            f"{r['hover_kw']:.0f} kW | {r['installed_kw']:.0f} kW | {r['genset_kw']:.0f} kW | "
            f"{r['battery_kwh']:.0f} kWh, {r['parts']['battery']:.0f} kg | {r['fuel_kg']:.0f} kg | {r['hull_m']:.1f} m | "
            f"{r['top_m']:.1f} m | {r['waterline_m'] * 100:.0f} cm | {r['gm_m']:.1f} m | {r['roll_s']:.1f} s | "
            f"{'yes' if r['rights'] else 'no: floats upside down past %.0f°' % r['vanishes_deg']} |")
    lines += ["", "Hover is shaft power; installed has the margin for climb and gusts. The battery-hop genset recharges the "
              "battery afloat; the others' gensets carry the hover. Fuel: four recharges for the battery hop, 30 min "
              "of hover for the rest. Waterline is above the keel.", "",
              "## Where the Beet-4's weight goes", "", "| Part | " + " | ".join(
                  r["power"] for r in res["cases"] if r["case"] == "beet-4") + " |",
              "|---|" + "---|" * sum(r["case"] == "beet-4" for r in res["cases"])]
    b4 = [r for r in res["cases"] if r["case"] == "beet-4"]
    for part in b4[0]["parts"]:
        lines.append(f"| {part} | " + " | ".join(f"{r['parts'][part]:.0f} kg" for r in b4) + " |")
    lines.append("| **total** | " + " | ".join(f"**{r['mass_kg']:.0f} kg**" for r in b4) + " |")
    lines += ["", "## Beet-4: disc loading", "", "| Power | Disc loading | Max weight | Rotor | Hover | Downwash |",
              "|---|---|---|---|---|---|"]
    for r in _sweep(res, "disc_loading_kgm2"):
        lines.append(f"| {r['power']} | {r['disc_loading_kgm2']:.0f} kg/m² | {r['mass_kg']:.0f} kg | {r['rotor_m']:.1f} m | "
                     f"{r['hover_kw']:.0f} kW | {r['downwash_ms']:.1f} m/s |")
    lines += ["", "## Beet-4: time at the top", "", "| Power | At the top | Max weight | Battery |", "|---|---|---|---|"]
    for r in _sweep(res, "view_min"):
        lines.append(f"| {r['power']} | {r['view_min']:g} min | "
                     + (f"{r['mass_kg']:.0f} kg | {r['battery_kwh']:.0f} kWh, {r['parts']['battery']:.0f} kg |" if r["ok"]
                        else "doesn't close | |"))
    lines += ["", "## Beet-4 battery hop: pack power", "", "| Pack power | Max weight | Battery |", "|---|---|---|"]
    for r in _sweep(res, "batt_kw_kg"):
        lines.append(f"| {r['over']['batt_kw_kg']:g} kW/kg | {r['mass_kg']:.0f} kg | {r['battery_kwh']:.0f} kWh, "
                     f"{r['parts']['battery']:.0f} kg |")
    lines += ["", "## Beet-4 hybrid: will it always come back upright?", "",
              "The cabin's roof radius over its floor's (1 is a cylinder, lower a cone, like the Roton's) and a keel pod "
              "under the hull holding the battery, genset and fuel.", "",
              "| Roof / floor | Keel pod | Max weight | CG above keel | Waterline | GM | Rights itself | Least GZ |",
              "|---|---|---|---|---|---|---|---|"]
    for r in [r for r in res["sweeps"] if "keel_pod_m" in r["over"]]:
        lines.append(f"| {r['over']['cabin_top_ratio']:.2f} | {r['keel_pod_m']:.1f} m | {r['mass_kg']:.0f} kg | "
                     f"{r['zg_m']:.2f} m | {r['waterline_m'] * 100:.0f} cm | {r['gm_m']:.1f} m | "
                     f"{'yes' if r['rights'] else 'no: floats upside down past %.0f°' % r['vanishes_deg']} | "
                     f"{r['least_gz_m'] * 100:+.0f} cm |")
    return "\n".join(lines) + "\n"
