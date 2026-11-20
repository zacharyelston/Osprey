"""The sailplane's lift, solved: a vortex lattice of the wing, the braces and the tail (OpenAeroStruct).

The loads and the drag build-up in recon/sailplane.py assume the lift: elliptic over the span, a fixed share
on the braces, a guessed span efficiency. This solves it instead, the way Ting, Reynolds, Nguyen and Totah
do for the truss-braced wing:

- whole: every lifting surface in one lattice, each in the others' wash;
- by components (their superposition method 2): each surface solved alone and the forces added. They found
  the whole-configuration lattice a long way from CFD on the truss-braced wing and the sum of components
  close, so the sum is what the loads take; the gap between the two is how far to trust either.

A lattice is linear in the angle of attack, so two angles give every other: each surface's forces are
a + b * alpha, and the angle for any lift follows (`at_lift`).

Surfaces are camber sheets: the wing carries the SD7037's mean line, the braces their fairing's, the tail is
flat. Left out: the body, the pods and booms, the fins (no lift in straight flight), thickness, and anything
viscous, so no stall. The tail is at zero incidence, not trimmed.

Stations as in recon/sailplane.py, in metres here: x aft, y to starboard, z up. The lattice is the port half,
mirrored.
"""

from __future__ import annotations

import math
import warnings

import numpy as np

from osprey.recon import sailplane as sp

G = sp.G
ALPHAS = (0.0, 5.0)


# ---- the lattices ------------------------------------------------------------------------------------

def _sheet(le: np.ndarray, chord: np.ndarray, normal: np.ndarray, camber, nx: int) -> np.ndarray:
    """A camber sheet (nx, ny, 3): leading-edge points and chords along the span, the camber line set off
    along each station's normal."""
    xc = np.linspace(0.0, 1.0, nx)
    zc = np.array([camber(u) for u in xc])
    mesh = np.zeros((nx, len(chord), 3))
    for i in range(nx):
        mesh[i] = le + np.outer(chord * xc[i], [1.0, 0.0, 0.0]) + (chord * zc[i])[:, None] * normal
    return mesh


def _mean_line(s):
    _, up, lo = sp.airfoil(s.wing.airfoil)
    return lambda u: float(np.interp(u, up[:, 0], up[:, 1]) + np.interp(u, lo[:, 0], lo[:, 1])) / 2


def _naca_line(m: float, p: float = 0.4):
    return lambda u: m / p**2 * (2 * p * u - u * u) if u < p else m / (1 - p) ** 2 * (1 - 2 * p + 2 * p * u - u * u)


def _stations(breaks: list[float], per_m: float) -> np.ndarray:
    """Span stations from the tip in to the root, through every break, about per_m to the metre."""
    out = []
    for a, b in zip(breaks[:-1], breaks[1:]):
        n = max(2, int(round(abs(b - a) * per_m)))
        out.extend(np.linspace(a, b, n, endpoint=False))
    return np.array([*out, breaks[-1]])


def wing_mesh(s, nx: int = 5, per_m: float = 9.0) -> np.ndarray:
    w = s.wing
    h, jy, ys = sp.half_span(s) / 1e3, sp.joint_y(s) / 1e3, sp.strut_points(s)["y"] / 1e3
    y = _stations(sorted({-h, -jy, -ys, 0.0}), per_m)
    c = np.array([sp.chord_at(s, v * 1e3) for v in y]) / 1e3
    le = np.c_[(w.le_x_mm + s.spar.x_frac * (w.chord_mm - c * 1e3)) / 1e3, y,
               w.chord_z_mm / 1e3 + np.clip(np.abs(y) - jy, 0, None) * math.tan(math.radians(w.dihedral_deg))]
    g = np.where(np.abs(y) > jy, math.radians(w.dihedral_deg), 0.0)
    normal = np.c_[np.zeros_like(y), np.sin(g), np.cos(g)]                    # the port wing's, leaning inboard
    return _sheet(le, c, normal, _mean_line(s), nx)


def brace_mesh(s, nx: int = 3, ny: int = 9) -> np.ndarray:
    st = sp.strut_points(s)
    c = s.strut.chord_mm / 1e3
    a, b = st["wing"] / 1e3 * [1, -1, 1], st["root"] / 1e3 * [1, -1, 1]       # port: from the wing's pin in to the root
    line = a + np.linspace(0, 1, ny)[:, None] * (b - a)
    line[:, 0] -= 0.3 * c                                                     # the tube is at 30 % of the fairing
    d = (b - a) / np.linalg.norm(b - a)
    n = np.array([0.0, -d[2], d[1]])
    n = n / np.linalg.norm(n) * (1 if n[2] > 0 else -1)
    return _sheet(line, np.full(ny, c), np.tile(n, (ny, 1)), _naca_line(s.strut.camber), nx)


def tail_mesh(s, nx: int = 3, ny: int = 9) -> np.ndarray:
    """The V-tail's port panel, or the port half of the boom tail's tailplane. Flat."""
    tl = sp.tail(s)
    flat = lambda u: 0.0                                                      # noqa: E731
    if tl["kind"] == "boom":
        y = np.linspace(-tl["span_mm"] / 2e3, 0.0, ny)
        z = (sp.spar_xz(s, tl["span_mm"] / 2)[1] - s.pods.diameter_mm / 5) / 1e3
        le = np.c_[np.full(ny, tl["le_x_mm"] / 1e3), y, np.full(ny, z)]
        return _sheet(le, np.full(ny, tl["chord_mm"] / 1e3), np.tile([0.0, 0.0, 1.0], (ny, 1)), flat, nx)
    t = s.tail
    g = math.radians(t.dihedral_deg) * (1 if t.kind == "v" else -1)
    u = np.linspace(1.0, 0.0, ny)                                             # from the tip in to the root
    span = tl["panel_mm"] / 1e3 * u
    c = (t.root_chord_mm + (t.tip_chord_mm - t.root_chord_mm) * u) / 1e3
    le = np.c_[t.x_mm / 1e3 + 0.25 * (t.root_chord_mm / 1e3 - c), -span * math.cos(g), span * math.sin(g)]
    return _sheet(le, c, np.tile([0.0, math.sin(g), math.cos(g)], (ny, 1)), flat, nx)


def meshes(s, braced: bool = True) -> dict[str, np.ndarray]:
    out = {"wing": wing_mesh(s)}
    if braced:
        out["brace"] = brace_mesh(s)
    out["tail"] = tail_mesh(s)
    return out


# ---- the solve ---------------------------------------------------------------------------------------

def _solve(ms: dict[str, np.ndarray], alphas, v: float, rho: float) -> dict:
    """One lattice of the given surfaces at each angle: every surface's panel forces (N, body axes, the
    port half) at each angle."""
    import openmdao.api as om
    from openaerostruct.aerodynamics.aero_groups import AeroPoint
    from openaerostruct.geometry.geometry_group import Geometry

    surfs = [{"name": n, "symmetry": True, "S_ref_type": "projected", "mesh": m, "CL0": 0.0, "CD0": 0.0,
              "k_lam": 0.05, "t_over_c_cp": np.array([0.09]), "c_max_t": 0.3, "with_viscous": False,
              "with_wave": False} for n, m in ms.items()]
    prob = om.Problem(reports=False)
    iv = prob.model.add_subsystem("iv", om.IndepVarComp(), promotes=["*"])
    for name, val, units in (("v", v, "m/s"), ("alpha", 0.0, "deg"), ("Mach_number", v / 340.0, None),
                             ("re", rho * v / 1.81e-5, "1/m"), ("rho", rho, "kg/m**3"), ("cg", np.zeros(3), "m")):
        iv.add_output(name, val, units=units)
    for sf in surfs:
        prob.model.add_subsystem(sf["name"], Geometry(surface=sf))
    prob.model.add_subsystem("pt", AeroPoint(surfaces=surfs),
                             promotes_inputs=["v", "alpha", "Mach_number", "re", "rho", "cg"])
    for sf in surfs:
        n = sf["name"]
        prob.model.connect(f"{n}.mesh", f"pt.{n}.def_mesh")
        prob.model.connect(f"{n}.mesh", f"pt.aero_states.{n}_def_mesh")
        prob.model.connect(f"{n}.t_over_c", f"pt.{n}_perf.t_over_c")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prob.setup()
        out = {n: [] for n in ms}
        for a in alphas:
            prob.set_val("alpha", a, units="deg")
            prob.run_model()
            for n in ms:
                out[n].append(np.array(prob.get_val(f"pt.aero_states.{n}_sec_forces", units="N")))
    return {n: np.array(f) for n, f in out.items()}


def _key(s, braced: bool) -> tuple:
    w, st, t = s.wing, sp.strut_points(s), sp.tail(s)
    return (braced, w.span_mm, w.center_span_mm, w.chord_mm, w.tip_chord_mm, w.dihedral_deg, w.chord_z_mm, w.airfoil,
            st["y"], tuple(st["root"]), s.strut.chord_mm, s.strut.camber, t["kind"], round(t["area_m2"], 6),
            round(t["x_mm"], 3), s.tail.dihedral_deg, s.flight.rho_kgm3)


_CACHE: dict[tuple, dict] = {}


def lattice(s, braced: bool = True) -> dict:
    """Both ways of solving the configuration, at the two reference angles: for each surface, the lift and
    the drag due to lift of each span strip (N, both sides together, at the reference speed), with the whole
    lattice and with each surface alone. Cached by the geometry."""
    key = _key(s, braced)
    if key in _CACHE:
        return _CACHE[key]
    v, rho = s.climb.speed_ms, s.flight.rho_kgm3
    ms = meshes(s, braced)
    whole = _solve(ms, ALPHAS, v, rho)
    alone = {n: _solve({n: m}, ALPHAS, v, rho)[n] for n, m in ms.items()}
    out = {"v_ms": v, "q_pa": 0.5 * rho * v**2, "y_m": {}, "width_m": {}, "edges_m": {}, "whole": {}, "alone": {}}
    for n, m in ms.items():
        qc = m[0] + 0.25 * (m[-1] - m[0])
        mid = (qc[:-1] + qc[1:]) / 2
        out["y_m"][n] = mid[:, 1]
        out["edges_m"][n] = qc[:, 1]
        out["width_m"][n] = np.linalg.norm((qc[1:] - qc[:-1])[:, 1:], axis=1)
        for how, f in (("whole", whole[n]), ("alone", alone[n])):
            strips = f.sum(axis=1)                                            # (angle, strip, 3): over the chord
            lift, drag = [], []
            for a, fs in zip(ALPHAS, strips):
                ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                lift.append(2 * (fs[:, 2] * ca - fs[:, 0] * sa))
                drag.append(2 * (fs[:, 0] * ca + fs[:, 2] * sa))
            out[how][n] = {"lift_n": np.array(lift), "drag_n": np.array(drag)}
    _CACHE[key] = out
    return out


def _at(pair: np.ndarray, alpha: float) -> np.ndarray:
    """A lattice's forces at any angle, from the two it was solved at."""
    return pair[0] + (pair[1] - pair[0]) * (alpha - ALPHAS[0]) / (ALPHAS[1] - ALPHAS[0])


def at_lift(s, lift_n: float, v_ms: float, how: str = "alone", braced: bool = True, carry=("wing", "brace")) -> dict:
    """The configuration carrying a lift at a speed: the angle of attack at which the wing and braces
    together make it (the tail's own lift is reported but left out of the balance, as the loads leave it),
    and each surface's strips there."""
    lt = lattice(s, braced)
    k = (v_ms / lt["v_ms"]) ** 2
    carry = [n for n in carry if n in lt[how]]
    l0 = sum(lt[how][n]["lift_n"][0].sum() for n in carry) * k
    l1 = sum(lt[how][n]["lift_n"][1].sum() for n in carry) * k
    alpha = ALPHAS[0] + (lift_n - l0) / (l1 - l0) * (ALPHAS[1] - ALPHAS[0])
    out = {"alpha_deg": float(alpha), "strips": {}, "lift_n": {}, "y_m": lt["y_m"], "width_m": lt["width_m"],
           "edges_m": lt["edges_m"]}
    for n in lt[how]:
        out["strips"][n] = _at(lt[how][n]["lift_n"], alpha) * k
        out["lift_n"][n] = float(out["strips"][n].sum())
    return out


def polar(s, how: str = "alone", braced: bool = True) -> dict:
    """The lift curve and the drag due to lift, on the wing's area: the slope and zero-angle lift, each
    surface's share of the lift at the loiter's lift coefficient, and the span efficiency there. The lattice's
    drag is the sum of its panels' forces along the wind, which is rough; the efficiency is a guide."""
    lt = lattice(s, braced)
    S, q = sp.wing_area_m2(s), lt["q_pa"]
    names = [n for n in ("wing", "brace") if n in lt[how]]
    cl = [sum(lt[how][n]["lift_n"][i].sum() for n in names) / (q * S) for i in (0, 1)]
    slope = (cl[1] - cl[0]) / math.radians(ALPHAS[1] - ALPHAS[0])
    v = s.climb.speed_ms
    target = s.mass.auw_kg * G
    here = at_lift(s, target, v, how, braced)
    a = here["alpha_deg"]
    # Drag due to lift is quadratic in the angle; three points fix it, the third from a solve at the trim angle.
    ms = meshes(s, braced)
    if how == "whole":
        f = _solve(ms, [a], v, s.flight.rho_kgm3)
        strips = {n: f[n][0].sum(axis=0) for n in names}
    else:
        strips = {n: _solve({n: ms[n]}, [a], v, s.flight.rho_kgm3)[n][0].sum(axis=0) for n in names}
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    di = sum(2 * float((fs[:, 0] * ca + fs[:, 2] * sa).sum()) for fs in strips.values())
    cl_here, cdi = target / (q * S), di / (q * S)
    ar = (s.wing.span_mm / 1e3) ** 2 / S
    return {"how": how, "cl_alpha": float(slope), "cl0": float(cl[0]), "alpha_deg": float(a), "cl": cl_here, "cdi": cdi,
            "span_eff": cl_here**2 / (math.pi * ar * cdi) if cdi > 0 else float("nan"),
            "share": {n: here["lift_n"][n] / target for n in here["lift_n"]},
            "tail_lift_frac": here["lift_n"].get("tail", 0.0) / target}


def wing_lift_between(s, here: dict, y0_mm: float, y1_mm: float) -> float:
    """The solved wing's lift (N) between two span stations (mm): its strips, shared out by overlap."""
    e, f = here["edges_m"]["wing"] * 1e3, here["strips"]["wing"]
    total = 0.0
    for sign in (1, -1):                                                      # the strips are the port half's, doubled
        a, b = sign * e[:-1], sign * e[1:]
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        over = np.clip(np.minimum(hi, y1_mm) - np.maximum(lo, y0_mm), 0, None)
        total += float((f / 2 * over / (hi - lo)).sum())
    return total


def run(variant: str = "pusher") -> dict:
    return run_for(sp.inputs(variant))


def run_for(s) -> dict:
    """The lattice's answers for one design: both ways, and against what the loads and the drag assumed."""
    out = {"variant": s.variant.name, "assumed": {"brace_share": s.aero.brace_lift_frac, "span_eff": s.aero.oswald},
           "whole": polar(s, "whole"), "alone": polar(s, "alone"), "unbraced": polar(s, "alone", braced=False)}
    pull = at_lift(s, s.loads.n * s.mass.auw_kg * G, s.flight.stall_clean_ms * math.sqrt(s.loads.n))
    y = pull["y_m"]["wing"]
    h = sp.half_span(s) / 1e3
    per_m = pull["strips"]["wing"] / 2 / pull["width_m"]["wing"]
    ell = 2 * pull["lift_n"]["wing"] / (math.pi * h) * np.sqrt(np.clip(1 - (y / h) ** 2, 0, None))
    out["pull_up"] = {"alpha_deg": pull["alpha_deg"], "y_m": y.tolist(), "lift_n_per_m": per_m.tolist(),
                      "elliptic_n_per_m": ell.tolist(), "brace_share": pull["lift_n"].get("brace", 0.0) / sum(
                          pull["lift_n"][n] for n in ("wing", "brace") if n in pull["lift_n"]),
                      "centre_m": float((per_m * np.abs(y) * pull["width_m"]["wing"]).sum()
                                        / (per_m * pull["width_m"]["wing"]).sum()),
                      "elliptic_centre_m": 4 * h / (3 * math.pi)}
    return out
