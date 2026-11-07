"""Camera stations: where each camera is, what it is, and what it can see."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey import frames, optics


@dataclass
class Station:
    id: str
    cam_key: str
    cam: object            # camera namespace from cameras.toml
    pos: np.ndarray        # body frame, m
    face_az: float         # rad, CCW from the bow
    on_mast: bool
    zones: tuple[str, ...]
    pod: str | None = None
    sector: float = 2 * math.pi   # watch sector, full width, centred on face_az

    def in_sector(self, az: np.ndarray) -> np.ndarray:
        """Is a body azimuth inside the sector this camera sweeps on watch?"""
        daz = np.angle(np.exp(1j * (np.asarray(az, float) - self.face_az)))
        return np.abs(daz) <= self.sector / 2 + 1e-9

    @property
    def fixed(self) -> bool:
        return bool(getattr(self.cam, "fixed", False))

    @property
    def fisheye(self) -> bool:
        return getattr(self.cam, "projection", "pinhole") == "equidistant"

    @property
    def boresight(self) -> np.ndarray:
        """A fixed camera's look direction in the body frame."""
        return frames.direction(self.face_az, math.radians(self.cam.tilt_deg[0]))

    @property
    def f_min(self) -> float:
        return self.cam.focal_mm[0]

    @property
    def f_max(self) -> float:
        return self.cam.focal_mm[1]

    def ifov(self, focal_mm: float | None = None) -> float:
        """Radial pixel angle; for an equidistant fisheye it is the same at every
        field angle (tangentially it is finer away from the centre)."""
        return optics.ifov(self.cam.pixel_um, focal_mm or self.f_max)

    def hfov(self, focal_mm: float | None = None) -> float:
        if self.fisheye:
            return math.radians(self.cam.fov_deg)
        return optics.fov(self.cam.width_px, self.cam.pixel_um, focal_mm or self.f_min)

    def vfov(self, focal_mm: float | None = None) -> float:
        if self.fisheye:
            return math.radians(self.cam.fov_deg)
        return optics.fov(self.cam.height_px, self.cam.pixel_um, focal_mm or self.f_min)

    @property
    def image_circle_px(self) -> int:
        """A fisheye's image circle diameter: the fov_deg circle, cropped to the sensor's short side."""
        f_px = self.f_min * 1e3 / self.cam.pixel_um
        return min(int(2 * f_px * math.radians(self.cam.fov_deg) / 2), self.cam.width_px, self.cam.height_px)

    def can_point(self, az: np.ndarray, el: np.ndarray) -> np.ndarray:
        """Inside the pan/tilt envelope (a fixed camera: inside its field of view)."""
        az, el = np.asarray(az, float), np.asarray(el, float)
        lo, hi = (math.radians(v) for v in self.cam.tilt_deg)
        if self.fisheye:
            cos_off = frames.direction(az, el) @ self.boresight
            return cos_off >= math.cos(math.radians(self.cam.fov_deg) / 2)
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
                           math.radians(s.face_az_deg), s.on_mast, tuple(s.zones), getattr(s, "pod", None),
                           math.radians(getattr(s, "sector_deg", 360.0))))
    return out


@dataclass
class Pod:
    """A two-sided mount: its cameras, and the SOC, IMU and housing between them."""
    id: str
    kit: object
    soc: object
    imu: object
    pos: np.ndarray
    on_mast: bool
    members: list[Station]

    @property
    def electronics_kg(self) -> float:
        return self.kit.housing_kg + self.soc.mass_kg + self.imu.mass_kg

    @property
    def has_computer(self) -> bool:
        return self.soc.tops_int8 > 0

    @property
    def horizontal(self) -> bool:
        return getattr(self.kit, "layout", "vertical") == "horizontal"

    def ports(self) -> list[tuple[str, float]]:
        """PoE ports and their peak draw: one per pod with a computer, one per
        camera when each camera has its own cable."""
        if self.has_computer:
            return [(self.id, self.load_w("active"))]
        return [(s.id, s.cam.power_w[1] / self.kit.pd_efficiency) for s in self.members]

    def load_w(self, mode: str, working: set[str] = frozenset()) -> float:
        """Power the pod draws from its PoE port. mode "active": everything
        working; "watch": SOC at watch power, cameras parked unless in `working`."""
        i = 1 if mode == "active" else 0
        cams = sum(s.cam.power_w[1 if (mode == "active" or s.id in working or s.fixed) else 0]
                   for s in self.members)
        return (cams + self.soc.power_w[i] + self.imu.power_w) / self.kit.pd_efficiency

    def pixel_rate(self, fps: float) -> float:
        """Pixels per second off both sensors (a fisheye: its image circle's square)."""
        return sum((s.image_circle_px ** 2 if s.fisheye else s.cam.width_px * s.cam.height_px) * fps
                   for s in self.members)


def pods(p) -> list[Pod]:
    el = p.electronics
    sts = stations(p)
    out = []
    for d in p.pod:
        kit = getattr(el.kit, d.kit)
        out.append(Pod(d.id, kit, getattr(el.soc, kit.soc), getattr(el.imu, kit.imu), np.array(d.pos_m, float),
                       d.on_mast, [s for s in sts if s.pod == d.id]))
    return out


def mass_aloft(sts: list[Station], truck_z: float, pods: list[Pod] = ()) -> tuple[float, float]:
    """Total mass above the deck and its masthead equivalent: the mass at the
    truck with the same heeling moment (sum of m z / z_truck). Cameras, plus
    each pod's SOC, IMU and housing at the pod centre."""
    items = [(s.cam.mass_kg, s.pos[2]) for s in sts if s.on_mast]
    items += [(pd.electronics_kg, pd.pos[2]) for pd in pods if pd.on_mast]
    return sum(m for m, _ in items), sum(m * z / truck_z for m, z in items)
