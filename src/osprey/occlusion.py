"""What the boat itself hides from each camera: the mast, the sails, the hull
and the camera pods.

Everything is in the body frame. The mast is a vertical cylinder, each sail a
flat triangle (luff, foot, leech) swung to leeward by its sheet angle, the
hull a prism (the deck planform extruded from below the waterline to the
deck), and each pod housing a sphere, which is what hides the nadir from a
PTZ sitting on top of its own pod.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

EPS = 1e-6


@dataclass
class Occluders:
    mast: tuple[float, float, float]                     # radius, z0, z1 (axis at x = y = 0)
    sails: list[np.ndarray] = field(default_factory=list)  # (3, 3) triangles
    hull: object = None                                   # boat namespace, for the planform
    housings: list[tuple[np.ndarray, float]] = field(default_factory=list)  # pod centre, radius

    def half_beam(self, x: np.ndarray) -> np.ndarray:
        b = self.hull
        hb = b.beam_m / 2
        fwd = hb * (1 - ((x - b.max_beam_x_m) / (b.bow_x_m - b.max_beam_x_m)) ** 2)
        aft = hb * (1 - (1 - b.transom_beam_frac) * ((x - b.max_beam_x_m) / (b.stern_x_m - b.max_beam_x_m)) ** 2)
        hw = np.where(x >= b.max_beam_x_m, fwd, aft)
        return np.where((x <= b.bow_x_m) & (x >= b.stern_x_m), np.maximum(hw, 0), 0.0)

    def in_hull(self, p: np.ndarray) -> np.ndarray:
        return (p[..., 2] < self.hull.freeboard_m) & (p[..., 2] > -self.hull.draft_m) & \
               (np.abs(p[..., 1]) < self.half_beam(p[..., 0]))

    def blocked(self, cam: np.ndarray, pts: np.ndarray, *, hull: bool = True) -> np.ndarray:
        """Is the segment from cam (3,) to each of pts (M, 3) blocked?"""
        pts = np.atleast_2d(np.asarray(pts, float))
        d = pts - cam[None, :]
        out = self._mast(cam, d)
        for tri in self.sails:
            out |= _tri_hits(cam, d, tri)
        for c, r in self.housings:
            out |= _ball_hits(cam, d, c, r)
        if hull and self.hull is not None:
            ts = np.linspace(0.02, 0.98, 64)
            samples = cam[None, None, :] + ts[None, :, None] * d[:, None, :]
            out |= self.in_hull(samples).any(axis=1)
        return out

    def _mast(self, cam, d):
        r, z0, z1 = self.mast
        a = d[:, 0] ** 2 + d[:, 1] ** 2
        b = 2 * (cam[0] * d[:, 0] + cam[1] * d[:, 1])
        c = cam[0] ** 2 + cam[1] ** 2 - r**2
        disc = b**2 - 4 * a * c
        hit = np.zeros(d.shape[0], bool)
        ok = (disc >= 0) & (a > 1e-12)
        sq = np.sqrt(np.where(ok, disc, 0))
        for sgn in (-1, 1):
            t = np.where(ok, (-b + sgn * sq) / np.where(ok, 2 * a, 1), -1)
            z = cam[2] + t * d[:, 2]
            hit |= ok & (t > EPS) & (t < 1 - EPS) & (z >= z0) & (z <= z1)
        return hit


def _ball_hits(o: np.ndarray, d: np.ndarray, c: np.ndarray, r: float) -> np.ndarray:
    """Segment o + t d, t in (0, 1), against a sphere (a camera inside it sees out)."""
    f = o - c
    cc = f @ f - r**2
    if cc <= 0:
        return np.zeros(d.shape[0], bool)
    a = np.einsum("ij,ij->i", d, d)
    b = 2 * (d @ f)
    disc = b**2 - 4 * a * cc
    t = (-b - np.sqrt(np.maximum(disc, 0))) / (2 * a)
    return (disc >= 0) & (t > EPS) & (t < 1 - EPS)


def _tri_hits(o: np.ndarray, d: np.ndarray, tri: np.ndarray) -> np.ndarray:
    """Moller-Trumbore, segment o + t d, t in (0, 1)."""
    v0, v1, v2 = tri
    e1, e2 = v1 - v0, v2 - v0
    h = np.cross(d, e2)
    a = h @ e1
    ok = np.abs(a) > 1e-12
    f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
    s = o - v0
    u = f * (h @ s)
    q = np.cross(s, e1)
    v = f * (d @ q)
    t = f * (q @ e2)
    return ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > EPS) & (t < 1 - EPS)


def build(p, sail: str | None = None, heel_deg: float | None = None) -> Occluders:
    """Occluders for the scenario's sail plan. Sails sheet to leeward: heel +
    (starboard down) means wind from port, so the booms swing to starboard."""
    sail = sail if sail is not None else p.scenario.sail
    heel = heel_deg if heel_deg is not None else p.scenario.heel_deg
    lee = -1.0 if heel >= 0 else 1.0
    rg, m = p.sailplan, p.mast
    occ = Occluders((m.radius_m, m.deck_z_m, m.truck_z_m), [], p.boat)
    for pod in getattr(p, "pod", []):
        kit = getattr(p.electronics.kit, pod.kit)
        occ.housings.append((np.array(pod.pos_m, float), kit.housing_radius_m))
    if sail in ("main", "main+jib"):
        a = math.radians(rg.main_sheet_deg)
        clew = [-rg.boom_length_m * math.cos(a), lee * rg.boom_length_m * math.sin(a), rg.boom_z_m]
        occ.sails.append(np.array([[-m.radius_m, 0, rg.boom_z_m], [-m.radius_m, 0, rg.main_head_z_m], clew]))
    if sail == "main+jib":
        a = math.radians(rg.jib_sheet_deg)
        tack = np.array([rg.forestay_tack_x_m, 0, p.boat.freeboard_m])
        head = np.array([m.radius_m + 0.03, 0, rg.forestay_head_z_m])
        foot = rg.forestay_tack_x_m + rg.jib_clew_aft_m
        clew = [rg.forestay_tack_x_m - foot * math.cos(a), lee * foot * math.sin(a), rg.jib_clew_z_m]
        occ.sails.append(np.array([tack, head, clew]))
    elif sail not in ("down", "main"):
        raise ValueError(f"sail plan {sail!r}: use down, main or main+jib")
    return occ
