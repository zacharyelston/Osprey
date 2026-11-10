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
    if d.get("airframe") == "tandem":
        return build_tandem(p, d, explode=explode)
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
    if d.get("vtol") == "tailsitter":
        parts += _tailsitter_parts(p, d, y, le, c, lz)
        return parts
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


def _pod(x_bottom: float, y: float, z: float, r: float, length: float, n: int = 18) -> tuple[np.ndarray, np.ndarray]:
    """A float pod: a body of revolution along x, round at both ends, bottom (aft) end at x_bottom."""
    s = np.linspace(0, 1, n)
    radius = r * np.sqrt(np.clip(1 - (np.clip(np.abs(s - 0.5) - 0.5 + r / length, 0, None) * length / r) ** 2, 0.03, 1))
    a = np.linspace(0, 2 * math.pi, 20, endpoint=False)
    return loft([np.stack([np.full_like(a, x_bottom + q * length), y + rr * np.cos(a), z + rr * np.sin(a)], 1)
                 for q, rr in zip(s, radius)])


def _tailsitter_parts(p, d: dict, y, le, c, lz) -> list[Part]:
    """Two tractor props on the leading edge, and four float pods on struts at the trailing edge:
    one at each wing tip, and one either side of the wing plane on struts from the root."""
    h, fp = p.hover, p.floats
    half = d["span_m"] / 2
    parts = []
    rp = h.prop_diameter_m / 2
    for sign in (1, -1):
        yp = h.prop_y_frac * d["span_m"]
        xle = -float(np.interp(yp, y, le))
        zp = float(np.interp(yp, y, lz))
        v, f = _tube([xle + 0.06, sign * yp, zp], [xle - 0.02, sign * yp, zp], 0.018, 12)      # motor nacelle
        parts.append(Part(f"nacelle_{sign}", "carbon", v, f))
        xd = xle + 0.07
        v, f = _tube([xd, sign * yp, zp], [xd - 0.004, sign * yp, zp], rp, 40)
        parts.append(Part(f"prop_disc_{sign}", "disc", v, f))
        for blade in (0, math.pi):
            ang = 0.6 + blade + (0.8 if sign < 0 else 0.0)
            tip = np.array([0, math.cos(ang), math.sin(ang)]) * rp * 0.97
            v, f = _tube([xd - 0.002, sign * yp, zp], [xd - 0.002, sign * yp + tip[1], zp + tip[2]], 0.009, 8)
            parts.append(Part(f"blade_{sign}_{blade:.0f}", "prop", v, f))
    x_te = -(le + c)
    x_bottom = float(x_te.min()) - fp.pod_drop_m
    r, L = fp.pod_radius_m, fp.pod_length_m
    for sign in (1, -1):                                         # wing-tip pods, under the tip trailing edge
        v, f = _pod(x_bottom, sign * (half - r), float(lz[-1]), r, L)
        parts.append(Part(f"float_tip_{sign}", "pod", v, f))
        v, f = _tube([float(x_te[-1]) + 0.02, sign * (half - r), float(lz[-1])], [x_bottom + L, sign * (half - r),
                     float(lz[-1])], 0.006, 8)
        parts.append(Part(f"strut_tip_{sign}", "carbon", v, f))
    for sign in (1, -1):                                         # strut pods, above and below the wing plane
        zs = sign * fp.strut_half_m
        v, f = _pod(x_bottom, 0.0, zs, r, L)
        parts.append(Part(f"float_strut_{sign}", "pod", v, f))
        for x0 in (float(x_te[0]) + 0.10, float(x_te[0]) + 0.01):
            v, f = _tube([x0, 0.0, float(lz[0])], [x_bottom + L * 0.7, 0.0, zs], 0.007, 8)
            parts.append(Part(f"strut_{sign}_{x0:.2f}", "carbon", v, f))
    return parts


def build_cyclone(p, d: dict, cy, phi_deg: float, *, axis_frac: float = 0.25, mount_m: float = 0.04,
                  gimbal_drop_m: float = 0.07, spin_disc: bool = False) -> list[Part]:
    """The Cyclone (recon/cyclone.py) in its own frame: z up the spin axis, the hub at the origin, the arms
    evenly apart (arm 0 along +y, which mode 4 turns straight down: cyclone.layout), each twisted by B phi_deg
    off centre (0: chord and A pointing up the spin axis; the spin setting near 80: the chords nearly in the
    spin plane, leading edges going round), A's motor and prop on the leading edge a_station along each arm
    (or every other), the gimbal under the hub. spin_disc draws the disc it sweeps."""
    from osprey.recon import cyclone

    g = cyclone.geometry(p, d, cy)
    c, r0, R, ra = g["chord_m"], g["r0_m"], g["R_m"], g["a_r_m"]
    lay = cyclone.layout(cy)
    foil = naca4(0.0, 0.4, p.wing.t_over_c, 24)
    phi = math.radians(phi_deg)
    zhat = np.array([0.0, 0.0, 1.0])
    parts = []
    for k in range(cy.arms):
        psi = math.radians(lay["theta_deg"][k] - 90)
        er = np.array([math.cos(psi), math.sin(psi), 0.0])
        et = np.array([-math.sin(psi), math.cos(psi), 0.0])
        ch = math.cos(phi) * zhat + math.sin(phi) * et                 # toward the leading edge
        nn = -math.sin(phi) * zhat + math.cos(phi) * et
        u, w = foil
        sec = (axis_frac - u)[:, None] * c * ch + (w * c)[:, None] * nn
        v, f = loft([r * er + sec for r in (r0, R)])
        parts.append(Part(f"arm{k}", "shell0", v, f))
        if k % cy.a_every:
            continue
        le = ra * er + axis_frac * c * ch
        v, f = _tube(le - 0.03 * ch, le + mount_m * ch, 0.014, 12)
        parts.append(Part(f"motor{k}", "carbon", v, f))
        hub = le + mount_m * ch
        v, f = _tube(hub, hub + 0.003 * ch, cy.tri_prop_diameter_m / 2, 28)
        parts.append(Part(f"disc{k}", "disc", v, f))
        side = np.cross(ch, er)
        v, f = _tube(hub - cy.tri_prop_diameter_m / 2 * side, hub + cy.tri_prop_diameter_m / 2 * side, 0.006, 8)
        parts.append(Part(f"prop{k}", "prop", v, f))
    v, f = _sphere([0.0, 0.0, 0.0], r0, 20)
    parts.append(Part("hub", "pod", v, f))
    v, f = _sphere([0.0, 0.0, -gimbal_drop_m + 0.03], 0.03, 14)
    parts.append(Part("gimbal", "gimbal", v, f))
    v, f = _sphere([0.022, 0.0, -gimbal_drop_m + 0.025], 0.012, 10)
    parts.append(Part("lens", "lens", v, f))
    if spin_disc:
        v, f = _tube([0.0, 0.0, -0.002], [0.0, 0.0, 0.002], R, 64)
        parts.append(Part("rotor", "disc", v, f))
    return parts


def _tilt(parts: list[Part], xp: float, zp: float, tilt: float) -> list[Part]:
    """Turn parts about the spanwise axis through (xp, zp), leading edge up by tilt radians."""
    c, sn = math.cos(tilt), math.sin(tilt)
    for q in parts:
        dx, dz = q.verts[:, 0] - xp, q.verts[:, 2] - zp
        q.verts = np.stack([xp + dx * c - dz * sn, q.verts[:, 1], zp + dx * sn + dz * c], 1)
    return parts


def _streamlined(x_front: float, x_back: float, y: float, z: float, r: float, nose: float = 0.15,
                 full: float = 0.45, n: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """A streamlined body of revolution along x, from x_front back to x_back: a round nose over the first
    `nose` of its length, full radius r to `full`, then tapering to a point."""
    s = np.linspace(0, 1, n)
    k = np.where(s < nose, np.sqrt(np.clip(1 - ((nose - s) / nose) ** 2, 0, 1)),
                 np.where(s < full, 1.0, np.clip(1 - ((s - full) / (1 - full)) ** 2, 0, 1) ** 0.8))
    k = np.maximum(k, 0.03)
    a = np.linspace(0, 2 * math.pi, 20, endpoint=False)
    return loft([np.stack([np.full_like(a, x_front + q * (x_back - x_front)), y + rr * r * np.cos(a),
                           z + rr * r * np.sin(a)], 1) for q, rr in zip(s, k)])


def _hull(x_front: float, x_back: float, z: float, r: float, keel: float, nose: float = 0.15, full: float = 0.75,
          n: int = 28) -> tuple[np.ndarray, np.ndarray]:
    """A hull along x from x_front back to x_back, its sections a teardrop point down: a round top of radius r over
    the axis at height z, the sides falling straight from the beam, then closing to a V keel keel x r below the axis
    (deadrise atan(keel / 2)). Side on, the same nose, full length and taper as _streamlined."""
    s = np.linspace(0, 1, n)
    k = np.where(s < nose, np.sqrt(np.clip(1 - ((nose - s) / nose) ** 2, 0, 1)),
                 np.where(s < full, 1.0, np.clip(1 - ((s - full) / (1 - full)) ** 2, 0, 1) ** 0.8))
    k = np.maximum(k, 0.03)
    a = np.linspace(0, 2 * math.pi, 32, endpoint=False)
    top = np.sin(a) >= 0
    y = np.where(top, np.cos(a), np.cos(a) * np.abs(np.cos(a)))          # below the beam: y = r (1 - s^2), s = depth
    zz = np.where(top, np.sin(a), keel * np.sin(a))
    return loft([np.stack([np.full_like(a, x_front + q * (x_back - x_front)), rr * r * y, z + rr * r * zz], 1)
                 for q, rr in zip(s, k)])


def build_tandem(p, d: dict, *, explode: float = 0.0) -> list[Part]:
    """The tandem tilt-wing, after the quad tilt-wing model it is based on, both wings high: the front's
    half-wings start at the hull's sides on its top, the rear sits on a short pylon over the tail (the wings'
    gap, which also serves as the fin), turning on a shaft through the pylon's head. The hull is a teardrop
    point down, a V keel under a round top: it floats on the keel and tracks straight on it. A prop a side on
    each wing; each nacelle is one streamlined body, spinner, motor, through the wing at its full section and
    on behind the trailing edge, tapering, as a float. Each wing, with its nacelles and props, turns about its
    shaft by d["wing_tilt_deg"] (0 in cruise, 90 to hover). On the water the wings stand part way up, at
    the floats' stance tilt: the front float tails dip in as outriggers either side of the keel, the rear
    ones, a pylon higher, stay clear of it."""
    g, h = p.geometry, p.hover
    parts: list[Part] = []
    tilt = math.radians(d.get("wing_tilt_deg", 0.0))
    nf = d.get("nacelle_floats") or {"diameter_m": 0.07, "length_m": 0.35}
    rf, Lf = nf["diameter_m"] / 2, nf["length_m"]
    rp = h.prop_diameter_m / 2
    fu = p.fuselage
    R, zc = fu.diameter_m / 2, fu.axis_z_m
    keel = getattr(fu, "keel", 1.0)
    head_r = 0.035                                           # the rear shaft's housing, on the pylon
    # Each row's floats carry its share of the weight, standing: the CG between the pivots sets it.
    piv = {n: -(d["surfaces"][n]["le_x_m"][-1] + p.wing.pivot_frac * d["surfaces"][n]["chords_m"][-1])
           for n in ("front", "rear")}
    front_share = (-d.get("cg_x_m", 0.6) - piv["rear"]) / (piv["front"] - piv["rear"])
    share = {"front": front_share, "rear": 1 - front_share}
    for name, kind, tc in (("front", "shell0", p.wing.t_over_c), ("rear", "shell1", p.rear.t_over_c)):
        s_ = d["surfaces"][name]
        dd = {**d, **{k: s_[k] for k in ("half_span_y_m", "le_x_m", "le_z_m", "chords_m", "twist_deg", "span_m")},
              "t_over_c_cp": [tc]}
        y0, le0, c0, tw0, _, lz0 = _stations(p, dd, 25)
        root = R + 0.01 if name == "front" else head_r + 0.01   # the hull's side, or the pylon head's
        y = np.linspace(root, y0[-1], 12)
        le, c, tw, lz = (np.interp(y, y0, q) for q in (le0, c0, tw0, lz0))
        u, z = naca4(g.airfoil_camber, g.airfoil_camber_pos, tc, 32)
        wing: list[Part] = []
        for sign in (1, -1):
            v, f = loft([_section(u, z, le[i], c[i], sign * y[i], tw[i], lz[i]) for i in range(len(y))])
            wing.append(Part(f"{name}_{'L' if sign > 0 else 'R'}", kind, v, f))
            v, f = _sphere([-le[-1] - 0.02, sign * (y[-1] + 0.004), lz[-1]], 0.010, 10)
            wing.append(Part(f"light_{name}_{sign}", "red" if sign > 0 else "green", v, f))
        for frac in h.prop_y_frac:
            yp = frac * s_["span_m"]
            xle = -float(np.interp(yp, y, le))
            zp = float(np.interp(yp, y, lz))
            cp = float(np.interp(yp, y, c))
            r = max(rf * math.sqrt(2 * share[name]), 0.6 * tc * cp, 0.035)
            x_nose, x_tail = xle + 0.16, xle - cp - Lf
            for sign in (1, -1):
                tag = f"{name}_{sign}_{frac:.2f}"
                # One body: spinner and motor ahead of the wing, full through it, the float tapering behind.
                v, f = _streamlined(x_nose, x_tail, sign * yp, zp, r, nose=0.12, full=(0.16 + cp) / (x_nose - x_tail))
                wing.append(Part(f"float_{tag}", "pod", v, f))
                xd = x_nose - 0.03
                v, f = _tube([xd, sign * yp, zp], [xd - 0.004, sign * yp, zp], rp, 40)
                wing.append(Part(f"prop_disc_{tag}", "disc", v, f))
                for blade in (0, math.pi):
                    ang = 0.6 + blade + (0.8 if sign < 0 else 0.0)
                    tip = np.array([0, math.cos(ang), math.sin(ang)]) * rp * 0.97
                    v, f = _tube([xd - 0.002, sign * yp, zp], [xd - 0.002, sign * yp + tip[1], zp + tip[2]], 0.009, 8)
                    wing.append(Part(f"blade_{tag}_{blade:.0f}", "prop", v, f))
        xp, zp0 = -(le[0] + p.wing.pivot_frac * c[0]), float(lz[0])
        if name == "front":
            v, f = _tube([xp, -(R + 0.02), zp0], [xp, R + 0.02, zp0], 0.012, 10)
        else:
            v, f = _tube([xp, -(head_r + 0.02), zp0], [xp, head_r + 0.02, zp0], 0.012, 10)
            parts.append(Part("shaft_head", "pod", *_streamlined(xp + 0.10, xp - 0.22, 0.0, zp0, head_r, nose=0.3, full=0.5)))
            # The pylon: a symmetric section, its chord along x, from inside the hull up into the head.
            cy = 0.9 * c[0]
            uu, zz = naca4(0.0, 0.4, 0.15, 24)
            x_le = xp + 0.3 * cy
            rings = [np.stack([x_le - uu * cy, zz * cy, np.full_like(uu, zh)], 1) for zh in (zc, zp0)]
            parts.append(Part("pylon", "pod", *loft(rings)))
        parts.append(Part(f"shaft_{name}", "carbon", v, f))
        parts += _tilt(wing, xp, zp0, tilt)
    # The hull: round nose, full section past the front shaft, a fair tail; a V keel under it.
    v, f = _hull(fu.nose_x_m, fu.nose_x_m - fu.length_m, zc, R, keel, nose=0.15, full=0.70)
    parts.append(Part("pod", "pod", v, f))
    # The gimbal in the nose turret, over the waterline, looking forward and down.
    rg = g.gimbal_radius_m
    xc, zg = fu.nose_x_m - 1.1 * rg, zc + 0.45 * R
    v, f = _sphere([xc, 0, zg], rg)
    parts.append(Part("gimbal", "gimbal", v, f))
    v, f = _sphere([xc + rg * 0.75, 0, zg - 0.4 * rg], rg * 0.45)
    parts.append(Part("lens", "lens", v, f))
    return parts
