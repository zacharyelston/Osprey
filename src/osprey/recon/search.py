"""Search theory for the drone's camera: how wide a swath it sweeps, how
likely one pass is to find the person, and the probability of detection
(POD) over a drifting search area.

The camera looks ahead and down at depression_deg. Its swath is the
footprint's cross-track width, cut short where the person is too far to
resolve (Johnson detect), lost in haze, or behind a wave crest (the same wave
model the mast cameras use, at the drone's much steeper grazing angle).
POD follows Koopman: a cell crossed by the footprint with per-pass detection
p keeps a probability (1 - p) of still being unfound.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.special import erf

from osprey import optics


@dataclass
class Sweep:
    alt_m: float
    half_width_m: float    # cross-track half-width of the useful footprint
    near_m: float          # ground distance ahead of the drone to the footprint's near edge
    far_m: float           # and its far edge
    range_det_m: float     # slant range at which the person is still resolved
    binding: str
    p_vis: float           # chance the person is not behind a crest
    p_pass: float          # chance one pass finds a person inside the footprint
    # Several footprints at once (side-looking eyes and a belly camera), each
    # (along_lo, along_hi, cross_lo, cross_hi, p_pass) in track coordinates,
    # cross positive to the right. Empty: the one forward footprint above.
    rects: tuple = ()

    @property
    def width_eff_m(self) -> float:
        """Effective sweep width: the swath times the per-pass detection."""
        if self.rects:
            # Cross-track coverage, overlaps counted once at the better detection.
            xs = sorted({r[2] for r in self.rects} | {r[3] for r in self.rects})
            w = 0.0
            for a, b in zip(xs[:-1], xs[1:]):
                ps = [r[4] for r in self.rects if r[2] <= a and r[3] >= b]
                w += (b - a) * (1 - np.prod([1 - q for q in ps])) if ps else 0.0
            return w
        return 2 * self.half_width_m * self.p_pass

    def footprints(self):
        return self.rects or ((self.near_m, self.far_m, -self.half_width_m, self.half_width_m, self.p_pass),)

    @property
    def along_m(self) -> float:
        return self.far_m - self.near_m


def sweep(p, alt_m: float, depression_deg: float | None = None) -> Sweep:
    """The camera's useful footprint at an altitude, looking down at the
    payload's search depression (or depression_deg: 90 is straight down)."""
    cam, kind, pl = p.camera, p.target, p.payload
    f = pl.search_focal_mm
    ifov = optics.ifov(cam.pixel_um, f)
    hfov = optics.fov(cam.width_px, cam.pixel_um, f)
    vfov = optics.fov(cam.height_px, cam.pixel_um, f)
    k = p.atmosphere.k_refraction
    limits = {
        "resolution": optics.johnson_range_m(kind.crit_m, ifov, p.johnson.detect),
        "atmosphere": optics.contrast_range_m(p.mission.visibility_km * 1e3, kind.contrast,
                                              p.atmosphere.contrast_threshold),
        "horizon": optics.geometric_range_m(alt_m, kind.height_m, k),
    }
    r_det = min(limits.values())
    binding = min(limits, key=limits.get)
    dep = math.radians(pl.depression_deg if depression_deg is None else depression_deg)
    if r_det <= alt_m:
        return Sweep(alt_m, 0.0, 0.0, 0.0, r_det, binding, 0.0, 0.0)
    g_det = math.sqrt(r_det**2 - alt_m**2)
    lo, hi = dep - vfov / 2, dep + vfov / 2
    near = alt_m / math.tan(hi) if abs(hi - math.pi / 2) > 1e-9 else 0.0     # behind the drone past nadir
    far = min(alt_m / math.tan(lo) if lo > 0 else math.inf, g_det)
    slant = alt_m / math.sin(dep)
    fov_half = slant * math.tan(hfov / 2)
    half = min(fov_half, g_det)
    if fov_half <= g_det:
        binding = "field of view"
    centre = alt_m / math.tan(dep) if dep < math.pi / 2 - 1e-9 else 0.0
    p_vis = optics.wave_exposure(alt_m, max(centre, 1.0), kind.height_m, p.sea.hs_m, p.sea.tp_s, k=k, n=120) \
        if p.sea.hs_m > 0 else 1.0
    p_pass = pl.detector_recall * p_vis
    if getattr(pl, "layout", "gimbal") == "dual" and depression_deg is None:
        return side_sweep(p, alt_m, r_det, binding)
    return Sweep(alt_m, half, near, max(far, near), r_det, binding, p_vis, p_pass)


def side_sweep(p, alt_m: float, r_det: float, binding: str) -> Sweep:
    """Payload "dual": a PTZ eye on each side, looking out and down at
    side_depression_deg, each searching a strip on its own side of the track.
    The belly fisheye fills the gap underneath, as far out as it can still
    resolve the person."""
    cam, kind, pl = p.camera, p.target, p.payload
    f = pl.search_focal_mm
    k = p.atmosphere.k_refraction
    hfov = optics.fov(cam.width_px, cam.pixel_um, f)          # along the track
    vfov = optics.fov(cam.height_px, cam.pixel_um, f)         # across it, out from the side
    dep = math.radians(pl.side_depression_deg)
    g_det = math.sqrt(max(r_det**2 - alt_m**2, 0.0))
    lo, hi = dep - vfov / 2, dep + vfov / 2
    near = alt_m / math.tan(hi)
    far = min(alt_m / math.tan(lo) if lo > 0 else math.inf, g_det)
    slant = alt_m / math.sin(dep)
    half_along = slant * math.tan(hfov / 2)
    centre = alt_m / math.tan(dep)
    p_vis = optics.wave_exposure(alt_m, max(centre, 1.0), kind.height_m, p.sea.hs_m, p.sea.tp_s, k=k, n=120) \
        if p.sea.hs_m > 0 else 1.0
    q = pl.detector_recall * p_vis
    rects = [(-half_along, half_along, near, far, q), (-half_along, half_along, -far, -near, q)]
    if p.belly is not None:
        ifov_b = optics.ifov(p.belly.pixel_um, p.belly.focal_mm[0])
        r_b = optics.johnson_range_m(kind.crit_m, ifov_b, p.johnson.detect)
        g_b = min(math.sqrt(max(r_b**2 - alt_m**2, 0.0)), alt_m * math.tan(math.radians(pl.belly_halfangle_deg)))
        if g_b > 0:
            rects.append((-g_b, g_b, -min(g_b, near), min(g_b, near), pl.detector_recall))
    return Sweep(alt_m, far, -half_along, half_along, r_det, binding + " (side eyes)", p_vis, q, tuple(rects))


@dataclass
class Plan:
    coverage: float        # C = effective sweep width / track spacing
    half_size_m: float     # half the side of the square searched round the datum
    spacing_m: float
    track_m: float         # track length to search the square once at that spacing
    pod: float             # expected POD for that plan


def plan(sw: Sweep, sigma_m: float, pod_goal: float) -> Plan:
    """The cheapest square and coverage that reach pod_goal for a circular
    normal datum of sigma_m: POD = P(inside the square) * (1 - exp(-C))."""
    best = None
    if sw.width_eff_m <= 0:
        return Plan(0.0, 0.0, math.inf, math.inf, 0.0)
    for C in np.linspace(0.5, 6.0, 111):
        for a_s in np.linspace(1.0, 4.0, 61):
            a = a_s * sigma_m
            pod = erf(a / (sigma_m * math.sqrt(2))) ** 2 * (1 - math.exp(-C))
            if pod < pod_goal:
                continue
            track = (2 * a) ** 2 * C / sw.width_eff_m
            if best is None or track < best.track_m:
                best = Plan(float(C), float(a), sw.width_eff_m / C, float(track), float(pod))
    return best or Plan(6.0, 4 * sigma_m, sw.width_eff_m / 6, (8 * sigma_m) ** 2 * 6 / sw.width_eff_m, 0.0)


def expanding_square(spacing_m: float, half_size_m: float, first_deg: float = 0.0) -> np.ndarray:
    """Waypoints (N, 2) round the origin, legs S, S, 2S, 2S, ... turning right,
    until the square reaches half_size_m."""
    pts = [np.zeros(2)]
    head = math.radians(first_deg)
    n = 1
    while True:
        for _ in range(2):
            step = n * spacing_m * np.array([math.sin(head), math.cos(head)])
            pts.append(pts[-1] + step)
            head += math.pi / 2
        if np.abs(pts[-1]).max() >= half_size_m:
            break
        n += 1
    return np.array(pts)


class Grid:
    """The search area in the water's frame (it drifts with the person). Each
    cell holds its prior probability of holding the person and the chance it
    is still unfound."""

    def __init__(self, datum: np.ndarray, drift: np.ndarray, sigma_m: float, extent_sigma: float = 4.0,
                 cell_m: float | None = None):
        self.datum, self.drift = np.asarray(datum, float), np.asarray(drift, float)
        cell = cell_m or max(sigma_m / 15, 5.0)
        ax = np.arange(-extent_sigma * sigma_m, extent_sigma * sigma_m + 1e-9, cell)
        self.x, self.y = np.meshgrid(ax, ax)
        prior = np.exp(-(self.x**2 + self.y**2) / (2 * sigma_m**2))
        self.prior = prior / prior.sum()
        self.unfound = np.ones_like(prior)

    def look(self, pos: np.ndarray, track_rad: float, t: float, dt: float, v_ground: float, sw: Sweep):
        """One time step of the camera footprint ahead of the drone (ground
        position pos, ground track track_rad clockwise from north)."""
        if sw.p_pass <= 0 or sw.along_m <= 0:
            return
        rel = np.asarray(pos, float) - self.datum - self.drift * t
        fx, fy = math.sin(track_rad), math.cos(track_rad)
        dx, dy = self.x - rel[0], self.y - rel[1]
        along = dx * fx + dy * fy
        cross = dx * fy - dy * fx
        for a0, a1, c0, c1, q in sw.footprints():
            if q <= 0 or a1 <= a0:
                continue
            inside = (along >= a0) & (along <= a1) & (cross >= c0) & (cross <= c1)
            if inside.any():
                self.unfound[inside] *= (1 - q) ** (v_ground * dt / (a1 - a0))

    @property
    def pod(self) -> float:
        return float((self.prior * (1 - self.unfound)).sum())

    def remaining(self) -> np.ndarray:
        """Where the person is now most likely to be, given they haven't been found."""
        r = self.prior * self.unfound
        return r / max(r.sum(), 1e-300)
