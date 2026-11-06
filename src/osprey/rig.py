"""Camera stations: where each camera is, what it is, and what it can see."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey import optics


@dataclass
class Station:
    id: str
    cam_key: str
    cam: object            # camera namespace from cameras.toml
    pos: np.ndarray        # body frame, m
    face_az: float         # rad, CCW from the bow
    on_mast: bool
    zones: tuple[str, ...]

    @property
    def fixed(self) -> bool:
        return bool(getattr(self.cam, "fixed", False))

    @property
    def f_min(self) -> float:
        return self.cam.focal_mm[0]

    @property
    def f_max(self) -> float:
        return self.cam.focal_mm[1]

    def ifov(self, focal_mm: float | None = None) -> float:
        return optics.ifov(self.cam.pixel_um, focal_mm or self.f_max)

    def hfov(self, focal_mm: float | None = None) -> float:
        return optics.fov(self.cam.width_px, self.cam.pixel_um, focal_mm or self.f_min)

    def vfov(self, focal_mm: float | None = None) -> float:
        return optics.fov(self.cam.height_px, self.cam.pixel_um, focal_mm or self.f_min)

    def can_point(self, az: np.ndarray, el: np.ndarray) -> np.ndarray:
        """Inside the pan/tilt envelope (a fixed camera: inside its field of view)."""
        az, el = np.asarray(az, float), np.asarray(el, float)
        lo, hi = (math.radians(v) for v in self.cam.tilt_deg)
        if self.fixed:
            daz = np.angle(np.exp(1j * (az - self.face_az)))
            return (np.abs(daz) <= self.hfov() / 2) & (np.abs(el - lo) <= self.vfov() / 2)
        return (el >= lo - 1e-9) & (el <= hi + 1e-9)

    def slew_s(self, d_angle: float, zoom_change: bool = True) -> float:
        if self.fixed:
            return 0.0
        return d_angle / math.radians(self.cam.slew_dps) + (self.cam.zoom_s if zoom_change else 0.0)


def stations(p) -> list[Station]:
    out = []
    for s in p.station:
        out.append(Station(s.id, s.camera, getattr(p.camera, s.camera), np.array(s.pos_m, float),
                           math.radians(s.face_az_deg), s.on_mast, tuple(s.zones)))
    return out


def mass_aloft(sts: list[Station], truck_z: float) -> tuple[float, float]:
    """Total camera mass above the deck and its masthead equivalent: the mass
    at the truck with the same heeling moment (sum of m z / z_truck)."""
    m = sum(s.cam.mass_kg for s in sts if s.on_mast)
    eq = sum(s.cam.mass_kg * s.pos[2] / truck_z for s in sts if s.on_mast)
    return m, eq
