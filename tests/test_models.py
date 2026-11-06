"""Conventions and physics of the screening models: frames, optics, motion,
stabilization, occlusion and the design files."""
import math
from types import SimpleNamespace

import mujoco
import numpy as np
import pytest

from osprey import frames, motion, occlusion, optics, stabilize
from osprey.params import RIGS, SCENARIOS, load, load_rig
from osprey.render import scene
from osprey.rig import stations


def test_attitude_conventions():
    R = frames.attitude(math.radians(10), 0, 0)
    assert (R @ [0, 1, 0])[2] > 0                    # roll + lifts port: starboard down
    R = frames.attitude(0, math.radians(5), 0)
    assert (R @ [1, 0, 0])[2] < 0                    # pitch + is bow down
    R = frames.attitude(0, 0, frames.heading_to_yaw(0))
    assert np.allclose(R @ [1, 0, 0], [0, 1, 0])     # heading 0: bow points north


def test_look_frame_and_quaternion():
    for d in ([1, 0, 0], [0.3, -0.5, -0.8], [0, 0, -1]):
        F = frames.look_frame(d)
        assert np.allclose(F.T @ F, np.eye(3))
        assert np.allclose(-F[:, 2], np.asarray(d) / np.linalg.norm(d))
        q = frames.quat_from_matrix(F)
        M = np.zeros(9)
        mujoco.mju_quat2Mat(M, q)
        assert np.allclose(M.reshape(3, 3), F, atol=1e-9)
    assert frames.look_frame([1, 0, 0])[2, 1] > 0     # image up is world up for a level camera


def test_horizon_and_dip_ranging():
    assert optics.horizon_m(18.9) == pytest.approx(16_640, rel=0.01)
    assert optics.horizon_m(2.5) == pytest.approx(6_050, rel=0.01)
    for d in (300.0, 2000.0, 9000.0):
        delta = float(optics.dip(d, 18.9)) - optics.horizon_dip(18.9)
        assert optics.dip_range(delta, 18.9) == pytest.approx(d, rel=1e-6)
    near, _ = optics.dip_ranging(1000, 18.9, 1e-5, hs=0.9)
    far, _ = optics.dip_ranging(5000, 18.9, 1e-5, hs=0.9)
    assert near < far


def test_height_beats_waves():
    deck = optics.wave_exposure(2.5, 1000, 0.2, 0.9, 5.0, n=150)
    mast = optics.wave_exposure(18.9, 1000, 0.2, 0.9, 5.0, n=150)
    assert mast > deck + 0.2
    assert optics.wave_exposure(2.5, 1000, 0.2, 0.0, 5.0) == 1.0


def test_motion_is_rigid_and_calm_is_calm():
    p = load("coastal-watch")
    m = motion.from_scenario(p, duration_s=60)
    _, _, _, w_low = m.mount([0, 0, 3.0], on_mast=False)
    _, _, a_top, w_top = m.mount([0, 0, 18.9], on_mast=False)
    _, _, a_low, _ = m.mount([0, 0, 3.0], on_mast=False)
    assert np.allclose(w_low, w_top)                 # one rigid body: one angular rate
    assert np.percentile(np.linalg.norm(a_top, axis=1), 95) > np.percentile(np.linalg.norm(a_low, axis=1), 95)
    glassy = SimpleNamespace(hs_m=0.0, tp_s=4.0)
    calm = motion.simulate(p, glassy, sail="down", heel_deg=0, wave_rel_deg=90, speed_kn=0, duration_s=20)
    assert np.abs(calm.roll).max() < 1e-9 and np.abs(calm.heave).max() < 1e-9


def test_stabilization_rejects_slow_motion():
    p = load("coastal-watch")
    m = motion.from_scenario(p, duration_s=120)
    _, _, _, w = m.mount([0, 0, 18.9])
    none = stabilize.residual(w, m.dt, SimpleNamespace(outer_hz=0, inner_hz=0, inner_stroke_deg=0, floor_urad=0))
    assert np.allclose(none.rate, w)
    top = stabilize.residual(w, m.dt, p.camera.ptz_long.stabilization)
    d = np.array([1.0, 0, 0])
    assert stabilize.jitter_rad(top, d) < 0.05 * stabilize.jitter_rad(none, d)


def test_occlusion():
    p = load("coastal-watch")
    up = occlusion.build(p)                           # main+jib, heeled to starboard
    down = occlusion.build(p, sail="down")
    cam = np.array([0.0, 0.3, 11.0])                  # port side of the mast
    through_mast = np.array([[0.0, -50.0, 11.0]])
    lee = np.array([[200.0, -400.0, 2.0]])            # starboard bow, beyond the sails
    assert up.blocked(cam, through_mast)[0]
    assert up.blocked(cam, lee)[0] and not down.blocked(cam, lee)[0]
    assert not up.blocked(np.array([0.5, 0, 18.9]), lee)[0]   # the masthead sees over the sails
    assert up.in_hull(np.array([0.0, 0.0, 0.5])) and not up.in_hull(np.array([0.0, 3.0, 0.5]))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenarios_load_with_every_rig(scenario):
    for rig in RIGS:
        p = load(scenario, rig=rig)
        assert len(stations(p)) >= 5


def test_whole_boat_extends_mast5():
    mast5 = {s["id"] for s in load_rig("mast5")["station"]}
    whole = {s["id"] for s in load_rig("whole-boat")["station"]}
    assert mast5 < whole
    zones = {z for s in load_rig("whole-boat")["station"] for z in s["zones"]}
    assert {"exterior", "deck", "interior"} <= zones


def test_scene_compiles():
    p = load("docking")
    sts = [s for s in stations(p) if "exterior" in s.zones]
    m = mujoco.MjModel.from_xml_string(scene.mjcf(p, sts, 640, 360))
    names = [m.geom(i).name.split("__")[0] for i in range(m.ngeom)]
    assert set(names) <= set(scene.CLASSES)
    assert m.ncam == len(sts) + 1
