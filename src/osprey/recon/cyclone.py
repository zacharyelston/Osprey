"""Recon as a Cyclone: three arms that are wings, after Nick Rehm's Cyclone-Rotor
tricopter. The arms twist about their own axes, and the tip motors twist with them.

Built from the twin-boom one-bird. Each arm is one of its wing halves; a third
arm replaces the booms and tail; three tip motors replace the pusher.

The modes:
- Spinning, the only way it hovers: the tip motors push round, the whole bird
  spins and its three wings are the blades, the lift spread over the whole disc.
  Blade elements for the thrust and the arms' drag, momentum theory with an
  induced factor for the rest, the tip props driving the rotor. It climbs,
  holds station in a wind until the retreating arm stalls, and spins up from
  rest in a moment on deck.
- Motors off, it comes down like a sycamore seed; with forward speed, as an
  autogyro. The flare: whether the spin can soak up the sink before the water.
- Flight: the arms twisted 90 degrees, the old spin axis along the flight path,
  two arms up at the dihedral as the wing and one down as the fin, all three
  motors pushing forward. The motors' PWM is the fine control, the twist servos
  the large corrections. Spinning, the blades all have the same handedness; the
  wings must be mirror images, so the sections are symmetric. Flown through all
  seven jobs in the 3-DOF sim.
- Sea lift-off: floating flat, the arms and props are in the water and it can't
  spin up there, so for a few seconds it lifts as a tricopter, motors up, then
  twists into the spin.

The transitions:
- Spin to wing, at height: the arms driven slowly toward the flight setting as
  the spin dies, it pitches over nose-down with the motors pushing forward and
  flies out of the dive. A 2-D point mass through the fly-out sets the height.
- Wing to spin, a forced move: pitch up hard, the zoom trades speed for height,
  and the inflow spins the rotor up.

The motors are rated for the spinning peak, or for the sea lift-off carried at a
short burst over the rating, whichever is more. The camera spins with the bird.
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
    """Three tip motors: their mass (kg) and rated shaft power in all (W). Rated for the spinning
    peak thrust, or for the sea lift-off as a tricopter carried at the burst factor, whichever is more."""
    spin = rotor(p, d, cy, mass_kg, cy.thrust_to_weight * mass_kg * G)["p_shaft_w"]
    liftoff = tri_power(p, cy, cy.tri_thrust_to_weight * mass_kg * G) / cy.burst_factor
    rated = max(spin, liftoff)
    return cy.specific_kg_per_kw * rated / 1000 + cy.fixed_kg, rated


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


# --------------------------------------------------------------------------- flight mode and the transitions

def _wing(p, d: dict, cy) -> dict:
    """Flight mode's wing: the two upper arms at the dihedral, the fin arm adding its drag. Lift is
    tilted by the dihedral, so the usable lift coefficient is each wing's times its cosine, and the
    induced drag goes with the projected span."""
    g = geometry(p, d, cy)
    dih = math.radians(cy.dihedral_deg)
    b = 2 * g["R_m"] * math.cos(dih)
    cd0_wing = d["cd0"] - p.body.cda_m2 / d["S_m2"]
    return {"S_m2": d["S_m2"], "span_m": b, "cl_max": cy.cl_max * math.cos(dih),
            "cd0": (cd0_wing + cy.cd_symmetric_extra) * cy.arms / 2 + cy.hub_cda_m2 / d["S_m2"],
            "k": d["k"] * (d["span_m"] / b) ** 2 * cy.k_factor}


def _thrust(p, cy, shaft_w: float, v: float) -> float:
    """The three tip props pushing forward: static thrust from momentum theory, falling as eta P / v."""
    A = cy.arms * math.pi * (cy.tri_prop_diameter_m / 2) ** 2
    static = (cy.tri_figure_of_merit * shaft_w) ** (2 / 3) * (2 * flight.rho(0.0) * A) ** (1 / 3)
    return min(static, p.propulsion.prop_efficiency * shaft_w / max(v, 0.1))


def fly_out(p, d: dict, cy, m: dict, dt: float = 0.005) -> dict:
    """Spin to wing: the spin has died with the arms at the flight setting, the bird nose-down with
    the motors pushing forward at the burst. Pitch up at a set rate to level flight; done when level
    at 1.2 x the stall and no longer sinking. A 2-D point mass with lift and drag past the stall."""
    w = _wing(p, d, cy)
    S, clm = w["S_m2"], w["cl_max"]
    ar = w["span_m"] ** 2 / S
    cla = 2 * math.pi * ar / (ar + 2)
    a_stall = clm / cla
    W, mk = m["mass_kg"] * G, m["mass_kg"]
    v_wing = 1.2 * math.sqrt(2 * W / (flight.rho(0.0) * S * clm))
    shaft = m["motor_peak_w"] * cy.burst_factor
    theta, theta_end = math.radians(cy.flyout_pitch_deg), math.radians(4.0)
    t = x = z = vx = vz = 0.0
    z_min = 0.0
    while t < 60:
        theta = min(theta + math.radians(cy.pitch_rate_dps) * dt, theta_end)
        sp = math.hypot(vx, vz)
        gam = math.atan2(vz, vx) if sp > 0.1 else theta
        a = theta - gam
        cl = cla * a if abs(a) <= a_stall else clm * math.sin(2 * a) / math.sin(2 * a_stall)
        cd = w["cd0"] + w["k"] * min(cl * cl, clm ** 2) + 1.2 * math.sin(a) ** 2
        q = 0.5 * flight.rho(0.0) * sp * sp
        L, D = q * S * cl, q * S * cd
        T = _thrust(p, cy, shaft, sp)
        vx += (T * math.cos(theta) - D * math.cos(gam) - L * math.sin(gam)) / mk * dt
        vz += (T * math.sin(theta) - D * math.sin(gam) + L * math.cos(gam) - W) / mk * dt
        x += vx * dt
        z += vz * dt
        z_min = min(z_min, z)
        t += dt
        if theta >= theta_end - 1e-9 and sp >= v_wing and vz >= 0:
            break
    return {"t_s": t, "height_lost_m": -z_min, "distance_m": x, "v_ms": math.hypot(vx, vz), "v_wing_ms": v_wing,
            "ok": t < 60}


def conversion(p, d: dict, cy, m: dict) -> dict:
    """From the spin to the wing at a height that leaves the safety margin under the fly-out; the
    spinning climb up to it."""
    fo = fly_out(p, d, cy, m)
    h = fo["height_lost_m"] + cy.safety_height_m
    return {**fo, "height_m": h, "climb_s": h / cy.climb_ms,
            "climb_j": m["mass_kg"] * G * h / cy.tip_prop_efficiency}


def entry(p, d: dict, cy, m: dict, v0: float) -> dict:
    """Wing to spin, the forced move: the zoom trades speed for height, then the inflow spins the
    rotor up while it sinks at the autorotation rate."""
    zoom = cy.zoom_efficiency * v0 * v0 / (2 * G)
    loss = autorotation(p, d, cy, m)["sink_ms"] * cy.entry_s
    return {"v0_ms": v0, "zoom_m": zoom, "entry_loss_m": loss, "net_m": zoom - loss}


def hover_j(p, d: dict, cy, m: dict) -> float:
    """Each sortie's time off the wing, as the tailsitter's: all of it spinning but the sea lift-off
    as a tricopter, and the spinning climb to the height the fly-out onto the wing needs. Charged as
    if every sortie launched from the sea."""
    spin = rotor(p, d, cy, m["mass_kg"])["p_shaft_w"] * (cy.hover_time_s - cy.sea_liftoff_s)
    tri = tri_power(p, cy, cy.tri_thrust_to_weight * m["mass_kg"] * G) * cy.sea_liftoff_s
    return (spin + tri + conversion(p, d, cy, m)["climb_j"]) / p.propulsion.motor_efficiency


def aircraft(p, d: dict, cy, m: dict) -> flight.Aircraft:
    """The base bird's Aircraft, changed for the Cyclone's mass, energy and flight-mode wing."""
    ac = flight.Aircraft.from_design(p, d)
    pr = p.propulsion
    energy = d["battery_kg"] * pr.battery_wh_per_kg * 3600 * pr.battery_usable - hover_j(p, d, cy, m)
    ac = replace(ac, mass_kg=m["mass_kg"], energy_j=energy, p_shaft_max_w=m["motor_peak_w"])
    return replace(ac, **_wing(p, d, cy))


def fly(d: dict, payload: str, cy=None) -> dict:
    """Every job flown in flight mode: whether it succeeds, and the battery left on landing."""
    from osprey.recon import fleet
    from osprey.recon.params import MISSIONS, load

    cy = cy or inputs()
    out = {}
    for mn in MISSIONS:
        p = load(mn, payload=payload)
        ac = aircraft(p, d, cy, mass(p, d, cy))
        s = flight.summary(p, ac, flight.simulate(p, ac))
        out[mn] = {"ok": fleet.ok(s), "energy_left": s["energy_left_frac"], "power_w": s["power_mean_w"]}
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
            S = 2 * n * m * G * lim.stall_margin ** 2 / (flight.rho(0.0) * vs ** 2 * cy.cl_max
                                                         * math.cos(math.radians(cy.dihedral_deg)))
            sc = max(1.0, S / d["S_m2"])
        return {**_scaled(p, d, sc, add), "v_search_ms": vs}

    def jobs(d2):
        out = {}
        for mn, pm in ps.items():
            ac = aircraft(pm, d2, cy, mass(pm, d2, cy))
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


def _climb_rate(p, d: dict, cy, m: dict, shaft_w: float) -> float:
    """Steepest spinning climb on a shaft power: momentum theory's induced power in a climb,
    k T (Vc/2 + sqrt(Vc^2/4 + vh^2)), with the arms' and nacelles' drag on top, through the tip props."""
    h = rotor(p, d, cy, m["mass_kg"])
    T = h["thrust_n"]
    vh = math.sqrt(T / (2 * flight.rho(0.0) * geometry(p, d, cy)["disc_m2"]))
    avail = shaft_w * cy.tip_prop_efficiency - h["p_profile_w"] - h["p_nacelle_w"]
    need = lambda vc: cy.induced_factor * T * (vc / 2 + math.sqrt(vc * vc / 4 + vh * vh))   # noqa: E731
    if avail <= need(0.0):
        return 0.0
    lo, hi = 0.0, 40.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if need(mid) < avail else (lo, mid)
    return lo


def abilities(p, d: dict, cy, m: dict, base: dict) -> dict:
    """What each mode can do. Spinning: hover power and endurance, climb, wind, the seed fall.
    Flying: stall, the speeds for least power and best range, top speed, lift-to-drag, endurance and
    range, against the twin-boom it was built from. The sea lift-off as a tricopter. Both transitions."""
    from osprey.recon.params import payload_w

    pr = p.propulsion
    W = m["mass_kg"] * G
    aux = p.avionics.power_w + payload_w(p)
    battery = d["battery_kg"] * pr.battery_wh_per_kg * 3600 * pr.battery_usable
    h = rotor(p, d, cy, m["mass_kg"])
    rated, burst = m["motor_peak_w"], m["motor_peak_w"] * cy.burst_factor

    def envelope(ac, shaft_max):
        vs = ac.v_stall(0.0)
        vv = [vs * (1.2 + 0.01 * i) for i in range(400)]
        pw = [ac.power(v, 0.0) for v in vv]
        i_e = pw.index(min(pw))
        cost = [x / v for x, v in zip(pw, vv)]
        i_r = cost.index(min(cost))
        top = max((v for v in vv if ac.drag(v, 0.0) * v / ac.eta_prop <= shaft_max), default=math.nan)
        return {"v_stall_ms": vs, "v_endurance_ms": vv[i_e], "p_endurance_w": pw[i_e], "v_range_ms": vv[i_r],
                "p_range_w": pw[i_r], "v_top_ms": top, "ld_max": max(ac.W / ac.drag(v, 0.0) for v in vv),
                "endurance_h": ac.energy_j / pw[i_e] / 3600, "range_km": ac.energy_j / cost[i_r] / 1000}

    wing = aircraft(p, d, cy, m)
    bac = flight.Aircraft.from_design(p, base)
    A3 = cy.arms * math.pi * (cy.tri_prop_diameter_m / 2) ** 2
    lift_burst = (burst * cy.tri_figure_of_merit * math.sqrt(2 * flight.rho(0.0) * A3)) ** (2 / 3)
    cv = conversion(p, d, cy, m)
    fl = envelope(wing, rated)
    return {
        "spin": {"hover_w": h["p_shaft_w"], "hover_elec_w": h["p_shaft_w"] / pr.motor_efficiency + aux,
                 "hover_min": battery / (h["p_shaft_w"] / pr.motor_efficiency + aux) / 60,
                 "climb_ms": _climb_rate(p, d, cy, m, rated), "climb_burst_ms": _climb_rate(p, d, cy, m, burst),
                 "wind_ms": cy.mu_max * h["v_tip_ms"], "rpm": h["rpm"], "v_tip_ms": h["v_tip_ms"]},
        "seed": autorotation(p, d, cy, m),
        "flight": {**fl, "v_top_burst_ms": envelope(wing, burst)["v_top_ms"]},
        "base_flight": envelope(bac, bac.p_shaft_max_w),
        "liftoff": {"thrust_to_weight": lift_burst / W, "power_w": burst, "seconds": cy.sea_liftoff_s},
        "to_wing": cv, "to_spin": entry(p, d, cy, m, fl["v_range_ms"]),
    }


def cruise_curves(p, d: dict, cy, m: dict, base: dict, h: float) -> dict:
    """Electric power against airspeed: the twin-boom it was built from and the Cyclone in flight mode."""
    b, w = flight.Aircraft.from_design(p, base), aircraft(p, d, cy, m)
    v = [3.0 + 0.5 * i for i in range(55)]
    curve = lambda ac: [ac.power(x, h) if x >= 1.2 * ac.v_stall(h) else math.nan for x in v]  # noqa: E731
    return {"v": v, "base": curve(b), "wing": curve(w), "v_stall_base": b.v_stall(h), "v_stall_wing": w.v_stall(h)}


def assess(d: dict, payload: str, ts: dict, ts_water: dict) -> dict:
    """The Cyclone built from a one-bird: flown as built, then re-sized to do all seven jobs, and
    the re-sized one's abilities in every mode. ts and ts_water are the tailsitter one-bird's design
    and water sheet, to compare against."""
    from osprey.recon.params import load

    cy = inputs()
    p = load("sar-offshore", payload=payload)
    n = 1 / math.cos(math.radians(p.limits.bank_max_deg))
    margin = lambda dd: dd["v_search_ms"] / (aircraft(p, dd, cy, mass(p, dd, cy)).v_stall(0.0, n))  # noqa: E731
    built = {"mass": mass(p, d, cy), "jobs": fly(d, payload, cy), "stall_margin": margin(d)}
    rs = resize(d, payload, cy)
    dc = rs["design"]
    rs["stall_margin"] = margin(dc)
    m = mass(p, dc, cy)
    hov = rotor(p, dc, cy, m["mass_kg"])
    out = {"base": {k: d[k] for k in ("mass_total_kg", "span_m", "S_m2", "battery_kg", "v_search_ms")},
           "built": built, "resized": {k: v for k, v in rs.items() if k != "design"}, "design": dc,
           "geometry": geometry(p, dc, cy), "wing": _wing(p, dc, cy), "mass": m, "hover": hov,
           "hover_peak": rotor(p, dc, cy, m["mass_kg"], cy.thrust_to_weight * m["mass_kg"] * G),
           "liftoff_w": tri_power(p, cy, cy.tri_thrust_to_weight * m["mass_kg"] * G),
           "hover_wh": hover_j(p, dc, cy, m) / 3600, "abilities": abilities(p, dc, cy, m, d),
           "spin_up": spin_up(p, dc, cy, m), "one_motor_w": m["motor_peak_w"] / cy.arms,
           "one_motor_burst_w": m["motor_peak_w"] * cy.burst_factor / cy.arms,
           "smear_px": smear_px(p, cy, hov["omega_rads"]),
           "curves": cruise_curves(p, dc, cy, m, d, p.mission.cruise_alt_m), "cyclone": vars(cy),
           "stall_margin_min": p.limits.stall_margin, "bank_deg": p.limits.bank_max_deg}
    out["curves"]["base_v_search"], out["curves"]["v_search"] = d["v_search_ms"], dc["v_search_ms"]
    pt = load("sar-offshore", payload=payload, airframe="tailsitter")
    out["tailsitter"] = {"mass_kg": ts["mass_total_kg"], "span_m": ts["span_m"], "motor_kg": ts["motor_kg"],
                         "motor_peak_w": ts["motor_peak_w"], "hover_wh": ts["hover_energy_wh"],
                         "hover_w": tailsitter.hover_power(pt, ts["mass_total_kg"] * G),
                         "wing_borne_s": ts_water["launch"]["t_wing_borne_s"], "wind_max_ms": ts_water["hover_wind_max_ms"]}
    return out


def report(a: dict, title: str) -> str:
    """The Cyclone's sheet: the bird, what each mode can do, the transitions, the jobs."""
    from osprey.recon.params import MISSIONS

    g, m, h, cy, rs, ts, ab = (a["geometry"], a["mass"], a["hover"], a["cyclone"], a["resized"], a["tailsitter"],
                               a["abilities"])
    sp, sd, fl, bf, lo, tw, tsp = (ab["spin"], ab["seed"], ab["flight"], ab["base_flight"], ab["liftoff"], ab["to_wing"],
                                   ab["to_spin"])
    yes = lambda ok: "✓" if ok else "✗"                                # noqa: E731
    lines = [f"# Recon as a Cyclone: {title}", "",
             "Three arms that are wings, after Nick Rehm's Cyclone-Rotor tricopter. It hovers only by spinning, the "
             "whole bird a rotor and its arms the blades. It flies with the arms twisted 90°, two up at "
             f"{cy['dihedral_deg']:g}° dihedral as the wing and one down as the fin, all three tip motors pushing forward. "
             "The motors push up only for the few seconds it takes to pull clear of the water on a sea launch. Built "
             "from the twin-boom one-bird (each arm one of its wing halves, a third arm for the booms and tail, three "
             "tip motors for the pusher), then re-sized to do all seven jobs. REF inputs in "
             "`design/recon/cyclone.toml`.", "",
             "## The bird", "",
             "| | Twin-boom one-bird | Cyclone as built | Cyclone re-sized for all seven jobs | Tailsitter one-bird |",
             "|---|---|---|---|---|",
             f"| Mass | {a['base']['mass_total_kg']:.2f} kg | {a['built']['mass']['mass_kg']:.2f} kg | **{m['mass_kg']:.2f} kg** | "
             f"{ts['mass_kg']:.2f} kg |",
             f"| Size | {a['base']['span_m']:.2f} m span | {2 * g['R_m']:.2f} m rotor | {2 * g['R_m']:.2f} m rotor, "
             f"{a['wing']['span_m']:.2f} m flying span, chord ×{rs['chord_scale']:.2f} | {ts['span_m']:.2f} m span |",
             f"| Battery | {a['base']['battery_kg']:.2f} kg | the same | {a['design']['battery_kg']:.2f} kg | |",
             f"| Motors | one pusher | three at the tips, rated {a['built']['mass']['motor_peak_w']:.0f} W | three, rated "
             f"{m['motor_peak_w']:.0f} W, {m['motor_kg']:.2f} kg | {ts['motor_peak_w']:.0f} W, {ts['motor_kg']:.2f} kg |",
             f"| Search speed, over the stall banked {a['bank_deg']:g}° | {a['base']['v_search_ms']:.1f} m/s | the same, "
             f"only {a['built']['stall_margin']:.2f}× | {rs['v_search_ms']:.1f} m/s, {rs['stall_margin']:.2f}× (the limit is "
             f"{a['stall_margin_min']:g}×) | |",
             f"| Jobs done | 7 / 7 | {sum(r['ok'] for r in a['built']['jobs'].values())} / 7 | "
             f"{sum(r['ok'] for r in rs['jobs'].values())} / 7 | 7 / 7 |", "",
             "The motors are rated for the larger of the spinning peak "
             f"({a['hover_peak']['p_shaft_w']:.0f} W at {cy['thrust_to_weight']:g} × weight) and the sea lift-off "
             f"({a['liftoff_w']:.0f} W at {cy['tri_thrust_to_weight']:g} × weight) carried at {cy['burst_factor']:g} × the "
             "rating for its few seconds.", "",
             "## What each mode can do", "",
             "| Mode | Ability | |", "|---|---|---|",
             f"| Spinning | Hover | **{sp['hover_w']:.0f} W** shaft at {sp['rpm']:.0f} rpm, tips at {sp['v_tip_ms']:.1f} m/s (tailsitter "
             f"{ts['hover_w']:.0f} W); figure of merit {h['figure_of_merit']:.2f} |",
             f"| | Hover on the whole battery | {sp['hover_min']:.0f} min at {sp['hover_elec_w']:.0f} W from the battery |",
             f"| | Climb | {sp['climb_ms']:.1f} m/s on the rated power, {sp['climb_burst_ms']:.1f} m/s at the burst |",
             f"| | Wind it can hold station in | {sp['wind_ms']:.1f} m/s, before the retreating arm stalls (tailsitter "
             f"{ts['wind_max_ms']:.1f} m/s) |",
             f"| | Spin-up from rest | {a['spin_up']['t_s']:.1f} s, plus the motors' spool |",
             f"| | One motor | {yes(a['one_motor_w'] >= h['p_shaft_w'])} rated {a['one_motor_w']:.0f} W, "
             f"{yes(a['one_motor_burst_w'] >= h['p_shaft_w'])} at the burst {a['one_motor_burst_w']:.0f} W, against "
             f"{h['p_shaft_w']:.0f} W to hover |",
             f"| | The camera | turns {a['smear_px']:.0f} px in a {cy['exposure_ms']:g} ms exposure: blind unless de-spun |",
             f"| Motors off | Seed fall | **{sd['sink_ms']:.1f} m/s**; the spin holds {sd['flare_ratio']:.1f}× the sink's energy, "
             f"so a flare can stop it ({sd['splash_g']:.1f} g into the water unflared) |",
             f"| Flight | Stall | {fl['v_stall_ms']:.1f} m/s (twin-boom {bf['v_stall_ms']:.1f}) |",
             f"| | Least power | {fl['p_endurance_w']:.0f} W at {fl['v_endurance_ms']:.1f} m/s (twin-boom {bf['p_endurance_w']:.0f} W) |",
             f"| | Best lift-to-drag | {fl['ld_max']:.1f} (twin-boom {bf['ld_max']:.1f}) |",
             f"| | Top speed | {fl['v_top_ms']:.0f} m/s on the rated power, {fl['v_top_burst_ms']:.0f} m/s at the burst "
             f"(twin-boom {bf['v_top_ms']:.0f}) |",
             f"| | Endurance, range on the battery | {fl['endurance_h']:.1f} h, {fl['range_km']:.0f} km (twin-boom "
             f"{bf['endurance_h']:.1f} h, {bf['range_km']:.0f} km) |",
             f"| | Control | the tip motors' PWM for the fine corrections, the arms' twist servos for the large |",
             f"| Sea lift-off | As a tricopter | {lo['thrust_to_weight']:.2f} × weight at the burst, for {lo['seconds']:g} s, "
             "then it twists into the spin |", "",
             "## The transitions", "",
             f"- **Spin to wing:** climb spinning to **{tw['height_m']:.0f} m** ({tw['climb_s']:.0f} s at {cy['climb_ms']:g} m/s), "
             f"drive the arms to the flight setting as the spin dies, pitch over nose-down "
             f"({-cy['flyout_pitch_deg']:g}°) and fly out: {tw['height_lost_m']:.0f} m lost, {tw['t_s']:.1f} s, "
             f"{tw['distance_m']:.0f} m on, {tw['v_ms']:.1f} m/s at the bottom, {cy['safety_height_m']:g} m above the water.",
             f"- **Wing to spin:** pitch up hard from {tsp['v0_ms']:.0f} m/s: the zoom gains {tsp['zoom_m']:.0f} m, the inflow "
             f"spins the rotor up in about {cy['entry_s']:g} s for {tsp['entry_loss_m']:.0f} m, {tsp['net_m']:+.0f} m in all. "
             "Powered from there, or an autogyro.",
             f"- **Each sortie off the wing**, as the tailsitter's {cy['hover_time_s']:.0f} s: "
             f"{cy['hover_time_s'] - cy['sea_liftoff_s']:.0f} s spinning, {cy['sea_liftoff_s']:g} s lifting off the sea and "
             f"the climb to the fly-out: **{a['hover_wh']:.1f} Wh** (tailsitter {ts['hover_wh']:.1f} Wh).", "",
             "## The jobs", "",
             "| Job | As built | Re-sized |", "|---|---|---|"]
    for mn in MISSIONS:
        b, r = a["built"]["jobs"][mn], rs["jobs"][mn]
        lines.append(f"| {mn} | {yes(b['ok'])} {b['energy_left']:.0%} left, {b['power_w']:.0f} W | {yes(r['ok'])} "
                     f"{r['energy_left']:.0%} left |")
    lines += ["", "Not modelled: floating and the sea lift-off itself (it floats flat, so the tip props need pylons), "
              "the spin dying and starting again (the fly-out starts with it stopped; the entry is a fixed time), "
              "stability and control in each mode, the PWM and servo authority, a de-spun camera mount, and the arms' "
              "loads in the spin."]
    return "\n".join(lines) + "\n"
