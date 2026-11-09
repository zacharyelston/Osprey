"""Water operations: Recon lands on the sea beside the boat and takes off
from it. That asks five things of a sized bird:

- it floats: the sealed volume (wing, pod, booms and tail, from the same
  meshes the renders use) against the volume it displaces, and the attitude
  it floats at, with the centre of buoyancy under the centre of gravity;
- the prop clears the water: the pusher's lowest tip above the calm
  waterline afloat, or the pylon it needs to get there; and whether the
  cameras under the belly sit in the water;
- it gets off: a take-off run on the water, with the prop's thrust against
  air drag and the water's resistance, which peaks at the hump before the
  shoe climbs onto its step and planes;
- it survives landing: the hull load factor of FAR 23.527, which grows with
  touchdown speed and falls with the shoe's deadrise;
- the sea lets it: take-off in significant waves up to a fraction of the
  planing shoe's length.

The float kit (planing shoe, seals, prop pylon) adds mass and drag, so every
job is flown again carrying it.

Body frame: x forward from the root leading edge (the spar for the
twin-boom), y port, z up, metres. Afloat, pitch is positive nose up.
"""

from __future__ import annotations

import math

import numpy as np

from osprey.recon import flight, geometry

G = 9.81
SEALED = ("shell0", "shell1", "pod", "tail", "carbon")     # the closed volumes that keep it afloat
CAMERAS = ("gimbal", "lens")
KN, LB = 0.514444, 0.453592


def _below(meshes, h: float) -> tuple[float, float, np.ndarray]:
    """Volume of closed, outward-wound meshes below the plane z = h, its
    centroid x, and the points where the surface crosses the plane.

    Divergence theorem with F = (0, 0, z - h): the volume is the sum over
    the surface below the plane of (z - h) n_z dA, and the waterplane itself
    adds nothing. With F = (0, 0, x (z - h)) the same sum gives the first
    moment in x."""
    V = Mx = 0.0
    cross_pts = []
    for v, f in meshes:
        T = v[f]
        g = T[:, :, 2] - h
        below = (g <= 0).all(1)
        crossing = ~below & (g <= 0).any(1)
        tris = list(T[below])
        for tri in T[crossing]:
            poly = []
            for k in range(3):
                a, b = tri[k], tri[(k + 1) % 3]
                ga, gb = a[2] - h, b[2] - h
                if ga <= 0:
                    poly.append(a)
                if (ga <= 0) != (gb <= 0):
                    q = a + (b - a) * ga / (ga - gb)
                    poly.append(q)
                    cross_pts.append(q)
            tris += [np.array([poly[0], poly[i], poly[i + 1]]) for i in range(1, len(poly) - 1)]
        if not tris:
            continue
        T = np.array(tris)
        az = 0.5 * np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 2]
        gz = T[:, :, 2] - h
        x = T[:, :, 0]
        V += float((az * gz.mean(1)).sum())
        Mx += float((az / 12 * ((x * gz).sum(1) + x.sum(1) * gz.sum(1))).sum())
    return V, (Mx / V if V > 1e-12 else 0.0), np.array(cross_pts).reshape(-1, 3)


def _pitch(v: np.ndarray, cg: np.ndarray, theta: float) -> np.ndarray:
    """Points about the CG, pitched nose-up by theta: forward points rise."""
    c, s = math.cos(theta), math.sin(theta)
    r = v - cg
    return np.c_[r[:, 0] * c - r[:, 2] * s, r[:, 1], r[:, 0] * s + r[:, 2] * c]


def cg(p, d: dict) -> np.ndarray:
    """Where the centre of gravity sits. A flying wing's comes from the sizing
    (the battery and payload's station, which carries nearly all the mass);
    the twin-boom balances at its spar."""
    if d.get("airframe") == "tandem":
        return np.array([-d["cg_x_m"], 0.0, p.fuselage.axis_z_m])       # in the pod, with the battery
    return np.array([-d["cg_x_m"], 0.0, 0.0]) if d.get("airframe") in ("bwb", "crescent") else np.zeros(3)


def afloat(p, d: dict, mass_kg: float | None = None) -> dict:
    """The floating equilibrium: draft, trim, reserve buoyancy and clearances."""
    w = p.water
    parts = geometry.build(p, d)
    sealed = [(q.verts, q.faces) for q in parts if q.kind in SEALED]
    m = mass_kg or d["mass_total_kg"] + (0.0 if d.get("float_kit") else w.kit_kg)
    need = m / w.density_kgm3
    c = cg(p, d)
    V_all, _, _ = _below(sealed, 1e3)

    def level(theta):
        ms = [(_pitch(v, c, theta), f) for v, f in sealed]
        lo = min(float(v[:, 2].min()) for v, _ in ms)
        hi = max(float(v[:, 2].max()) for v, _ in ms)
        if V_all < need:
            return hi, ms
        for _ in range(50):
            h = (lo + hi) / 2
            if _below(ms, h)[0] < need:
                lo = h
            else:
                hi = h
        return (lo + hi) / 2, ms

    def moment(theta):
        h, ms = level(theta)
        return _below(ms, h)[1]                      # centre of buoyancy x, ahead of the CG

    a, b = math.radians(-20), math.radians(20)
    ma, mb = moment(a), moment(b)
    theta = a if ma < 0 else b if mb > 0 else None
    if theta is None:
        for _ in range(30):
            t = (a + b) / 2
            if moment(t) > 0:
                a = t
            else:
                b = t
        theta = (a + b) / 2
    h, ms = level(theta)
    V, cbx, pts = _below(ms, h)

    def lowest(kind_or_names):
        zs = [float(_pitch(q.verts, c, theta)[:, 2].min()) for q in parts
              if q.kind in kind_or_names or q.name in kind_or_names]
        return min(zs) - h if zs else math.nan

    prop = lowest(("disc",))
    return {
        "mass_kg": m, "displaced_l": need * 1e3, "sealed_l": V_all * 1e3, "reserve": V_all / need,
        "trim_deg": math.degrees(theta), "draft_m": float(min(v[:, 2].min() for v, _ in ms)) - h,
        "waterline_m": float(np.ptp(pts[:, 0])) if len(pts) else 0.0,
        "beam_m": float(np.ptp(pts[:, 1])) if len(pts) else 0.0,
        "prop_clear_m": prop, "pylon_m": max(0.0, w.prop_clearance_m - prop),
        "camera_clear_m": lowest(CAMERAS), "waterline_z": h, "cg": c.tolist(),
    }


def static_thrust(p) -> float:
    """Momentum theory with a figure of merit: T = (FM P)^(2/3) (2 rho A)^(1/3)."""
    A = math.pi * (p.geometry.prop_diameter_m / 2) ** 2
    return (p.water.figure_of_merit * p.propulsion.motor_peak_w) ** (2 / 3) * (2 * flight.rho(0.0) * A) ** (1 / 3)


def resistance(p, u: float) -> float:
    """Water resistance over weight on the water at u = speed / lift-off speed:
    rising to the hump at hump_speed_frac, then falling away as the shoe
    climbs onto its step and planes."""
    w = p.water
    if u <= w.hump_speed_frac:
        return w.r_hump * u / w.hump_speed_frac
    return w.r_plane + (w.r_hump - w.r_plane) * math.exp(-(((u - w.hump_speed_frac) / 0.15) ** 2))


def takeoff(p, d: dict, mass_kg: float, dt: float = 0.01) -> dict:
    """A take-off run on calm water at full power: run length, time, energy
    and the worst thrust margin (thrust less air drag and water resistance,
    over weight). The run is stepped in Rust (sim/src/water.rs)."""
    import osprey_sim

    w, pr = p.water, p.propulsion
    W, S = mass_kg * G, d["S_m2"]
    rho = flight.rho(0.0)
    v_stall = math.sqrt(2 * W / (rho * S * p.wing.cl_max))
    v_lof = w.liftoff_frac * v_stall
    T0 = static_thrust(p)
    cd = d["cd0"] + w.kit_cda_m2 / S + d["k"] * w.cl_run ** 2
    r = osprey_sim.takeoff({"mass_kg": mass_kg, "S_m2": S, "v_lof": v_lof, "T0": T0, "cd": cd,
                            "prop_efficiency": pr.prop_efficiency, "motor_peak_w": pr.motor_peak_w, "cl_run": w.cl_run,
                            "r_hump": w.r_hump, "r_plane": w.r_plane, "hump_speed_frac": w.hump_speed_frac, "dt": dt})
    ok = r["v"] >= v_lof
    return {"v_liftoff_ms": v_lof, "v_stall_ms": v_stall, "static_thrust_n": T0, "thrust_to_weight": T0 / W,
            "run_m": r["x"] if ok else math.inf, "run_s": r["t"] if ok else math.inf,
            "energy_wh": pr.motor_peak_w / pr.motor_efficiency * r["t"] / 3600, "margin_min": r["worst"],
            "margin_at_ms": r["at"], "gets_off": ok and r["worst"] >= w.thrust_margin_min}


def impact_factor(p, v_stall_ms: float, mass_kg: float) -> float:
    """FAR 23.527 hull load factor: C1 V_S0^2 / (tan^(2/3)(deadrise) W^(1/3)), knots and pounds."""
    w = p.water
    return w.impact_c1 * (v_stall_ms / KN) ** 2 / (math.tan(math.radians(w.deadrise_deg)) ** (2 / 3)
                                                   * (mass_kg / LB) ** (1 / 3))


def hull_length(p, d: dict) -> float:
    """The planing shoe's length: under the pod, or the blended wing's centre body."""
    if d.get("airframe") == "tandem":
        return d["nacelle_floats"]["length_m"]
    return d["root_chord_m"] if d.get("airframe") == "bwb" else p.geometry.pod_length_m


def sea_limit(p, hull_m: float) -> tuple[float, str]:
    """The largest significant wave height for take-off, and the roughest sea state under it."""
    from osprey.params import DESIGN, _toml

    hs = p.water.wave_frac * hull_m
    states = _toml(DESIGN / "sea.toml")["sea"]
    under = [k for k, s in sorted(states.items()) if s["hs_m"] <= hs]
    return hs, (under[-1] if under else "none")


def refly(d: dict, payload: str, airframe: str) -> dict:
    """Every job flown again carrying the float kit: whether it still succeeds,
    and the battery left on landing, with the kit and without it. A bird
    sized with the kit aboard flies only with it."""
    from osprey.recon import fleet
    from osprey.recon.params import MISSIONS, load

    out = {}
    sized_with_kit = d.get("float_kit", False)
    for mn in MISSIONS:
        p = load(mn, payload=payload, airframe=airframe, water=sized_with_kit)
        row = {}
        for kit in ((True,) if sized_with_kit else (False, True)):
            ac = flight.Aircraft.from_design(p, d)
            if kit and not sized_with_kit:
                ac.mass_kg += p.water.kit_kg
                ac.cd0 += p.water.kit_cda_m2 / d["S_m2"]
            s = flight.summary(p, ac, flight.simulate(p, ac))
            row["kit" if kit else "bare"] = {"ok": fleet.ok(s), "energy_left": s["energy_left_frac"]}
        out[mn] = row
    return out


def assess(p, d: dict, payload: str, airframe: str, fly: bool = True) -> dict:
    fl = afloat(p, d)
    m = fl["mass_kg"]
    to = takeoff(p, d, m)
    hull = hull_length(p, d)
    hs, ss = sea_limit(p, hull)
    out = {"afloat": fl, "takeoff": to, "impact_g": impact_factor(p, to["v_stall_ms"], m),
           "hull_m": hull, "sea_hs_m": hs, "sea_state": ss, "kit_kg": p.water.kit_kg,
           "load_factor": p.limits.load_factor, "water": vars(p.water)}
    if fly:
        out["jobs"] = refly(d, payload, airframe)
    return out


def report(a: dict, title: str) -> str:
    """The water-operations spec sheet for one bird: each requirement, what the bird does, and whether it passes."""
    from osprey.recon.params import MISSIONS

    fl, to = a["afloat"], a["takeoff"]
    w = a["water"]
    yes = lambda ok: "✓" if ok else "✗"                                # noqa: E731
    lines = [f"# Water operations: {title}", "",
             f"With the float kit ({a['kit_kg']:.2f} kg: planing shoe, seals, prop pylon), {fl['mass_kg']:.2f} kg "
             "in all. REF inputs in `[water]` of `design/recon/airframe.toml`.", "",
             "| Requirement | Spec | This bird | |", "|---|---|---|---|",
             f"| Reserve buoyancy (sealed volume / displaced) | ≥ {w['reserve_min']:.1f} | {fl['reserve']:.2f} "
             f"({fl['sealed_l']:.1f} l sealed, {fl['displaced_l']:.1f} l displaced) | {yes(fl['reserve'] >= w['reserve_min'])} |",
             f"| Floating trim | level | {fl['trim_deg']:+.1f}° (nose up +), draft {-fl['draft_m'] * 100:.1f} cm | "
             f"{yes(abs(fl['trim_deg']) <= 5)} |",
             f"| Prop tips above the water, afloat | ≥ {w['prop_clearance_m'] * 100:.0f} cm | {fl['prop_clear_m'] * 100:+.1f} cm: "
             f"needs a {fl['pylon_m'] * 100:.0f} cm pylon | {yes(fl['pylon_m'] <= 0)} |",
             f"| Cameras out of the water, afloat | > 0 | {fl['camera_clear_m'] * 100:+.1f} cm | {yes(fl['camera_clear_m'] > 0)} |",
             f"| Thrust margin over the hump | ≥ {w['thrust_margin_min']:.2f} W | {to['margin_min']:.2f} W at "
             f"{to['margin_at_ms']:.1f} m/s (static thrust {to['static_thrust_n']:.0f} N, T/W {to['thrust_to_weight']:.2f}) | "
             f"{yes(to['gets_off'])} |",
             f"| Take-off run, calm water | | {to['run_m']:.0f} m, {to['run_s']:.1f} s, {to['energy_wh']:.2f} Wh, "
             f"lift-off at {to['v_liftoff_ms']:.1f} m/s | |",
             f"| Waves for take-off ({w['wave_frac']:.0%} of the {a['hull_m'] * 100:.0f} cm shoe) | | "
             f"H_s ≤ {a['sea_hs_m'] * 100:.0f} cm: sea state {a['sea_state'][2:] if a['sea_state'] != 'none' else 'none'} | |",
             f"| Landing load factor (FAR 23.527, {w['deadrise_deg']:.0f}° deadrise) | ≤ {a['load_factor']:.1f} g "
             f"(sized for) | {a['impact_g']:.1f} g | {yes(a['impact_g'] <= a['load_factor'])} |", ""]
    if "jobs" in a:
        reserve = 0.2 / 1.2
        bare = all("bare" in r for r in a["jobs"].values())
        lines += [("Every job again, carrying the kit: battery left on landing, without the kit and with it. "
                   if bare else "Every job, sized with the kit aboard: battery left on landing. ")
                  + f"The missions keep a 20 % energy reserve, about {reserve:.0%} of the battery at landing; "
                  "✗ marks a job that fails or lands into it.", "",
                  "| Job | Bare | With the kit |" if bare else "| Job | With the kit |",
                  "|---|---|---|" if bare else "|---|---|"]
        for mn in MISSIONS:
            r = a["jobs"][mn]
            cell = lambda c: f"{yes(c['ok'] and c['energy_left'] >= reserve - 0.03)} {c['energy_left']:.0%}"  # noqa: E731
            lines.append(f"| {mn} | {cell(r['bare'])} | {cell(r['kit'])} |" if bare else f"| {mn} | {cell(r['kit'])} |")
        lines.append("")
    return "\n".join(lines)
