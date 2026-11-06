"""What a stabilized camera still sees of the mast's motion.

Each stage is a first-order rejection loop: it passes disturbance above its
bandwidth fc and removes it below, S(f) = jf / (jf + fc). The outer gimbal
takes the large, slow motion (heel, roll, pitch); the inner fast stage (sensor
shift or a steering mirror) cleans up what is left, but only while the
residual angle stays inside its stroke. No gimbal means S = 1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def _reject(x: np.ndarray, dt: float, fc: float) -> np.ndarray:
    if fc <= 0:
        return x
    n = x.shape[0]
    f = np.fft.rfftfreq(n, dt)
    S = (1j * f) / (1j * f + fc)
    return np.fft.irfft(np.fft.rfft(x, axis=0) * S[:, None], n=n, axis=0)


@dataclass
class Residual:
    rate: np.ndarray       # (N, 3) rad/s left after stabilization
    angle: np.ndarray      # (N, 3) rad pointing jitter, mean removed
    saturated: float       # fraction of time the inner stage ran out of stroke


def residual(rate: np.ndarray, dt: float, stab) -> Residual:
    """rate is the camera mount's angular rate (N, 3), rad/s."""
    r1 = _reject(rate, dt, stab.outer_hz)
    sat = np.zeros(rate.shape[0], bool)
    out = r1
    if stab.inner_hz > 0:
        a1 = np.cumsum(r1, axis=0) * dt
        a1 -= a1.mean(axis=0)
        sat = np.linalg.norm(a1, axis=1) > math.radians(stab.inner_stroke_deg)
        r2 = _reject(r1, dt, stab.inner_hz)
        out = np.where(sat[:, None], r1, r2)
    ang = np.cumsum(out, axis=0) * dt
    ang -= ang.mean(axis=0)
    if stab.floor_urad > 0:
        ang = ang + np.random.default_rng(0).normal(0, stab.floor_urad * 1e-6 / math.sqrt(3), ang.shape)
    return Residual(out, ang, float(sat.mean()))


def across(v: np.ndarray, d: np.ndarray) -> np.ndarray:
    """|component of v (N, 3) perpendicular to the unit boresight d|."""
    d = d / np.linalg.norm(d)
    return np.linalg.norm(v - (v @ d)[:, None] * d[None, :], axis=1)


def blur_px(res: Residual, d_body: np.ndarray, exposure_ms: float, ifov_rad: float,
            vel: np.ndarray | None = None, range_m: float | None = None) -> np.ndarray:
    """Motion blur in pixels per frame along boresight d. With vel and range_m,
    adds the parallax of the camera's own translation, which no gimbal removes
    for a near target (docking) unless it tracks."""
    w = across(res.rate, d_body)
    if vel is not None and range_m:
        w = w + across(vel, d_body) / range_m
    return w * exposure_ms * 1e-3 / ifov_rad


def jitter_rad(res: Residual, d_body: np.ndarray) -> float:
    """RMS pointing jitter across the boresight."""
    return float(np.sqrt(np.mean(across(res.angle, d_body) ** 2)))
