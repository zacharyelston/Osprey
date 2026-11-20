"""The sailplane: a 4.8 m thermal-soaring relay with a truss-braced wing, from a handoff package to parts.

A laminar body of revolution (a Myring body) carries a thin, high-aspect-ratio wing in three pieces. The wing
is braced as NASA's transonic truss-braced wing is: one brace a side runs from low on the body up to the
wing at about mid-span, with a jury strut from the brace up to the wing. The brace is an aerofoil and lifts.
Everything is read from design/recon/sailplane.toml.

This module:
- lays the wing out as a frame (`model`): the spar from tip to tip, pinned to the body at its saddle, the two
  braces pinned at their roots, and the jury struts;
- flies it through a pull-up and a push-over (`loads`, `solve`, `evaluate`): an elliptic lift on the wing, the
  braces' own share on the braces, less the wing's weight, for each tube's axial load, bending, Euler buckling
  and stress; the same wing with no braces, and the braces' wing station swept (`sweep`);
- builds the drag up by components (`aero`) as Ting, Reynolds, Nguyen and Totah do for the truss-braced wing
  (AIAA, "Aerodynamic Analysis of the Truss-Braced Wing Aircraft Using Vortex-Lattice Superposition
  Approach"): flat-plate skin friction with transition and form factors for the wing, braces, tail and body,
  plus induced drag, for the glide ratio and sink with and without the braces;
- lists every tube to cut (`cut_list`, `bom`) and checks the package against itself (`checks`);
- writes the parts as parametric OpenSCAD (`export`): src/osprey/recon/scad holds the modules, and `export`
  writes params.scad beside them.

Stations in millimetres: x aft from the nose tip, y to starboard, z up from the body's axis.
"""

from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path

import numpy as np

from osprey.params import _toml, ns
from osprey.recon.params import RECON

G = 9.81
SCAD = Path(__file__).parent / "scad"
WINGS = ("day", "night")


def inputs():
    return ns(_toml(RECON / "sailplane.toml"))


# ---- the body and the wing section ------------------------------------------------------------------------

def myring_r(f, x, clamp: bool = True):
    """The body's radius at station x (mm). The tail cone's cubic closes at the full length; with `clamp`
    it is not let below the spinner's radius, as the package's OpenSCAD has it."""
    a, b, R = f.nose_mm, f.mid_mm, f.radius_mm
    c = f.length_mm - a - b
    x = np.asarray(x, float)
    nose = R * np.clip(1.0 - ((np.clip(x, 0.0, a) - a) / a) ** 2, 0.0, None) ** (1.0 / f.nose_exp)
    dx = np.clip(x - a - b, 0.0, None)
    t = math.tan(math.radians(f.tail_angle_deg))
    tail = R - (3 * R / c**2 - t / c) * dx**2 + (2 * R / c**3 - t / c**2) * dx**3
    if clamp:
        tail = np.maximum(tail, f.spinner_r_mm)
    return np.where(x < a, nose, np.where(x <= a + b, R, tail))


def airfoil(name: str):
    """A section's points as given (from the trailing edge over the top and back), and its upper and lower
    surfaces from the nose aft, in chord units."""
    pts = np.loadtxt(RECON / "airfoils" / f"{name}.dat", skiprows=1)
    i = int(np.argmin(pts[:, 0]))
    return pts, pts[: i + 1][::-1], pts[i:]


def surface_z(s, x_mm):
    """The centre section's upper and lower surface heights (mm) at station x."""
    w = s.wing
    _, up, lo = airfoil(w.airfoil)
    xc = (np.asarray(x_mm, float) - w.le_x_mm) / w.chord_mm
    return (w.chord_z_mm + w.chord_mm * np.interp(xc, up[:, 0], up[:, 1]),
            w.chord_z_mm + w.chord_mm * np.interp(xc, lo[:, 0], lo[:, 1]))


# ---- the wing as a frame -------------------------------------------------------------------------------

def half_span(s) -> float:
    return s.wing.span_mm / 2


def joint_y(s) -> float:
    """Where the outer panels plug on."""
    return s.wing.center_span_mm / 2


def spar_xz(s, y: float = 0.0) -> tuple[float, float]:
    """The spar's centre at span station y: mid-way through the section at its chord station, rising with
    the outer panels' dihedral."""
    w = s.wing
    x = w.le_x_mm + s.spar.x_frac * w.chord_mm
    up, lo = surface_z(s, x)
    return x, float(up + lo) / 2 + max(abs(y) - joint_y(s), 0.0) * math.tan(math.radians(w.dihedral_deg))


def strut_points(s, strut_y: float | None = None) -> dict:
    """One brace, starboard: its root pin outside the hull on the front main bulkhead, its wing pin under the
    wing's lower skin, and where the jury strut leaves it."""
    st = s.strut
    y = half_span(s) * st.y_frac if strut_y is None else strut_y
    r = float(myring_r(s.fuselage, st.root_x_mm))
    root = np.array([st.root_x_mm, math.sqrt(r**2 - st.root_z_mm**2) + st.root_out_mm, st.root_z_mm])
    x, z = spar_xz(s, y)
    wing = np.array([x, y, z - s.spar.od_mm / 2 - s.wing.skin_mm - st.wing_drop_mm])
    return {"root": root, "wing": wing, "jury": root + s.jury.frac * (wing - root), "y": y}


def section(sec) -> tuple[float, float, float]:
    """A tube's area (mm^2), second moment (mm^4) and half-depth (mm): round or square."""
    od, i = sec.od_mm, sec.od_mm - 2 * sec.wall_mm
    if sec.shape == "square":
        return od**2 - i**2, (od**4 - i**4) / 12, od / 2
    return math.pi / 4 * (od**2 - i**2), math.pi / 64 * (od**4 - i**4), od / 2


def _sec(s, kind: str):
    return {"spar": s.spar, "panel": s.spar, "bracket": s.spar, "strut": s.strut, "jury": s.jury}[kind]


def model(s, strut_y: float | None = None, braced: bool = True) -> tuple[dict, list[dict], dict]:
    """Nodes (name -> xyz), members and supports (name -> fixed degrees of freedom). The outer panels' spar
    is taken as the centre section's (REF)."""
    sp = strut_points(s, strut_y)
    h, jy = half_span(s), joint_y(s)
    ys = {0.0, s.spar.saddle_y_mm, jy, h} | {jy + k * (h - jy) / 4 for k in range(1, 4)}
    if braced:
        ys |= {sp["y"], float(sp["jury"][1])}
    ys = sorted(ys)
    ys = [-y for y in ys[:0:-1]] + ys
    nodes, members = {}, []

    def add(group, a, b, kind):
        members.append({"name": f"{a}>{b}", "group": group, "a": a, "b": b, "kind": kind})

    for y in ys:
        x, z = spar_xz(s, y)
        nodes[f"W{y:+.0f}"] = np.array([x, y, z])
    for y1, y2 in zip(ys[:-1], ys[1:]):
        inner = max(abs(y1), abs(y2)) <= jy + 1e-6
        add("centre spar" if inner else "outer panel spar", f"W{y1:+.0f}", f"W{y2:+.0f}", "spar" if inner else "panel")
    fixed = {f"W{sg * s.spar.saddle_y_mm:+.0f}": [0, 1, 2, 4] for sg in (-1, 1)}
    if braced:
        for sg, side in ((1, "+"), (-1, "-")):
            m = np.array([1, sg, 1])
            nodes[f"R{side}"], nodes[f"M{side}"], nodes[f"K{side}"] = sp["root"] * m, sp["jury"] * m, sp["wing"] * m
            add("brace", f"R{side}", f"M{side}", "strut")
            add("brace", f"M{side}", f"K{side}", "strut")
            add("bracket", f"K{side}", f"W{sg * sp['y']:+.0f}", "bracket")
            add("jury strut", f"M{side}", f"W{sg * sp['jury'][1]:+.0f}", "jury")
            fixed[f"R{side}"] = [0, 1, 2]
    return nodes, members, fixed


def _k_local(E, Gs, A, I, L) -> np.ndarray:
    k = np.zeros((12, 12))
    a, t = E * A / L, Gs * 2 * I / L
    b1, b2, b3, b4 = 12 * E * I / L**3, 6 * E * I / L**2, 4 * E * I / L, 2 * E * I / L
    terms = [(0, 0, a), (0, 6, -a), (6, 6, a), (3, 3, t), (3, 9, -t), (9, 9, t),
             (1, 1, b1), (1, 5, b2), (1, 7, -b1), (1, 11, b2), (5, 5, b3), (5, 7, -b2), (5, 11, b4),
             (7, 7, b1), (7, 11, -b2), (11, 11, b3),
             (2, 2, b1), (2, 4, -b2), (2, 8, -b1), (2, 10, -b2), (4, 4, b3), (4, 8, b2), (4, 10, b4),
             (8, 8, b1), (8, 10, b2), (10, 10, b3)]
    for i, j, v in terms:
        k[i, j] = k[j, i] = v
    return k


def _rotation(d: np.ndarray) -> np.ndarray:
    ex = d / np.linalg.norm(d)
    ref = np.array([0.0, 0.0, 1.0]) if abs(ex[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    ey = np.cross(ref, ex)
    ey /= np.linalg.norm(ey)
    return np.array([ex, ey, np.cross(ex, ey)])


def solve(s, nodes: dict, members: list[dict], fixed: dict, F: dict) -> dict:
    """The frame under nodal forces F (name -> [fx, fy, fz], N). Joints carry moment. Returns each member's
    axial load (N, tension positive) and largest end moment (N mm), the supports' reactions and every node's
    rise."""
    idx = {k: i for i, k in enumerate(nodes)}
    E, Gs = s.carbon.e_gpa * 1e3, s.carbon.g_gpa * 1e3
    K = np.zeros((6 * len(nodes),) * 2)
    els = []
    for m in members:
        a, b = nodes[m["a"]], nodes[m["b"]]
        A, I, _ = section(_sec(s, m["kind"]))
        L = float(np.linalg.norm(b - a))
        k = _k_local(E, Gs, A, I, L)
        T = np.kron(np.eye(4), _rotation(b - a))
        dof = np.r_[6 * idx[m["a"]] + np.arange(6), 6 * idx[m["b"]] + np.arange(6)]
        K[np.ix_(dof, dof)] += T.T @ k @ T
        els.append((k, T, dof, L))
    f = np.zeros(6 * len(nodes))
    for k_, v in F.items():
        f[6 * idx[k_]: 6 * idx[k_] + 3] += v
    fx = np.array([6 * idx[k_] + d for k_, dofs in fixed.items() for d in dofs])
    free = np.setdiff1d(np.arange(len(f)), fx)
    u = np.zeros_like(f)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free])
    r = K @ u - f
    out = []
    for m, (k, T, dof, L) in zip(members, els):
        q = k @ T @ u[dof]
        out.append({"length_mm": L, "axial_n": float(q[6]),
                    "moment_nmm": float(max(math.hypot(q[4], q[5]), math.hypot(q[10], q[11])))})
    return {"members": out, "reactions_n": {k_: r[6 * idx[k_]: 6 * idx[k_] + 3].tolist() for k_ in fixed},
            "rise_mm": {k_: float(u[6 * idx[k_] + 2]) for k_ in nodes}, "applied_z_n": float(f[2::6].sum())}


# ---- the loads -----------------------------------------------------------------------------------------

def _lift(s, total_n: float, y0: float, y1: float) -> tuple[float, float]:
    """An elliptic lift's force (N) between span stations y0 and y1 (mm), and its moment about y0 (N mm)."""
    h = s.wing.span_mm / 2
    y = np.linspace(y0, y1, 401)
    l = 2 * total_n / (math.pi * h) * np.sqrt(np.clip(1 - (y / h) ** 2, 0, None))
    return float(np.trapezoid(l, y)), float(np.trapezoid(l * (y - y0), y))


def loads(s, nodes: dict, wings: str, n: float) -> tuple[dict, dict]:
    """Nodal forces at n g. The wing carries all the lift but the braces' share (none on the body, no tail
    load), elliptic over the span, put on the spar's nodes; each brace's share goes on its own three nodes.
    The wing's weight comes off where it is."""
    w = s.wing
    auw = s.mass.auw_kg if wings == "day" else s.mass.auw_night_kg
    m_panel = w.panel_day_kg if wings == "day" else w.panel_night_kg
    braced = "K+" in nodes
    share = s.aero.brace_lift_frac if braced else 0.0
    L, jy, h = n * G * auw, joint_y(s), half_span(s)
    F = {}

    def add(k, fz):
        F[k] = F.get(k, np.zeros(3)) + np.array([0.0, 0.0, fz])

    spar = sorted((p[1], k) for k, p in nodes.items() if k[0] == "W")
    for i, (y, k) in enumerate(spar):
        lo = (spar[i - 1][0] + y) / 2 if i else y
        hi = (spar[i + 1][0] + y) / 2 if i < len(spar) - 1 else y
        add(k, _lift(s, L * (1 - share), lo, hi)[0])
        for a, b, kg, length in ((-h, -jy, m_panel, h - jy), (-jy, jy, w.center_kg, 2 * jy), (jy, h, m_panel, h - jy)):
            add(k, -n * G * kg * max(min(hi, b) - max(lo, a), 0.0) / length)
    if braced:
        for side in "+-":
            for k, part in ((f"R{side}", 0.25), (f"M{side}", 0.5), (f"K{side}", 0.25)):
                add(k, L * share / 2 * part)
    return F, {"wings": wings, "n": n, "auw_kg": auw, "lift_n": L, "brace_lift_n": L * share / 2}


def evaluate(s, members: list[dict], res: dict) -> list[dict]:
    """Each member's margins at ultimate (limit x fs): Euler buckling between its ends, pinned, and stress,
    axial plus bending, against the carbon's allowables."""
    E, fs, rows = s.carbon.e_gpa * 1e3, s.loads.fs, []
    for m, r in zip(members, res["members"]):
        A, I, c = section(_sec(s, m["kind"]))
        N, M, L = r["axial_n"], r["moment_nmm"], r["length_mm"]
        pcr = math.pi**2 * E * I / L**2
        sigma = abs(N) / A + M * c / I
        allow = s.carbon.comp_allow_mpa if N < 0 else s.carbon.tens_allow_mpa
        rows.append({**m, **r, "pcr_n": pcr, "sigma_mpa": sigma,
                     "u_buckle": fs * max(-N, 0.0) / pcr, "u_stress": fs * sigma / allow})
    return rows


def cases(s) -> list[tuple[str, str, float]]:
    return [(f"{w} wings, {n:+g} g", w, n) for n in (s.loads.n, s.loads.n_neg) for w in WINGS]


def analyse(s, strut_y: float | None = None, braced: bool = True) -> dict:
    """The wing through every case: each member's loads and margins, and the numbers that sum the wing up."""
    nodes, members, fixed = model(s, strut_y, braced)
    jy, h = joint_y(s), half_span(s)
    out = {"nodes": {k: v.tolist() for k, v in nodes.items()}, "cases": {}, "braced": braced,
           "strut_y_mm": strut_points(s, strut_y)["y"] if braced else None}
    for name, wings, n in cases(s):
        F, summary = loads(s, nodes, wings, n)
        res = solve(s, nodes, members, fixed, F)
        rows = evaluate(s, members, res)
        spar = [r for r in rows if r["kind"] in ("spar", "panel")]
        at_joint = [r for r in spar if f"W{jy:+.0f}" in (r["a"], r["b"])]
        brace = [r for r in rows if r["group"] == "brace"]
        out["cases"][name] = {
            **summary, "members": rows, "applied_z_n": res["applied_z_n"], "reactions_n": res["reactions_n"],
            "spar_moment_nm": max(r["moment_nmm"] for r in spar) / 1e3,
            "root_moment_nm": max(r["moment_nmm"] for r in spar if "W+0" in (r["a"], r["b"])) / 1e3,
            "joiner_moment_nm": max(r["moment_nmm"] for r in at_joint) / 1e3,
            "tip_rise_mm": res["rise_mm"][f"W{h:+.0f}"],
            "brace_axial_n": max((r["axial_n"] for r in brace), key=abs) if brace else 0.0,
            "spar_axial_n": min(r["axial_n"] for r in spar),
            "u_max": max(max(r["u_buckle"], r["u_stress"]) for r in rows)}
    out["governing"] = max(out["cases"], key=lambda c: out["cases"][c]["u_max"])
    return out


def sweep(s) -> list[dict]:
    """The pull-up with no braces, and with the braces meeting the wing at each station of the sweep."""
    pull = cases(s)[0][0]
    push = cases(s)[2][0]
    rows = []
    for y in [None, *s.loads.sweep_y_mm]:
        a = analyse(s, y, braced=y is not None)
        c, d = a["cases"][pull], a["cases"][push]
        worst = max((max(r["u_buckle"], r["u_stress"]) for cc in a["cases"].values() for r in cc["members"]
                     if r["group"] == "brace"), default=0.0)
        rows.append({"strut_y_mm": y, "spar_moment_nm": c["spar_moment_nm"], "root_moment_nm": c["root_moment_nm"],
                     "tip_rise_mm": c["tip_rise_mm"], "brace_tension_n": c["brace_axial_n"],
                     "brace_compression_n": -d["brace_axial_n"], "spar_axial_n": c["spar_axial_n"],
                     "brace_used": worst, "u_max": max(cc["u_max"] for cc in a["cases"].values())})
    return rows


# ---- the drag, by components ---------------------------------------------------------------------------

def _cf(re_len: float, x_frac: float) -> float:
    """A flat plate's mean skin friction with transition at x_frac of its length (Ting et al., Eq. 3):
    laminar to there, turbulent after."""
    if x_frac >= 1.0:
        return 1.328 / math.sqrt(re_len)
    re_x = max(re_len * x_frac, 1.0)
    return x_frac * 1.328 / math.sqrt(re_x) + 0.072 * re_len**-0.2 - x_frac * 0.072 * re_x**-0.2


def brace_length_m(s) -> float:
    sp = strut_points(s)
    return float(np.linalg.norm(sp["wing"] - sp["root"])) / 1e3


def wing_area_m2(s) -> float:
    w = s.wing
    return (w.center_span_mm * w.chord_mm + (w.span_mm - w.center_span_mm) * (w.chord_mm + w.tip_chord_mm) / 2) / 1e6


def aero(s) -> dict:
    """Zero-lift drag by components (skin friction x form factor x wetted area, their Eqs. 1-2) and induced
    drag, at each loiter speed, with the braces and without. Left out, as there: interference where the
    parts meet, and here also the jury struts, gaps, antennas and the stopped propeller."""
    a, w, f, fl = s.aero, s.wing, s.fuselage, s.flight
    S = wing_area_m2(s)
    mac = S / (w.span_mm / 1e3)
    _, up, lo = airfoil(w.airfoil)
    xc = np.linspace(0, 1, 201)
    tc = float(np.max(np.interp(xc, up[:, 0], up[:, 1]) - np.interp(xc, lo[:, 0], lo[:, 1])))
    x = np.linspace(0.0, f.truncate_mm, 2000)
    r = myring_r(f, x)
    s_body = float(np.sum(math.pi * (r[1:] + r[:-1]) * np.hypot(np.diff(x), np.diff(r)))) / 1e6
    fine = f.length_mm / (2 * f.radius_mm)

    def foil_k(t):
        return 1 + 2 * t + 100 * t**4

    parts = {   # name: (length m, wetted area m^2, form factor, transition)
        "wing": (mac, 2 * S * (1 + 0.2 * tc), foil_k(tc), a.transition.wing),
        "braces": (s.strut.chord_mm / 1e3, 2 * 2 * brace_length_m(s) * s.strut.chord_mm / 1e3 * (1 + 0.2 * s.strut.t_over_c),
                   foil_k(s.strut.t_over_c), a.transition.brace),
        "tail": (a.tail_chord_mm / 1e3, 2 * a.tail_area_m2 * (1 + 0.2 * a.tail_t_over_c), foil_k(a.tail_t_over_c),
                 a.transition.tail),
        "body": (f.truncate_mm / 1e3, s_body, 1 + 1.5 / fine**1.5 + 7 / fine**3, a.transition.fuselage),
    }
    ar = (w.span_mm / 1e3) ** 2 / S
    rows = []
    for v in a.speeds_ms:
        cd0 = {k: _cf(v * ln / a.nu_m2s, tr) * kf * sw / S for k, (ln, sw, kf, tr) in parts.items()}
        q = 0.5 * fl.rho_kgm3 * v**2
        cl = s.mass.auw_kg * G / (q * S)
        cdi = cl**2 / (math.pi * ar * a.oswald)
        row = {"v_ms": v, "cl": cl, "cd0": cd0, "cdi": cdi, "re_wing": v * mac / a.nu_m2s}
        for label, total in (("braced", sum(cd0.values())), ("unbraced", sum(cd0.values()) - cd0["braces"])):
            ld = cl / (total + cdi)
            row[label] = {"cd": total + cdi, "l_over_d": ld, "sink_ms": v / ld}
        rows.append(row)
    return {"area_m2": S, "ar": ar, "wing_t_over_c": tc, "body_wetted_m2": s_body, "rows": rows,
            "brace_area_frac": 2 * brace_length_m(s) * s.strut.chord_mm / 1e3 / S}


# ---- the cut list --------------------------------------------------------------------------------------

def cut_list(s) -> list[dict]:
    sp, j = strut_points(s), s.joiner
    x, z = spar_xz(s, float(sp["jury"][1]))
    jury = z - s.spar.od_mm / 2 - s.wing.skin_mm - s.strut.wing_drop_mm - float(sp["jury"][2])
    rear = ns({"shape": "round", "od_mm": s.spar.rear_od_mm, "wall_mm": (s.spar.rear_od_mm - s.spar.rear_id_mm) / 2})
    joiner = ns({"shape": "square", "od_mm": j.size_mm, "wall_mm": j.wall_mm})
    return [
        {"part": "centre spar", "sec": s.spar, "qty": 1, "cut_mm": s.wing.center_span_mm, "note": "joiners slide into its ends"},
        {"part": "rear spar", "sec": rear, "qty": 1, "cut_mm": s.wing.center_span_mm, "note": "ahead of the flaps"},
        {"part": "brace tube", "sec": s.strut, "qty": 2,
         "cut_mm": float(np.linalg.norm(sp["wing"] - sp["root"])) - 2 * s.strut.seat_mm, "note": "pin to pin less two end fittings"},
        {"part": "jury strut", "sec": s.jury, "qty": 2, "cut_mm": jury - 2 * s.jury.seat_mm, "note": "pin to pin less two end fittings"},
        {"part": "wing joiner", "sec": joiner, "qty": 2, "cut_mm": j.engage_mm + j.panel_engage_mm, "note": "into the spar and the outer panel"},
    ]


def bom(s, cuts: list[dict]) -> list[dict]:
    rho = s.carbon.rho_kgm3 * 1e-9
    rows = []
    for c in cuts:
        sec = c["sec"]
        rows.append({"item": c["part"], "stock": f"carbon {sec.shape} tube {sec.od_mm:g} x {sec.od_mm - 2 * sec.wall_mm:g} mm",
                     "qty": c["qty"], "cut_mm": c["cut_mm"], "note": c["note"],
                     "mass_g": c["qty"] * c["cut_mm"] * section(sec)[0] * rho * 1e3})
    for b in s.bulkhead:
        r = float(myring_r(s.fuselage, b.x_mm)) - s.fuselage.wall_mm
        rows.append({"item": f"ring bulkhead, x = {b.x_mm:g}", "stock": f"{b.material} plate, {b.t_mm:g} mm", "qty": 1,
                     "cut_mm": 2 * r, "note": f"ring {2 * r:.1f} OD x {2 * max(10.0, r - b.web_mm):.1f} ID; "
                                             f"blank {2 * r:.0f} x {2 * r:.0f}", "mass_g": None})
    ra = s.rails
    rows.append({"item": "CG trim rail", "stock": f"{ra.material}, {ra.section_mm:g} mm", "qty": 2,
                 "cut_mm": ra.x_mm[1] - ra.x_mm[0], "note": f"y = +/-{ra.y_mm:g}, z = {ra.z_mm:g}", "mass_g": None})
    return rows


# ---- the belly's flat and the flaps --------------------------------------------------------------------

def nadir_flat(s) -> dict:
    """A flat for the camera's window: the body cut by one plane, through the hull where the pane's two ends
    are, wide enough there for the pane. A convex body cut by a plane leaves a flat facet and no step, so
    the flat follows the nose's slope instead of being recessed across it."""
    nd, f = s.nadir, s.fuselage
    pane = nd.window_mm + 2 * nd.ledge_mm
    xc = (nd.x_mm[0] + nd.x_mm[1]) / 2
    xa, xb = xc - pane / 2 - nd.margin_mm, xc + pane / 2 + nd.margin_mm
    hw = pane / 2 + nd.margin_mm
    za, zb = (-math.sqrt(float(myring_r(f, x)) ** 2 - hw**2) for x in (xa, xb))
    slope = (zb - za) / (xb - xa)
    x = np.arange(0.0, f.truncate_mm, 1.0)
    r = myring_r(f, x)
    cut = r > -(za + slope * (x - xa))                 # where the plane is inside the hull
    half_w = np.sqrt(np.clip(r**2 - (za + slope * (x - xa)) ** 2, 0, None))
    return {"pane_mm": pane, "xa_mm": xa, "za_mm": za, "tilt_deg": math.degrees(math.atan(-slope)),
            "from_mm": float(x[cut][0]), "to_mm": float(x[cut][-1]), "max_half_w_mm": float(half_w[cut].max()),
            "depth_mm": float((r + za + slope * (x - xa))[cut].max()), "window_x_mm": [xc - nd.window_mm / 2,
                                                                                    xc + nd.window_mm / 2]}


def flap_split(s) -> dict:
    """Where the centre flaps must start: fully down as a brake, a flap's trailing edge comes below the
    body's crown line, so nothing can swing over the body or the fairing."""
    w, fl = s.wing, s.flap
    cf = fl.chord_frac * w.chord_mm
    xh = w.le_x_mm + w.chord_mm - cf
    zh = float(surface_z(s, xh)[1])
    a = math.radians(fl.crow_deg)
    x_te, z_te = xh + cf * math.cos(a), zh - cf * math.sin(a)
    r = float(myring_r(s.fuselage, x_te))
    clash = math.sqrt(max(r**2 - z_te**2, 0.0)) if abs(z_te) < r else 0.0
    return {"hinge_x_mm": xh, "hinge_z_mm": zh, "te_down_z_mm": z_te, "clash_half_w_mm": clash,
            "inboard_y_mm": max(clash, s.fairing.half_w_mm) + s.fairing.fillet_mm}


# ---- the package against itself ------------------------------------------------------------------------

def checks(s, an: dict, bare: dict, ae: dict) -> list[dict]:
    """Design findings: ok is True, False (a FAIL) or None (a note)."""
    out = []

    def add(name, ok, text):
        out.append({"name": name, "ok": ok, "text": text})

    w, f, b, st = s.wing, s.fuselage, s.battery, s.strut
    x, _ = spar_xz(s)
    up, lo = surface_z(s, [x - s.spar.od_mm / 2, x + s.spar.od_mm / 2])
    room = float(min(up) - max(lo)) - 2 * w.skin_mm
    add("spar inside the wing section", room >= s.spar.od_mm,
        f"a {s.spar.od_mm:g} mm spar at {s.spar.x_frac:.0%} chord; {room:.1f} mm inside the {w.airfoil.upper()}'s skin")
    fs = s.loads.fs
    for grp in ("centre spar", "outer panel spar", "brace", "jury strut"):
        worst = max(((max(r["u_buckle"], r["u_stress"]), c, r) for c, cc in an["cases"].items() for r in cc["members"]
                     if r["group"] == grp), key=lambda t: t[0])
        u, c, r = worst
        how = (f"buckling, {-r['axial_n']:.0f} N on {r['length_mm']:.0f} mm against {r['pcr_n']:.0f} N"
               if r["u_buckle"] >= r["u_stress"] else f"stress, {r['sigma_mpa']:.0f} MPa")
        add(f"{grp} at ultimate", u <= 1, f"{u:.2f} of what it can take ({c}: {how})")
    pull, push = (an["cases"][cases(s)[i][0]] for i in (0, 2))
    jn = ns({"shape": "square", "od_mm": s.joiner.size_mm, "wall_mm": s.joiner.wall_mm})
    _, ij, cj = section(jn)
    mj = max(c["joiner_moment_nm"] for c in an["cases"].values())
    sj = fs * mj * 1e3 * cj / ij
    add("wing joiners at ultimate", sj <= s.carbon.comp_allow_mpa,
        f"{mj:.1f} N m at the joint, {sj:.0f} MPa in a {s.joiner.size_mm:g} mm square tube")
    t = max(abs(c["brace_axial_n"]) for c in an["cases"].values())
    bearing = fs * t / (s.fitting.pin_mm * s.fitting.tang_mm)
    add("brace pins in a printed tang", bearing <= s.fitting.bearing_allow_mpa,
        f"{t:.0f} N on a {s.fitting.pin_mm:g} mm pin through {s.fitting.tang_mm:g} mm is {bearing:.0f} MPa in bearing "
        f"against {s.fitting.bearing_allow_mpa:g}: " + ("printed will do" if bearing <= s.fitting.bearing_allow_mpa
                                                         else "make the brace's end fittings in aluminium"))
    inside = st.chord_mm * st.t_over_c - 2 * st.skin_mm
    add("brace tube inside its fairing", inside >= st.od_mm, f"{inside:.1f} mm inside a {st.chord_mm:g} mm, "
        f"{st.t_over_c:.0%} thick fairing for a {st.od_mm:g} mm tube")
    b0 = bare["cases"][cases(s)[0][0]]
    add("what the braces buy", None,
        f"in the pull-up the spar's bending falls from {b0['spar_moment_nm']:.0f} to {pull['spar_moment_nm']:.0f} N m and "
        f"the tip's rise from {b0['tip_rise_mm']:.0f} to {pull['tip_rise_mm']:.0f} mm; each brace pulls "
        f"{pull['brace_axial_n']:.0f} N and puts {-pull['spar_axial_n']:.0f} N of compression in the spar; in the "
        f"push-over it carries {-push['brace_axial_n']:.0f} N in compression")
    row = min(ae["rows"], key=lambda r: r["braced"]["sink_ms"])
    add("glide and sink", None,
        f"best sink {row['braced']['sink_ms']:.2f} m/s at {row['v_ms']:g} m/s with the braces "
        f"(L/D {row['braced']['l_over_d']:.0f}), {row['unbraced']['sink_ms']:.2f} without (L/D "
        f"{row['unbraced']['l_over_d']:.0f}); the package quotes {s.flight.min_sink_ms:g}. The braces are "
        f"{row['cd0']['braces'] / (sum(row['cd0'].values()) + row['cdi']):.0%} of the drag there. Skin friction and "
        f"induced drag only: no interference, gaps, antennas or propeller")
    r_end = float(myring_r(f, f.truncate_mm, clamp=False))
    xx = np.arange(f.nose_mm + f.mid_mm, f.truncate_mm, 0.5)
    rr = myring_r(f, xx, clamp=False)
    x22 = float(xx[np.argmax(rr < f.spinner_r_mm)])
    steep = math.degrees(math.atan(float(np.max(-np.gradient(rr, xx)))))
    add("tail cone meets the spinner at the firewall", abs(r_end - f.spinner_r_mm) < 1.0,
        f"the cubic is down to {r_end:.1f} mm radius at x = {f.truncate_mm:g}, not {f.spinner_r_mm:g}: it reaches the "
        f"spinner's radius at x = {x22:.0f}, and held there the last {f.truncate_mm - x22:.0f} mm are a parallel "
        f"stinger. Cut at x = {x22:.0f} or close the cubic on the spinner. Its steepest slope is {steep:.1f} deg")
    nf = nadir_flat(s)
    add("belly flat ends ahead of the tail cone's recovery", nf["to_mm"] < s.nadir.recovery_from_mm,
        f"one plane tilted {nf['tilt_deg']:.1f} deg nose-up, flat from x = {nf['from_mm']:.0f} to {nf['to_mm']:.0f}, "
        f"up to {2 * nf['max_half_w_mm']:.0f} mm wide and {nf['depth_mm']:.1f} mm off the round")
    wh = b.cells * b.cell_v * b.cell_ah
    add("battery holds what it weighs", abs(wh - b.quoted_wh) / b.quoted_wh < 0.15,
        f"{b.cells} cells are {b.cells * b.cell_kg:.2f} kg and {wh:.0f} Wh ({b.cells // b.series}P, "
        f"{b.cells // b.series * b.cell_ah:.0f} Ah), not {b.quoted_wh:.0f} Wh; {b.quoted_ah:g} Ah at {b.series}S is "
        f"{round(b.quoted_ah / b.cell_ah) * b.series} cells, {round(b.quoted_ah / b.cell_ah) * b.series * b.cell_kg:.1f} kg. "
        f"The loiter needs {b.loiter_w * b.loiter_h:.0f} Wh")
    area = ae["area_m2"]
    add("wing area", None, f"{area:.3f} m^2 from the planform (quoted {w.quoted_area_m2:g}), aspect ratio "
                           f"{ae['ar']:.1f} (quoted {w.quoted_ar:g}), {s.mass.auw_kg / area * 10:.0f} g/dm^2 by day")
    cl = 2 * s.mass.auw_kg * G / (s.flight.rho_kgm3 * s.flight.stall_clean_ms**2 * area)
    add("stall speed", None, f"{s.flight.stall_clean_ms:g} m/s clean at {s.mass.auw_kg:g} kg takes a lift "
                             f"coefficient of {cl:.2f}")
    fs_ = flap_split(s)
    add("centre flaps", None, f"hinge at x = {fs_['hinge_x_mm']:.0f}; {s.flap.crow_deg:g} deg down the trailing edge is at "
                              f"z = {fs_['te_down_z_mm']:.0f}, inside the body within {fs_['clash_half_w_mm']:.0f} mm of the "
                              f"centreline, so the flaps start at y = +/-{fs_['inboard_y_mm']:.0f} and the middle is fixed")
    return out


def run() -> dict:
    s = inputs()
    an, bare, ae = analyse(s), analyse(s, braced=False), aero(s)
    cuts = cut_list(s)
    rows = bom(s, cuts)
    sp = strut_points(s)
    return {"analysis": an, "unbraced": bare, "sweep": sweep(s), "aero": ae, "bom": rows,
            "strut": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in sp.items()},
            "tube_mass_g": sum(r["mass_g"] for r in rows if r["mass_g"]),
            "nadir": nadir_flat(s), "flap": flap_split(s), "checks": checks(s, an, bare, ae)}


def failed(res: dict) -> list[str]:
    return [c["name"] for c in res["checks"] if c["ok"] is False]


# ---- the report ----------------------------------------------------------------------------------------

def report(res: dict) -> str:
    s = inputs()
    an = res["analysis"]
    mark = {True: "ok", False: "**FAIL**", None: "note"}
    L = ["# The sailplane: a truss-braced wing, its loads, drag and cut list", "",
         "From `design/recon/sailplane.toml` by `osprey recon-sailplane`. Stations in mm: x aft from the nose, "
         "y to starboard, z up. Values marked REF in the design file are stand-ins.", "",
         "## Findings", "", "| Check | | |", "|---|---|---|"]
    L += [f"| {c['name']} | {mark[c['ok']]} | {c['text']} |" for c in res["checks"]]
    L += ["", f"## The loads: {s.loads.n:+g} g and {s.loads.n_neg:+g} g, ultimate factor {s.loads.fs:g}", "",
          f"The wing carries the lift but the braces' {s.aero.brace_lift_frac:.1%}, elliptic over the span; the wing's "
          f"weight comes off where it is. The braces meet the wing at y = +/-{an['strut_y_mm']:.0f}.", "",
          "| Case | Lift, N | Spar bending, N m | at the joint, N m | Brace, N | Spar axial, N | Tip, mm | Most used |",
          "|---|---|---|---|---|---|---|---|"]
    for name, c in an["cases"].items():
        L.append(f"| {name} | {c['lift_n']:.0f} | {c['spar_moment_nm']:.1f} | {c['joiner_moment_nm']:.1f} | "
                 f"{c['brace_axial_n']:+.0f} | {c['spar_axial_n']:+.0f} | {c['tip_rise_mm']:+.0f} | {c['u_max']:.2f} |")
    L += ["", "Tension is positive. \"Used\" is the ultimate load over what the tube can take: above 1.00 it fails.", "",
          "## Where the braces meet the wing", "",
          "| Brace at y, mm | Spar bending, N m | at the root, N m | Tip in the pull-up, mm | Brace tension, N | "
          "Brace compression in the push-over, N | Spar compression, N | Brace used | Most used |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in res["sweep"]:
        y = "no braces" if r["strut_y_mm"] is None else f"{r['strut_y_mm']:.0f}"
        L.append(f"| {y} | {r['spar_moment_nm']:.0f} | {r['root_moment_nm']:.0f} | {r['tip_rise_mm']:.0f} | "
                 f"{r['brace_tension_n']:.0f} | {r['brace_compression_n']:.0f} | {max(-r['spar_axial_n'], 0):.0f} | "
                 f"{r['brace_used']:.2f} | {r['u_max']:.2f} |")
    ae = res["aero"]
    L += ["", "## Drag, by components", "",
          "Skin friction with transition times a form factor times wetted area for each part, plus induced drag, as "
          "Ting, Reynolds, Nguyen and Totah build the truss-braced wing's up. Counts are 0.0001 on the wing's "
          f"{ae['area_m2']:.2f} m^2. The braces' planform is {ae['brace_area_frac']:.0%} of the wing's.", "",
          "| Speed, m/s | CL | Wing | Braces | Tail | Body | Induced | L/D | Sink, m/s | L/D, no braces | Sink, no braces |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in ae["rows"]:
        c = r["cd0"]
        L.append(f"| {r['v_ms']:g} | {r['cl']:.2f} | {c['wing'] * 1e4:.0f} | {c['braces'] * 1e4:.0f} | {c['tail'] * 1e4:.0f} | "
                 f"{c['body'] * 1e4:.0f} | {r['cdi'] * 1e4:.0f} | {r['braced']['l_over_d']:.1f} | {r['braced']['sink_ms']:.2f} | "
                 f"{r['unbraced']['l_over_d']:.1f} | {r['unbraced']['sink_ms']:.2f} |")
    L += ["", "## Cut list", "", "| Item | Stock | Qty | Cut, mm | Mass, g | |", "|---|---|---|---|---|---|"]
    for r in res["bom"]:
        L.append(f"| {r['item']} | {r['stock']} | {r['qty']} | {r['cut_mm']:.1f} | "
                 f"{'' if r['mass_g'] is None else format(r['mass_g'], '.0f')} | {r['note']} |")
    L += ["", f"Carbon tube: {res['tube_mass_g']:.0f} g. The outer panels' own spars are not in this list.", ""]
    return "\n".join(L)


# ---- OpenSCAD ------------------------------------------------------------------------------------------

def _scad(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (list, tuple, np.ndarray)):
        return "[" + ", ".join(_scad(x) for x in v) + "]"
    return f"{float(v):.6f}".rstrip("0").rstrip(".")


def params_scad(s, res: dict) -> str:
    """params.scad: every number the OpenSCAD modules use, from the design file and this module's results."""
    from osprey.recon.geometry import naca4

    f, w, j, nd, fl, fa, st, ft = s.fuselage, s.wing, s.joiner, s.nadir, s.flap, s.fairing, s.strut, s.fitting
    pts, _, lo = airfoil(w.airfoil)
    nf, fs_, sp = res["nadir"], res["flap"], res["strut"]
    x, z = spar_xz(s)
    rear_x = w.le_x_mm + s.spar.rear_x_frac * w.chord_mm
    ru, rl = surface_z(s, rear_x)
    bu, bz = naca4(st.camber, 0.4, st.t_over_c, 24)
    v = {
        "L": f.length_mm, "R": f.radius_mm, "nose_len": f.nose_mm, "mid_len": f.mid_mm, "nose_exp": f.nose_exp,
        "tail_angle": f.tail_angle_deg, "r_spinner": f.spinner_r_mm, "x_max": f.truncate_mm, "shell_t": f.wall_mm,
        "hatch_x": f.hatch_mm, "hatch_half_w": f.hatch_half_w_mm, "hatch_z": f.hatch_z_mm,
        "bulkheads": [[b.x_mm, b.t_mm, b.web_mm] for b in s.bulkhead],
        "rail_y": s.rails.y_mm, "rail_z": s.rails.z_mm, "rail_x": s.rails.x_mm, "rail_s": s.rails.section_mm,
        "span": w.span_mm, "center_span": w.center_span_mm, "chord": w.chord_mm, "tip_chord": w.tip_chord_mm,
        "le_x": w.le_x_mm, "chord_z": w.chord_z_mm, "skin_t": w.skin_mm, "rib_t": w.rib_mm, "rib_y": w.rib_y_mm,
        "dihedral": w.dihedral_deg, "airfoil_pts": pts[:-1], "lower_tab": lo,
        "flap_frac": fl.chord_frac, "flap_gap": fl.gap_mm, "flap_y0": fs_["inboard_y_mm"], "flap_end_gap": fl.end_gap_mm,
        "hinges_per_flap": fl.hinges_per_flap, "hinge_pocket": fl.hinge_pocket_mm, "hinge_z": fs_["hinge_z_mm"],
        "fair_half_w": fa.half_w_mm, "fair_fillet": fa.fillet_mm, "fair_step": fa.step_mm,
        "spar_x": x, "spar_z": z, "spar_od": s.spar.od_mm, "spar_wall": s.spar.wall_mm, "spar_frac": s.spar.x_frac,
        "rear_x": rear_x, "rear_z": float(ru + rl) / 2, "rear_od": s.spar.rear_od_mm,
        "strut_root": sp["root"], "strut_wing": sp["wing"], "strut_jury": sp["jury"], "strut_od": st.od_mm,
        "strut_chord": st.chord_mm, "strut_seat": st.seat_mm, "brace_pts": np.c_[bu, bz],
        "jury_od": s.jury.od_mm, "jury_seat": s.jury.seat_mm, "wing_drop": st.wing_drop_mm,
        "fit_socket": ft.socket_mm, "bond_gap": ft.bond_gap_mm, "fit_wall": ft.wall_mm, "pin_d": ft.pin_mm,
        "jury_pin_d": ft.jury_pin_mm, "tang_t": ft.tang_mm, "cheek_t": ft.cheek_mm, "groove": ft.groove_mm,
        "grooves": ft.grooves,
        "joiner_size": j.size_mm, "joiner_engage": j.engage_mm, "end_rib_t": j.rib_mm, "mpx": j.mpx_mm, "xt30": j.xt30_mm,
        "connector_x": w.le_x_mm + j.connector_x_frac * w.chord_mm, "shoulder": j.shoulder_mm,
        "nadir_window": nd.window_mm, "nadir_pane": nf["pane_mm"], "nadir_pane_t": nd.pane_mm,
        "nadir_floor": nd.floor_mm, "nadir_xa": nf["xa_mm"], "nadir_za": nf["za_mm"], "nadir_tilt": nf["tilt_deg"],
        "nadir_margin": nd.margin_mm, "nadir_mount": nd.mount_mm, "nadir_boss": nd.boss_mm, "nadir_m3": nd.m3_mm,
    }
    head = ("// Written by `osprey recon-sailplane` from design/recon/sailplane.toml: do not edit, change the design "
            "file.\n// mm. Origin at the nose tip; +x aft, +y starboard, +z up.\n")
    return head + "".join(f"{k} = {_scad(x)};\n" for k, x in v.items())


def export(res: dict, out: Path) -> list[Path]:
    """The OpenSCAD parts, params.scad beside them, and the cut list as CSV."""
    s = inputs()
    d = out / "scad"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.scad"):
        old.unlink()
    files = [Path(shutil.copy(src, d / src.name)) for src in sorted(SCAD.glob("*.scad"))]
    (d / "params.scad").write_text(params_scad(s, res))
    with open(out / "cutlist.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["item", "stock", "qty", "cut_mm", "note"])
        for r in res["bom"]:
            wr.writerow((r["item"], r["stock"], r["qty"], f"{r['cut_mm']:.1f}", r["note"]))
    return files + [d / "params.scad", out / "cutlist.csv"]
