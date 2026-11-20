"""The sailplane: its body, the centre wing's frame in a pull-up, the lugs and the cut list (recon/sailplane.py)."""

import math
import re
import shutil
import subprocess

import numpy as np
import pytest

from osprey.recon import sailplane as sp


@pytest.fixture(scope="module")
def s():
    return sp.inputs()


@pytest.fixture(scope="module")
def res():
    return sp.run()


def test_the_body_is_smooth_and_its_cubic_closes_at_the_full_length(s):
    f = s.fuselage
    assert sp.myring_r(f, 0.0) == 0.0
    assert np.all(sp.myring_r(f, [f.nose_mm, f.nose_mm + f.mid_mm]) == f.radius_mm)
    x = np.arange(1.0, f.truncate_mm, 1.0)
    assert np.abs(np.diff(sp.myring_r(f, x))).max() < 8.0                      # no step anywhere but the blunt nose tip
    assert sp.myring_r(f, f.length_mm, clamp=False) == pytest.approx(0.0, abs=1e-6)
    slope = (sp.myring_r(f, f.length_mm, clamp=False) - sp.myring_r(f, f.length_mm - 0.01, clamp=False)) / 0.01
    assert math.degrees(math.atan(-slope)) == pytest.approx(f.tail_angle_deg, abs=0.05)
    assert sp.myring_r(f, f.truncate_mm) == f.spinner_r_mm                     # held at the spinner's radius


def test_the_section_is_the_sd7037(s):
    _, up, lo = sp.airfoil(s.wing.airfoil)
    xc = np.linspace(0, 1, 501)
    t = np.interp(xc, up[:, 0], up[:, 1]) - np.interp(xc, lo[:, 0], lo[:, 1])
    assert t.max() == pytest.approx(0.092, abs=0.001)


def test_the_frame_is_the_package_s(s):
    nodes, members = sp.truss(s)
    count = {}
    for m in members:
        count[m["group"]] = count.get(m["group"], 0) + 1
    assert count["post"] == 10 and count["cross brace"] == 10 and count["face diagonal"] == 8
    assert count["planform diagonal"] == 8 and count["pylon"] == 4
    assert count["station diagonal"] == 3                                     # the tips' two give way to the joiner boxes
    assert {m["chord"] for m in members if m["group"] == "chord"} == {"FB", "FT", "RB", "RT"}


def test_the_pull_up_balances_and_is_the_same_either_side(s, res):
    for case in sp.CASES:
        p = res["pull_up"][case]
        w = s.wing
        wing_kg = w.center_kg + 2 * (w.panel_day_kg if case == "day" else w.panel_night_kg)
        assert p["applied_z_n"] == pytest.approx(p["lift_n"] - s.loads.n * sp.G * wing_kg, rel=1e-3)
        assert -sum(r[2] for r in p["reactions_n"].values()) == pytest.approx(p["applied_z_n"], rel=1e-6)
        by = {m["name"]: m["axial_n"] for m in p["members"]}
        for p_ in "FR":
            for lv in "BT":
                assert by[f"{p_}{lv}+0>{p_}{lv}+400"] == pytest.approx(by[f"{p_}{lv}-400>{p_}{lv}+0"], rel=1e-6) \
                    if lv == "T" else True


def test_the_frame_carries_the_bending_the_loads_make(s, res):
    """Cut the frame at y = 200: the members' axial loads there balance the bending of everything outboard."""
    p = res["pull_up"]["day"]
    nodes = {k: np.array(v) for k, v in res["nodes"].items()}
    F, _ = sp.loads(s, "day")
    yc = 200.0
    zc = (s.truss.z_bot_mm + s.truss.z_top_mm) / 2
    outboard = sum(v[2] * (nodes[k][1] - yc) for k, v in F.items() if nodes[k][1] > yc)
    inside = 0.0
    for m in p["members"]:
        a, b = nodes[m["a"]], nodes[m["b"]]
        if min(a[1], b[1]) < yc < max(a[1], b[1]):
            d = (b - a) / np.linalg.norm(b - a) * (1 if b[1] > a[1] else -1)
            z = a[2] + (b[2] - a[2]) * (yc - a[1]) / (b[1] - a[1])
            inside += -m["axial_n"] * d[1] * (z - zc)
    assert inside == pytest.approx(outboard, rel=0.05)                         # the rest is the tubes' own bending


def test_the_top_chords_buckle_and_the_frame_is_deeper_than_the_wing(res):
    bad = sp.failed(res)
    assert "frame inside the wing section" in bad
    assert any(n.startswith("chords at") for n in bad)
    g = res["pull_up"][res["pull_up"]["governing"]]
    worst = max((m for m in g["members"] if m["group"] == "chord"), key=lambda m: m["u_buckle"])
    assert worst["name"][1] == "T" and worst["axial_n"] < 0                    # a top chord, in compression


def test_every_socket_clears_its_neighbours_and_a_shallow_diagonal_sits_far_out(s, res):
    lg = s.lug
    assert len(res["lugs"]) == 24
    for arms in res["lugs"].values():
        assert sum(a["kind"] > 0 for a in arms) == 1                           # one chord through each
        for a in arms:
            if a["kind"]:
                continue
            P = sp._bore_points(np.array(a["dir"]), a["od"] / 2 + lg.bond_gap_mm, a["seat"], a["seat"] + lg.socket_mm)
            chord = arms[0]
            t0 = -400.0 if chord["kind"] == 1 else -chord["seat"]
            assert sp._to_segment(P, np.array(chord["dir"]), t0, 400.0).min() >= chord["od"] / 2 + lg.bond_gap_mm + lg.web_mm - 1e-6
    seats = {c["group"]: c["seats_mm"] for c in res["cuts"] if "seats_mm" in c}
    assert seats["post"] == [6.5, 6.5]
    assert min(seats["face diagonal"]) > 60.0                                  # 6.6 degrees off its chord


def test_the_cut_list_has_every_tube(s, res):
    nodes, members = sp.truss(s)
    cuts = res["cuts"]
    assert len(cuts) == 4 + sum(m["group"] != "chord" for m in members)
    assert all(c["cut_mm"] > c["in_sockets_mm"] for c in cuts)
    tubes = [r for r in res["bom"] if r["mass_g"] is not None]
    assert sum(r["qty"] for r in tubes) == len(cuts)
    assert sum(r["qty"] * r["cut_mm"] for r in tubes) == pytest.approx(sum(c["cut_mm"] for c in cuts), abs=len(cuts) * 0.05)
    assert sum(r["item"].startswith("ring bulkhead") for r in res["bom"]) == len(s.bulkhead)


def test_the_belly_flat_takes_the_pane_and_ends_ahead_of_the_tail_cone(s, res):
    nf, nd = res["nadir"], s.nadir
    r = float(sp.myring_r(s.fuselage, nf["xa_mm"]))
    assert math.sqrt(r**2 - nf["za_mm"] ** 2) == pytest.approx(nf["pane_mm"] / 2 + nd.margin_mm)
    assert nf["from_mm"] < nd.x_mm[0] and nd.x_mm[1] < nf["to_mm"] < nd.recovery_from_mm
    assert 0 < nf["tilt_deg"] < 15


def test_params_scad_is_whole_and_used(s, res):
    text = sp.params_scad(s, res)
    names = re.findall(r"^(\w+) = .*;$", text, flags=re.M)
    assert len(names) == len([ln for ln in text.splitlines() if ln and not ln.startswith("//")])
    assert text.count("[") == text.count("]")
    scad = "".join(f.read_text() for f in sp.SCAD.glob("*.scad"))
    assert [n for n in names if not re.search(rf"\b{n}\b", scad)] == []


@pytest.mark.skipif(not shutil.which("openscad"), reason="OpenSCAD is not installed")
@pytest.mark.parametrize("part", ["lugs", "joiner_box", "nadir_belly"])
def test_the_parts_build_in_openscad(res, tmp_path, part):
    sp.export(res, tmp_path)
    out = tmp_path / f"{part}.stl"
    extra = ["-D", "lug_index=0"] if part == "lugs" else []
    subprocess.run(["openscad", *extra, "-o", str(out), str(tmp_path / "scad" / f"{part}.scad")], check=True,
                   capture_output=True, timeout=600)
    assert out.stat().st_size > 1000
