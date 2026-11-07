"""Gecko pods: a PTZ on top, another hung underneath, electronics between.
Also the fisheye camera class, which pods used before gecko eyes."""
import math

import numpy as np

from osprey import calcs, occlusion
from osprey.params import load
from osprey.render import scene
from osprey.rig import Station, pods, stations


def _fisheye(p, z=12.0):
    return Station("fe", "fisheye_down", p.camera.fisheye_down, np.array([0.0, 1.0, z]), 0.0, True, ("near",))


def test_pods_expand_into_two_cameras_each():
    p = load("docking", rig="gecko5")
    sts = {s.id: s for s in stations(p)}
    assert len(sts) == 10
    for pd in pods(p):
        up, down = sts[pd.id], sts[f"{pd.id}-down"]
        assert up.pos[2] > pd.pos[2] > down.pos[2]
        assert "exterior" in up.zones and "exterior" in down.zones
        assert not up.fixed and not down.fixed
        assert {s.id for s in pd.members} == {up.id, down.id}


def test_fisheye_sees_a_hemisphere_and_more():
    p = load("docking", rig="gecko5")
    fe = _fisheye(p)
    assert fe.can_point(0.0, math.radians(-89)).all()
    assert fe.can_point(np.radians([0, 90, 180]), np.radians([2, 2, 2])).all()   # 190 deg: just above level
    assert not fe.can_point(0.0, math.radians(10)).any()
    pts = np.array([[0, 30, 0.0], [0, 0, fe.pos[2] + 5]])
    assert calcs.in_fov(fe, fe.pos + fe.boresight, fe.f_min, pts).tolist() == [True, False]


def test_the_pod_splits_the_sphere_between_its_eyes():
    """The pod hides the nadir from the upper eye and the zenith from the lower;
    both see the horizon."""
    p = load("docking", rig="gecko5")
    occ = occlusion.build(p, sail="down")
    sts = {s.id: s for s in stations(p)}
    up, down = sts["port"], sts["port-down"]
    below, above = up.pos - [0, 0, 5.0], up.pos + [0, 0, 5.0]
    assert occ.blocked(up.pos, below[None], hull=False)[0]
    assert not occ.blocked(down.pos, below[None], hull=False)[0]
    assert occ.blocked(down.pos, above[None], hull=False)[0]
    level = up.pos + [0, 50.0, 0]
    assert not occ.blocked(up.pos, level[None], hull=False)[0]
    assert not occ.blocked(down.pos, level[None], hull=False)[0]


def test_fisheye_lut_matches_the_projection():
    p = load("docking", rig="gecko5")
    fe = _fisheye(p)
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
    p = load("coastal-watch", rig="gecko5")
    checks = calcs.run(p)
    groups = {c.group for c in checks}
    assert {"Pod power", "Pod network", "Pod timing"} <= groups
    by = {c.name: c for c in checks}
    flex = next(c for n, c in by.items() if n.startswith("Mast flex"))
    gyro = by["Relative orientation with pod gyros between horizon fixes"]
    assert float(flex.value.split()[0]) > float(gyro.value.split()[0])
    poe = [c for c in checks if c.name.endswith("peak draw at the PoE port")]
    assert len(poe) == len(pods(p))
    for c in poe:                                    # PASS exactly when one PoE class can feed the pod
        assert (c.status == "PASS") == (float(c.value.split()[0]) <= 71.3)


def test_rigs_without_pods_skip_the_pod_checks():
    checks = calcs.run(load("docking", rig="mast5"))
    assert not {c.group for c in checks} & {"Pod power", "Pod network", "Pod timing"}


def test_dual_mounts_face_fore_and_aft_with_a_port_each():
    p = load("docking", rig="spreader-pairs")
    sts = {s.id: s for s in stations(p)}
    for pd in pods(p):
        if not pd.horizontal:
            continue
        fwd, aft = sts[f"{pd.id}-fwd"], sts[f"{pd.id}-aft"]
        assert fwd.pos[0] > pd.pos[0] > aft.pos[0]
        assert math.degrees(fwd.face_az) == 0 and abs(math.degrees(aft.face_az)) == 180
        assert not pd.has_computer and len(pd.ports()) == 2


def test_same_height_pairs_cancel_mast_flex():
    p = load("coastal-watch", rig="spreader-pairs")
    checks = {c.name: c for c in calcs.run(p)}
    flex = [c for n, c in checks.items() if "baseline and mast flex" in n]
    assert flex and all(c.value.endswith(", 0 urad") for c in flex)
    near = [c for n, c in checks.items() if "stereo range at 30 m" in n]
    assert near and all(c.status == "PASS" for c in near)
