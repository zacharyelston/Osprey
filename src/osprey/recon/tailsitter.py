"""The tailsitter: a flying wing that takes off and lands standing on its
trailing edge, with two tractor props on the leading edge for the hover.
In the water it floats upright on four pods at the ends of its landing
struts, props high and dry, and launches straight up out of the sea.

- Hover: momentum theory with a figure of merit sets the motors (peak
  thrust over weight) and the energy every sortie spends hovering, which
  the sizing charges against the battery.
- Afloat upright: the draft on the pods, how high the props sit, and the
  metacentric height each way, from the same meshes the renders draw,
  tilted a few degrees and floated again. Natural periods follow, to set
  against the waves'.
- The launch: throttle up; climb out of the water against the pods' drag,
  the water they carry, surface tension and the buoyancy they lose; climb
  to a safe height; pitch over to wing-borne flight. A 2-D point mass
  through the pitch-over, with lift and drag past the stall.
- The sea: the design wave's slope (how far the water tips the bird before
  it lifts) and its surface speed (what the climb has to outrun).

Body frame: x forward, y port, z up. Upright, the body x axis points up:
the world frame there is z up, with the body's z axis along world -x.
"""

from __future__ import annotations

import math

import numpy as np

from osprey.recon import flight, geometry, water

G = 9.81


def vtol(p) -> bool:
    return getattr(p.layout, "vtol", None) == "tailsitter"


def _disc(p) -> float:
    return p.hover.props * math.pi * (p.hover.prop_diameter_m / 2) ** 2


def hover_power(p, thrust_n):
    """Shaft power (W) for a total thrust in the hover: n T_i^1.5 / sqrt(2 rho A_i) / FM.
    Written with ** so a complex step goes through it."""
    h = p.hover
    a_i = _disc(p) / h.props
    return h.props * (thrust_n / h.props) ** 1.5 / (2 * flight.rho(0.0) * a_i) ** 0.5 / h.figure_of_merit


def thrust_for_power(p, shaft_w: float) -> float:
    h = p.hover
    a_i = _disc(p) / h.props
    return h.props * (shaft_w / h.props * h.figure_of_merit * (2 * flight.rho(0.0) * a_i) ** 0.5) ** (2 / 3)


def motors(p, mass_kg: float) -> tuple[float, float]:
    """Motor, ESC and prop mass (kg) and total peak shaft power (W) for the peak hover thrust."""
    h = p.hover
    peak = hover_power(p, h.thrust_to_weight * mass_kg * G)
    return h.specific_kg_per_kw * peak / 1000 + h.fixed_kg, peak


def hover_energy_j(p, mass_kg):
    """What one sortie's launch and landing hover take from the battery."""
    return hover_power(p, mass_kg * G) / p.propulsion.motor_efficiency * p.hover.time_s


# --------------------------------------------------------------------------- afloat, upright

def _rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


UPRIGHT = _rot_y(-math.pi / 2)                     # body x (forward) to world z (up)


def _posed(parts, cg, R):
    return [((q.verts - cg) @ R.T, q.faces) for q in parts]


def _level(meshes, need: float) -> float:
    lo = min(float(v[:, 2].min()) for v, _ in meshes)
    hi = max(float(v[:, 2].max()) for v, _ in meshes)
    for _ in range(50):
        h = (lo + hi) / 2
        if water._below(meshes, h)[0] < need:
            lo = h
        else:
            hi = h
    return (lo + hi) / 2


def upright(p, d: dict, mass_kg: float | None = None, tilt_deg: float = 5.0) -> dict:
    """Floating upright on the pods: draft, prop height, metacentric heights."""
    parts = geometry.build(p, d)
    sealed = [q for q in parts if q.kind in water.SEALED]
    m = mass_kg or d["mass_total_kg"]
    need = m / p.water.density_kgm3
    cg = water.cg(p, d)
    V_all = sum(water._below([(q.verts, q.faces)], 1e3)[0] for q in sealed)

    def gz(R):
        ms = _posed(sealed, cg, R)
        h = _level(ms, need)
        return water._below(ms, h)[1], h, ms

    # Each axis in turn tipped toward world +x: about the span (yaw 0), and about the body z axis (yaw 90).
    out = {}
    for axis, yaw in (("across", 0.0), ("along", math.pi / 2)):
        R0 = _rot_z(yaw) @ UPRIGHT
        x0, h0, ms0 = gz(R0)
        x1, _, _ = gz(_rot_y(math.radians(tilt_deg)) @ R0)
        out[f"gm_{axis}_m"] = (x1 - x0) / math.sin(math.radians(tilt_deg))
        if axis == "across":
            h, ms, x_off = h0, ms0, x0
    lowest = min(float(v[:, 2].min()) for v, _ in ms)
    prop_parts = [q for q in parts if q.kind == "disc"]
    prop_h = min(float(((q.verts - cg) @ UPRIGHT.T)[:, 2].min()) for q in prop_parts) - h
    cams = [q for q in parts if q.kind in water.CAMERAS]
    cam_h = min(float(((q.verts - cg) @ UPRIGHT.T)[:, 2].min()) for q in cams) - h if cams else math.nan
    pods = [q for q in parts if q.name.startswith("float")]
    pod_bottom = min(float(((q.verts - cg) @ UPRIGHT.T)[:, 2].min()) for q in pods)
    # What is in the water: the pods' end area and waterline length, and the wing, if it dips.
    wet = [q for q in parts if q.kind in water.SEALED and float(((q.verts - cg) @ UPRIGHT.T)[:, 2].min()) < h]
    _, _, pts = water._below(_posed(wet, cg, UPRIGHT), h)
    return {"mass_kg": m, "displaced_l": need * 1e3, "sealed_l": V_all * 1e3, "reserve": V_all / need,
            "draft_m": h - lowest, "waterline_z": h, "prop_height_m": prop_h, "camera_height_m": cam_h,
            "pod_bottom_z": pod_bottom, "cb_offset_m": x_off, "wet_parts": sorted({q.name for q in wet}),
            "pods_only": all(q.name.startswith("float") for q in wet), "waterline_points": len(pts), **out,
            "cg": cg.tolist()}


def periods(p, d: dict, fl: dict) -> dict:
    """Natural periods afloat upright, T = 2 pi k / sqrt(g GM), with REF radii of gyration:
    a quarter of the root chord tipping across the span, a third of the half span tipping along it."""
    k_across = 0.25 * d["root_chord_m"]
    k_along = 0.33 * d["span_m"] / 2
    T = lambda k, gm: 2 * math.pi * k / math.sqrt(G * gm) if gm > 0 else math.inf     # noqa: E731
    return {"period_across_s": T(k_across, fl["gm_across_m"]), "period_along_s": T(k_along, fl["gm_along_m"])}


# --------------------------------------------------------------------------- the launch

def _submerged_table(p, d: dict, fl: dict, n: int = 30):
    """Volume (m^3) and waterline length (m) in the water as the bird rises by r (m) from afloat."""
    parts = [q for q in geometry.build(p, d) if q.kind in water.SEALED]
    ms = _posed(parts, np.array(fl["cg"]), UPRIGHT)
    rs = np.linspace(0.0, fl["draft_m"] + 1e-3, n)
    V, perim = [], []
    for r in rs:
        v_, _, pts = water._below(ms, fl["waterline_z"] - r)
        V.append(max(v_, 0.0))
        perim.append(_perimeter(pts))
    return rs, np.array(V), np.array(perim)


def _perimeter(pts: np.ndarray) -> float:
    """The waterline's length: crossing points grouped into the closed loops round each pod or part."""
    if len(pts) < 3:
        return 0.0
    xy = pts[:, :2]
    left = list(range(len(xy)))
    total = 0.0
    while left:
        loop = [left.pop(0)]
        while left:
            last = xy[loop[-1]]
            dist = np.linalg.norm(xy[left] - last, axis=1)
            k = int(np.argmin(dist))
            if dist[k] > 0.03:
                break
            loop.append(left.pop(k))
        if len(loop) > 2:
            ring = xy[loop + [loop[0]]]
            total += float(np.linalg.norm(np.diff(ring, axis=0), axis=1).sum())
    return total


def launch(p, d: dict, fl: dict | None = None, dt: float = 0.005) -> dict:
    """Throttle up on the water, climb out, climb to the safe height, pitch over to wing-borne flight."""
    h, fp = p.hover, p.floats
    fl = fl or upright(p, d)
    m = d["mass_total_kg"]
    W = m * G
    T_max = h.thrust_to_weight * W
    rho_w = p.water.density_kgm3
    rs, Vs, Ps = _submerged_table(p, d, fl)
    end_area = 4 * math.pi * fp.pod_radius_m ** 2
    t = z = v = 0.0
    worst_tension = 0.0
    phase_t = {}
    track = []                                           # (t, x, rise, pitch) every 0.05 s, for the pictures

    def mark(x_, z_, th_):
        if not track or t - track[-1][0] >= 0.05:
            track.append((t, x_, z_, th_))
    # 1. Out of the water: thrust ramps up; buoyancy, pod drag, the water they carry and surface tension.
    while z < rs[-1] and t < 30:
        T = T_max * min(t / h.spool_s, 1.0)
        V = float(np.interp(z, rs, Vs))
        perim = float(np.interp(z, rs, Ps))
        tension = fp.surface_tension_npm * perim
        worst_tension = max(worst_tension, tension)
        drag = 0.5 * rho_w * fp.cd * end_area * v * abs(v) if V > 0 else 0.0
        net = T + rho_w * G * V - W - drag - (tension if V > 0 else 0.0)
        m_eff = m + fp.added_mass * rho_w * V
        v = max(v + net / m_eff * dt, 0.0)
        z += v * dt
        t += dt
        mark(0.0, z, math.pi / 2)
    phase_t["clear_s"] = t
    v_exit = v
    # 2. Climb to the safe height, holding the climb speed (thrust trimmed to it).
    while z < rs[-1] + h.safe_height_m and t < 60:
        T = min(T_max, W + m * (h.climb_ms - v) / 0.3)
        v += (T - W) / m * dt
        z += v * dt
        t += dt
        mark(0.0, z, math.pi / 2)
    phase_t["safe_s"] = t
    # 3. Pitch over at a set rate from vertical to the cruise attitude, at full thrust, until wing-borne.
    S, b = d["S_m2"], d["span_m"]
    ar = b * b / S
    cla = 2 * math.pi * ar / (ar + 2)
    a_stall = p.wing.cl_max / cla
    v_wing = 1.2 * math.sqrt(2 * W / (flight.rho(0.0) * S * p.wing.cl_max))
    theta = math.pi / 2
    theta_end = math.radians(4.0)
    x, vx, vz = 0.0, 0.0, v
    z_min = z
    while t < 60:
        theta = max(theta - math.radians(h.pitch_rate_dps) * dt, theta_end)
        sp = math.hypot(vx, vz)
        gam = math.atan2(vz, vx) if sp > 0.1 else math.pi / 2
        a = theta - gam
        cl = cla * a if abs(a) <= a_stall else p.wing.cl_max * math.sin(2 * a) / math.sin(2 * a_stall)
        cd = d["cd0"] + d["k"] * min(cl * cl, p.wing.cl_max ** 2) + 1.2 * math.sin(a) ** 2
        q = 0.5 * flight.rho(z) * sp * sp
        L, D = q * S * cl, q * S * cd
        # Thrust: what holds a gentle climb (half the climb speed) through the pitch-over, the wing taking
        # more of the weight as it speeds up; whatever that leaves drives it forward.
        lift_up = L * math.cos(gam) - D * math.sin(gam)
        hold = (W - lift_up + m * (0.5 * h.climb_ms - vz) / 0.5) / max(math.sin(theta), 0.2)
        T = min(max(hold, 0.3 * W), T_max)
        ax = T * math.cos(theta) - D * math.cos(gam) - L * math.sin(gam)
        az = T * math.sin(theta) - D * math.sin(gam) + L * math.cos(gam) - W
        vx += ax / m * dt
        vz += az / m * dt
        x += vx * dt
        z += vz * dt
        z_min = min(z_min, z)
        t += dt
        mark(x, z, theta)
        if theta <= theta_end + 1e-9 and sp >= v_wing:
            break
    phase_t["wing_borne_s"] = t
    hover_e = hover_power(p, W) / p.propulsion.motor_efficiency
    return {"t_clear_s": phase_t["clear_s"], "t_safe_s": phase_t["safe_s"], "t_wing_borne_s": phase_t["wing_borne_s"],
            "v_exit_ms": v_exit, "height_min_m": z_min - rs[-1], "v_wing_ms": v_wing, "distance_m": x,
            "surface_tension_n": worst_tension, "surface_tension_of_weight": worst_tension / W,
            "buoyancy_n": rho_w * G * float(Vs[0]), "thrust_max_n": T_max, "weight_n": W,
            "hover_power_w": hover_e, "energy_wh": hover_e * phase_t["wing_borne_s"] / 3600 * 1.3,
            "ok": phase_t["wing_borne_s"] <= p.floats.launch_s_max and z_min - rs[-1] > 1.0,
            "track": track}


def sail_arm(p, d: dict, fl: dict) -> float:
    """Upright, the wing is a sail: the height of its planform's centroid above the pods' centre of
    lateral resistance (half the draft down)."""
    y, le, c, *_ = geometry._stations(p, d)
    xc = -(le + c / 2)                                             # each station's mid-chord, body x
    w = c * np.gradient(y)
    height = float((xc * w).sum() / w.sum()) - fl["cg"][0]         # above the CG, upright
    return height - fl["waterline_z"] + fl["draft_m"] / 2


def hover_wind_max(p, d: dict) -> float:
    """The strongest wind it can hover in, broadside: the side force it can lean into with its thrust
    margin, W sqrt((T/W)^2 - 1), against the wind on the upright wing."""
    W = d["mass_total_kg"] * G
    return math.sqrt(2 * W * math.sqrt(p.hover.thrust_to_weight ** 2 - 1)
                     / (flight.rho(0.0) * d["S_m2"] * p.floats.wind_cd))


def sea(p, d: dict, fl: dict, per: dict) -> list[dict]:
    """Each sea state against the launch: the design wave's slope and surface speed, the wave period
    against the bird's natural periods, and the state's wind heeling it afloat (wind broadside to the
    wing, against GM across the span) and pushing it in the hover."""
    from osprey.params import DESIGN, _toml

    fp = p.floats
    W = d["mass_total_kg"] * G
    arm = sail_arm(p, d, fl)
    v_hover = hover_wind_max(p, d)
    rows = []
    for (k, s), wind in zip(sorted(_toml(DESIGN / "sea.toml")["sea"].items()), fp.wind_ms):
        H = fp.design_wave * s["hs_m"]
        T = s["tp_s"]
        lam = G * T * T / (2 * math.pi)
        slope = math.degrees(math.atan(math.pi * H / lam))
        w = math.pi * H / T
        near = min(abs(T / per["period_across_s"] - 1), abs(T / per["period_along_s"] - 1))
        F = 0.5 * flight.rho(0.0) * wind ** 2 * d["S_m2"] * fp.wind_cd
        heel = math.degrees(math.atan(F * arm / (W * fl["gm_across_m"]))) if fl["gm_across_m"] > 0 else 90.0
        room = math.radians(max(fp.tilt_max_deg - slope, 1.0))     # what the wave slope leaves for the heel
        gm_need = F * arm / (W * math.tan(room))
        rows.append({"state": k, "hs_m": s["hs_m"], "tp_s": T, "slope_deg": slope, "surface_ms": w,
                     "resonance": near < 0.3, "wind_ms": wind, "heel_deg": heel, "gm_needed_m": gm_need,
                     "hover_ok": wind <= v_hover,
                     "ok": (slope + heel <= fp.tilt_max_deg and w < p.hover.climb_ms and near >= 0.3
                            and wind <= v_hover)})
    return rows


def landing_g(p, d: dict, fl: dict) -> float:
    """Settling onto the pods at the sink speed: stopped over the draft, 1 + v^2 / (2 g draft)."""
    return 1 + p.floats.sink_ms ** 2 / (2 * G * max(fl["draft_m"], 0.01))


def assess(p, d: dict) -> dict:
    fl = upright(p, d)
    per = periods(p, d, fl)
    lr = launch(p, d, fl)
    return {"afloat": fl, "periods": per, "launch": lr, "sea": sea(p, d, fl, per), "landing_g": landing_g(p, d, fl),
            "sail_arm_m": sail_arm(p, d, fl), "hover_wind_max_ms": hover_wind_max(p, d),
            "load_factor": p.limits.load_factor, "prop_d_cm": p.hover.prop_diameter_m * 100,
            "floats": {**vars(p.floats), "safe_height_m": p.hover.safe_height_m}}


def report(a: dict, title: str, d: dict) -> str:
    """The tailsitter's water-operations sheet: each requirement, what it does, and whether it passes."""
    fl, per, lr, fp = a["afloat"], a["periods"], a["launch"], a["floats"]
    yes = lambda ok: "✓" if ok else "✗"                                # noqa: E731
    lines = [f"# Tailsitter on the water: {title}", "",
             f"{d['mass_total_kg']:.2f} kg, {d['span_m'] * 100:.0f} cm span. Two {a['prop_d_cm']:.0f} cm tractor props "
             f"({d['motor_peak_w']:.0f} W peak in all, {d['motor_kg']:.2f} kg of motors), four float pods on struts. "
             "REF inputs in `[hover]` and `[floats]` of `design/recon/airframes/tailsitter.toml`.", "",
             "| Requirement | Spec | This bird | |", "|---|---|---|---|",
             f"| Floats upright on its pods, the wing clear | pods only | draft {fl['draft_m'] * 100:.1f} cm; in the water: "
             f"{', '.join(n for n in fl['wet_parts'] if not n.startswith('strut'))} | {yes(fl['pods_only'] or all(n.startswith(('float', 'strut')) for n in fl['wet_parts']))} |",
             f"| Reserve buoyancy | ≥ 2.0 | {fl['reserve']:.1f} | {yes(fl['reserve'] >= 2)} |",
             f"| Props above the water | ≥ {fp['prop_height_min_m'] * 100:.0f} cm | {fl['prop_height_m'] * 100:.0f} cm | "
             f"{yes(fl['prop_height_m'] >= fp['prop_height_min_m'])} |",
             f"| Cameras above the water | > 0 | {fl['camera_height_m'] * 100:.0f} cm | {yes(fl['camera_height_m'] > 0)} |",
             f"| Stays upright: GM tipping across the span / along it | ≥ {fp['gm_min_m'] * 100:.0f} cm | "
             f"{fl['gm_across_m'] * 100:.0f} / {fl['gm_along_m'] * 100:.0f} cm | "
             f"{yes(min(fl['gm_across_m'], fl['gm_along_m']) >= fp['gm_min_m'])} |",
             f"| Natural periods, across / along | away from the waves' 2–9 s | {per['period_across_s']:.2f} / "
             f"{per['period_along_s']:.2f} s | {yes(not any(r['resonance'] for r in a['sea']))} |",
             f"| Launch: throttle-up to wing-borne | ≤ {fp['launch_s_max']:.0f} s | {lr['t_wing_borne_s']:.1f} s (clear of the "
             f"water {lr['t_clear_s']:.2f} s, {fp['safe_height_m']:g} m up {lr['t_safe_s']:.1f} s) | {yes(lr['ok'])} |",
             f"| Lowest point in the pitch-over | > 1 m above the water | {lr['height_min_m']:.1f} m | {yes(lr['height_min_m'] > 1)} |",
             f"| Surface tension at the waterline | | {lr['surface_tension_n']:.2f} N, {lr['surface_tension_of_weight']:.1%} of "
             f"the weight | |",
             f"| Thrust, weight, buoyancy at the start | | {lr['thrust_max_n']:.0f} N, {lr['weight_n']:.0f} N, "
             f"{lr['buoyancy_n']:.0f} N | |",
             f"| Landing: settling onto the pods at {fp['sink_ms']:g} m/s | ≤ {a['load_factor']:.1f} g (sized for) | "
             f"{a['landing_g']:.1f} g | {yes(a['landing_g'] <= a['load_factor'])} |",
             f"| Hover energy per sortie (launch and landing) | | {d['hover_energy_wh']:.1f} Wh at {lr['hover_power_w']:.0f} W | |",
             f"| Strongest wind it can hover in, broadside | | {a['hover_wind_max_ms']:.1f} m/s (leaning on its "
             f"thrust margin) | |",
             "", "The sea, for a vertical launch:",
             "- The design wave (the highest in a hundred) tips the bird by its slope, and lifts the water under it "
             "at its surface speed, which the climb out has to beat.",
             f"- The wind, broadside to the upright wing, heels it afloat. Its sail ({a['sail_arm_m'] * 100:.0f} cm "
             "above the pods' grip) is held only by GM across the span.",
             f"- The launch needs the slope and the heel together under {fp['tilt_max_deg']:.0f}°, and a wind it can hover "
             "in.", "",
             "| Sea state | H_s, T_p | Typical wind | Wave slope | Heel in the wind | GM it would need | Surface speed | Launch |",
             "|---|---|---|---|---|---|---|---|"]
    for r in a["sea"]:
        lines.append(f"| {r['state'][2:]} | {r['hs_m']:g} m, {r['tp_s']:g} s | {r['wind_ms']:g} m/s | {r['slope_deg']:.1f}° | "
                     f"{r['heel_deg']:.0f}° | {r['gm_needed_m'] * 100:.0f} cm | {r['surface_ms']:.2f} m/s | {yes(r['ok'])} |")
    return "\n".join(lines) + "\n"

