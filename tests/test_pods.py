"""Two-sided pods: a PTZ on top, a fisheye underneath, electronics between."""
import math

import numpy as np

from osprey import calcs, occlusion
from osprey.params import load
from osprey.render import scene
from osprey.rig import pods, stations


def test_pods_expand_into_two_cameras_each():
    p = load("docking", rig="pods5")
    sts = {s.id: s for s in stations(p)}
    assert len(sts) == 10
    for pd in pods(p):
        up, down = sts[pd.id], sts[f"{pd.id}-down"]
        assert up.pos[2] > pd.pos[2] > down.pos[2]
        assert "exterior" in up.zones and down.zones == ("near", "deck")
        assert down.fisheye and not up.fisheye
        assert {s.id for s in pd.members} == {up.id, down.id}


def test_fisheye_sees_a_hemisphere_and_more():
    p = load("docking", rig="pods5")
    fe = next(s for s in stations(p) if s.fisheye)
    assert fe.can_point(0.0, math.radians(-89)).all()
    assert fe.can_point(np.radians([0, 90, 180]), np.radians([2, 2, 2])).all()   # 190 deg: just above level
    assert not fe.can_point(0.0, math.radians(10)).any()
    pts = np.array([[0, 30, 0.0], [0, 0, fe.pos[2] + 5]])
    assert calcs.in_fov(fe, fe.pos + fe.boresight, fe.f_min, pts).tolist() == [True, False]


def test_housing_hides_the_nadir_from_the_ptz_not_the_fisheye():
    p = load("docking", rig="pods5")
    occ = occlusion.build(p, sail="down")
    sts = {s.id: s for s in stations(p)}
    below = sts["port"].pos - [0, 0, 5.0]
    assert occ.blocked(sts["port"].pos, below[None], hull=False)[0]
    assert not occ.blocked(sts["port-down"].pos, below[None], hull=False)[0]
    level = sts["port"].pos + [0, 50.0, 0]
    assert not occ.blocked(sts["port"].pos, level[None], hull=False)[0]


def test_fisheye_lut_matches_the_projection():
    p = load("docking", rig="pods5")
    fe = next(s for s in stations(p) if s.fisheye)
    size, face_px = 400, 240
    lut = scene._fisheye_lut(fe, size, face_px)
    assert lut["face"][size // 2, size // 2] == 0                    # the centre looks down the boresight
    assert not lut["inside"][0, 0] and lut["inside"][size // 2, 5]   # corners are void, the rim is in
    rng = np.random.default_rng(0)
    for v, u in rng.integers(0, size, (200, 2)):
        if not lut["inside"][v, u]:
            continue
        x, y = u + 0.5 - size / 2, -(v + 0.5 - size / 2)
        th = math.hypot(x, y) / lut["f_px"]
        want = np.array([math.sin(th) * x, math.sin(th) * y, 0]) / max(math.hypot(x, y), 1e-9)
        want[2] = -math.cos(th)
        F = scene._face_frame(*scene.FACES[lut["face"][v, u]])
        c, r = lut["col"][v, u] + 0.5, lut["row"][v, u] + 0.5
        got = F @ np.array([2 * c / face_px - 1, 1 - 2 * r / face_px, -1.0])
        assert np.degrees(np.arccos(got @ want / np.linalg.norm(got))) < 2 * 90 / face_px


def test_pod_checks_report_power_network_and_flex():
    p = load("coastal-watch", rig="pods5")
    checks = calcs.run(p)
    groups = {c.group for c in checks}
    assert {"Pod power", "Pod network", "Pod timing"} <= groups
    by = {c.name: c for c in checks}
    flex = next(c for n, c in by.items() if n.startswith("Mast flex"))
    gyro = by["Relative orientation with pod gyros between horizon fixes"]
    assert float(flex.value.split()[0]) > float(gyro.value.split()[0])
    assert all(c.status == "PASS" for c in checks if c.name.endswith("peak draw at the PoE port"))


def test_rigs_without_pods_skip_the_pod_checks():
    checks = calcs.run(load("docking", rig="mast5"))
    assert not {c.group for c in checks} & {"Pod power", "Pod network", "Pod timing"}
