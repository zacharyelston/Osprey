"""The Trident in MuJoCo, afloat (trident_sim.py)."""

import math

import numpy as np
import pytest

from osprey import trident
from osprey import trident_sim as ts
from osprey.beet import revolve
from osprey.recon import water
from osprey.recon.puffin import rot_y, rot_z


@pytest.fixture(scope="module")
def found():
    return trident.size("found")


def test_the_clipper_agrees_with_the_waterline_code_and_finds_the_centroid(found):
    ms = [m for _, m in trident.meshes(found["params"])]
    cg = np.array([0.0, 0.0, found["zg_m"]])
    for phi in (0.0, 0.9, 2.6):
        posed = [((v - cg) @ (rot_y(phi) @ rot_z(-0.4)).T, f) for v, f in ms]
        T = ts.soup(posed)
        for h in (-0.8, 0.3):
            V0, x0, _ = water._below(posed, h)
            V1, cb = ts.wetted(T, np.full(T.shape[:2], h))
            assert V1 == pytest.approx(V0, rel=1e-9) and cb[0] == pytest.approx(x0, abs=1e-9)
    can = revolve([(0.0, 0.0), (0.5, 0.0), (0.5, 2.0), (0.0, 2.0)], 64)   # a can, half under
    T = ts.soup([can])
    V, cb = ts.wetted(T, np.full(T.shape[:2], 1.0))
    assert V == pytest.approx(math.pi * 0.25, rel=0.01) and cb == pytest.approx([0.0, 0.0, 0.5], abs=1e-6)


def test_at_rest_upright_it_stays_put(found):
    a = ts.Afloat(found)
    a.place(0.0)
    z0 = a.data.xipos[1, 2]
    for _ in range(1000):
        a.step()
    assert a.tilt_deg() < 0.5 and abs(a.data.xipos[1, 2] - z0) < 0.02


def test_undamped_it_rocks_at_the_period_its_gm_and_inertia_give(found):
    sim = dict(ts.inputs(), roll_damping=0.0, heave_damping=0.0)
    a = ts.Afloat(found, sim)
    a.place(math.radians(3.0))
    lean, t = [], []
    for _ in range(int(4 * a.roll_period_s / sim["dt_s"])):
        a.step()
        R, _ = a.pose()
        lean.append(R[0, 2])
        t.append(a.data.time)
    s = np.sign(lean)
    ups = [t[k] for k in range(1, len(s)) if s[k - 1] < 0 <= s[k]]
    assert np.mean(np.diff(ups)) == pytest.approx(a.roll_period_s, rel=0.1)


def test_let_go_the_found_layout_comes_back_and_the_balanced_one_stays_down():
    assert ts.drop("found", 120.0, 0.0, 15.0)["rights"]
    held = ts.drop("balanced", 90.0, 30.0, 15.0)
    assert not held["rights"] and 60 < held["end_tilt_deg"] < 120


def test_a_steep_wave_rocks_it_more_than_a_swell():
    swell = ts.ride("found", 1.0, 0.05, 0.0, 25.0)
    steep = ts.ride("found", 1.0, 0.10, 0.0, 25.0)
    assert 0 < swell["tilt_max_deg"] < steep["tilt_max_deg"]
    assert steep["props_min_m"] < swell["props_min_m"]
