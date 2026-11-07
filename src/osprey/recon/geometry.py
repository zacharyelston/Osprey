"""The drone as triangle meshes, built from a sized design: the printed wing
panels (split where the printer bed splits them), the carbon spar, the pod,
gimbal, twin booms, tail and pusher prop. Body frame: x forward, y left,
z up, origin at the spar on the centreline.

The wing comes from the sizing loop; everything else is REF geometry from
[geometry] in design/recon/airframe.toml, with the tail set by volume
coefficients.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Part:
    name: str
    kind: str            # shell, spar, carbon, pod, gimbal, tail, prop, light
    verts: np.ndarray    # (N, 3)
    faces: np.ndarray    # (M, 3) int


def naca4(m: float, pos: float, t: float, n: int = 36) -> tuple[np.ndarray, np.ndarray]:
    """A closed NACA 4-digit section: (u, z) in chord units, u from 0 at the
    leading edge, running trailing edge -> upper -> leading edge -> lower."""
    beta = np.linspace(0, math.pi, n)
    x = (1 - np.cos(beta)) / 2
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1036 * x**4)
    if m > 0:
        yc = np.where(x < pos, m / pos**2 * (2 * pos * x - x**2), m / (1 - pos) ** 2 * (1 - 2 * pos + 2 * pos * x - x**2))
        dy = np.where(x < pos, 2 * m / pos**2 * (pos - x), 2 * m / (1 - pos) ** 2 * (pos - x))
    else:
        yc, dy = np.zeros_like(x), np.zeros_like(x)
    th = np.arctan(dy)
    xu, zu = x - yt * np.sin(th), yc + yt * np.cos(th)
    xl, zl = x + yt * np.sin(th), yc - yt * np.cos(th)
    u = np.r_[xu[::-1], xl[1:-1]]
    z = np.r_[zu[::-1], zl[1:-1]]
    return u, z


def loft(rings: list[np.ndarray], cap: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Join closed rings of equal length (each (k, 3)) into a mesh, capping the
    ends. Every face is wound to point outward (renderers cull the back face):
    a side face away from the local axis between its two rings, a cap away
    from the neighbouring ring."""
    k = len(rings[0])
    v = np.concatenate(rings)
    cent = [r.mean(0) for r in rings]
    f, out = [], []
    for r in range(len(rings) - 1):
        a, b = r * k, (r + 1) * k
        mid = (cent[r] + cent[r + 1]) / 2
        for i in range(k):
            j = (i + 1) % k
            for tri in ((a + i, b + i, b + j), (a + i, b + j, a + j)):
                f.append(tri)
                out.append(v[list(tri)].mean(0) - mid)
    if cap:
        for r, nb in ((0, 1), (len(rings) - 1, len(rings) - 2)):
            c = len(v)
            v = np.vstack([v, cent[r]])
            base = r * k
            for i in range(k):
                j = (i + 1) % k
                f.append((c, base + i, base + j))
                out.append(cent[r] - cent[nb])
    f = np.array(f, int)
    n = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    flip = np.einsum("ij,ij->i", n, np.array(out)) < 0
    f[flip] = f[flip][:, ::-1]
    return v, f


def _wing_ring(foil, x_spar_frac: float, chord: float, y: float, z: float, twist: float = 0.0) -> np.ndarray:
    u, w = foil
    x = (x_spar_frac - u) * chord
    zz = w * chord
    c, s = math.cos(twist), math.sin(twist)
    return np.stack([x * c + zz * s, np.full_like(x, y), z - x * s + zz * c], 1)


def _tube(p0, p1, r: float, n: int = 16) -> tuple[np.ndarray, np.ndarray]:
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax = (p1 - p0) / np.linalg.norm(p1 - p0)
    ref = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(ax, ref)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    circ = r * (np.cos(a)[:, None] * e1 + np.sin(a)[:, None] * e2)
    return loft([p0 + circ, p1 + circ])


def _sphere(c, r: float, n: int = 16) -> tuple[np.ndarray, np.ndarray]:
    rings = []
    for lat in np.linspace(-math.pi / 2 + 0.15, math.pi / 2 - 0.15, n // 2):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        rings.append(np.asarray(c) + r * np.stack([math.cos(lat) * np.cos(a), math.cos(lat) * np.sin(a),
                                                    np.full_like(a, math.sin(lat))], 1))
    return loft(rings)


def tail_size(p, d: dict) -> dict:
    """Tail by volume coefficients: arm, horizontal span and chord, fin height and chord."""
    g = p.geometry
    b, S = d["span_m"], d["S_m2"]
    cbar = S / b
    arm = max(g.tail_arm_min_m, g.tail_arm_frac * b)
    boom_y = max(g.boom_y_min_m, g.boom_y_frac * b)
    bh = 2 * boom_y                                              # the stabilizer spans the booms
    ch = max(g.tail_volume_h * S * cbar / arm / bh, g.tail_chord_min_m)
    Sv = g.tail_volume_v * S * b / arm / 2                       # each of two fins
    cv = max(math.sqrt(Sv / g.fin_aspect), g.tail_chord_min_m)
    hv = max(Sv / cv, 0.6 * cv)
    return {"arm": arm, "boom_y": boom_y, "Sh": bh * ch, "bh": bh, "ch": ch, "Sv": hv * cv, "hv": hv, "cv": cv}


def build(p, d: dict, *, explode: float = 0.0) -> list[Part]:
    """The whole drone. explode > 0 pulls the printed wing panels apart along
    the span by that many metres per joint, to show how it prints."""
    g, w = p.geometry, p.wing
    foil = naca4(g.airfoil_camber, g.airfoil_camber_pos, w.t_over_c)
    fo = w.fem_origin
    ys = np.array(d["half_span_y_m"])
    cs = np.array(d["chords_m"])
    order = np.argsort(ys)
    ys, cs = ys[order], cs[order]
    half = d["span_m"] / 2
    bed = p.print.bed_m[2]
    cuts = list(np.arange(0, half, bed)) + [half]
    dih = math.radians(g.dihedral_deg)
    twist = np.radians(d.get("twist_deg", [0, 0]))
    parts: list[Part] = []
    for side in (1, -1):
        for k in range(len(cuts) - 1):
            y0, y1 = cuts[k], cuts[k + 1]
            shift = explode * (k + 0.5) * side
            rings = []
            for y in np.linspace(y0, y1, 4):
                c = float(np.interp(y, ys, cs))
                tw = float(np.interp(y / half, [0, 1], [twist[-1], twist[0]]))
                rings.append(_wing_ring(foil, fo, c, side * y + shift, y * math.tan(dih), tw))
            v, f = loft(rings)
            parts.append(Part(f"panel_{'L' if side > 0 else 'R'}{k}", f"shell{k % 2}", v, f))
    r_spar = d["spar_radius_mm"][-1] / 1e3
    span_e = half + explode * len(cuts)
    v, f = _tube([0, -span_e, 0], [0, span_e, 0], r_spar)
    parts.append(Part("spar", "spar", v, f))
    for side in (1, -1):                                        # nav lights: red port, green starboard
        v, f = _sphere([-0.02, side * (half + explode * (len(cuts) - 1.5)), half * math.tan(dih)], 0.012, 10)
        parts.append(Part(f"light_{side}", "red" if side > 0 else "green", v, f))

    # Fuselage pod: a body of revolution, nose ahead of the spar, motor at the back.
    L, R, x0 = g.pod_length_m, g.pod_diameter_m / 2, g.pod_nose_x_m
    xs = np.linspace(0, 1, 18)
    radius = R * np.where(xs < 0.3, np.sqrt(np.clip(1 - ((0.3 - xs) / 0.3) ** 2, 0.02, 1)),
                          1 - 0.55 * (np.clip(xs - 0.3, 0, None) / 0.7) ** 1.6)
    a = np.linspace(0, 2 * math.pi, 24, endpoint=False)
    zc = -0.25 * R
    rings = [np.stack([np.full_like(a, x0 - x * L), r * np.cos(a), zc + r * np.sin(a)], 1) for x, r in zip(xs, radius)]
    v, f = loft(rings)
    parts.append(Part("pod", "pod", v, f))
    v, f = _sphere([x0 - 0.18 * L, 0, zc - R * 0.95], g.gimbal_radius_m)
    parts.append(Part("gimbal", "gimbal", v, f))
    v, f = _sphere([x0 - 0.18 * L + g.gimbal_radius_m * 0.75, 0, zc - R * 0.95], g.gimbal_radius_m * 0.45)
    parts.append(Part("lens", "lens", v, f))

    # Twin booms to an H-tail, two fins; a pusher prop behind the pod.
    t = tail_size(p, d)
    xt = -t["arm"]
    for side in (1, -1):
        y = side * t["boom_y"]
        v, f = _tube([0.08, y, 0], [xt - 0.75 * t["ch"] - 0.02, y, 0], g.boom_radius_m, 10)
        parts.append(Part(f"boom_{side}", "carbon", v, f))
    hfoil = naca4(0, 0.4, g.tail_t_over_c)
    zt = t["hv"] * 0.85
    rings = [_wing_ring(hfoil, 0.25, t["ch"], y, zt) for y in np.linspace(-t["bh"] / 2, t["bh"] / 2, 3)]
    v, f = loft(rings)
    v[:, 0] += xt
    parts.append(Part("htail", "tail", v, f))
    for side in (1, -1):
        rings = []
        for z in np.linspace(0, t["hv"], 3):
            r_ = _wing_ring(hfoil, 0.25, t["cv"], 0.0, 0.0)
            r_ = r_[:, [0, 2, 1]]                                 # section in x-y, extruded up z
            r_[:, 1] += side * t["boom_y"]
            r_[:, 2] = z
            rings.append(r_)
        v, f = loft(rings)
        v[:, 0] += xt - 0.2 * (t["ch"] - t["cv"])
        parts.append(Part(f"fin_{side}", "tail", v, f))
    xp = x0 - L - 0.01
    rp = g.prop_diameter_m / 2
    v, f = _tube([xp, 0, zc], [xp - 0.004, 0, zc], rp, 40)
    parts.append(Part("prop_disc", "disc", v, f))
    for blade in (0, math.pi):
        ang = 0.6 + blade
        tip = np.array([0, math.cos(ang), math.sin(ang)]) * rp * 0.97
        v, f = _tube([xp - 0.002, 0, zc], [xp - 0.002, tip[1], zc + tip[2]], 0.009, 8)
        parts.append(Part(f"blade_{blade:.0f}", "prop", v, f))
    return parts


def bounds(parts: list[Part]) -> tuple[np.ndarray, np.ndarray]:
    allv = np.concatenate([q.verts for q in parts])
    return allv.min(0), allv.max(0)
