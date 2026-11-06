"""Frames and rotations.

Body frame: x forward, y port, z up, origin on the waterline under the mast.
World frame: ENU (x east, y north, z up). Attitude R maps body to world:
R = Rz(yaw) Ry(pitch) Rx(roll), where roll + is starboard down, pitch + is
bow down and yaw is the ENU angle CCW from east (heading 0 = north = 90 deg).
Every function takes scalars or arrays of angles; arrays give (N, 3, 3).
"""

from __future__ import annotations

import math

import numpy as np


def _rot(axis: int, a) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    c, s = np.cos(a), np.sin(a)
    R = np.zeros(a.shape + (3, 3))
    i, j = [(1, 2), (2, 0), (0, 1)][axis]
    R[..., axis, axis] = 1.0
    R[..., i, i] = c
    R[..., j, j] = c
    R[..., i, j] = -s
    R[..., j, i] = s
    return R


def rot_x(a):
    return _rot(0, a)


def rot_y(a):
    return _rot(1, a)


def rot_z(a):
    return _rot(2, a)


def heading_to_yaw(heading_deg: float) -> float:
    """Nautical heading (clockwise from north) to the ENU yaw angle, radians."""
    return math.radians(90.0 - heading_deg)


def attitude(roll, pitch, yaw) -> np.ndarray:
    return rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)


def body_rates(R: np.ndarray, dt: float) -> np.ndarray:
    """Body-frame angular velocity (N, 3) from an attitude history (N, 3, 3)."""
    dR = np.swapaxes(R[:-1], -1, -2) @ R[1:]
    w = 0.5 * np.stack([dR[:, 2, 1] - dR[:, 1, 2],
                        dR[:, 0, 2] - dR[:, 2, 0],
                        dR[:, 1, 0] - dR[:, 0, 1]], axis=-1) / dt
    return np.vstack([w, w[-1:]])


def direction(az, el) -> np.ndarray:
    """Unit vector at azimuth az (CCW from +x) and elevation el, radians."""
    az, el = np.asarray(az, float), np.asarray(el, float)
    return np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], axis=-1)


def az_el(v) -> tuple[np.ndarray, np.ndarray]:
    v = np.asarray(v, float)
    return np.arctan2(v[..., 1], v[..., 0]), np.arctan2(v[..., 2], np.hypot(v[..., 0], v[..., 1]))


def bearing_to_az(bearing_deg) -> np.ndarray:
    """Nautical relative bearing (clockwise from the bow) to body azimuth (CCW), radians."""
    return np.radians(-np.asarray(bearing_deg, float))


def look_frame(d) -> np.ndarray:
    """Camera-to-world rotation for a camera looking along unit d with the
    horizon level: columns are image right, image up, and -d (MuJoCo's camera
    convention). Straight down is fine: right is then taken from d's azimuth."""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    az = math.atan2(d[1], d[0]) if np.hypot(d[0], d[1]) > 1e-9 else 0.0
    right = np.array([math.sin(az), -math.cos(az), 0.0])
    up = np.cross(right, d)
    return np.column_stack([right, up, -d])


def quat_from_matrix(R: np.ndarray) -> np.ndarray:
    """(w, x, y, z), the order MuJoCo uses."""
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    else:
        i = int(np.argmax(np.diag(R)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = math.sqrt(1.0 + R[i, i] - R[j, j] - R[k, k]) * 2
        q = [0.0] * 4
        q[0] = (R[k, j] - R[j, k]) / s
        q[1 + i] = 0.25 * s
        q[1 + j] = (R[j, i] + R[i, j]) / s
        q[1 + k] = (R[k, i] + R[i, k]) / s
    q = np.array(q)
    return q / np.linalg.norm(q)
