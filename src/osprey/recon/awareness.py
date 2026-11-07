"""Anti-piracy awareness: how far out each eye can detect, recognize and
identify a fast skiff, and how many minutes of warning that buys.

Each range is the smallest of four limits:
- resolution: Johnson cycles across the target at the camera's longest
  focal length, with the stabilizer's residual jitter folded into the pixel;
- the geometric horizon from the eye height to the target's top;
- the atmosphere: contrast lost to haze (Koschmieder);
- waves: the target visible at least half the time past the crests.

A drone at altitude beats the mast on every limit except resolution. Its
small gimbal can't match a 200 mm stabilized PTZ, so it gains most where
the horizon and the waves bind.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from osprey import optics
from osprey.motion import KN
from osprey.params import DESIGN, _toml, ns


@dataclass
class Eye:
    name: str
    height_m: float
    camera: str
    focal_mm: float | None = None     # default: the camera's longest


EYES = [
    Eye("Spreader bullet (12.5 m, 8 mm)", 12.5, "bullet_4k"),
    Eye("Masthead long PTZ (18.9 m, 200 mm)", 18.9, "ptz_long"),
    Eye("Drone gimbal at 120 m (30 mm)", 120.0, "recon_eo"),
    Eye("Drone side PTZ eye at 120 m (30 mm)", 120.0, "recon_ptz_mini"),
    Eye("Drone gimbal at 300 m (30 mm)", 300.0, "recon_eo"),
    Eye("Drone gimbal at 500 m (30 mm)", 500.0, "recon_eo"),
]
TARGETS = [("skiff_wake", "detect"), ("skiff", "detect"), ("skiff", "recognize"), ("person_aboard", "identify")]


def reach(eye: Eye, kind, need: str, johnson, sea: dict, visibility_m: float, atm) -> tuple[float, str]:
    cams = _toml(DESIGN / "cameras.toml")["camera"]
    cam = ns(cams[eye.camera])
    f = eye.focal_mm or cam.focal_mm[1]
    ifov = optics.ifov(cam.pixel_um, f)
    blur = max(1.0, cam.stabilization.floor_urad * 1e-6 / ifov) if cam.stabilization.floor_urad else 1.0
    k = atm.k_refraction
    limits = {
        "resolution": optics.johnson_range_m(kind.crit_m, ifov, getattr(johnson, need)) / blur,
        "horizon": optics.geometric_range_m(eye.height_m, kind.height_m, k),
        "atmosphere": optics.contrast_range_m(visibility_m, kind.contrast, atm.contrast_threshold),
    }
    d = min(limits.values())
    why = min(limits, key=limits.get)
    if sea["hs_m"] > 0 and optics.wave_exposure(eye.height_m, d, kind.height_m, sea["hs_m"], sea["tp_s"], k=k,
                                                n=120) < 0.5:
        lo, hi = 10.0, d
        for _ in range(16):
            mid = math.sqrt(lo * hi)
            if optics.wave_exposure(eye.height_m, mid, kind.height_m, sea["hs_m"], sea["tp_s"], k=k, n=120) >= 0.5:
                lo = mid
            else:
                hi = mid
        d, why = lo, "waves"
    return d, why


def table(sea_state: str = "ss3", visibility_km: float = 15.0, closing_kn: float = 30.0) -> list[dict]:
    tg = _toml(DESIGN / "targets.toml")
    sea_all = _toml(DESIGN / "sea.toml")
    sea = sea_all["sea"][sea_state]
    atm = ns(sea_all["atmosphere"])
    johnson = ns(tg["johnson"])
    rows = []
    for eye in EYES:
        row = {"eye": eye.name, "height_m": eye.height_m}
        for cls, need in TARGETS:
            d, why = reach(eye, ns(tg["target"][cls]), need, johnson, sea, visibility_km * 1e3, atm)
            row[f"{cls}:{need}"] = (d, why, d / (closing_kn * KN) / 60)
        rows.append(row)
    return rows
