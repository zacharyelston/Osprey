"""The sailplane's sections: lift, drag and moment against angle and Reynolds number (NeuralFoil).

The wing works at Reynolds numbers of 250,000 to 400,000, the braces' fairings near 70,000 and the tail near
150,000, where a section's drag and its most lift are set by laminar separation and not by a flat plate's
skin friction. NeuralFoil is a neural-network stand-in for XFOIL: a panel method with a boundary layer. It
gives each section's polar in milliseconds, with a confidence in its own answer.

This module:
- tabulates each section once on a grid of angle and Reynolds number (`table`) and reads it by lift
  coefficient (`at_cl`) and for its most lift (`cl_max`);
- finds the wing's stall with the vortex lattice (`stall`): the angle at which the first span strip reaches
  its own section's most lift at its own Reynolds number, the critical-section method;
- adds up the wing's, braces' and tail's profile drag strip by strip at each strip's own lift and Reynolds
  number (`profile`), in place of the flat-plate skin friction.

Nothing here knows about the body, the pods or the booms, or about how one surface's boundary layer meets
another's.
"""

from __future__ import annotations

import math
import warnings

import numpy as np

from osprey.recon import sailplane as sp
from osprey.recon import sailplane_vlm as vlm

ALPHA = np.arange(-8.0, 18.01, 0.5)
RE = np.geomspace(2.0e4, 3.0e6, 28)
_TABLES: dict[tuple, dict] = {}


def coordinates(s, surface: str) -> tuple[tuple, np.ndarray]:
    """A surface's section, in Selig order, and a key that names it."""
    from osprey.recon.geometry import naca4

    if surface == "wing":
        return ("file", s.wing.airfoil), sp.airfoil(s.wing.airfoil)[0]
    m, t = (s.strut.camber, s.strut.t_over_c) if surface == "brace" else (0.0, s.tail.t_over_c)
    u, z = naca4(m, 0.4, t, 80)
    return ("naca", m, t), np.c_[u, z]


def table(s, surface: str) -> dict:
    """The section's lift, drag, moment, upper-surface transition and NeuralFoil's confidence on the grid of
    angle (rows) and Reynolds number (columns), and its most lift at each Reynolds number."""
    import neuralfoil as nf

    key, xy = coordinates(s, surface)
    if key not in _TABLES:
        A, R = np.meshgrid(ALPHA, RE, indexing="ij")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = nf.get_aero_from_coordinates(xy, alpha=A.ravel(), Re=R.ravel())
        t = {k: np.asarray(r[v]).reshape(A.shape) for k, v in (("cl", "CL"), ("cd", "CD"), ("cm", "CM"),
                                                                ("xtr", "Top_Xtr"), ("conf", "analysis_confidence"))}
        t["i_max"] = np.argmax(t["cl"], axis=0)
        t["cl_max"] = t["cl"].max(axis=0)
        _TABLES[key] = t
    return _TABLES[key]


def _column(t: dict, re: float) -> tuple[int, int, float]:
    x = np.clip(math.log(re), math.log(RE[0]), math.log(RE[-1]))
    j = min(int(np.searchsorted(np.log(RE), x, side="right")) - 1, len(RE) - 2)
    return j, j + 1, (x - math.log(RE[j])) / (math.log(RE[j + 1]) - math.log(RE[j]))


def cl_max(s, surface: str, re: float) -> float:
    t = table(s, surface)
    a, b, f = _column(t, re)
    return float(t["cl_max"][a] * (1 - f) + t["cl_max"][b] * f)


def at_cl(s, surface: str, cl: float, re: float) -> dict:
    """The section at a lift coefficient and Reynolds number, on the branch below its stall: its drag,
    moment, angle, where the upper surface goes turbulent, and NeuralFoil's confidence. Past its most lift
    it is read at its most lift and marked stalled."""
    t = table(s, surface)
    a, b, f = _column(t, re)
    out = {}
    for k in ("cd", "cm", "xtr", "conf", "alpha"):
        v = []
        for j in (a, b):
            i = int(t["i_max"][j]) + 1
            col = ALPHA[:i] if k == "alpha" else t[k][:i, j]
            v.append(float(np.interp(cl, t["cl"][:i, j], col)))
        out[k] = v[0] * (1 - f) + v[1] * f
    out["stalled"] = cl > cl_max(s, surface, re)
    return out


# ---- the wing's stall -------------------------------------------------------------------------------

def _strip_cl(s, name: str, lt: dict, how: str = "alone"):
    """A surface's strips' lift coefficients at the lattice's two angles, and their chords (m)."""
    m = vlm.meshes(s)[name]
    c = (m[-1, :, 0] - m[0, :, 0])
    chord = (c[:-1] + c[1:]) / 2
    cl = lt[how][name]["lift_n"] / 2 / (lt["q_pa"] * chord * lt["width_m"][name])
    return cl, chord


def stall(s) -> dict:
    """The stall by the critical section: raise the angle until one strip of the wing reaches its own
    section's most lift at its own Reynolds number. The wing's and braces' lift there is the most the
    aircraft has; the speed follows, and the Reynolds numbers with it, so it goes round."""
    lt = vlm.lattice(s)
    cl2, chord = _strip_cl(s, "wing", lt)
    S, W, rho, nu = sp.wing_area_m2(s), s.mass.auw_kg * sp.G, s.flight.rho_kgm3, s.aero.nu_m2s
    v = s.flight.stall_clean_ms
    for _ in range(6):
        lim = np.array([cl_max(s, "wing", v * c / nu) for c in chord])
        slope = (cl2[1] - cl2[0]) / (vlm.ALPHAS[1] - vlm.ALPHAS[0])
        a_strip = vlm.ALPHAS[0] + (lim - cl2[0]) / slope
        k = int(np.argmin(a_strip))
        alpha = float(a_strip[k])
        lift = sum(float(vlm._at(lt["alone"][n]["lift_n"], alpha).sum()) for n in ("wing", "brace") if n in lt["alone"])
        cl_all = lift / (lt["q_pa"] * S)
        v = math.sqrt(2 * W / (rho * S * cl_all))
    return {"vs_ms": v, "cl_max": cl_all, "alpha_deg": alpha, "section_cl_max": float(lim[k]),
            "first_y_m": float(abs(lt["y_m"]["wing"][k])), "re_there": v * float(chord[k]) / nu,
            "margin": s.flight.loiter_ms[0] / v, "ok": s.flight.loiter_ms[0] / v >= s.flight.stall_margin}


# ---- profile drag, strip by strip -------------------------------------------------------------------

def profile(s, v: float) -> dict:
    """Each lifting surface's profile drag coefficient (on the wing's area) in level flight at a speed: every
    strip's section drag at its own lift coefficient and Reynolds number. The wing's and braces' lift is the
    lattice's; the tail is read at zero lift. Also the least confidence NeuralFoil had, the wing's mean
    transition, and whether any strip is past its section's stall."""
    lt = vlm.lattice(s)
    S, nu = sp.wing_area_m2(s), s.aero.nu_m2s
    here = vlm.at_lift(s, s.mass.auw_kg * sp.G, v)
    q = 0.5 * s.flight.rho_kgm3 * v**2
    out = {"cd": {}, "conf": 1.0, "stalled": False}
    for name in lt["alone"]:
        _, chord = _strip_cl(s, name, lt)
        w = lt["width_m"][name]
        cl = here["strips"][name] / 2 / (q * chord * w) if name != "tail" else np.zeros_like(chord)
        rows = [at_cl(s, name, float(c_), v * float(ch) / nu) for c_, ch in zip(cl, chord)]
        cd = np.array([r["cd"] for r in rows])
        out["cd"][name] = float(2 * (cd * chord * w).sum() / S)
        out["conf"] = min(out["conf"], min(r["conf"] for r in rows))
        out["stalled"] = out["stalled"] or any(r["stalled"] for r in rows)
        if name == "wing":
            out["wing_cl"] = [float(cl.min()), float(cl.max())]
            out["wing_xtr"] = float(np.mean([r["xtr"] for r in rows]))
            out["wing_re"] = [v * float(chord.min()) / nu, v * float(chord.max()) / nu]
    return out


def summary(s) -> dict:
    """What the sections say about one design: the wing's section at the loiter, the stall, and each
    surface's Reynolds number."""
    v, nu = s.flight.loiter_ms[0], s.aero.nu_m2s
    re_w = v * s.wing.chord_mm / 1e3 / nu
    S = sp.wing_area_m2(s)
    cl = s.mass.auw_kg * sp.G / (0.5 * s.flight.rho_kgm3 * v**2 * S)
    sec = at_cl(s, "wing", cl, re_w)
    rows = []
    for name, chord in (("wing", s.wing.chord_mm), ("wing tip", s.wing.tip_chord_mm), ("brace", s.strut.chord_mm),
                        ("tail", sp.tail(s)["chord_mm"])):
        surf = "wing" if name.startswith("wing") else name
        re = v * chord / 1e3 / nu
        zero = at_cl(s, surf, cl if surf == "wing" else 0.0, re)
        rows.append({"surface": name, "chord_mm": chord, "re": re, "cl_max": cl_max(s, surf, re), "cd": zero["cd"],
                     "xtr": zero["xtr"], "conf": zero["conf"], "at_cl": cl if surf == "wing" else 0.0})
    return {"v_ms": v, "cl": cl, "section": {**sec, "re": re_w, "cl_max": cl_max(s, "wing", re_w)}, "rows": rows,
            "stall": stall(s), "profile": profile(s, v)}
