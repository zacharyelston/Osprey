"""Boat and masthead motion in a seaway.

Linear seakeeping, screening level: a Bretschneider wave spectrum drives roll,
pitch and heave through damped single-degree-of-freedom responses, at the
encounter frequency for the boat's speed and wave heading. Wave slope is
averaged over the beam (roll) or waterline (pitch), so short waves do little.
Steady heel, helm yaw wander and the mast's first bending mode are added on
top. Waves are long-crested from one direction.

This is the model the Bosun's Chair pod (Phase 0) exists to replace: feed a
measured attitude log through `Motion` and every downstream calc is unchanged.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from osprey import frames

G = 9.81
KN = 0.514444


def bretschneider(w: np.ndarray, hs: float, tp: float) -> np.ndarray:
    """Wave elevation spectrum S(w), m^2 s / rad."""
    if hs <= 0:
        return np.zeros_like(w)
    wp = 2 * math.pi / tp
    return 5 / 16 * hs**2 * wp**4 / w**5 * np.exp(-1.25 * (wp / w) ** 4)


def _rao(w, period_s: float, zeta: float):
    r = w / (2 * math.pi / period_s)
    return 1.0 / np.sqrt((1 - r**2) ** 2 + (2 * zeta * r) ** 2)


def _avg(k, length):
    """Average of a sinusoid of wavenumber k over a hull length (|sinc|)."""
    x = k * length / 2
    return np.abs(np.sinc(x / math.pi))


@dataclass
class Motion:
    t: np.ndarray
    roll: np.ndarray      # rad, includes steady heel
    pitch: np.ndarray     # rad
    yaw: np.ndarray       # rad, deviation from the mean heading
    heave: np.ndarray     # m
    rig_tip: np.ndarray   # rad, mast-tip slope from the first bending mode
    deck_z: float
    truck_z: float

    @property
    def dt(self) -> float:
        return float(self.t[1] - self.t[0])

    def R(self, heading_deg: float = 0.0) -> np.ndarray:
        return frames.attitude(self.roll, self.pitch, frames.heading_to_yaw(heading_deg) + self.yaw)

    def mount(self, pos_body, on_mast: bool = True, heading_deg: float = 0.0):
        """World position (N, 3), velocity, acceleration and body-frame angular
        rate (N, 3) of a point fixed to the hull, or to the mast (on_mast adds
        the bending mode, scaled by the square of height up the mast)."""
        R = self.R(heading_deg)
        r = np.asarray(pos_body, float)
        if on_mast and r[2] > self.deck_z:
            frac = ((r[2] - self.deck_z) / (self.truck_z - self.deck_z)) ** 2
            R = R @ frames.rot_y(self.rig_tip * frac)
        p = R @ r + np.stack([np.zeros_like(self.heave), np.zeros_like(self.heave), self.heave], -1)
        v = np.gradient(p, self.dt, axis=0)
        a = np.gradient(v, self.dt, axis=0)
        return p, v, a, frames.body_rates(R, self.dt)


def simulate(boat, sea, *, sail: str, heel_deg: float, wave_rel_deg: float,
             speed_kn: float, duration_s: float, dt: float = 0.02, seed: int = 0,
             n_waves: int = 120) -> Motion:
    m = boat.motion
    rng = np.random.default_rng(seed)
    t = np.arange(0.0, duration_s, dt)
    hs, tp = sea.hs_m, sea.tp_s
    w = np.linspace(0.25, 6.0, n_waves)
    dw = w[1] - w[0]
    amp = np.sqrt(2 * bretschneider(w, hs, tp) * dw)
    k = w**2 / G
    beta = math.radians(wave_rel_deg)
    we = np.abs(w - k * speed_kn * KN * math.cos(beta))
    we = np.maximum(we, 0.05)
    phase = rng.uniform(0, 2 * math.pi, (3, n_waves))
    zeta_roll = m.roll_damping_motoring if sail == "down" else m.roll_damping_sailing

    def series(a, ph):
        return (a[None, :] * np.cos(we[None, :] * t[:, None] + ph[None, :])).sum(1)

    slope = amp * k * m.wave_slope_factor
    roll = series(slope * abs(math.sin(beta)) * _avg(k, boat.boat.beam_m)
                  * _rao(we, m.roll_period_s, zeta_roll), phase[0])
    pitch = series(slope * abs(math.cos(beta)) * _avg(k, boat.boat.lwl_m)
                   * _rao(we, m.pitch_period_s, m.pitch_damping), phase[1])
    heave = series(amp * _avg(k, boat.boat.lwl_m) * _rao(we, m.heave_period_s, m.heave_damping), phase[2])
    yaw = math.radians(m.yaw_wander_deg) * np.sin(2 * math.pi * t / m.yaw_wander_period_s + rng.uniform(0, 6.28))
    tip = (math.radians(m.rig_mode_tip_deg) * min(hs, 2.0) / 2.0
           * np.sin(2 * math.pi * m.rig_mode_hz * t + rng.uniform(0, 6.28)))
    return Motion(t, roll + math.radians(heel_deg), pitch, yaw, heave, tip,
                  boat.mast.deck_z_m, boat.mast.truck_z_m)


def from_scenario(p, duration_s: float | None = None, dt: float = 0.02) -> Motion:
    s = p.scenario
    return simulate(p, p.sea, sail=s.sail, heel_deg=s.heel_deg, wave_rel_deg=s.wave_rel_deg,
                    speed_kn=s.boat_speed_kn, duration_s=duration_s or s.duration_s, dt=dt, seed=s.seed)


def stats(x: np.ndarray) -> dict:
    x = np.abs(x)
    return {"rms": float(np.sqrt(np.mean(x**2))), "p95": float(np.percentile(x, 95)), "max": float(x.max())}
