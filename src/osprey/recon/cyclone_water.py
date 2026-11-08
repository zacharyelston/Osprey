"""The Cyclone on the water. Afloat with B centred it stands on its three arms' trailing edges, chords up
and A's props up, as in mode 1: three thin keels 120 degrees apart, the hub on top.

- Afloat: the arms' symmetric sections (NACA 00xx at the wing's thickness) cut at the waterline, and the
  hub, a sealed sphere on B's axis, set the draft; A's props and the camera's height above the water follow.
  The waterplane is three long thin strips reaching out to the tips, so the metacentre is high: it sits
  very stiffly and its natural periods are short, so it rides the waves' slope rather than rolling to them.
- Each B servo holds its arm chord-up against the water: the buoyancy below B's axis and A's motor above
  it both want to lay the arm flat.
- Wind afloat: the arms above the water are three flat plates, as in mode 1; the arms below are three
  keels. It heels a little and drifts at the speed where the water's pull on the keels matches the wind's.
- The launch: A at its burst, a vertical point mass; the arms slide up out of the water edge first, against
  their skin friction and the water's surface tension along both faces, the buoyancy falling away. Then
  mode 1 up to the clearance (cyclone_modes).
- The sea: each sea state's design wave against the tilt A can still lift at, the wave's surface speed
  against mode 1's climb, its wind against mode 1's lean (cyclone_dynamics), and the camera's height.
- Landing on the water in mode 1, the arms stopping over the draft; motors out, the seed fall's splash.
"""

from __future__ import annotations

import math

import numpy as np
import osprey_sim

from osprey.params import DESIGN, _toml, ns
from osprey.recon import cyclone, cyclone_dynamics, flight
from osprey.recon.params import RECON

G = 9.81


def inputs():
    return ns(_toml(RECON / "cyclone.toml")["water"])


def _thickness(t: float, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """A symmetric NACA 4-digit section's half-thickness, in chords, at chord stations from the leading edge."""
    x = (1 - np.cos(np.linspace(0, math.pi, n))) / 2
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    return x, yt


def _cap(r: float, h: float) -> tuple[float, float]:
    """A sphere's cap of height h from its bottom: volume, and its centroid's height above the bottom."""
    h = min(max(h, 0.0), 2 * r)
    if h <= 0:
        return 0.0, 0.0
    v = math.pi * h * h * (3 * r - h) / 3
    return v, r - 3 * (2 * r - h) ** 2 / (4 * (3 * r - h))


def afloat(p, d: dict, cy=None, wt=None, m: dict | None = None) -> dict:
    """Standing on the arms, B centred: draft from the trailing edge, A's props and the camera above the
    water, the metacentric height, natural periods, and what B has to hold."""
    cy, wt = cy or cyclone.inputs(), wt or inputs()
    m = m or cyclone.mass(p, d, cy)
    g = cyclone.geometry(p, d, cy)
    c, arm, r0, R, N = g["chord_m"], g["arm_m"], g["r0_m"], g["R_m"], cy.arms
    rho_w = p.water.density_kgm3
    M = m["mass_kg"]
    need = M / rho_w
    x, yt = _thickness(p.wing.t_over_c)
    z = (1 - x) * c                                              # height above the trailing edge
    w = 2 * yt * c                                               # thickness, m
    dz = np.gradient(z)

    def arm_below(h):
        """One arm's volume under a waterline h above the trailing edge, and its centroid's height."""
        wet = z <= h
        a = float(np.sum(w[wet] * np.abs(dz[wet])))
        zc = float(np.sum(w[wet] * z[wet] * np.abs(dz[wet]))) / a if a > 0 else 0.0
        return a * arm, zc

    z_hub = (1 - wt.axis_frac) * c

    def below(h):
        va, za = arm_below(h)
        vh, zh = _cap(r0, h - (z_hub - r0))
        v = N * va + vh
        return v, (N * va * za + vh * (z_hub - r0 + zh)) / v if v > 0 else 0.0

    v_sealed = below(1e3)[0]
    lo, hi = 0.0, z_hub + r0
    sinks = below(hi)[0] < need
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if below(mid)[0] < need else (lo, mid)
    h = (lo + hi) / 2
    V, kb = below(h)
    # The waterplane: three strips, each the section's thickness where the water cuts it, out to the tips,
    # and the hub's circle if the water reaches it.
    w_wl = float(np.interp(h, z[::-1], w[::-1]))
    a_hub = math.sqrt(max(r0 * r0 - (h - z_hub) ** 2, 0.0))
    I_wp = w_wl * (R ** 3 - r0 ** 3) / 3 * (N / 2) + math.pi * a_hub ** 4 / 4
    A_wp = N * w_wl * arm + math.pi * a_hub ** 2
    # The weights: A's motors on top, the arms at their sections' centroid, everything else at the hub.
    z_arm = float(np.sum(w * z * np.abs(dz)) / np.sum(w * np.abs(dz)))
    z_mot = c + wt.mount_m / 2
    arms_kg = N * g["arm_kg"]
    rest = M - m["motor_kg"] - arms_kg
    kg = (m["motor_kg"] * z_mot + arms_kg * z_arm + rest * z_hub) / M
    bm = I_wp / V
    gm = kb + bm - kg
    I = cyclone.inertia(p, d, cy, m["motor_kg"])
    k_roll = math.sqrt(I / 2 / M)
    # B holding each arm chord-up: the arm's buoyancy below B's axis and A's motor above it tip it over, the
    # arm's own weight below the axis rights it; the twist about the arm's axis is its own.
    va, za = arm_below(h)
    per_rad = (rho_w * G * va * (z_hub - za) + m["motor_kg"] / N * G * (z_mot - z_hub)
               - g["arm_kg"] * G * (z_hub - z_arm))
    return {"mass_kg": M, "displaced_l": need * 1e3, "sealed_l": v_sealed * 1e3, "reserve": v_sealed / need,
            "sinks": sinks, "draft_m": h, "chord_m": c, "hub_wet": h > z_hub - r0, "prop_height_m": c + wt.mount_m - h,
            "mount_more_m": max(wt.prop_height_min_m - (c + wt.mount_m - h), 0.0),
            "camera_height_m": z_hub - wt.gimbal_drop_m - h, "kb_m": kb, "bm_m": bm, "kg_m": kg, "gm_m": gm,
            "waterplane_m2": A_wp, "period_roll_s": 2 * math.pi * k_roll / math.sqrt(G * gm) if gm > 0 else math.inf,
            "period_heave_s": 2 * math.pi * math.sqrt(M / (rho_w * G * A_wp)),
            "b_hold_nm_10deg": per_rad * math.sin(math.radians(10)), "b_torque_nm": wt.b_torque_nm,
            "z_hub_m": z_hub, "arm_m": arm, "r0_m": r0, "R_m": R}


def windage(p, d: dict, cy, wt, fl: dict, V: float) -> dict:
    """Afloat in a wind: the arms above the water as three flat plates (1.5 times one arm's force along the
    wind, as in mode 1), the arms below as keels; the heel on the metacentric height, the lever between the
    two areas' centres; the drift where the keels' pull matches the wind's."""
    dy = cyclone_dynamics.inputs()
    above, below = fl["arm_m"] * (fl["chord_m"] - fl["draft_m"]), fl["arm_m"] * fl["draft_m"]
    F = 0.5 * flight.rho(0.0) * V * V * dy.wind_cd * 1.5 * above
    W = fl["mass_kg"] * G
    heel = math.degrees(math.atan(F * fl["chord_m"] / 2 / (W * fl["gm_m"]))) if fl["gm_m"] > 0 else 90.0
    drift = V * math.sqrt(flight.rho(0.0) * above / (p.water.density_kgm3 * below)) if below > 0 else math.inf
    return {"force_n": F, "heel_deg": heel, "drift_ms": drift}


def launch(p, d: dict, cy, wt, fl: dict, m: dict, dt: float = 0.001) -> dict:
    """A at its burst from afloat until the trailing edges leave the water: buoyancy falling away, the arms'
    skin friction on both faces, the surface tension along both faces' waterlines, the weight. Stepped in
    Rust (sim/src/rotor.rs)."""
    rho_w = p.water.density_kgm3
    M = m["mass_kg"]
    W = M * G
    T = sum(n * cyclone_dynamics.a_max(cy, P, 0.0) for _, n, P in cyclone_dynamics.rings(p, d, cy, m))
    N, arm, h0 = cy.arms, fl["arm_m"], fl["draft_m"]
    x, yt = _thickness(p.wing.t_over_c)
    c = fl["chord_m"]
    z, w = (1 - x) * c, 2 * yt * c
    dz = np.abs(np.gradient(z))
    order = np.argsort(z)
    cum = np.cumsum((w * dz)[order]) * arm * N
    tension = wt.surface_tension_nm * 2 * N * arm
    r = osprey_sim.cyclone_water_launch({"thrust_n": T, "mass_kg": M, "rho_w": rho_w, "draft_m": h0,
                                         "zs": z[order].tolist(), "cum": cum.tolist(), "tension_n": tension,
                                         "skin_cf": wt.skin_cf, "wetted_per_m": 2 * N * arm, "dt": dt})
    return {"thrust_n": T, "thrust_to_weight": T / W, "t_clear_s": r["t"], "v_exit_ms": r["v"],
            "surface_tension_n": tension, "surface_tension_of_weight": tension / W,
            "buoyancy_n": rho_w * G * fl["displaced_l"] / 1e3}


def sea(p, d: dict, cy, wt, fl: dict, m: dict, lr: dict) -> list[dict]:
    """Each sea state: the design wave's slope with the wind's heel against the tilt A can still lift at, the
    wave's surface speed against mode 1's climb, the wind against mode 1's lean, and the drift afloat.
    The design wave and the winds are the tailsitter's (the same sea)."""
    from osprey.recon import cyclone_modes
    from osprey.recon.params import load

    fp = load("sar-offshore", payload="gimbal", airframe="tailsitter").floats
    md = cyclone_modes.inputs()
    dy = cyclone_dynamics.inputs()
    v1 = cyclone_dynamics.wind_one_max(p, d, cy, dy, m)
    v2 = cyclone_dynamics.wind(p, d, cy, m)["two_max_ms"]
    rows = []
    for (k, s), V in zip(sorted(_toml(DESIGN / "sea.toml")["sea"].items()), fp.wind_ms):
        H = fp.design_wave * s["hs_m"]
        T = s["tp_s"]
        lam = G * T * T / (2 * math.pi)
        slope = math.degrees(math.atan(math.pi * H / lam))
        surf = math.pi * H / T
        wd = windage(p, d, cy, wt, fl, V)
        rows.append({"state": k, "label": s["label"], "hs_m": s["hs_m"], "tp_s": T, "wind_ms": V, "slope_deg": slope,
                     "heel_deg": wd["heel_deg"], "drift_ms": wd["drift_ms"], "surface_ms": surf,
                     "tilt_ok": slope + wd["heel_deg"] <= wt.tilt_max_deg, "outrun_ok": surf < md.climb1_ms,
                     "mode1_ok": V <= v1, "mode2_ok": V <= v2,
                     "ok": slope + wd["heel_deg"] <= wt.tilt_max_deg and surf < md.climb1_ms and V <= v1})
    return rows


def assess(p, d: dict, cy=None, m: dict | None = None) -> dict:
    from osprey.recon import cyclone_modes

    cy, wt = cy or cyclone.inputs(), inputs()
    m = m or cyclone.mass(p, d, cy)
    md = cyclone_modes.inputs()
    fl = afloat(p, d, cy, wt, m)
    lr = launch(p, d, cy, wt, fl, m)
    au = cyclone.autorotation(p, d, cy, m)
    return {"afloat": fl, "launch": lr, "sea": sea(p, d, cy, wt, fl, m, lr), "water": vars(wt),
            "landing_g": 1 + md.descent1_ms ** 2 / (2 * G * fl["draft_m"]), "descent_ms": md.descent1_ms,
            "seed_ms": au["sink_ms"], "seed_g": au["splash_g"], "seed_flared_g": au["flared_g"]}


def report(a: dict, title: str) -> str:
    """The sheet: afloat, B holding the arms, the launch, the sea, landing."""
    fl, lr, wt = a["afloat"], a["launch"], a["water"]
    yes = lambda ok: "✓" if ok else "✗"                                # noqa: E731
    lines = [f"# The Cyclone on the water: {title}", "",
             "Afloat with B centred it stands on its three arms' trailing edges, chords up and A's props up, as in "
             "mode 1: three thin keels 120° apart with the hub on top. REF inputs in `[water]` of "
             "`design/recon/cyclone.toml`.", "",
             "## Afloat", "",
             "| | |", "|---|---|",
             f"| Displaces | {fl['displaced_l']:.2f} L of {fl['sealed_l']:.1f} L sealed ({fl['reserve']:.1f}×) |",
             f"| Draft | {fl['draft_m'] * 100:.1f} cm up a {fl['chord_m'] * 100:.1f} cm chord"
             + (", the hub's bottom in the water" if fl["hub_wet"] else "") + " |",
             f"| A's props | {fl['prop_height_m'] * 100:.0f} cm above the water "
             + (f"✗ (the tailsitter's rule is {wt['prop_height_min_m'] * 100:.0f} cm: {fl['mount_more_m'] * 100:.0f} cm "
                "more motor mount)" if fl["mount_more_m"] > 0 else "✓") + " |",
             f"| The camera | {fl['camera_height_m'] * 100:+.0f} cm " + ("✗ in the water" if fl["camera_height_m"] < 0.02 else "✓")
             + " |",
             f"| Metacentric height | **{fl['gm_m']:.2f} m**: the waterplane is three strips out to the tips (BM "
             f"{fl['bm_m']:.2f} m) |",
             f"| Natural periods | roll {fl['period_roll_s']:.2f} s, heave {fl['period_heave_s']:.2f} s: it rides the waves' "
             "slope |",
             f"| Each B holding its arm chord-up | {fl['b_hold_nm_10deg']:.2f} N m at 10° off, against "
             f"{fl['b_torque_nm']:g} N m it can hold |", "",
             "## The launch", "",
             f"A at its burst ({lr['thrust_to_weight']:.2f} × the weight) with the buoyancy still under it: the arms slide up "
             f"out of the water edge first and clear it in **{lr['t_clear_s']:.2f} s** at {lr['v_exit_ms']:.1f} m/s. The "
             f"surface tension along both faces is {lr['surface_tension_n']:.2f} N ({lr['surface_tension_of_weight']:.1%} of "
             "the weight) and the skin friction less: there is nothing to break free of. Then mode 1 to the clearance.", "",
             "## The sea", "",
             "Each sea state's design wave and typical wind (the tailsitter's). Afloat it rides the slope; A can still lift "
             f"tilted {wt['tilt_max_deg']:g}°. The wave's surface rises at the speed shown; mode 1's climb has to outrun it.", "",
             "| Sea | Wind | Slope + heel | Surface | Mode 1 holds station | Mode 2 holds station | Drift afloat | Launch |",
             "|---|---|---|---|---|---|---|---|"]
    for r in a["sea"]:
        lines.append(f"| {r['state']} {r['label']} | {r['wind_ms']:g} m/s | {yes(r['tilt_ok'])} "
                     f"{r['slope_deg'] + r['heel_deg']:.0f}° | {yes(r['outrun_ok'])} {r['surface_ms']:.1f} m/s | "
                     f"{yes(r['mode1_ok'])} | {yes(r['mode2_ok'])} | {r['drift_ms']:.2f} m/s | {yes(r['ok'])} |")
    lines += ["", "## Landing", "",
              f"In mode 1 at {a['descent_ms']:g} m/s the arms enter edge first and stop over the draft: "
              f"{a['landing_g']:.1f} g. Motors out, the seed fall meets the water at {a['seed_ms']:.1f} m/s: "
              f"{a['seed_g']:.1f} g unflared, {a['seed_flared_g']:.1f} g if the spin is spent on a flare. After a seed fall it "
              "lies flat, A's props in the water; B has to stand the arms up before it can launch.", "",
              "Not modelled: the arms' twist from flat to standing in the water, waves breaking over it, and the hub's seals."]
    return "\n".join(lines) + "\n"
