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
    the span by that many metres per joint, to show how it prints (a blended
    wing body: its upper and lower mould halves apart)."""
    if d.get("airframe") in ("bwb", "crescent"):
        return build_bwb(p, d, explode=explode)
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
    if getattr(p.payload, "layout", "gimbal") == "dual":
        # A PTZ eye on each side of the pod, looking out, and a belly fisheye dome.
        xc = x0 - 0.22 * L
        for side in (1, -1):
            yc = side * (R * 0.85 + 0.03)
            v, f = _sphere([xc, yc, zc - 0.2 * R], 0.034, 14)
            parts.append(Part(f"eye_{side}", "gimbal", v, f))
            v, f = _sphere([xc + 0.01, yc + side * 0.024, zc - 0.32 * R], 0.016, 10)
            parts.append(Part(f"lens_{side}", "lens", v, f))
        v, f = _sphere([x0 - 0.55 * L, 0, zc - R * 0.9], 0.02, 12)
        parts.append(Part("belly", "lens", v, f))
    else:
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


# --------------------------------------------------------------------------- blended wing body

def _stations(p, d: dict, n_span: int = 25):
    """Spanwise stations of a sized BWB, tip to root on one side: y, leading-edge
    x, chord, twist (rad) and thickness ratio, interpolated from the design."""
    ys = np.array(d["half_span_y_m"])
    order = np.argsort(ys)
    y0, le0, c0 = ys[order], np.array(d["le_x_m"])[order], np.array(d["chords_m"])[order]
    half = d["span_m"] / 2
    y = np.linspace(0, half, n_span)
    lez0 = np.array(d.get("le_z_m", np.zeros_like(ys)))[order]
    tw = np.array(d["twist_deg"])                       # control points, tip to root (OpenAeroStruct's order)
    tc = np.array(d.get("t_over_c_cp", [p.wing.t_over_c]))
    pos = 1 - y / half                                  # 0 at the tip, 1 at the root
    twist = np.radians(np.interp(pos, np.linspace(0, 1, len(tw)), tw)) if len(tw) > 1 else \
        np.radians(np.full_like(y, tw[0]))
    t_over_c = np.interp(pos, np.linspace(0, 1, len(tc)), tc) if len(tc) > 1 else np.full_like(y, tc[0])
    return y, np.interp(y, y0, le0), np.interp(y, y0, c0), twist, t_over_c, np.interp(y, y0, lez0)


def _section(foil_u, foil_z, le_x, chord, y, twist, z0=0.0) -> np.ndarray:
    """One closed section in the body frame (x forward): the leading edge at
    -le_x (OpenAeroStruct's x runs aft), twisted about the leading edge."""
    x = -(le_x + foil_u * chord)
    z = foil_z * chord
    xr = (x + le_x)
    c, s = math.cos(twist), math.sin(twist)
    return np.stack([-le_x + xr * c + z * s, np.full_like(x, y), z0 - xr * s + z * c], 1)


def bwb_surface(p, d: dict, n_span: int = 25, n_chord: int = 40, half: str | None = None):
    """The outer mould line as rings, root to tip for both sides (port y > 0
    first, mirrored). half="upper" or "lower" closes each section along its
    chord line instead, giving the solid above or below the parting surface:
    a plug for that half of the mould."""
    g = p.geometry
    y, le, c, tw, tc, lz = _stations(p, d, n_span)
    rings = []
    for sign in (1, -1):
        idx = range(n_span - 1, -1, -1) if sign < 0 else range(n_span)
        for i in idx:
            u, z = naca4(g.airfoil_camber, g.airfoil_camber_pos, float(tc[i]), n_chord)
            if half:
                k = len(u) // 2                              # the leading edge
                upper = (u[: k + 1], z[: k + 1])            # trailing edge to leading edge, top
                lower = (u[k:], z[k:])                      # leading edge back towards the trailing edge, bottom
                if half == "upper":
                    uu = np.r_[upper[0], np.linspace(0, 1, 12)[1:-1]]
                    zz = np.r_[upper[1], np.zeros(10)]
                else:
                    uu = np.r_[lower[0], 1.0, np.linspace(1, 0, 12)[1:-1]]
                    zz = np.r_[lower[1], 0.0, np.zeros(10)]
                rings.append(_section(uu, zz, le[i], c[i], sign * y[i], tw[i], lz[i]))
            else:
                rings.append(_section(u, z, le[i], c[i], sign * y[i], tw[i], lz[i]))
    return rings


def build_bwb(p, d: dict, *, explode: float = 0.0) -> list[Part]:
    """The blended wing body. explode > 0 pulls the upper and lower mould
    halves apart by that many metres, to show where the skins part."""
    g = p.geometry
    parts: list[Part] = []
    if explode > 0:
        for half, dz, kind in (("upper", explode, "shell0"), ("lower", -explode, "shell1")):
            rings = bwb_surface(p, d, half=half)
            n = len(rings) // 2
            for side, rr in (("L", rings[:n]), ("R", rings[n:])):
                v, f = loft(rr)
                v[:, 2] += dz
                parts.append(Part(f"skin_{half}_{side}", kind, v, f))
    else:
        rings = bwb_surface(p, d)
        n = len(rings) // 2
        for side, rr in (("L", rings[:n]), ("R", rings[n:])):
            v, f = loft(rr)
            parts.append(Part(f"wing_{side}", "shell0", v, f))
    y, le, c, tw, tc, lz = _stations(p, d)
    half = d["span_m"] / 2
    r_spar = d["spar_radius_mm"][-1] / 1e3
    xs = -(le + 0.30 * c)                                   # the 30 % chord line, swept back to the tips
    kind = d.get("airframe", "bwb")
    for sign in (1, -1):
        if kind == "bwb":
            k = int(0.92 * (len(y) - 1))
            v, f = _tube([xs[0], 0.0, lz[0]], [xs[k], sign * y[k], lz[k]], r_spar)
            parts.append(Part(f"spar_{sign}", "spar", v, f))
            continue
        # A curved wing takes its spar in short straight tubes, joined panel to panel.
        k_end = int(0.85 * (len(y) - 1))
        for j in range(0, k_end, 3):
            j2 = min(j + 3, k_end)
            v, f = _tube([xs[j], sign * y[j], lz[j]], [xs[j2], sign * y[j2], lz[j2]], r_spar * 0.8, 10)
            parts.append(Part(f"spar_{sign}_{j}", "spar", v, f))
    if kind == "crescent":
        # A slim nose pod for the camera and battery; the tips already curve up.
        L, R, x0 = g.pod_length_m, g.pod_diameter_m / 2, g.pod_nose_x_m
        xs_ = np.linspace(0, 1, 18)
        radius = R * np.where(xs_ < 0.3, np.sqrt(np.clip(1 - ((0.3 - xs_) / 0.3) ** 2, 0.02, 1)),
                              1 - 0.6 * (np.clip(xs_ - 0.3, 0, None) / 0.7) ** 1.4)
        a = np.linspace(0, 2 * math.pi, 24, endpoint=False)
        rings_p = [np.stack([np.full_like(a, x0 - x * L), r * np.cos(a), -0.2 * R + r * np.sin(a)], 1)
                   for x, r in zip(xs_, radius)]
        v, f = loft(rings_p)
        parts.append(Part("pod", "pod", v, f))
    hw = g.winglet_height_frac * d["span_m"] if kind == "bwb" else 0.0
    ct = c[-1]
    for sign in (1, -1):
        base = np.array([-le[-1], sign * half, lz[-1]])
        if hw <= 0:
            v, f = _sphere([base[0] - 0.02, sign * (half + 0.004), lz[-1]], 0.010, 10)
            parts.append(Part(f"light_{sign}", "red" if sign > 0 else "green", v, f))
            continue
        rings_w = []
        for k, zz in enumerate((0.0, hw)):
            cw = ct * (1.0 - 0.45 * k)
            u, z = naca4(0, 0.4, 0.09, 24)
            xw = base[0] - 0.4 * ct * k - u * cw
            rings_w.append(np.stack([xw, base[1] + z * cw, np.full_like(xw, zz)], 1))
        v, f = loft(rings_w)
        parts.append(Part(f"winglet_{sign}", "tail", v, f))
        v, f = _sphere([base[0] - 0.02, sign * (half + 0.004), 0.0], 0.010, 10)
        parts.append(Part(f"light_{sign}", "red" if sign > 0 else "green", v, f))
    # Payload under the centre body, at the CG station; pusher prop at the root trailing edge.
    xc = -d.get("cg_x_m", 0.25)
    depth = c[0] * tc[0]
    if kind == "crescent":
        xc, depth = g.pod_nose_x_m - 0.12, g.pod_diameter_m * 1.3          # under the nose pod
    if getattr(p.payload, "layout", "gimbal") == "dual":
        for sign in (1, -1):
            v, f = _sphere([xc, sign * 0.11, -0.45 * depth], 0.032, 14)
            parts.append(Part(f"eye_{sign}", "gimbal", v, f))
            v, f = _sphere([xc + 0.01, sign * 0.135, -0.5 * depth], 0.015, 10)
            parts.append(Part(f"lens_{sign}", "lens", v, f))
        v, f = _sphere([xc - 0.12, 0, -0.42 * depth], 0.02, 12)
        parts.append(Part("belly", "lens", v, f))
    else:
        v, f = _sphere([xc + 0.04, 0, -0.42 * depth], g.gimbal_radius_m)
        parts.append(Part("gimbal", "gimbal", v, f))
        v, f = _sphere([xc + 0.04 + g.gimbal_radius_m * 0.75, 0, -0.42 * depth - 0.01], g.gimbal_radius_m * 0.45)
        parts.append(Part("lens", "lens", v, f))
    xp = -(le[0] + c[0]) - 0.03                             # behind the root trailing edge
    if kind == "crescent":
        xp = min(xp, g.pod_nose_x_m - g.pod_length_m - 0.02)
    rp = g.prop_diameter_m / 2
    v, f = _tube([xp, 0, 0], [xp - 0.004, 0, 0], rp, 40)
    parts.append(Part("prop_disc", "disc", v, f))
    for blade in (0, math.pi):
        ang = 0.6 + blade
        tip = np.array([0, math.cos(ang), math.sin(ang)]) * rp * 0.97
        v, f = _tube([xp - 0.002, 0, 0], [xp - 0.002, tip[1], tip[2]], 0.009, 8)
        parts.append(Part(f"blade_{blade:.0f}", "prop", v, f))
    return parts
