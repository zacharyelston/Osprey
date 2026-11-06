"""Optics over water: horizon, resolution, atmosphere, wave shadowing and ranging.

Angles are radians and lengths metres unless a name says otherwise. Refraction
is the usual effective-earth-radius model, R_eff = R / (1 - k).
"""

from __future__ import annotations

import math

import numpy as np

from osprey.motion import G, bretschneider

R_EARTH = 6_371_000.0


def r_eff(k: float = 0.13) -> float:
    return R_EARTH / (1 - k)


def horizon_m(h: float, k: float = 0.13) -> float:
    return math.sqrt(2 * r_eff(k) * max(h, 0.0))


def geometric_range_m(h_eye: float, h_target: float, k: float = 0.13) -> float:
    """Farthest range at which the target's top is above the horizon."""
    return horizon_m(h_eye, k) + horizon_m(h_target, k)


def hidden_m(d: float, h_eye: float, k: float = 0.13) -> float:
    """Height hidden below the horizon at range d."""
    return max(0.0, d - horizon_m(h_eye, k)) ** 2 / (2 * r_eff(k))


def ifov(pixel_um: float, focal_mm: float) -> float:
    return pixel_um * 1e-6 / (focal_mm * 1e-3)


def fov(pixels: int, pixel_um: float, focal_mm: float) -> float:
    return 2 * math.atan(pixels * pixel_um * 1e-3 / (2 * focal_mm))


def johnson_range_m(crit_m: float, ifov_rad: float, cycles: float) -> float:
    """Range at which crit_m spans 2 px per Johnson cycle."""
    return crit_m / (2 * cycles * ifov_rad)


def contrast_range_m(visibility_m: float, contrast: float, threshold: float = 0.02) -> float:
    """Koschmieder: range at which apparent contrast falls to the threshold."""
    if contrast <= threshold:
        return 0.0
    return visibility_m / 3.912 * math.log(contrast / threshold)


def dip(d, h: float, k: float = 0.13):
    """Depression below level of the waterline at range d, seen from height h."""
    d = np.asarray(d, float)
    return h / d + d / (2 * r_eff(k))


def horizon_dip(h: float, k: float = 0.13) -> float:
    return math.sqrt(2 * h / r_eff(k))


def dip_range(delta: float, h: float, k: float = 0.13) -> float:
    """Invert the waterline-below-horizon angle to a range (bisection)."""
    lo, hi = 1.0, horizon_m(h, k)
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if dip(mid, h, k) - horizon_dip(h, k) > delta:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def dip_ranging(d: float, h: float, ifov_rad: float, *, hs: float = 0.0, subpx: float = 0.3,
                k: float = 0.13, dk: float = 0.04) -> tuple[float, float]:
    """1-sigma random error and refraction bias of horizon-dip ranging at range d.

    The waterline and the horizon are in the same frame, so camera attitude
    cancels. Random error is sub-pixel edge noise plus the waterline moving
    with the waves (sigma = Hs/4); the bias is what an error of dk in the
    assumed refraction coefficient does."""
    if d >= horizon_m(h, k):
        return math.inf, math.inf
    sens = abs(-h / d**2 + 1 / (2 * r_eff(k)))
    sigma_a = math.hypot(ifov_rad * subpx, (hs / 4) / d)
    delta = float(dip(d, h, k)) - horizon_dip(h, k)
    bias = abs(dip_range(delta, h, k + dk) - d)
    return sigma_a / sens, bias


def stereo_sigma_m(d: float, baseline_perp: float, ifov_rad: float, *, subpx: float = 0.3,
                   rel_orient_urad: float = 50.0) -> float:
    """1-sigma triangulation range error for two views separated by baseline_perp
    (the baseline component perpendicular to the line of sight). rel_orient_urad
    is how well the two cameras' relative orientation is known: tens of urad
    when they share a fiducial (the deck, the horizon), mrad on a flexing rig."""
    if baseline_perp <= 1e-6:
        return math.inf
    sigma = math.hypot(math.sqrt(2) * ifov_rad * subpx, rel_orient_urad * 1e-6)
    return d**2 * sigma / baseline_perp


def wave_exposure(h_eye: float, d: float, h_target: float, hs: float, tp: float, *,
                  k: float = 0.13, n: int = 200, seed: int = 0, span_m: float = 400.0,
                  dx: float = 0.25) -> float:
    """Fraction of moments the target's top clears every crest between it and
    the eye. 1-D Monte Carlo along the line of sight with long-crested waves
    running along it (the worst case); the target rides the surface."""
    if hs <= 0:
        return 1.0
    rng = np.random.default_rng(seed)
    w = np.linspace(0.3, 5.0, 80)
    amp = np.sqrt(2 * bretschneider(w, hs, tp) * (w[1] - w[0]))
    kw = w**2 / G
    L = min(d * 0.999, span_m)
    s = np.arange(0.0, L, dx)
    ph = rng.uniform(0, 2 * math.pi, (n, w.size))
    eta = np.zeros((n, s.size))
    for j in range(w.size):
        eta += amp[j] * np.cos(kw[j] * s[None, :] + ph[:, j:j + 1])
    top = eta[:, :1] + h_target
    ray = top + (h_eye - top) * s[None, :] / d - s[None, :] * (d - s[None, :]) / (2 * r_eff(k))
    clear = (ray[:, 2:] > eta[:, 2:]).all(axis=1)
    return float(clear.mean())
