"""Recon as a Cyclone: three arms that are wings, after Nick Rehm's Cyclone-Rotor
tricopter. Twisting the arms about their own axes turns it from a tricopter
(motors pushing up) into a rotor: the tip motors push round, the whole bird
spins, and its three wings are the blades.

Built from the twin-boom one-bird. Each arm is one of its wing halves; a third
arm replaces the booms and tail; three tip motors replace the pusher.

- Spinning hover: blade elements for the thrust and the arms' profile drag,
  momentum theory with an induced factor for the rest. The tip props drive
  the rotor at the tip speed.
- Spin-up from rest, the wind it can hover in (the retreating arm stalls),
  whether one motor can hold it up.
- Motors off: it comes down like a sycamore seed. The flare: whether the
  rotor's spin can soak up the sink before the water.
- Cruise, two ways, each flown through all seven jobs in the 3-DOF sim:
  as a tricopter, the motors carrying the weight; or stopped and locked as a
  fixed wing, one arm aft as the tail and two forward. One forward arm flies
  backwards in the spin, so it flips over: the sections are symmetric.
- The camera spins with it.
"""

from __future__ import annotations

import math
from dataclasses import replace

from osprey.params import _toml, ns
from osprey.recon import flight, tailsitter
from osprey.recon.params import RECON

G = 9.81


def inputs():
    return ns(_toml(RECON / "cyclone.toml")["cyclone"])


def geometry(p, d: dict, cy=None) -> dict:
    """The rotor from the base bird's wing: arm length, radius, chord, disc, and the masses that change."""
    cy = cy or inputs()
    arm = d["span_m"] / 2
    R = cy.hub_radius_m + arm
    chord = d["S_m2"] / d["span_m"]
    wing_kg = d["spar_kg"] + d["skin_kg"]
    return {"arm_m": arm, "R_m": R, "r0_m": cy.hub_radius_m, "chord_m": chord, "disc_m2": math.pi * R * R,
            "solidity": cy.arms * chord * arm / (math.pi * R * R), "arm_kg": wing_kg / 2}


def tri_power(p, cy, thrust_n: float, v: float = 0.0, h: float = 0.0, cda: float = 0.0) -> float:
    """Shaft power flying as a tricopter at airspeed v: induced power from momentum
    theory (Glauert's inflow, solved by iteration), the props' profile power from
    the hover figure of merit, and the drag of the airframe."""
    rho = flight.rho(h)
    A = cy.arms * math.pi * (cy.tri_prop_diameter_m / 2) ** 2
    D = 0.5 * rho * v * v * cda
    T = math.hypot(thrust_n, D)
    vh = math.sqrt(T / (2 * rho * A))
    vi = vh
    for _ in range(60):
        vi = 0.5 * vi + 0.5 * vh * vh / math.sqrt(v * v + vi * vi)
    p_ideal = T * vh
    return cy.induced_factor * T * vi + p_ideal * (1 / cy.tri_figure_of_merit - cy.induced_factor) + D * v


def motors(p, d: dict, cy, mass_kg: float) -> tuple[float, float]:
    """Three tip motors, sized for the tricopter transition's peak thrust: their mass (kg) and peak shaft power (W)."""
    peak = tri_power(p, cy, cy.tri_thrust_to_weight * mass_kg * G)
    return cy.specific_kg_per_kw * peak / 1000 + cy.fixed_kg, peak


def mass(p, d: dict, cy=None) -> dict:
    """The base bird with its pod, booms, tail and pusher swapped for the hub, a third arm and three
    tip motors. The motors are sized for the mass they lift, so iterate."""
    cy = cy or inputs()
    g = geometry(p, d, cy)
    base = d["mass_total_kg"] - p.body.mass_kg - p.propulsion.motor_kg + cy.hub_kg + g["arm_kg"]
    m = base
    for _ in range(30):
        mk, peak = motors(p, d, cy, m)
        m = base + mk
    return {"mass_kg": m, "motor_kg": mk, "motor_peak_w": peak, "delta_kg": m - d["mass_total_kg"]}


def rotor(p, d: dict, cy, mass_kg: float, thrust_n: float | None = None) -> dict:
    """Spinning hover at a thrust (the weight unless given): spin rate, tip speed and power."""
    g = geometry(p, d, cy)
    rho = flight.rho(0.0)
    T = mass_kg * G if thrust_n is None else thrust_n
    R, r0, c, N = g["R_m"], g["r0_m"], g["chord_m"], cy.arms
    omega = math.sqrt(6 * T / (rho * N * c * cy.cl_mean * (R ** 3 - r0 ** 3)))
    v_tip = omega * R
    p_ideal = T ** 1.5 / math.sqrt(2 * rho * g["disc_m2"])
    p_induced = cy.induced_factor * p_ideal
    p_profile = rho * N * c * cy.cd_section * omega ** 3 * (R ** 4 - r0 ** 4) / 8
    p_nacelle = N * 0.5 * rho * v_tip ** 3 * cy.nacelle_cda_m2
    p_rotor = p_induced + p_profile + p_nacelle
    shaft = p_rotor / cy.tip_prop_efficiency
    return {"thrust_n": T, "omega_rads": omega, "rpm": omega * 60 / (2 * math.pi), "v_tip_ms": v_tip,
            "p_ideal_w": p_ideal, "p_induced_w": p_induced, "p_profile_w": p_profile, "p_nacelle_w": p_nacelle,
            "p_rotor_w": p_rotor, "p_shaft_w": shaft, "figure_of_merit": p_ideal / shaft, "tip_thrust_n": p_rotor / v_tip / N}


def inertia(p, d: dict, cy, motor_kg: float) -> float:
    """Spin inertia (kg m^2): three uniform arms from the hub out, and a motor at each tip."""
    g = geometry(p, d, cy)
    R, r0 = g["R_m"], g["r0_m"]
    arm = g["arm_kg"] * (R ** 3 - r0 ** 3) / (3 * (R - r0))
    return cy.arms * (arm + motor_kg / cy.arms * R * R)


def spin_up(p, d: dict, cy, m: dict, dt: float = 0.002) -> dict:
    """From rest to the hover spin, motors at their peak: each tip prop's static thrust, falling
    away as P / v as the tip speeds up, against the arms' drag. Lifts off at the hover spin."""
    hov = rotor(p, d, cy, m["mass_kg"])
    g = geometry(p, d, cy)
    rho = flight.rho(0.0)
    I = inertia(p, d, cy, m["motor_kg"])
    p_each = m["motor_peak_w"] / cy.arms
    a_prop = math.pi * (cy.tri_prop_diameter_m / 2) ** 2
    f_static = (cy.tri_figure_of_merit * p_each) ** (2 / 3) * (2 * rho * a_prop) ** (1 / 3)
    k_drag = hov["p_rotor_w"] / hov["omega_rads"] ** 3                    # torque grows with the spin squared
    t, w = 0.0, 0.0
    while w < hov["omega_rads"] and t < 60:
        v = w * g["R_m"]
        f = min(f_static, cy.tip_prop_efficiency * p_each / max(v, 1e-6))
        w += (cy.arms * f * g["R_m"] - k_drag * w * w) / I * dt
        t += dt
    return {"t_s": t, "inertia_kgm2": I, "tip_static_n": f_static}


def autorotation(p, d: dict, cy, m: dict) -> dict:
    """Motors off: the sink speed on the disc's drag, the energy in the spin against the
    sink's, and the splash, flared or not."""
    g = geometry(p, d, cy)
    rho = flight.rho(0.0)
    W = m["mass_kg"] * G
    v = math.sqrt(2 * W / (rho * g["disc_m2"] * cy.autorotation_cd))
    hov = rotor(p, d, cy, m["mass_kg"])
    e_spin = 0.5 * inertia(p, d, cy, m["motor_kg"]) * hov["omega_rads"] ** 2
    e_sink = 0.5 * m["mass_kg"] * v * v
    splash = lambda u: 1 + u * u / (2 * G * cy.splash_stop_m)                  # noqa: E731
    return {"sink_ms": v, "spin_j": e_spin, "sink_j": e_sink, "flare_ratio": e_spin / e_sink,
            "splash_g": splash(v), "flared_g": splash(v * math.sqrt(max(1 - e_spin / e_sink, 0.0)))}


def smear_px(p, cy, omega: float) -> float:
    """How far the image turns during one exposure at the spin rate, in pixels at the wide end."""
    ifov = p.camera.pixel_um * 1e-6 / (p.camera.focal_mm[0] * 1e-3)
    return omega * cy.exposure_ms * 1e-3 / ifov


# --------------------------------------------------------------------------- the two ways to cruise

class Tricopter(flight.Aircraft):
    """Cruising as a tricopter: no wing lift, the motors carry the weight."""
    cy = None
    cda = 0.0

    def drag(self, v, h, n=1.0):
        return self.power_shaft(v, h, n) / max(v, 0.5)

    def power_shaft(self, v, h, n=1.0):
        return tri_power(None, self.cy, n * self.W, v, h, self.cda)

    def power(self, v, h, n=1.0, climb=0.0):
        return (self.power_shaft(v, h, n) + self.W * max(climb, 0.0)) / self.eta_motor + self.p_aux_w

    def v_stall(self, h, n=1.0):
        return 0.0

    def best_range_speed(self, h, headwind):
        grid = [3.0 + 0.5 * i for i in range(55)]
        cost = [self.power(v, h) / max(v - headwind, 0.5) for v in grid]
        return grid[cost.index(min(cost))]


def hover_j(p, d: dict, cy, m: dict) -> float:
    """Each sortie's time off the wing, as the tailsitter's: spinning, less the two transitions as a tricopter."""
    spin = rotor(p, d, cy, m["mass_kg"])["p_shaft_w"] * (cy.hover_time_s - 2 * cy.transition_s)
    tri = tri_power(p, cy, m["mass_kg"] * G) * 2 * cy.transition_s
    return (spin + tri) / p.propulsion.motor_efficiency


def aircraft(p, d: dict, cy, m: dict, mode: str) -> flight.Aircraft:
    """The base bird's Aircraft, changed for the Cyclone's mass and energy and for one way of cruising."""
    ac = flight.Aircraft.from_design(p, d)
    pr = p.propulsion
    energy = d["battery_kg"] * pr.battery_wh_per_kg * 3600 * pr.battery_usable - hover_j(p, d, cy, m)
    ac = replace(ac, mass_kg=m["mass_kg"], energy_j=energy, p_shaft_max_w=m["motor_peak_w"])
    if mode == "wing":
        g = geometry(p, d, cy)
        b_eff = 2 * g["R_m"] * math.sin(math.radians(60))                   # forward arms at +-60 deg from the nose
        cd0_wing = d["cd0"] - p.body.cda_m2 / d["S_m2"]
        cd0 = (cd0_wing + cy.cd_symmetric_extra) * cy.arms / 2 + cy.hub_cda_m2 / d["S_m2"]
        off = math.cos(math.radians(cy.prop_offaxis_deg))
        return replace(ac, span_m=b_eff, cd0=cd0, k=d["k"] * (d["span_m"] / b_eff) ** 2 * cy.k_factor,
                       cl_max=cy.cl_max, eta_prop=ac.eta_prop * off,
                       p_shaft_max_w=m["motor_peak_w"] * (cy.arms - 1) / cy.arms)
    t = Tricopter(**{**vars(ac), "eta_prop": 1.0})
    t.cy, t.cda = cy, cy.tri_cda_m2
    return t


def fly(d: dict, payload: str, cy=None) -> dict:
    """Every job flown both ways: whether it succeeds, and the battery left on landing."""
    from osprey.recon import fleet
    from osprey.recon.params import MISSIONS, load

    cy = cy or inputs()
    out = {}
    for mn in MISSIONS:
        p = load(mn, payload=payload)
        m = mass(p, d, cy)
        row = {}
        for mode in ("wing", "tricopter"):
            ac = aircraft(p, d, cy, m, mode)
            s = flight.summary(p, ac, flight.simulate(p, ac))
            row[mode] = {"ok": fleet.ok(s), "energy_left": s["energy_left_frac"], "flight_min": s["flight_time_s"] / 60,
                         "power_w": s["power_mean_w"]}
        out[mn] = row
    return out


def _scaled(p, d: dict, chord_scale: float, battery_add_kg: float) -> dict:
    """The base design with a wider chord (more skin, the same span) and more battery."""
    d2 = dict(d)
    S = d["S_m2"] * chord_scale
    d2.update(S_m2=S, skin_kg=d["skin_kg"] * chord_scale, battery_kg=d["battery_kg"] + battery_add_kg,
              k=d["k"] * chord_scale, cd0=d["cd0"] - p.body.cda_m2 / d["S_m2"] + p.body.cda_m2 / S,
              mass_total_kg=d["mass_total_kg"] + d["skin_kg"] * (chord_scale - 1) + battery_add_kg)
    return d2


def resize(d: dict, payload: str, cy=None, speeds=(1.0, 1.1, 1.2, 1.3, 1.4), tol_kg: float = 0.02) -> dict:
    """The lightest Cyclone that does all seven jobs as a stopped wing. Recovery is a vertical
    spin, so the 12 m/s stall limit for a net or hand catch doesn't apply; the search-speed margin
    does: at each search speed tried, the chord widens until the symmetric sections' stall, banked,
    sits under it by the stall margin. Then battery is added until every job closes."""
    from osprey.recon import fleet
    from osprey.recon.params import MISSIONS, load

    cy = cy or inputs()
    ps = {mn: load(mn, payload=payload) for mn in MISSIONS}
    p = ps["sar-offshore"]
    lim = p.limits
    n = 1 / math.cos(math.radians(lim.bank_max_deg))

    def build(vs, add):
        sc = 1.0
        for _ in range(30):
            m = mass(p, _scaled(p, d, sc, add), cy)["mass_kg"]
            S = 2 * n * m * G * lim.stall_margin ** 2 / (flight.rho(0.0) * vs ** 2 * cy.cl_max)
            sc = max(1.0, S / d["S_m2"])
        return {**_scaled(p, d, sc, add), "v_search_ms": vs}

    def jobs(d2):
        out = {}
        for mn, pm in ps.items():
            ac = aircraft(pm, d2, cy, mass(pm, d2, cy), "wing")
            s = flight.summary(pm, ac, flight.simulate(pm, ac))
            out[mn] = {"ok": fleet.ok(s), "energy_left": s["energy_left_frac"]}
        return out

    best = None
    for f in speeds:
        vs = d["v_search_ms"] * f
        lo, hi = 0.0, 2.0
        if all(r["ok"] for r in jobs(build(vs, lo)).values()):
            hi = lo
        elif not all(r["ok"] for r in jobs(build(vs, hi)).values()):
            continue
        while hi - lo > tol_kg:
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if all(r["ok"] for r in jobs(build(vs, mid)).values()) else (mid, hi)
        d2 = build(vs, hi)
        m = mass(p, d2, cy)["mass_kg"]
        if best is None or m < best["mass_kg"]:
            best = {"design": d2, "battery_add_kg": hi, "chord_scale": d2["S_m2"] / d["S_m2"], "mass_kg": m,
                    "v_search_ms": vs, "jobs": jobs(d2)}
    if best:
        best["ok"] = all(r["ok"] for r in best["jobs"].values())
    return best


def cruise_curves(p, d: dict, cy, m: dict, h: float) -> dict:
    """Electric power against airspeed: the base bird, the Cyclone stopped as a wing, and as a tricopter."""
    base = flight.Aircraft.from_design(p, d)
    wing = aircraft(p, d, cy, m, "wing")
    tri = aircraft(p, d, cy, m, "tricopter")
    v = [3.0 + 0.5 * i for i in range(55)]
    curve = lambda ac, lo: [ac.power(x, h) if x >= lo else math.nan for x in v]  # noqa: E731
    return {"v": v, "base": curve(base, 1.2 * base.v_stall(h)), "wing": curve(wing, 1.2 * wing.v_stall(h)),
            "tricopter": curve(tri, 0.0), "v_stall_base": base.v_stall(h), "v_stall_wing": wing.v_stall(h)}


def assess(d: dict, payload: str, ts: dict, ts_water: dict) -> dict:
    """The Cyclone built from a one-bird: flown as built, then re-sized to do all seven jobs; the
    re-sized one's spin, seed fall, camera and power curves. ts and ts_water are the tailsitter
    one-bird's design and water sheet, to compare against."""
    from osprey.recon.params import load

    cy = inputs()
    p = load("sar-offshore", payload=payload)
    built = {"mass": mass(p, d, cy), "jobs": fly(d, payload, cy)}
    rs = resize(d, payload, cy)
    dc = rs["design"]
    m = mass(p, dc, cy)
    hov = rotor(p, dc, cy, m["mass_kg"])
    tri = tri_power(p, cy, m["mass_kg"] * G)
    out = {"base": {k: d[k] for k in ("mass_total_kg", "span_m", "S_m2", "battery_kg", "v_search_ms")},
           "built": built, "resized": {k: v for k, v in rs.items() if k != "design"}, "design": dc,
           "geometry": geometry(p, dc, cy), "mass": m, "hover": hov,
           "hover_peak": rotor(p, dc, cy, m["mass_kg"], cy.thrust_to_weight * m["mass_kg"] * G), "tri_hover_w": tri,
           "hover_wh": hover_j(p, dc, cy, m) / 3600,
           "spin_up": spin_up(p, dc, cy, m), "autorotation": autorotation(p, dc, cy, m),
           "wind_max_ms": cy.mu_max * hov["v_tip_ms"], "one_motor_w": m["motor_peak_w"] / cy.arms,
           "smear_px": smear_px(p, cy, hov["omega_rads"]), "v_stall_wing_ms": aircraft(p, dc, cy, m, "wing").v_stall(0.0),
           "curves": cruise_curves(p, dc, cy, m, p.mission.cruise_alt_m), "cyclone": vars(cy)}
    out["curves"]["base_v_search"], out["curves"]["v_search"] = d["v_search_ms"], dc["v_search_ms"]
    pt = load("sar-offshore", payload=payload, airframe="tailsitter")
    out["tailsitter"] = {"mass_kg": ts["mass_total_kg"], "span_m": ts["span_m"], "motor_kg": ts["motor_kg"],
                         "motor_peak_w": ts["motor_peak_w"], "hover_wh": ts["hover_energy_wh"],
                         "hover_w": tailsitter.hover_power(pt, ts["mass_total_kg"] * G),
                         "wing_borne_s": ts_water["launch"]["t_wing_borne_s"], "wind_max_ms": ts_water["hover_wind_max_ms"]}
    return out


def report(a: dict, title: str) -> str:
    """The Cyclone's sheet: what changes from the one-bird, the spin, the seed fall, the jobs."""
    from osprey.recon.params import MISSIONS

    g, m, h, au, cy, rs = a["geometry"], a["mass"], a["hover"], a["autorotation"], a["cyclone"], a["resized"]
    ts = a["tailsitter"]
    yes = lambda ok: "✓" if ok else "✗"                                # noqa: E731
    lines = [f"# Recon as a Cyclone: {title}", "",
             "Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter: twisted one way the tip motors "
             "push up and it flies as a tricopter; twisted the other they push round and the whole bird spins, "
             "its arms the blades. Built from the twin-boom one-bird (each arm one of its wing halves, a third arm "
             "for the booms and tail, three tip motors for the pusher), then re-sized to do all seven jobs. REF "
             "inputs in `design/recon/cyclone.toml`.", "",
             "## The bird", "",
             "| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs |", "|---|---|---|---|",
             f"| Mass | {a['base']['mass_total_kg']:.2f} kg | {a['built']['mass']['mass_kg']:.2f} kg | **{m['mass_kg']:.2f} kg** |",
             f"| Wing | {a['base']['S_m2']:.3f} m², {a['base']['span_m']:.2f} m span | the same, in three arms | "
             f"{a['design']['S_m2']:.3f} m² (chord ×{rs['chord_scale']:.2f}); rotor {2 * g['R_m']:.2f} m across |",
             f"| Battery | {a['base']['battery_kg']:.2f} kg | the same | {a['design']['battery_kg']:.2f} kg |",
             f"| Search speed | {a['base']['v_search_ms']:.1f} m/s | the same | {rs['v_search_ms']:.1f} m/s |",
             f"| Jobs done, as a stopped wing | 7 / 7 | {sum(r['wing']['ok'] for r in a['built']['jobs'].values())} / 7 | "
             f"{sum(r['ok'] for r in rs['jobs'].values())} / 7 |",
             f"| Jobs done, as a tricopter | | {sum(r['tricopter']['ok'] for r in a['built']['jobs'].values())} / 7 | |", ""]
    lines += [f"Against the tailsitter one-bird for the same cameras: {ts['mass_kg']:.2f} kg, {ts['span_m']:.2f} m span.", ""]
    lines += ["## Spinning", "",
              "| | Cyclone | Tailsitter |", "|---|---|---|",
              f"| Hover power | **{h['p_shaft_w']:.0f} W** at {h['rpm']:.0f} rpm, tips at {h['v_tip_ms']:.1f} m/s: induced "
              f"{h['p_induced_w']:.0f}, arms' drag {h['p_profile_w']:.0f}, nacelles {h['p_nacelle_w']:.0f} W, through the tip props "
              f"| {ts['hover_w']:.0f} W on two 30 cm props |",
              f"| Figure of merit (ideal power over what it takes) | {h['figure_of_merit']:.2f} | |",
              f"| Hover energy per sortie | {a['hover_wh']:.1f} Wh: {cy['hover_time_s'] - 2 * cy['transition_s']:.0f} s spinning and "
              f"2 × {cy['transition_s']:.0f} s as a tricopter ({a['tri_hover_w']:.0f} W) to and from the wing "
              f"| {ts['hover_wh']:.1f} Wh |",
              f"| Motors | three, {m['motor_peak_w']:.0f} W peak in all, {m['motor_kg']:.2f} kg: sized by the tricopter "
              f"transition at {cy['tri_thrust_to_weight']:g} × weight | {ts['motor_peak_w']:.0f} W, {ts['motor_kg']:.2f} kg |",
              f"| Spin-up from rest to lift-off | {a['spin_up']['t_s']:.1f} s, plus the motors' spool | {ts['wing_borne_s']:.1f} s to "
              "wing-borne |",
              f"| Hover on one motor | {yes(a['one_motor_w'] >= h['p_shaft_w'])} {a['one_motor_w']:.0f} W against {h['p_shaft_w']:.0f} W "
              f"needed | ✗ |",
              f"| Wind it can hover in | {a['wind_max_ms']:.1f} m/s, before the retreating arm stalls "
              f"(advance ratio {cy['mu_max']:g}) | {ts['wind_max_ms']:.1f} m/s |",
              f"| The camera, spinning | turns {a['smear_px']:.0f} px in a {cy['exposure_ms']:g} ms exposure: blind unless "
              "de-spun | steady |", "",
              "## Motors off: down like a seed", "",
              f"- Sinks at **{au['sink_ms']:.1f} m/s** on the spinning disc (drag coefficient {cy['autorotation_cd']:g} on "
              f"{g['disc_m2']:.2f} m²): parachute speed, with nothing to deploy.",
              f"- The spin holds {au['spin_j']:.0f} J against the sink's {au['sink_j']:.0f} J ({au['flare_ratio']:.1f}×): "
              "pitching the arms up just before the water can stop the sink.",
              f"- Into the water at the sink speed: {au['splash_g']:.1f} g; flared: {au['flared_g']:.1f} g. The structure is "
              "sized for 3 g.", "",
              "## Cruising", "",
              f"- **Stopped as a wing:** one arm aft as the tail, two forward at ±60°, {a['curves']['v_stall_wing']:.1f} m/s stall "
              f"on symmetric sections (CL max {cy['cl_max']:g}). One forward arm flies backwards in the spin, so it flips "
              "over to cruise. Recovery is a vertical spin, so the 12 m/s stall limit for a catch doesn't apply.",
              f"- **As a tricopter:** no wing lift; it takes {min(x for x in a['curves']['tricopter'] if x == x):.0f} W at "
              f"best, against {min(x for x in a['curves']['base'] if x == x):.0f} W for the twin-boom.", "",
              "| Job | As built, stopped wing | As built, tricopter | Re-sized, stopped wing |", "|---|---|---|---|"]
    for mn in MISSIONS:
        b, r = a["built"]["jobs"][mn], rs["jobs"][mn]
        lines.append(f"| {mn} | {yes(b['wing']['ok'])} {b['wing']['energy_left']:.0%} left | {yes(b['tricopter']['ok'])} "
                     f"{b['tricopter']['energy_left']:.0%} left, {b['tricopter']['power_w']:.0f} W | {yes(r['ok'])} "
                     f"{r['energy_left']:.0%} left |")
    lines += ["", "Not modelled: floating and launching from the water (it would float flat, so the tip props need "
              "pylons), the transition between the spin and the wing (here a fixed time as a tricopter), stability "
              "and control in each mode, a de-spun camera mount, and the arms' structure under the spin's loads."]
    return "\n".join(lines) + "\n"
