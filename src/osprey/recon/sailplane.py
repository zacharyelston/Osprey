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


VARIANTS = ("pusher",) + tuple(sorted(f.stem for f in (RECON / "sailplanes").glob("*.toml")))


def _raw(variant: str = "pusher"):
    from osprey.recon.params import _merge

    d = _toml(RECON / "sailplane.toml")
    if variant != "pusher":
        d = _merge(d, _toml(RECON / "sailplanes" / f"{variant}.toml"))
    d["variant"]["name"] = variant
    return ns(d)


def package():
    """The sailplane exactly as the handoff package has it: the weights and tail the others are measured from."""
    return _raw()


def inputs(variant: str = "pusher"):
    """The sailplane as the package has it (the pusher), or a variant from design/recon/sailplanes laid over it,
    with its weights settled."""
    return settle(_raw(variant))


def panel_area_m2(s) -> float:
    w = s.wing
    return (w.span_mm - w.center_span_mm) / 2 * (w.chord_mm + w.tip_chord_mm) / 2 / 1e6


def settle(s):
    """Work out what follows from a design's geometry instead of being given: the outer panels' weight by
    their area, a V-tail marked "auto" at the angle and size that just meet its two volumes, and the all-up weight as the package's
    plus what the propulsion, tail, booms, body skin and panels add. A motor's weight follows the climb's
    power, which follows the weight, so it goes round a few times."""
    base = package()
    w, wb = s.wing, base.wing
    k = panel_area_m2(s) / panel_area_m2(base)
    w.panel_day_kg, w.panel_night_kg = wb.panel_day_kg * k, wb.panel_night_kg * k
    if s.tail.size == "auto" and s.tail.kind != "boom":
        # The V's angle that makes one area meet both volumes at once, then that area.
        S, b = wing_area_m2(s), w.span_mm / 1e3
        s.tail.dihedral_deg = math.degrees(math.atan(math.sqrt(s.tail.vv_target * b / (s.tail.vh_target * S / b))))
        s.aero.tail_area_m2 = tail(s)["area_needed_m2"]
    was = sum(m for _, m, _ in movable(base))
    skin = s.loads.shell_kgm2 * (body_wetted_m2(s) - body_wetted_m2(base))
    for _ in range(5):
        d = sum(m for _, m, _ in movable(s)) - was + skin
        s.mass.auw_kg = base.mass.auw_kg + d + 2 * (w.panel_day_kg - wb.panel_day_kg)
        s.mass.auw_night_kg = base.mass.auw_night_kg + d + 2 * (w.panel_night_kg - wb.panel_night_kg)
    return s


def stretched(s, span_m: float):
    """The same aircraft with its outer panels stretched to a new span."""
    import copy

    s2 = copy.deepcopy(s)
    s2.wing.span_mm = span_m * 1e3
    return settle(s2)


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
    y = (getattr(st, "y_mm", None) or round(half_span(s) * st.y_frac, 1)) if strut_y is None else strut_y
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
    ys = {0.0, s.spar.saddle_y_mm, jy, h, sp["y"]} | {jy + k * (h - jy) / 4 for k in range(1, 4)}
    if braced:
        ys |= {float(sp["jury"][1])}
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


def loads(s, nodes: dict, wings: str, n: float, pod_y: float | None = None, lift: str = "elliptic") -> tuple[dict, dict]:
    """Nodal forces at n g. The wing and braces carry all the lift (none on the body, no tail load): the
    wing's on the spar's nodes, each brace's on its own three. With lift "vlm" the spanwise lift and the
    braces' share are the vortex lattice's, each surface solved alone, at the angle of attack that carries
    the load at stall x sqrt(n); with "elliptic" the lift is elliptic over the span and the braces take a
    fixed share. The wing's weight comes off where it is."""
    w = s.wing
    auw = s.mass.auw_kg if wings == "day" else s.mass.auw_night_kg
    m_panel = w.panel_day_kg if wings == "day" else w.panel_night_kg
    braced = "K+" in nodes
    share = s.aero.brace_lift_frac if braced else 0.0
    L, jy, h = n * G * auw, joint_y(s), half_span(s)
    here = None
    if lift == "vlm":
        from osprey.recon import sailplane_vlm as vlm

        here = vlm.at_lift(s, L, s.flight.stall_clean_ms * math.sqrt(abs(n)), braced=braced)
        share = here["lift_n"].get("brace", 0.0) / L
    F = {}

    def add(k, fz):
        F[k] = F.get(k, np.zeros(3)) + np.array([0.0, 0.0, fz])

    spar = sorted((p[1], k) for k, p in nodes.items() if k[0] == "W")
    for i, (y, k) in enumerate(spar):
        lo = (spar[i - 1][0] + y) / 2 if i else y
        hi = (spar[i + 1][0] + y) / 2 if i < len(spar) - 1 else y
        add(k, vlm.wing_lift_between(s, here, lo, hi) if here else _lift(s, L * (1 - share), lo, hi)[0])
        for a, b, kg, length in ((-h, -jy, m_panel, h - jy), (-jy, jy, w.center_kg, 2 * jy), (jy, h, m_panel, h - jy)):
            add(k, -n * G * kg * max(min(hi, b) - max(lo, a), 0.0) / length)
    if braced:
        for side in "+-":
            for k, part in ((f"R{side}", 0.25), (f"M{side}", 0.5), (f"K{side}", 0.25)):
                add(k, L * share / 2 * part)
    if s.pods.count:                                   # a pod hangs on the wing at each brace's station
        y = strut_points(s)["y"] if pod_y is None else pod_y
        for sg in (-1, 1):
            add(f"W{sg * y:+.0f}", -n * G * pod(s)["kg"])
    return F, {"wings": wings, "n": n, "auw_kg": auw, "lift_n": L, "brace_lift_n": L * share / 2, "brace_share": share,
               "alpha_deg": here["alpha_deg"] if here else None}


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


def analyse(s, strut_y: float | None = None, braced: bool = True, lift: str | None = None) -> dict:
    """The wing through every case: each member's loads and margins, and the numbers that sum the wing up.
    The lift is the design file's choice, but elliptic when the braces are moved off their design station
    (the lattice is of the design)."""
    lift = lift or (s.aero.lift if strut_y is None else "elliptic")
    nodes, members, fixed = model(s, strut_y, braced)
    jy, h = joint_y(s), half_span(s)
    out = {"nodes": {k: v.tolist() for k, v in nodes.items()}, "cases": {}, "braced": braced, "lift": lift,
           "strut_y_mm": strut_points(s, strut_y)["y"] if braced else None}
    for name, wings, n in cases(s):
        F, summary = loads(s, nodes, wings, n, strut_points(s, strut_y)["y"], lift)
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
        a = analyse(s, y, braced=y is not None, lift="elliptic")
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
    if x_frac <= 0.0:
        return 0.072 * re_len**-0.2
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
    s_body = body_wetted_m2(s)
    fine = f.length_mm / (2 * f.radius_mm)

    def foil_k(t):
        return 1 + 2 * t + 100 * t**4

    parts = {   # name: (length m, wetted area m^2, form factor, transition)
        "wing": (mac, 2 * S * (1 + 0.2 * tc), foil_k(tc), a.transition.wing),
        "braces": (s.strut.chord_mm / 1e3, 2 * 2 * brace_length_m(s) * s.strut.chord_mm / 1e3 * (1 + 0.2 * s.strut.t_over_c),
                   foil_k(s.strut.t_over_c), a.transition.brace),
        "tail": (tail(s)["chord_mm"] / 1e3, 2 * tail(s)["area_m2"] * (1 + 0.2 * s.tail.t_over_c),
                 foil_k(s.tail.t_over_c), a.transition.tail),
        "body": (f.truncate_mm / 1e3, s_body, 1 + 1.5 / fine**1.5 + 7 / fine**3, a.transition.fuselage),
    }
    if s.pods.count:
        pl = pod_shape(s)["length_mm"]
        pf = pl / s.pods.diameter_mm
        parts["pods"] = (pl / 1e3, s.pods.count * 0.75 * math.pi * s.pods.diameter_mm * pl / 1e6,
                         1 + 1.5 / pf**1.5 + 7 / pf**3, 0.0)       # turbulent: they sit in the props' wash
    if s.tail.kind == "boom":
        ps, tl = pod_shape(s), tail(s)
        bl = (tl["le_x_mm"] + tl["chord_mm"] - ps["end_x_mm"]) / 1e3
        parts["booms"] = (bl, 2 * math.pi * s.boom.od_mm / 1e3 * bl, 1.05, 0.0)
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


# ---- the tail, the balance and the span -------------------------------------------------------------

def has_pusher(s) -> bool:
    return "pusher" in s.propulsion.layout


def tail(s) -> dict:
    """The tail as the horizontal and vertical tails it is or stands in for: its two volumes.

    A V-tail on the body is the area the design file gives it; this also says what it would need on its arm
    to reach the targets. A boom tail is sized here: the tailplane spans between the two booms with its
    leading edge clear behind the pusher's disc, its chord what the horizontal volume asks for (or the
    least allowed), and the two fins share what the vertical volume asks for."""
    tl, w = s.tail, s.wing
    S, b = wing_area_m2(s), w.span_mm / 1e3
    qc = w.le_x_mm + 0.25 * w.chord_mm
    if tl.kind == "boom":
        y = strut_points(s)["y"]
        le = s.fuselage.truncate_mm + 45.0 + tl.prop_clear_mm
        c = tl.h_chord_min_mm
        for _ in range(30):
            arm = (le + 0.25 * c - qc) / 1e3
            c = max(tl.vh_target * S * (S / b) / arm / (2 * y / 1e3) * 1e3, tl.h_chord_min_mm)
        sh, sv = c / 1e3 * 2 * y / 1e3, tl.vv_target * S * b / arm
        return {"kind": "boom", "area_m2": sh + sv, "sh_m2": sh, "sv_m2": sv, "arm_m": arm, "vh": sh * arm / (S * S / b),
                "vv": sv * arm / (S * b), "chord_mm": c, "le_x_mm": le, "fin_h_mm": sv / 2 / (tl.fin_chord_mm / 1e3) * 1e3,
                "span_mm": 2 * y, "x_mm": le + 0.25 * c, "area_needed_m2": sh + sv, "arm_needed_m": arm, "panel_mm": 0.0}
    A, g = s.aero.tail_area_m2, math.radians(tl.dihedral_deg)
    mean = (tl.root_chord_mm + tl.tip_chord_mm) / 2e3
    arm = (tl.x_mm + 0.25 * mean * 1e3 - qc) / 1e3
    need = max(tl.vh_target * S * (S / b) / (arm * math.cos(g) ** 2), tl.vv_target * S * b / (arm * math.sin(g) ** 2))
    return {"kind": tl.kind, "area_m2": A, "sh_m2": A * math.cos(g) ** 2, "sv_m2": A * math.sin(g) ** 2, "arm_m": arm,
            "panel_mm": A / 2 / mean * 1e3, "vh": A * math.cos(g) ** 2 * arm / (S * S / b), "chord_mm": mean * 1e3,
            "vv": A * math.sin(g) ** 2 * arm / (S * b), "area_needed_m2": need, "arm_needed_m": arm * need / max(A, 1e-9),
            "x_mm": tl.x_mm + 0.25 * mean * 1e3}


def booms(s) -> dict | None:
    """The two booms: carbon tubes from the pods' backs to the tailplane's trailing edge. Each is checked as a
    cantilever from the wing's spar, with half the tailplane's most lift at the pull-up's speed on its end."""
    if s.tail.kind != "boom":
        return None
    tl, ps = tail(s), pod_shape(s)
    end = tl["le_x_mm"] + tl["chord_mm"]
    A, I, c = section(s.boom)
    lever = tl["x_mm"] - spar_xz(s)[0]
    q = 0.5 * s.flight.rho_kgm3 * (s.flight.stall_clean_ms * math.sqrt(s.loads.n)) ** 2
    load = q * tl["sh_m2"] * s.boom.tail_cl_max / 2
    E = s.carbon.e_gpa * 1e3
    sigma = load * lever * c / I
    # The tail's load twists the wing between the body and the boom: a closed cell from the leading edge to
    # the rear spar, by Bredt.
    w = s.wing
    xs = np.linspace(w.le_x_mm + 1.0, w.le_x_mm + s.spar.rear_x_frac * w.chord_mm, 200)
    up, lo = surface_z(s, xs)
    cell = float(np.trapezoid(up - lo, xs))
    edge = float(np.sum(np.hypot(np.diff(xs), np.diff(up))) + np.sum(np.hypot(np.diff(xs), np.diff(lo))) + (up[-1] - lo[-1]))
    twist = load * lever * (ps["y_mm"] - s.spar.saddle_y_mm) * edge / (4 * cell**2 * w.skin_g_gpa * 1e3 * w.skin_mm)
    return {"twist_deg": math.degrees(twist), "from_x_mm": ps["end_x_mm"], "to_x_mm": end, "length_mm": end - ps["end_x_mm"], "y_mm": ps["y_mm"],
            "kg": 2 * (end - ps["end_x_mm"]) * A * s.carbon.rho_kgm3 * 1e-9, "tail_load_n": load, "lever_mm": lever,
            "sigma_mpa": sigma, "used": s.loads.fs * sigma / s.carbon.comp_allow_mpa,
            "droop_mm": load * lever**3 / (3 * E * I), "wing_torque_nm": load * lever / 1e3}


def chord_at(s, y: float) -> float:
    w = s.wing
    return w.chord_mm - (w.chord_mm - w.tip_chord_mm) * max(abs(y) - joint_y(s), 0.0) / (half_span(s) - joint_y(s))


def shaft_power(s, thrust: float, v: float) -> tuple[float, list[dict], int]:
    """The shaft power (W) the props take to give a thrust at a speed, each streamtube's share, and how many
    motors there are. A pod's one or two props are one tube, the body's pusher another."""
    c, pd, pr = s.climb, s.pods, s.propulsion
    tubes = [(2 if pd.layout == "both" else 1, pd.prop_in, getattr(c.install, pd.layout))] * pd.count if pd.count else []
    if has_pusher(s):
        tubes = tubes + [(1, pr.center_prop_in, pr.center_install)]
    motors = sum(n for n, _, _ in tubes)
    q = 0.5 * s.flight.rho_kgm3 * v**2
    shaft, each = 0.0, []
    for n, d_in, inst in tubes:
        t_tube = thrust * n / motors
        ideal = 2 / (1 + math.sqrt(1 + t_tube / (q * math.pi * (d_in * 0.0254) ** 2 / 4)))
        eff = ideal * c.blade_eff * inst
        shaft += t_tube * v / eff
        each.append({"motors": n, "prop_in": d_in, "ideal": ideal, "eff": eff, "motor_w": t_tube * v / eff / n})
    return shaft, each, motors


def endurance(s) -> dict:
    """Hours of level flight under power, with no help from thermals: the pack's usable energy over what the
    motors draw to hold the best-sink speed plus what the avionics draw."""
    b, c = s.battery, s.climb
    row = min(aero(s)["rows"], key=lambda r: r["braced"]["sink_ms"])
    drag = s.mass.auw_kg * G / row["braced"]["l_over_d"]
    shaft, _, _ = shaft_power(s, drag, row["v_ms"])
    draw = shaft / c.motor_eff + c.avionics_w
    wh = b.cells * b.cell_v * b.cell_ah * b.usable_frac
    return {"v_ms": row["v_ms"], "shaft_w": shaft, "draw_w": draw, "usable_wh": wh, "hours": wh / draw,
            "prop_eff": drag * row["v_ms"] / shaft}


def stall(s) -> dict:
    fl = s.flight
    vs = math.sqrt(2 * s.mass.auw_kg * G / (fl.rho_kgm3 * wing_area_m2(s) * fl.cl_max))
    return {"vs_ms": vs, "margin": fl.loiter_ms[0] / vs, "ok": fl.loiter_ms[0] / vs >= fl.stall_margin}


def climb(s) -> dict:
    """The climb the props are sized for: the thrust it takes, shared equally by the motors; each
    streamtube's efficiency (a pod's one or two props are one tube, the body's pusher another: the ideal of
    momentum theory times the blades' and the installation's); the shaft power each motor gives; and what is
    left with one pod motor stopped: the climb, and the lift coefficient the vertical tail needs to hold the
    yaw."""
    c = s.climb
    row = min(aero(s)["rows"], key=lambda r: abs(r["v_ms"] - c.speed_ms))
    W, v = s.mass.auw_kg * G, c.speed_ms
    drag = W / row["braced"]["l_over_d"]
    thrust = W * c.rate_ms / v + drag
    q = 0.5 * s.flight.rho_kgm3 * v**2
    shaft, each, motors = shaft_power(s, thrust, v)
    y = strut_points(s)["y"] / 1e3
    tl = tail(s)
    side = thrust / motors * y / tl["arm_m"]
    return {"motors": motors, "thrust_n": thrust, "ideal": each[0]["ideal"], "eff": thrust * v / shaft, "shaft_w": shaft,
            "motor_w": each[0]["motor_w"], "center_motor_w": each[-1]["motor_w"] if has_pusher(s) else 0.0, "tubes": each,
            "rate_ms": c.rate_ms,
            "out_thrust_frac": (motors - 1) / motors, "out_climb_ms": (thrust * (motors - 1) / motors - drag) * v / W,
            "out_yaw_nm": thrust / motors * y, "out_tail_cl": side / (q * tl["sv_m2"])}


def pod_shape(s) -> dict:
    """One pod as its layout has it: where it starts and ends, and which ends carry a prop."""
    pd = s.pods
    y = strut_points(s)["y"]
    ch = chord_at(s, y)
    le = s.wing.le_x_mm + s.spar.x_frac * (s.wing.chord_mm - ch)
    front, back = pd.layout in ("front", "both"), pd.layout in ("back", "both")
    nose = le - pd.nose_ahead_mm if front else le + ch + pd.tail_behind_mm - pd.length_mm
    end = le + ch + pd.tail_behind_mm if back else nose + pd.length_mm
    return {"layout": pd.layout, "length_mm": end - nose, "nose_x_mm": nose, "end_x_mm": end, "front": front,
            "back": back, "y_mm": y}


def pod(s) -> dict:
    """A pod's shape and what it weighs: the shell by its length, and a prop and a motor for each end that
    has one, the motor by the climb's power."""
    pd = s.pods
    if not pd.count:
        return {"kg": 0.0, "length_mm": 0.0}
    g = pod_shape(s)
    motor_kg = pd.prop_kg + climb(s)["motor_w"] / 1e3 / s.climb.motor_kw_per_kg
    items = [(pd.shell_kg_per_m * g["length_mm"] / 1e3, (g["nose_x_mm"] + g["end_x_mm"]) / 2)]
    items += [(motor_kg, g["nose_x_mm"] + 45.0)] if g["front"] else []
    items += [(motor_kg, g["end_x_mm"] - 45.0)] if g["back"] else []
    kg = sum(m for m, _ in items)
    return {**g, "kg": kg, "cg_x_mm": sum(m * x for m, x in items) / kg, "motor_kg": motor_kg}


def movable(s) -> list[tuple[str, float, float]]:
    """What differs between the variants and where it is: (name, kg, x in mm). The propulsion, the tail and
    the booms; the shell is left out."""
    pr = s.propulsion
    tl = tail(s)
    items = [("tail", s.loads.tail_kgm2 * tl["area_m2"], tl["x_mm"])]
    if s.pods.count:
        pd = pod(s)
        items.append(("pods", s.pods.count * pd["kg"], pd["cg_x_mm"]))
        if has_pusher(s):
            items.append(("pusher", pr.center_prop_kg + climb(s)["center_motor_w"] / 1e3 / s.climb.motor_kw_per_kg, pr.motor_x_mm))
    else:
        items.append(("pusher", pr.motor_kg, pr.motor_x_mm))
    bm = booms(s)
    if bm:
        items.append(("booms", bm["kg"], (bm["from_x_mm"] + bm["to_x_mm"]) / 2))
    return items


def balance(s) -> dict:
    """What the variant's propulsion, tail and booms do to the balance against the package's pusher: how far
    the battery has to slide on its rails (aft positive) to put the CG back, against the travel the rails
    leave it either way from the middle."""
    travel = (s.rails.x_mm[1] - s.rails.x_mm[0] - s.battery_bay.pack_length_mm) / 2
    cg = s.wing.le_x_mm + 0.30 * s.wing.chord_mm                         # near enough, to take moments about
    mine, base = movable(s), movable(package())
    moved = sum(m * (x - cg) for _, m, x in base) - sum(m * (x - cg) for _, m, x in mine)      # kg mm, forward
    return {"shift_mm": moved / s.mass.auw_kg, "battery_aft_mm": moved / s.mass.battery_kg, "travel_mm": travel,
            "items": [list(i) for i in mine], "delta_kg": sum(m for _, m, _ in mine) - sum(m for _, m, _ in base)}


def with_pods(s, layout: str):
    """The same aircraft with its pods' props at the front, the back or both: its weight follows the pods'."""
    import copy

    s2 = copy.deepcopy(s)
    s2.pods.layout = layout
    return settle(s2)


def pod_sweep(s) -> list[dict]:
    """Front, back and both: each pod layout's weight, balance, glide with the props folded, the climb and a
    motor out, and the most any tube is used."""
    rows = []
    for layout in s.pods.layouts:
        s2 = with_pods(s, layout)
        pd, cl, bl, ae, an = pod(s2), climb(s2), balance(s2), aero(s2), analyse(s2)
        best = min(ae["rows"], key=lambda r: r["braced"]["sink_ms"])
        prop_r = s.pods.prop_in * 25.4 / 2
        rows.append({"layout": layout, **{k: pd[k] for k in ("kg", "length_mm", "motor_kg")}, **cl, **bl,
                     "auw_kg": s2.mass.auw_kg, "pods_counts": best["cd0"]["pods"] * 1e4, "sink_ms": best["braced"]["sink_ms"],
                     "l_over_d": best["braced"]["l_over_d"], "used": max(c["u_max"] for c in an["cases"].values()),
                     "brace_pull_n": an["cases"][cases(s2)[0][0]]["brace_axial_n"],
                     "tail_ok": cl["out_tail_cl"] <= s.climb.tail_cl_max, "prop_r_mm": prop_r})
    return rows


def body_wetted_m2(s) -> float:
    f = s.fuselage
    x = np.linspace(0.0, f.truncate_mm, 2000)
    r = myring_r(f, x)
    return float(np.sum(math.pi * (r[1:] + r[:-1]) * np.hypot(np.diff(x), np.diff(r)))) / 1e6


def max_length_mm(s) -> float:
    """The longest this body can be drawn: past it the tail cone's cubic, held to its closing angle, swells
    beyond the body's radius before it narrows."""
    f = s.fuselage
    return f.nose_mm + f.mid_mm + 3 * f.radius_mm / math.tan(math.radians(f.tail_angle_deg))


def lengthened(s, length_m: float):
    """The same aircraft with its tail cone stretched to a new overall length. The tail rides aft with it
    and is re-sized to just meet its two volumes on the longer arm; the shell's and the tail's weights
    follow their areas. The laminar run stays what it was in millimetres, back to the end of the nose."""
    import copy

    s2 = copy.deepcopy(s)
    f, f2 = s.fuselage, s2.fuselage
    grow = length_m * 1e3 - f.length_mm
    f2.length_mm += grow
    f2.truncate_mm += grow
    s2.tail.x_mm += grow
    s2.tail.size = "auto"
    s2.aero.transition.fuselage = s.aero.transition.fuselage * f.truncate_mm / f2.truncate_mm
    return settle(s2)


def length_sweep(s) -> list[dict]:
    """How long can the body be? At each length the tail is the size its volumes ask for, so a short body
    pays in tail and a long one in skin. The first row is the variant as its design file has it."""
    f = s.fuselage
    rows = []
    if s.tail.kind == "boom":
        return rows                                    # the tail is not on the body: its length is its own business
    for ln, sized in [(f.length_mm / 1e3, False), *((x, True) for x in sorted({*s.loads.sweep_length_m, f.length_mm / 1e3}))]:
        s2 = lengthened(s, ln) if sized else s
        f2 = s2.fuselage
        tl, ae = tail(s2), aero(s2)
        x = np.arange(f2.nose_mm + f2.mid_mm, f2.truncate_mm, 0.5)
        r = myring_r(f2, x, clamp=False)
        best = min(ae["rows"], key=lambda r_: r_["braced"]["sink_ms"])
        rows.append({"length_m": ln, "sized": sized, "fineness": f2.length_mm / (2 * f2.radius_mm), "arm_m": tl["arm_m"],
                     "tail_m2": s2.aero.tail_area_m2, "vh": tl["vh"], "vv": tl["vv"], "body_m2": ae["body_wetted_m2"],
                     "auw_kg": s2.mass.auw_kg, "slope_deg": math.degrees(math.atan(float(np.max(-np.gradient(r, x))))),
                     "swells": bool(np.max(r) > f2.radius_mm + 1e-6), "cd0_body": best["cd0"]["body"],
                     "cd0_tail": best["cd0"]["tail"], "l_over_d": best["braced"]["l_over_d"],
                     "sink_ms": best["braced"]["sink_ms"], "ok": f2.length_mm <= max_length_mm(s) + 1e-6})
    return rows


def span_sweep(s) -> list[dict]:
    """How long can the wing be? The outer panels stretched to each span, the braces kept at the same share
    of the half-span, the tubes as they are. A span passes while no tube, joiner or brace is over what it
    can take at ultimate and the tip rises no more than the limit in the pull-up."""
    rows = []
    for b in s.loads.sweep_span_m:
        s2 = stretched(s, b)
        an, ae = analyse(s2), aero(s2)
        u, c, r = max(((max(m["u_buckle"], m["u_stress"]), cn, m) for cn, cc in an["cases"].items() for m in cc["members"]),
                      key=lambda t: t[0])
        jn = ns({"shape": "square", "od_mm": s.joiner.size_mm, "wall_mm": s.joiner.wall_mm})
        _, ij, cj = section(jn)
        uj = s.loads.fs * max(cc["joiner_moment_nm"] for cc in an["cases"].values()) * 1e3 * cj / ij / s.carbon.comp_allow_mpa
        pull = an["cases"][cases(s2)[0][0]]
        tip = abs(pull["tip_rise_mm"]) / (b * 500)
        best = min(ae["rows"], key=lambda r_: r_["braced"]["sink_ms"])
        limits = {f"{r['group']} ({'buckling' if r['u_buckle'] >= r['u_stress'] else 'stress'}, {c})": u,
                  "wing joiner": uj, "tip's rise": tip / s.loads.tip_rise_max_frac}
        worst = max(limits, key=limits.get)
        rows.append({"span_m": b, "area_m2": ae["area_m2"], "ar": ae["ar"], "auw_kg": s2.mass.auw_kg,
                     "brace_mm": brace_length_m(s2) * 1e3, "used": u, "joiner_used": uj, "tip_frac": tip,
                     "limit": worst, "limit_used": limits[worst], "ok": limits[worst] <= 1.0,
                     "l_over_d": best["braced"]["l_over_d"], "sink_ms": best["braced"]["sink_ms"], "v_ms": best["v_ms"],
                     "vv": tail(s2)["vv"]})
    return rows


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
    if an["lift"] == "vlm":
        from osprey.recon import sailplane_vlm as vlm

        lt, ell = vlm.run_for(s), analyse(s, lift="elliptic")["cases"][cases(s)[0][0]]
        pu = lt["pull_up"]
        add("the lift, solved", None,
            f"a vortex lattice has the braces carrying {lt['alone']['share'].get('brace', 0):.1%} of the lift in the loiter "
            f"with each surface alone and {lt['whole']['share'].get('brace', 0):.1%} all together (assumed "
            f"{s.aero.brace_lift_frac:.1%}), and the wing's lift centred {pu['centre_m']:.2f} m out in the pull-up, not an "
            f"ellipse's {pu['elliptic_centre_m']:.2f}. Against the elliptic assumption the spar's bending goes from "
            f"{ell['spar_moment_nm']:.0f} to {pull['spar_moment_nm']:.0f} N m and each brace's pull from "
            f"{ell['brace_axial_n']:.0f} to {pull['brace_axial_n']:.0f} N. Lift-curve slope {lt['alone']['cl_alpha']:.2f} per "
            f"radian; span efficiency {lt['whole']['span_eff']:.2f} before the body and anything viscous (the drag build-up "
            f"assumes {s.aero.oswald:g})")
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
    if has_pusher(s):
        meets = abs(r_end - f.spinner_r_mm) < 1.0
        add("tail cone meets the spinner at the firewall", meets,
            f"the cubic is at {r_end:.1f} mm radius at x = {f.truncate_mm:g}, the spinner's {f.spinner_r_mm:g}; its "
            f"steepest slope is {steep:.1f} deg" if meets else
            f"the cubic is down to {r_end:.1f} mm radius at x = {f.truncate_mm:g}, not {f.spinner_r_mm:g}: it reaches the "
            f"spinner's radius at x = {x22:.0f}, and held there the last {f.truncate_mm - x22:.0f} mm are a parallel "
            f"stinger. Cut at x = {x22:.0f} or close the cubic on the spinner. Its steepest slope is {steep:.1f} deg")
    else:
        add("tail cone", None, f"no spinner to meet: the cubic closes to {r_end:.1f} mm at x = {f.truncate_mm:g}, "
                               f"steepest slope {steep:.1f} deg")
    tl = tail(s)
    if tl["kind"] == "boom":
        bm = booms(s)
        add("tail volumes", tl["vh"] >= s.tail.vh_target - 1e-9 and tl["vv"] >= s.tail.vv_target - 1e-9,
            f"a {tl['span_mm'] / 1e3:.1f} m tailplane of {tl['chord_mm']:.0f} mm chord between the booms ({tl['sh_m2']:.2f} m^2) "
            f"and two fins {tl['fin_h_mm']:.0f} mm tall ({tl['sv_m2']:.2f} m^2), {tl['arm_m']:.2f} m behind the wing, give "
            f"volumes of {tl['vh']:.2f} horizontal and {tl['vv']:.3f} vertical")
        add("booms under the tail's load", bm["used"] <= 1 and bm["twist_deg"] == bm["twist_deg"],
            f"two {s.boom.od_mm:g} mm tubes {bm['length_mm']:.0f} mm long, {bm['kg'] * 1e3:.0f} g the pair; the tailplane's most "
            f"lift puts {bm['tail_load_n']:.0f} N on each end: {bm['sigma_mpa']:.0f} MPa at the spar ({bm['used']:.2f} of what it "
            f"can take), {bm['droop_mm']:.0f} mm of bend")
        add("wing's twist under the booms", bm["twist_deg"] <= s.wing.twist_max_deg,
            f"{bm['wing_torque_nm']:.0f} N m into the wing at each pod twists its skin box {bm['twist_deg']:.2f} deg between the "
            f"body and the boom, against {s.wing.twist_max_deg:g} allowed")
    else:
        add("tail volumes", tl["vh"] >= s.tail.vh_target - 1e-9 and tl["vv"] >= s.tail.vv_target - 1e-9,
            f"a {tl['area_m2']:.2f} m^2 V-tail at {s.tail.dihedral_deg:g} deg on a {tl['arm_m']:.2f} m arm gives volumes of "
            f"{tl['vh']:.2f} horizontal and {tl['vv']:.3f} vertical, against {s.tail.vh_target:g} and {s.tail.vv_target:g}: "
            f"it wants {tl['area_needed_m2']:.2f} m^2 on this arm, or a {tl['arm_needed_m']:.1f} m arm with this tail")
    if s.pods.count:
        bl = balance(s)
        prop_r = s.pods.prop_in * 25.4 / 2
        add("balance against the package's pusher", abs(bl["battery_aft_mm"]) <= bl["travel_mm"],
            "; ".join(f"{nm} {kg:.2f} kg at x = {x:.0f}" for nm, kg, x in bl["items"])
            + f": {bl['delta_kg']:+.2f} kg, and the CG {abs(bl['shift_mm']):.0f} mm {'forward' if bl['shift_mm'] > 0 else 'aft'}; "
            f"the battery slides {abs(bl['battery_aft_mm']):.0f} mm {'aft' if bl['battery_aft_mm'] > 0 else 'forward'} to put "
            f"it back, of {bl['travel_mm']:.0f} mm the rails leave it either way")
        cl = climb(s)
        add("climb, and one motor out", cl["out_tail_cl"] <= s.climb.tail_cl_max and cl["out_climb_ms"] > 0,
            f"{s.climb.rate_ms:g} m/s at {s.climb.speed_ms:g} m/s takes {cl['thrust_n']:.0f} N and {cl['shaft_w']:.0f} W of "
            f"shaft from {cl['motors']} motors (props {cl['eff']:.0%} efficient). One pod motor out leaves "
            f"{cl['out_climb_ms']:.1f} m/s of climb and {cl['out_yaw_nm']:.0f} N m of yaw, which the tail holds at a lift "
            f"coefficient of {cl['out_tail_cl']:.2f} (it has {s.climb.tail_cl_max:g})")
        ps = pod_sweep(s)
        add("where the props go on the pods", None, "; ".join(
            f"{r['layout']}: {r['motors']} motors, {r['kg']:.2f} kg a pod, {r['auw_kg']:.1f} kg all up, sink "
            f"{r['sink_ms']:.3f} m/s, one out leaves {r['out_climb_ms']:.1f} m/s" for r in ps))
        clear = strut_points(s)["y"] - prop_r - f.radius_mm
        if has_pusher(s):
            gap = strut_points(s)["y"] - s.boom.od_mm / 2 - s.propulsion.center_prop_in * 25.4 / 2
            add("pusher's disc between the booms", gap > 0, f"{gap:.0f} mm from a {s.propulsion.center_prop_in:g} in disc's "
                f"tip to each boom, and the tailplane's leading edge {s.tail.prop_clear_mm:g} mm behind it")
        add("props clear the body", clear > 0, f"{clear:.0f} mm between a {s.pods.prop_in:g} in disc and the body's side; "
            f"the discs' lowest point is {spar_xz(s, strut_points(s)['y'])[1] - prop_r + f.radius_mm:.0f} mm above the belly")
    ls = length_sweep(s)
    sized = [r for r in ls if r["sized"] and r["ok"]]
    best = min(sized, key=lambda r: r["sink_ms"]) if sized else None
    if best:
        add("how long the body can be", None,
            f"the tail cone's cubic can be drawn out to {max_length_mm(s) / 1e3:.2f} m overall before it swells past the "
            f"body's radius. With the tail sized to its volumes at each length, {ls[1]['length_m']:g} m needs "
            f"a {ls[1]['tail_m2']:.2f} m^2 tail and sinks at {ls[1]['sink_ms']:.3f} m/s; the best is {best['length_m']:g} m "
            f"({best['tail_m2']:.2f} m^2 of tail, {best['sink_ms']:.3f} m/s, {best['auw_kg']:.1f} kg); the longest, "
            f"{sized[-1]['length_m']:g} m, sinks at {sized[-1]['sink_ms']:.3f}")
    sw = span_sweep(s)
    ok = [r for r in sw if r["ok"]]
    first_bad = next((r for r in sw if not r["ok"]), None)
    add("how long the wing can be", None,
        (f"with these tubes it passes out to {ok[-1]['span_m']:g} m (aspect ratio {ok[-1]['ar']:.0f}, sink "
         f"{ok[-1]['sink_ms']:.2f} m/s)" if ok else "it does not pass at any span swept")
        + (f"; at {first_bad['span_m']:g} m the {first_bad['limit']} is over, at {first_bad['limit_used']:.2f}"
           if first_bad else "; nothing fails in the sweep"))
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
    stl = stall(s)
    add("stall speed", stl["ok"],
        f"at a lift coefficient of {s.flight.cl_max:g} and {s.mass.auw_kg:.1f} kg it stalls at {stl['vs_ms']:.1f} m/s clean; "
        f"the loiter's slow end, {s.flight.loiter_ms[0]:g} m/s, is {stl['margin']:.2f} times that (wants "
        f"{s.flight.stall_margin:g}). The package's {s.flight.stall_clean_ms:g} m/s would take {cl:.2f}")
    en = endurance(s)
    add("endurance under power", en["hours"] >= b.loiter_h,
        f"holding {en['v_ms']:g} m/s takes {en['shaft_w']:.0f} W of shaft (props {en['prop_eff']:.0%}), {en['draw_w']:.0f} W from "
        f"the pack with the avionics; {en['usable_wh']:.0f} Wh usable is {en['hours']:.1f} h with no help from thermals, "
        f"against {b.loiter_h:g}")
    fs_ = flap_split(s)
    add("centre flaps", None, f"hinge at x = {fs_['hinge_x_mm']:.0f}; {s.flap.crow_deg:g} deg down the trailing edge is at "
                              f"z = {fs_['te_down_z_mm']:.0f}, inside the body within {fs_['clash_half_w_mm']:.0f} mm of the "
                              f"centreline, so the flaps start at y = +/-{fs_['inboard_y_mm']:.0f} and the middle is fixed")
    return out


def run(variant: str = "pusher", pods: str | None = None) -> dict:
    s = inputs(variant)
    if pods:
        s = with_pods(s, pods)
    an, bare, ae = analyse(s), analyse(s, braced=False), aero(s)
    cuts = cut_list(s)
    rows = bom(s, cuts)
    sp = strut_points(s)
    return {"variant": variant, "label": s.variant.label, "span_sweep": span_sweep(s), "tail": tail(s),
            "lift": _lift_solved(s), "auw_kg": s.mass.auw_kg, "stall": stall(s), "endurance": endurance(s),
            "pod": pod(s), "pod_sweep": pod_sweep(s) if s.pods.count else [], "booms": booms(s),
            "length_sweep": length_sweep(s), "max_length_m": max_length_mm(s) / 1e3,
            "balance": balance(s),
            "analysis": an, "unbraced": bare, "sweep": sweep(s), "aero": ae, "bom": rows,
            "strut": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in sp.items()},
            "tube_mass_g": sum(r["mass_g"] for r in rows if r["mass_g"]),
            "nadir": nadir_flat(s), "flap": flap_split(s), "checks": checks(s, an, bare, ae)}


def _lift_solved(s) -> dict | None:
    if s.aero.lift != "vlm":
        return None
    from osprey.recon import sailplane_vlm as vlm

    return vlm.run_for(s)


def failed(res: dict) -> list[str]:
    return [c["name"] for c in res["checks"] if c["ok"] is False]


# ---- the report ----------------------------------------------------------------------------------------

def _inputs_of(res: dict):
    s = inputs(res["variant"])
    return with_pods(s, res["pod"]["layout"]) if res["pod"].get("layout") else s


def report(res: dict) -> str:
    s = _inputs_of(res)
    an = res["analysis"]
    mark = {True: "ok", False: "**FAIL**", None: "note"}
    L = ["# The sailplane: a truss-braced wing, its loads, drag and cut list", "", f"**{res['label']}**", "",
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
    L += ["", "Tension is positive. \"Used\" is the ultimate load over what the tube can take: above 1.00 it fails.", ""]
    if res.get("lift"):
        lt = res["lift"]
        L += ["## The lift, solved", "",
              "A vortex lattice of the wing, the braces and the tail (OpenAeroStruct), solved all together and, as "
              "Ting et al. do, each surface alone with the forces added. The loads take the second. Coefficients "
              "are on the wing's area, at the loiter's lift.", "",
              "| | Lift-curve slope, /rad | Lift at zero angle | Angle, deg | Wing's share | Braces' share | "
              "Tail, untrimmed | Span efficiency |", "|---|---|---|---|---|---|---|---|"]
        for k, name in (("alone", "each surface alone, summed"), ("whole", "all in one lattice"), ("unbraced", "no braces")):
            p_ = lt[k]
            eff = f"{p_['span_eff']:.2f}" if k != "alone" else "n/a"
            L.append(f"| {name} | {p_['cl_alpha']:.2f} | {p_['cl0']:.2f} | {p_['alpha_deg']:.1f} | {p_['share']['wing']:.1%} | "
                     f"{p_['share'].get('brace', 0):.1%} | {p_['tail_lift_frac']:+.1%} | {eff} |")
        L += ["", "Drag due to lift does not add up surface by surface (each is in the others' wash), so the summed "
              "solve gives no span efficiency. The lattice has no body, no thickness and nothing viscous.", ""]
    L += [
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
          "| Speed, m/s | CL | Wing | Braces | Tail | Body | Pods | Induced | L/D | Sink, m/s | L/D, no braces | Sink, no braces |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in ae["rows"]:
        c = r["cd0"]
        L.append(f"| {r['v_ms']:g} | {r['cl']:.2f} | {c['wing'] * 1e4:.0f} | {c['braces'] * 1e4:.0f} | {c['tail'] * 1e4:.0f} | "
                 f"{c['body'] * 1e4:.0f} | {c.get('pods', 0) * 1e4:.0f} | {r['cdi'] * 1e4:.0f} | {r['braced']['l_over_d']:.1f} | {r['braced']['sink_ms']:.2f} | "
                 f"{r['unbraced']['l_over_d']:.1f} | {r['unbraced']['sink_ms']:.2f} |")
    if res["pod_sweep"]:
        L += ["", "## Where the props go on the pods", "",
              f"A tractor at the front of each pod, a pusher at the back, or both. The props are sized for a "
              f"{s.climb.rate_ms:g} m/s climb at {s.climb.speed_ms:g} m/s; a motor's weight follows its power. Glide is with "
              "the props folded.", "",
              "| Props | Motors | Pod, mm | Pod, kg | All-up, kg | Battery slides aft, mm | Pods, counts | L/D | Sink, m/s | "
              "Props' efficiency | Shaft a motor, W | One out: thrust left | climb, m/s | yaw, N m | tail CL | Brace pull at 4 g, N |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in res["pod_sweep"]:
            L.append(f"| {r['layout']} | {r['motors']} | {r['length_mm']:.0f} | {r['kg']:.2f} | {r['auw_kg']:.1f} | "
                     f"{r['battery_aft_mm']:.0f} of {r['travel_mm']:.0f} | {r['pods_counts']:.1f} | {r['l_over_d']:.1f} | "
                     f"{r['sink_ms']:.3f} | {r['eff']:.0%} | {r['motor_w']:.0f} | {r['out_thrust_frac']:.0%} | "
                     f"{r['out_climb_ms']:.1f} | {r['out_yaw_nm']:.0f} | {r['out_tail_cl']:.2f}{'' if r['tail_ok'] else ' **over**'} | "
                     f"{r['brace_pull_n']:.0f} |")
    if res["length_sweep"]:
        L += ["", "## How long the body can be", "",
              f"The tail cone stretched, the nose and the parallel middle as they are. The cubic, held to its closing "
              f"angle, can be drawn out to {res['max_length_m']:.2f} m overall; past that it swells beyond the body's radius. "
              "At each length the V-tail is the size its two volumes ask for on that arm, and the shell's and tail's "
              "weights follow their areas. The first row is this variant as its design file has it.", "",
              "| Length, m | Fineness | Tail arm, m | Tail, m^2 | Volumes, horizontal and vertical | Body skin, m^2 | "
              "Body, counts | Tail, counts | All-up, kg | Tail cone's steepest, deg | L/D | Sink, m/s | |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["length_sweep"]:
        L.append(f"| {r['length_m']:g} | {r['fineness']:.1f} | {r['arm_m']:.2f} | {r['tail_m2']:.2f} | {r['vh']:.2f}, {r['vv']:.3f} | "
                 f"{r['body_m2']:.2f} | {r['cd0_body'] * 1e4:.0f} | {r['cd0_tail'] * 1e4:.0f} | {r['auw_kg']:.1f} | "
                 f"{r['slope_deg']:.1f} | {r['l_over_d']:.1f} | {r['sink_ms']:.3f} | "
                 f"{'as designed' if not r['sized'] else 'swells' if not r['ok'] else ''} |")
    L += ["", "## How long the wing can be", "",
          f"The outer panels stretched, the braces at the same share of the half-span, the tubes as they are. A span "
          f"passes while nothing is over 1.00 at ultimate and the tip rises no more than "
          f"{s.loads.tip_rise_max_frac:.0%} of the half-span in the pull-up.", "",
          "| Span, m | Area, m^2 | Aspect ratio | All-up, kg | Brace, mm | Most-used tube | Joiner | Tip's rise | "
          "What limits | L/D | Sink, m/s | Vertical tail volume | |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["span_sweep"]:
        L.append(f"| {r['span_m']:g} | {r['area_m2']:.2f} | {r['ar']:.1f} | {r['auw_kg']:.1f} | {r['brace_mm']:.0f} | "
                 f"{r['used']:.2f} | {r['joiner_used']:.2f} | {r['tip_frac']:.1%} | {r['limit']}, {r['limit_used']:.2f} | "
                 f"{r['l_over_d']:.1f} | {r['sink_ms']:.2f} | {r['vv']:.4f} | {'ok' if r['ok'] else '**over**'} |")
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


def params_scad(s, res: dict) -> str:  # noqa: C901
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
        "pusher": has_pusher(s), "tail_sign": 1 if s.tail.kind == "v" else -1, "tail_x": s.tail.x_mm,
        "tail_dihedral": s.tail.dihedral_deg, "tail_root": s.tail.root_chord_mm, "tail_tip": s.tail.tip_chord_mm,
        "tail_panel": res["tail"]["panel_mm"], "boom_tail": s.tail.kind == "boom",
        **({"boom_d": s.boom.od_mm, "boom_x": [res["booms"]["from_x_mm"], res["booms"]["to_x_mm"]],
            "htail_x": res["tail"]["le_x_mm"], "htail_chord": res["tail"]["chord_mm"], "fin_chord": s.tail.fin_chord_mm,
            "fin_h": res["tail"]["fin_h_mm"], "center_prop_d": s.propulsion.center_prop_in * 25.4}
           if s.tail.kind == "boom" else {"boom_d": 0, "boom_x": [0, 0], "htail_x": 0, "htail_chord": 0, "fin_chord": 0,
                                          "fin_h": 0, "center_prop_d": 0}), "tail_pts": np.c_[naca4(0.0, 0.4, s.tail.t_over_c, 20)],
        "pod_count": s.pods.count, **({"pod_d": s.pods.diameter_mm, "pod_len": res["pod"]["length_mm"],
                                        "pod_nose": res["pod"]["nose_x_mm"], "prop_d": s.pods.prop_in * 25.4,
                                        "pod_front": res["pod"]["front"], "pod_back": res["pod"]["back"]}
                                       if s.pods.count else {"pod_d": 0, "pod_len": 0, "pod_nose": 0, "prop_d": 0,
                                                             "pod_front": False, "pod_back": False}),
        "nadir_window": nd.window_mm, "nadir_pane": nf["pane_mm"], "nadir_pane_t": nd.pane_mm,
        "nadir_floor": nd.floor_mm, "nadir_xa": nf["xa_mm"], "nadir_za": nf["za_mm"], "nadir_tilt": nf["tilt_deg"],
        "nadir_margin": nd.margin_mm, "nadir_mount": nd.mount_mm, "nadir_boss": nd.boss_mm, "nadir_m3": nd.m3_mm,
    }
    head = ("// Written by `osprey recon-sailplane` from design/recon/sailplane.toml: do not edit, change the design "
            "file.\n// mm. Origin at the nose tip; +x aft, +y starboard, +z up.\n")
    return head + "".join(f"{k} = {_scad(x)};\n" for k, x in v.items())


def export(res: dict, out: Path) -> list[Path]:
    """The OpenSCAD parts, params.scad beside them, and the cut list as CSV."""
    s = _inputs_of(res)
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
