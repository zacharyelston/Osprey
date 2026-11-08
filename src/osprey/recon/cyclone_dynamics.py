"""The Cyclone's spin building and dying, what A and B can do in each mode, and the wind in modes 1 and 2.

- The spin, by blade elements: each arm a blade, its section's lift linear to the stall and falling to a flat
  plate's past it, the inflow from momentum theory. B twists each arm, and A on it, off vertical by phi: A's
  thrust splits into cos phi up and sin phi round, and the arm's pitch to the spin plane is 90 deg - phi.
  1->2: A at its burst, B turns phi up as fast as it can while the height holds; the spin builds until the
  arms carry the weight at the spin setting. 2->1: B turns back as fast as A can take the weight; the arms,
  broadside to their own motion, brake the spin, and B past centre turns A against it to finish.
- Authority, mode by mode. 1, a tricopter: A's thrust split for roll and pitch, B tilting A for yaw. 2,
  spinning: B's cyclic once a turn tilts the disc against the spin's angular momentum; A's PWM once a turn
  pushes it sideways. 4, wing-borne: A's PWM split between the fin's motor and the wings' for pitch and
  between the wings' for yaw; B twisting all three arms the same way rolls it.
- Wind. 1: the arms stand chord-up, three flat plates; it leans into the wind on A's margin. 2: spinning in
  an edgewise wind, the advancing arm lifts more than the retreating; B's cyclic trims the roll out until the
  retreating arm stalls, B runs out of swing, or A out of power.
"""

from __future__ import annotations

import math

import numpy as np

import osprey_sim

from osprey.params import _toml, ns
from osprey.recon import cyclone, flight
from osprey.recon.params import RECON

G = 9.81


def inputs():
    return ns(_toml(RECON / "cyclone.toml")["dynamics"])


# --------------------------------------------------------------------------- blade elements

def blades(p, d: dict, cy, dy) -> dict:
    """The arms as blades: element radii and widths, chord, and the section's constants (sim/src/rotor.rs
    takes these as they are)."""
    g = cyclone.geometry(p, d, cy)
    edges = np.linspace(g["r0_m"], g["R_m"], dy.stations + 1)
    return {"r": ((edges[1:] + edges[:-1]) / 2).tolist(), "dr": np.diff(edges).tolist(), "c": g["chord_m"],
            "N": float(cy.arms), "R": g["R_m"], "r0": g["r0_m"], "A": g["disc_m2"], "rho": flight.rho(0.0),
            "cla": dy.cla, "cl_max": cy.cl_max, "a_stall": cy.cl_max / dy.cla,
            "blend": math.radians(dy.stall_blend_deg), "cd0": cy.cd_section, "kappa": cy.induced_factor}


def loads(bl: dict, omega: float, theta: float, lam, V: float = 0.0, a1: float = 0.0, b1: float = 0.0,
          n_psi: int = 1) -> dict:
    """The arms' loads averaged over a turn: thrust up (in all, and ring by ring), the drag torque against
    the spin, the rolling and pitching moments, and the in-plane drag along an edgewise wind. The arms at
    pitch theta + a1 cos psi + b1 sin psi to the spin plane, the air coming down through each element's
    ring at lam and edgewise at V (the arm advancing into it at psi = 90 deg). Blade elements in Rust."""
    lam = np.broadcast_to(np.asarray(lam, float), (len(bl["r"]),)).tolist()
    ld = osprey_sim.rotor_loads(bl, omega, theta, lam, V, a1, b1, n_psi)
    return {**ld, "Tr": np.array(ld["Tr"]), "alpha": np.array(ld["alpha"]), "ut": np.array(ld["ut"])}


def spin_pitch(p, d: dict, cy, dy, m: dict) -> dict:
    """The arms' pitch to the spin plane that carries the weight at the hover's spin rate (cyclone.rotor's),
    the inflow ring by ring there, and the blade elements' torque against the rotor's sum."""
    bl = blades(p, d, cy, dy)
    h = cyclone.rotor(p, d, cy, m["mass_kg"])
    W, om = m["mass_kg"] * G, h["omega_rads"]
    r = osprey_sim.rotor_hover(bl, W, om)
    th, ld = r["theta"], r["loads"]
    alpha = np.array(ld["alpha"])
    return {"theta_rad": th, "phi_rad": math.pi / 2 - th, "lam": np.array(r["lam"]), "omega_rads": om,
            "alpha_tip_rad": float(alpha[0, -1]), "alpha_max_rad": float(alpha.max()),
            "alpha_rad": alpha[0].tolist(), "p_blades_w": ld["Q"] * om,
            "p_rotor_w": h["p_induced_w"] + h["p_profile_w"]}


# --------------------------------------------------------------------------- A on the arms

def rings(p, d: dict, cy, m: dict) -> list[tuple[float, int, float]]:
    """A (and A2) as rings of motors on the arms: (radius, how many, shaft power each at the burst)."""
    from osprey.recon import cyclone_modes

    g = cyclone.geometry(p, d, cy)
    over = cy.burst_factor if m["burst"] else 1.0
    out = [(g["R_m"], cy.arms, m["motor_peak_w"] * over / cy.arms)]
    if m["a2"]:
        out.append((g["r0_m"] + cyclone_modes.inputs().a2_station * g["arm_m"], cy.arms, m["a2_w"] * over / cy.arms))
    return out


def a_max(cy, shaft_w: float, u: float) -> float:
    """One prop's thrust on a shaft power with the air coming at u along its axis: static from momentum
    theory and the figure of merit, falling as eta P / u (as cyclone.spin_up)."""
    a = math.pi * (cy.tri_prop_diameter_m / 2) ** 2
    static = (cy.tri_figure_of_merit * shaft_w) ** (2 / 3) * (2 * flight.rho(0.0) * a) ** (1 / 3)
    return min(static, cy.tip_prop_efficiency * shaft_w / max(u, 1e-3))


# --------------------------------------------------------------------------- the spin building and dying

def transient(p, d: dict, cy, dy, m: dict, build: bool, dt: float = 0.005) -> dict:
    """1->2 (build) or 2->1 (not), at a steady height. Each step B may turn phi by its slew rate either way;
    of the settings it can reach, the one furthest along that A, up to its burst, can still hold the height
    at (a PD law on the height and climb), and A gives what holds it. Dying, B may turn past centre, A then
    pushing against the spin. Done when B is at the spin setting with the spin at 97% of the hover's, or the
    spin is under spun_down_frac of it. Stepped in Rust (sim/src/rotor.rs)."""
    bl, sp = blades(p, d, cy, dy), spin_pitch(p, d, cy, dy, m)
    I = cyclone.inertia(p, d, cy, m["motor_kg"])
    r = osprey_sim.rotor_transient(bl, {
        "prop_diameter_m": cy.tri_prop_diameter_m, "figure_of_merit": cy.tri_figure_of_merit,
        "induced_factor": cy.induced_factor, "tip_prop_efficiency": cy.tip_prop_efficiency,
        "nacelle_cda": cy.nacelle_cda_m2, "rings": [[float(a), float(b), float(c)] for a, b, c in rings(p, d, cy, m)],
        "mass_kg": m["mass_kg"], "inertia": I, "omega_h": sp["omega_rads"], "theta_h": sp["theta_rad"],
        "lam_h": sp["lam"].tolist(), "b_rate_rad_s": math.radians(dy.b_rate_dps),
        "b_back_rad": math.radians(dy.b_yaw_deg), "spun_down_frac": dy.spun_down_frac,
        "motor_efficiency": p.propulsion.motor_efficiency, "build": build, "dt": dt})
    track = [tuple(x) for x in r["track"]]
    return {"build": build, "t_s": r["t"], "energy_j": r["energy_j"], "dz_m": r["z"], "z_min_m": r["z_min"],
            "z_max_m": r["z_max"], "done": r["done"], "a_peak": r["a_peak"], "phi_min_deg": min(x[2] for x in track),
            "inertia_kgm2": I, "omega_h_rads": sp["omega_rads"], "phi_spin_deg": math.degrees(sp["phi_rad"]),
            "track": track}


_SPIN: dict = {}


def spin(p, d: dict, cy, m: dict) -> dict:
    """The spin building (1->2) and dying (2->1) for a design, kept: the modes' manager asks often."""
    dy = inputs()
    key = _key(d, m)
    if key not in _SPIN:
        _SPIN[key] = {"build": transient(p, d, cy, dy, m, True), "die": transient(p, d, cy, dy, m, False)}
    return _SPIN[key]


# --------------------------------------------------------------------------- authority

def _cyclic_gain(f_hz: float, f_band: float) -> float:
    return 1 / math.sqrt(1 + (f_hz / f_band) ** 2)


def authority(p, d: dict, cy, dy, m: dict) -> dict:
    """What A and B can do in modes 1, 2 and 4, against what each mode needs of them."""
    bl, sp = blades(p, d, cy, dy), spin_pitch(p, d, cy, dy, m)
    g = cyclone.geometry(p, d, cy)
    R, r0, c, N = g["R_m"], g["r0_m"], g["chord_m"], cy.arms
    I = cyclone.inertia(p, d, cy, m["motor_kg"])
    I_t = I / 2                                                   # a flat body: about any axis in its plane
    W = m["mass_kg"] * G
    rho = bl["rho"]
    rg = rings(p, d, cy, m)
    _, n_a, p_a = rg[0]

    # 1, a tricopter: one A up, the other two down, the height kept; B tilting all three A for yaw.
    t_hover = W / sum(n for _, n, _ in rg)
    t_max = a_max(cy, p_a, 0.0)
    a = min(t_max - t_hover, 2 * t_hover)
    m1 = 1.5 * R * a
    yaw1 = n_a * t_hover * math.sin(math.radians(dy.b_yaw_deg)) * R
    one = {"t_hover_n": t_hover, "t_max_n": t_max, "tilt_nm": m1, "tilt_acc_dps2": math.degrees(m1 / I_t),
           "tilt20_s": 2 * math.sqrt(math.radians(20) / (m1 / I_t)), "yaw_nm": yaw1,
           "yaw_acc_dps2": math.degrees(yaw1 / I)}

    # 2, spinning: B's cyclic and A's PWM, each once a turn.
    om, th, lam = sp["omega_rads"], sp["theta_rad"], sp["lam"]
    f_rev = om / (2 * math.pi)
    ld = loads(bl, om, th, lam, b1=math.radians(1.0), n_psi=36)
    per_deg = math.hypot(ld["roll"], ld["pitch"])
    headroom = math.degrees(bl["a_stall"] - sp["alpha_max_rad"])
    gain_b = _cyclic_gain(f_rev, dy.b_bandwidth_hz)
    swing = min(dy.b_cyclic_max_deg * gain_b, headroom)
    H = I * om
    m2 = per_deg * swing
    hov = cyclone.rotor(p, d, cy, m["mass_kg"])
    gain_a = 1 / math.sqrt(1 + (2 * math.pi * f_rev * dy.motor_tau_s) ** 2)
    dT = dy.pwm_depth * hov["tip_thrust_n"] * gain_a
    side = N / 2 * dT * math.sin(sp["phi_rad"])
    m_a = N / 2 * dT * math.cos(sp["phi_rad"]) * R
    two = {"rev_hz": f_rev, "b_gain": gain_b, "b_swing_deg": swing, "stall_headroom_deg": headroom,
           "b_nm_per_deg": per_deg, "b_nm": m2, "h_kgm2s": H, "tilt_dps": math.degrees(m2 / H),
           "tilt10_s": 10 / math.degrees(m2 / H), "a_gain": gain_a, "a_side_n": side,
           "a_side_lean_deg": math.degrees(math.atan(side / W)), "a_nm": m_a, "a_tilt_dps": math.degrees(m_a / H)}

    # 4, wing-borne: A's PWM for pitch (the fin's motor below the CG, the wings' above) and yaw (the wings'
    # either side); B twisting all three arms the same way rolls it, against all three arms' damping.
    ac = cyclone.aircraft(p, d, cy, m)
    w = cyclone._wing(p, d, cy)
    ar = w["span_m"] ** 2 / w["S_m2"]
    cla3 = dy.cla * ar / (ar + 2)
    four = {}
    for name, v in (("wing_borne", 1.2 * ac.v_stall(0.0)), ("search", d["v_search_ms"])):
        D = ac.drag(v, 0.0)
        trim = W * dy.static_margin * c
        t_fin = (trim + D * R / 2) / (1.5 * R)
        thrust_max = cyclone._thrust(p, cy, m["motor_peak_w"], v)
        p_ss = v * math.radians(5.0) * (R * R - r0 * r0) / 2 / ((R ** 3 - r0 ** 3) / 3)
        damp = 0.5 * rho * v * c * cla3 * N * (R ** 3 - r0 ** 3) / 3
        four[name] = {"v_ms": v, "drag_n": D, "trim_nm": trim, "fin_share": t_fin / D,
                      "pitch_up_nm": D * R - trim, "pitch_down_nm": D * R / 2 + trim, "pitch_max_nm": thrust_max * R,
                      "pitch_acc_dps2": math.degrees((D * R - trim) / I_t), "yaw_nm": D * R * math.cos(math.radians(30)),
                      "yaw_acc_dps2": math.degrees(D * R * math.cos(math.radians(30)) / I_t),
                      "roll_dps_5deg": math.degrees(p_ss), "roll_tau_s": I / damp,
                      "bank30_s": I / damp + 30 / math.degrees(p_ss)}
    return {"inertia_kgm2": I, "one": one, "two": two, "four": four, "motor_tau_s": dy.motor_tau_s,
            "b_rate_dps": dy.b_rate_dps}


# --------------------------------------------------------------------------- wind

def wind_one(p, d: dict, cy, dy, m: dict, V: float) -> dict:
    """Mode 1 in a wind: the arms standing chord-up are three flat plates, their normal forces summing to
    1.5 times one arm's along the wind (and no yaw, 120 degrees apart); A leans into it on its burst."""
    g = cyclone.geometry(p, d, cy)
    W = m["mass_kg"] * G
    F = 0.5 * flight.rho(0.0) * V * V * dy.wind_cd * 1.5 * g["arm_m"] * g["chord_m"]
    tw = sum(n * a_max(cy, P, 0.0) for _, n, P in rings(p, d, cy, m)) / W
    return {"v_ms": V, "force_n": F, "lean_deg": math.degrees(math.atan(F / W)), "a_frac": math.hypot(W, F) / (tw * W),
            "ok": math.hypot(W, F) <= tw * W}


def wind_one_max(p, d: dict, cy, dy, m: dict) -> float:
    g = cyclone.geometry(p, d, cy)
    W = m["mass_kg"] * G
    tw = sum(n * a_max(cy, P, 0.0) for _, n, P in rings(p, d, cy, m)) / W
    F = W * math.sqrt(max(tw * tw - 1, 0.0))
    return math.sqrt(2 * F / (flight.rho(0.0) * dy.wind_cd * 1.5 * g["arm_m"] * g["chord_m"]))


def _key(d: dict, m: dict) -> tuple:
    return (m["mass_kg"], m["motor_peak_w"], m["a2_w"], m["motor_kg"], d["S_m2"], d["span_m"], d["spar_kg"], d["skin_kg"])


_WIND: dict = {}


def wind(p, d: dict, cy, m: dict) -> dict:
    """wind_sweep for a design, kept: mode 3's top speed is mode 2's wind limit, asked for often."""
    key = _key(d, m)
    if key not in _WIND:
        _WIND[key] = wind_sweep(p, d, cy, inputs(), m)
    return _WIND[key]


def wind_sweep(p, d: dict, cy, dy, m: dict, v_max: float = 16.0, step: float = 0.25) -> dict:
    """Both modes against the wind, and the strongest each holds station in; for 2, the first of the
    retreating arm's stall, B's swing (cut by its bandwidth at the spin rate) and A's rating to run out."""
    bl, sp = blades(p, d, cy, dy), spin_pitch(p, d, cy, dy, m)
    swing = dy.b_cyclic_max_deg * _cyclic_gain(sp["omega_rads"] / (2 * math.pi), dy.b_bandwidth_hz)
    stall = math.degrees(bl["a_stall"])
    vv = [step * i for i in range(int(v_max / step) + 1)]
    one = [wind_one(p, d, cy, dy, m, v) for v in vv]
    # Mode 2, each wind's trim starting from the last (sim/src/rotor.rs): the disc tilted into it until the
    # arms' in-plane drag and the hub's balance, the collective and B's cyclic trimmed by Newton's method so
    # the arms carry the weight with no rolling or pitching moment, the inflow ring by ring with Glauert's
    # edgewise air; the retreating arm's angle of attack over its outer half, the cyclic, the power through A.
    sw = osprey_sim.rotor_wind_sweep(bl, {
        "omega": sp["omega_rads"], "theta_h": sp["theta_rad"], "lam_h": sp["lam"].tolist(), "weight_n": m["mass_kg"] * G,
        "hub_cda": cy.hub_cda_m2, "nacelle_cda": cy.nacelle_cda_m2, "tip_prop_efficiency": cy.tip_prop_efficiency,
        "stall_deg": stall, "swing_deg": swing, "rating_w": m["motor_peak_w"], "v_max": v_max, "step": step,
        "n_psi": 36})
    two, limit, v2 = sw["rows"], sw["why"], sw["v_max_ms"]
    # The wind's moment on the disc before B answers: a 1 m/s gust, no cyclic, and how fast it tips the disc.
    lam = sp["lam"]
    g1 = loads(bl, sp["omega_rads"], sp["theta_rad"], lam, 1.0, 0.0, 0.0, 36)
    I = cyclone.inertia(p, d, cy, m["motor_kg"])
    gust = math.hypot(g1["roll"], g1["pitch"])
    return {"v": vv, "one": one, "two": two, "one_max_ms": wind_one_max(p, d, cy, dy, m), "two_max_ms": v2,
            "two_limit": limit or "none in the range", "swing_deg": swing, "stall_deg": stall,
            "gust_nm_per_ms": gust, "gust_tilt_dps_per_ms": math.degrees(gust / (I * sp["omega_rads"])),
            "mu_max": v2 / (sp["omega_rads"] * bl["R"])}


def knob(p, d: dict, cy, m: dict, cls=(0.30, 0.35, 0.40, 0.45, 0.50, 0.55)) -> list[dict]:
    """Spinning faster for the same thrust lowers the arms' mean lift coefficient and leaves more of the
    stall for the retreating arm: the wind limit and the power, the design held, against cl_mean."""
    dy = inputs()
    rows = []
    for cl in cls:
        cy2 = ns({**vars(cy), "cl_mean": cl})
        h = cyclone.rotor(p, d, cy2, m["mass_kg"])
        w = wind_sweep(p, d, cy2, dy, m)
        rows.append({"cl_mean": cl, "rpm": h["rpm"], "hover_w": h["p_shaft_w"],
                     "spin_peak_w": cyclone.rotor(p, d, cy2, m["mass_kg"], cy.thrust_to_weight * m["mass_kg"] * G)["p_shaft_w"],
                     "wind_ms": w["two_max_ms"], "limit": w["two_limit"]})
    return rows


def assess(p, d: dict, cy=None, m: dict | None = None) -> dict:
    from osprey.params import DESIGN
    from osprey.recon import cyclone_modes
    from osprey.recon.params import load

    cy, dy = cy or cyclone.inputs(), inputs()
    m = m or cyclone.mass(p, d, cy)
    md = cyclone_modes.inputs()
    sp = spin_pitch(p, d, cy, dy, m)
    w = wind(p, d, cy, m)
    au = authority(p, d, cy, dy, m)
    return {"pitch": {k: v for k, v in sp.items() if k != "lam"}, "spin": spin(p, d, cy, m), "authority": au,
            "wind": w, "knob": knob(p, d, cy, m), "inputs": vars(dy), "b_ramp_s": md.b_ramp_s,
            "rating_w": m["motor_peak_w"], "hover_w": cyclone.rotor(p, d, cy, m["mass_kg"])["p_shaft_w"],
            "cl_mean": cy.cl_mean, "mu_ref": 0.35, "dihedral_deg": cy.dihedral_deg, "v_tip_ms": cyclone.rotor(p, d, cy, m["mass_kg"])["v_tip_ms"],
            "sea_winds": list(zip(sorted(_toml(DESIGN / "sea.toml")["sea"]),
                                  load("sar-offshore", payload="gimbal", airframe="tailsitter").floats.wind_ms))}


def report(a: dict, title: str) -> str:
    """The sheet: the spin building and dying, A's and B's authority mode by mode, the wind in 1 and 2."""
    sp, b, dd, au, w, iv = a["pitch"], a["spin"]["build"], a["spin"]["die"], a["authority"], a["wind"], a["inputs"]
    o, t, f = au["one"], au["two"], au["four"]
    two = w["two"][-1] if w["two"] else None
    lines = [f"# The Cyclone's spin, control and wind: {title}", "",
             "Blade elements along each arm (a symmetric section, linear to its stall at "
             f"{w['stall_deg']:.1f}° and a flat plate past it), the inflow from momentum theory ring by ring. REF inputs in "
             "`[dynamics]` of `design/recon/cyclone.toml`.", "",
             "## The spin setting", "",
             f"To carry the weight at {sp['omega_rads'] * 60 / (2 * math.pi):.0f} rpm "
             f"the arms sit at **{math.degrees(sp['theta_rad']):.1f}°** to the spin plane: B turns each "
             f"{math.degrees(sp['phi_rad']):.1f}° off centre. The tips meet the air at {math.degrees(sp['alpha_tip_rad']):.1f}°, "
             f"{w['stall_deg'] - math.degrees(sp['alpha_tip_rad']):.1f}° under the stall. The blade elements' hover power, "
             f"{sp['p_blades_w']:.0f} W into the air, matches the rotor model's {sp['p_rotor_w']:.0f} W.", "",
             "## The spin building and dying", "",
             f"B turns at {iv['b_rate_dps']:g}°/s. Building (1 → 2), A gives what holds the height, up to its burst, and B "
             "turns as far each step as the height allows. Dying (2 → 1), B turns back as fast as A, up to its burst, can "
             f"take the weight; past centre it turns A {iv['b_yaw_deg']:g}° against the spin to finish it.", "",
             "| | 1 → 2, the spin builds | 2 → 1, the spin dies |", "|---|---|---|",
             f"| Time | **{b['t_s']:.2f} s** | **{dd['t_s']:.2f} s** |",
             f"| B | 0° to {b['phi_spin_deg']:.0f}°: {b['phi_spin_deg'] / iv['b_rate_dps']:.2f} s at its slew | "
             f"{dd['phi_spin_deg']:.0f}° to {dd['phi_min_deg']:.0f}° and back |",
             f"| Height | {b['z_max_m']:+.2f} m at most | {dd['z_max_m']:+.2f} m at most |",
             f"| A, of its burst | {b['a_peak']:.0%} at most | {dd['a_peak']:.0%} at most |",
             f"| Energy | {b['energy_j'] / 3600:.2f} Wh | {dd['energy_j'] / 3600:.2f} Wh |", "",
             f"Both fit well inside the {a['b_ramp_s']:g} s the modes' manager allowed for each. The spin builds about as "
             "fast as B can turn, so B's slew sets it, not A; the arms, broadside to their own motion, stop the spin in "
             "about the same time.", "",
             "## Control: what A and B can do", "",
             f"Spin inertia {au['inertia_kgm2']:.2f} kg m²; A's thrust lags its PWM by {au['motor_tau_s'] * 1000:.0f} ms.", "",
             "| Mode | Axis | By | Can do |", "|---|---|---|---|",
             f"| 1 lift-off | roll, pitch | A, one up and two down | {o['tilt_nm']:.1f} N m: tilts 20° in {o['tilt20_s']:.2f} s |",
             f"| | yaw | B, all three A tilted {iv['b_yaw_deg']:g}° | {o['yaw_nm']:.1f} N m, {o['yaw_acc_dps2']:.0f}°/s² |",
             f"| 2 spinning | disc tilt | B's cyclic once a turn ({t['rev_hz']:.1f} Hz) | ±{t['b_swing_deg']:.1f}° "
             f"(the stall leaves {t['stall_headroom_deg']:.1f}°, B's bandwidth passes {t['b_gain']:.0%} of "
             f"{iv['b_cyclic_max_deg']:g}°): {t['b_nm']:.1f} N m, tilting the disc at **{t['tilt_dps']:.0f}°/s** against "
             f"the spin's {t['h_kgm2s']:.1f} kg m²/s |",
             f"| | sideways | A's PWM once a turn, ±{iv['pwm_depth']:.0%} | {t['a_side_n']:.2f} N, the push of a "
             f"{t['a_side_lean_deg']:.1f}° lean; the disc tilt it gives, {t['a_tilt_dps']:.1f}°/s, is nothing |",
             f"| 4 wing-borne | pitch | A, the fin's motor below against the wings' above | trims with "
             f"{f['search']['fin_share']:.0%} of the thrust on the fin's motor at {f['search']['v_ms']:.0f} m/s "
             f"(static margin {iv['static_margin']:.0%}); {f['search']['pitch_up_nm']:.1f} N m nose up beyond, "
             f"{f['search']['pitch_max_nm']:.0f} N m at full power |",
             f"| | yaw | A, one wing's motor against the other | {f['search']['yaw_nm']:.1f} N m at cruise thrust |",
             f"| | roll | B, all three arms twisted the same way | {f['search']['roll_dps_5deg']:.0f}°/s for 5° of twist at "
             f"{f['search']['v_ms']:.0f} m/s ({f['wing_borne']['roll_dps_5deg']:.0f}°/s at {f['wing_borne']['v_ms']:.0f}); "
             f"30° of bank in {f['search']['bank30_s']:.2f} s |", "",
             "Mode 4: twisting the fin alone gives a side force but no yaw: it sits at the CG's station along the flight "
             "path, with nothing behind it. So yaw and pitch are A's (the fine control), roll and lift B's (the large), as "
             "the modes say. Rolling in mode 4 is turning about the old spin axis, so the three arms damp it as they damp "
             "the spin.", "",
             "Mode 2: B steers. A's PWM once a turn barely tilts the disc (its thrust is nearly in the spin plane) but "
             "pushes the whole bird sideways, which helps hold station without tilting.", "",
             "## Wind", "",
             f"**Mode 1**, B centred: the arms stand chord-up, three flat plates whose pushes add to 1.5 arms' along the wind. "
             f"Leaning into it on A's burst, it holds station up to **{w['one_max_ms']:.1f} m/s**.", "",
             f"**Mode 2**, spinning: the advancing arm meets the air faster than the retreating one; B's cyclic trims the roll "
             f"out, the retreating arm's angle of attack climbing toward the stall. It holds station up to "
             f"**{w['two_max_ms']:.2f} m/s**, where {w['two_limit']}"
             + (f", with {two['cyclic_deg']:.1f}° of cyclic and the disc tilted {two['tilt_deg']:.1f}° into the wind; the power "
                f"falls from {w['two'][0]['shaft_w']:.0f} W in still air to {two['shaft_w']:.0f} W there (the wind's lift)." if two else "."),
             "", f"The retreating arm limits mode 3 the same way: its top speed is now {w['two_max_ms']:.2f} m/s, an advance "
             f"ratio of {w['mu_max']:.2f} (it was taken as {a['mu_ref']:g}, {a['mu_ref'] * a['v_tip_ms']:.1f} m/s).", "",
             f"A 1 m/s gust, before B answers, tips the disc at {w['gust_tilt_dps_per_ms']:.0f}°/s; B's cyclic tilts it at "
             f"{t['tilt_dps']:.0f}°/s, so it answers gusts of up to {t['tilt_dps'] / w['gust_tilt_dps_per_ms']:.1f} m/s.", "",
             "| Wind | Mode 1: lean, A of its burst | Mode 2: cyclic, retreating arm, power |", "|---|---|---|"]
    by_v = {r["v_ms"]: r for r in w["two"]}
    for k, v in a["sea_winds"]:
        r1 = next(r for r in w["one"] if abs(r["v_ms"] - v) < 1e-9)
        r2 = by_v.get(v)
        c1 = f"{r1['lean_deg']:.0f}°, {r1['a_frac']:.0%}" + ("" if r1["ok"] else " ✗")
        c2 = (f"{r2['cyclic_deg']:.1f}°, {r2['alpha_max_deg']:.1f}°, {r2['shaft_w']:.0f} W" if r2 else "✗ can't hold station")
        lines.append(f"| {v:g} m/s ({k}) | {c1} | {c2} |")
    lines += ["", "**Spinning faster** lowers the arms' mean lift coefficient for the same thrust and leaves the retreating "
              "arm more of the stall, at the price of more power and a bigger motor (the design held as it is):", "",
              "| Mean lift coefficient | rpm | Hover | Spinning peak (A rated " + f"{a['rating_w']:.0f} W) | Mode 2 wind limit |",
              "|---|---|---|---|---|"]
    for r in a["knob"]:
        mark = " (now)" if abs(r["cl_mean"] - a["cl_mean"]) < 1e-9 else ""
        lines.append(f"| {r['cl_mean']:.2f}{mark} | {r['rpm']:.0f} | {r['hover_w']:.0f} W | {r['spin_peak_w']:.0f} W | "
                     f"{r['wind_ms']:.2f} m/s |")
    lines += ["", "Not modelled: closed-loop stability in each mode, the arms flexing, gust dynamics beyond the first "
              "moment, and the wind's lift on the arms in mode 1 as it leans."]
    return "\n".join(lines) + "\n"
