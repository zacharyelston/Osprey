"""The sailplane: its body, its truss-braced wing under load, the drag build-up and the parts (recon/sailplane.py)."""

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


def test_the_section_is_the_sd7037_and_the_spar_fits_in_it(s, res):
    _, up, lo = sp.airfoil(s.wing.airfoil)
    xc = np.linspace(0, 1, 501)
    t = np.interp(xc, up[:, 0], up[:, 1]) - np.interp(xc, lo[:, 0], lo[:, 1])
    assert t.max() == pytest.approx(0.092, abs=0.001)
    assert next(c for c in res["checks"] if c["name"] == "spar inside the wing section")["ok"]


def test_the_brace_runs_from_low_on_the_body_to_mid_span(s):
    sp_ = sp.strut_points(s)
    assert sp_["y"] == pytest.approx(s.strut.y_frac * s.wing.span_mm / 2)
    assert sp_["root"][2] < -s.fuselage.radius_mm / 2 and sp_["wing"][2] > s.fuselage.radius_mm
    r = float(sp.myring_r(s.fuselage, s.strut.root_x_mm))
    assert math.hypot(sp_["root"][1], sp_["root"][2]) == pytest.approx(r + s.strut.root_out_mm, abs=3.0)
    assert sp_["root"][1] < sp_["jury"][1] < sp_["wing"][1]
    nodes, members, fixed = sp.model(s)
    assert sum(m["group"] == "brace" for m in members) == 4 and sum(m["group"] == "jury strut" for m in members) == 2
    assert set(fixed) == {"W+110", "W-110", "R+", "R-"}


def test_every_case_balances_and_is_the_same_either_side(s, res):
    w = s.wing
    for c in res["analysis"]["cases"].values():
        wing_kg = w.center_kg + 2 * (w.panel_day_kg if c["wings"] == "day" else w.panel_night_kg)
        assert c["applied_z_n"] == pytest.approx(c["lift_n"] - c["n"] * sp.G * wing_kg, rel=2e-3)
        assert -sum(r[2] for r in c["reactions_n"].values()) == pytest.approx(c["applied_z_n"], rel=1e-6)
        by = {m["name"]: m for m in c["members"]}
        assert by["R+>M+"]["axial_n"] == pytest.approx(by["R->M-"]["axial_n"], rel=1e-6)
        assert c["reactions_n"]["R+"][2] == pytest.approx(c["reactions_n"]["R-"][2], rel=1e-6)


def test_with_no_braces_the_root_bending_is_the_cantilever_s(s, res):
    """Elliptic lift's centre is 4/(3 pi) of the half-span out; the wing's own weight comes off."""
    c = res["unbraced"]["cases"][sp.cases(s)[0][0]]
    w, h = s.wing, s.wing.span_mm / 2e3
    jy = w.center_span_mm / 2e3
    cr, ct = w.chord_mm, w.tip_chord_mm
    lift = c["lift_n"] / 2 * 4 / (3 * math.pi) * h
    weight = c["n"] * sp.G * (w.center_kg / 2 * jy / 2 + w.panel_day_kg * (jy + (h - jy) / 2))
    saddle = s.spar.saddle_y_mm / 1e3                                          # the wing is held at +/-110, not on the centre line
    cantilever = lift - weight - c["applied_z_n"] / 2 * saddle
    assert c["root_moment_nm"] == pytest.approx(cantilever, rel=0.06)
    assert cr > ct


def test_the_braces_take_the_bending_off_the_spar(s, res):
    pull, push = (res["analysis"]["cases"][sp.cases(s)[i][0]] for i in (0, 2))
    bare = res["unbraced"]["cases"][sp.cases(s)[0][0]]
    assert pull["spar_moment_nm"] < 0.3 * bare["spar_moment_nm"]
    assert abs(pull["tip_rise_mm"]) < 0.2 * abs(bare["tip_rise_mm"])
    assert pull["brace_axial_n"] > 0 and pull["spar_axial_n"] < 0              # the brace pulls, the spar is squeezed
    assert push["brace_axial_n"] < 0                                           # and pushed in the push-over
    sw = {r["strut_y_mm"]: r for r in res["sweep"]}
    assert sw[None]["brace_tension_n"] == 0
    ys = sorted(y for y in sw if y is not None)
    assert all(sw[a]["tip_rise_mm"] > sw[b]["tip_rise_mm"] for a, b in zip(ys[:-1], ys[1:]))
    assert all(sw[a]["brace_used"] < sw[b]["brace_used"] for a, b in zip(ys[:-1], ys[1:]))   # a longer brace buckles sooner


def test_the_drag_build_up_adds_up_and_the_braces_cost_some_glide(s, res):
    ae = res["aero"]
    assert sp._cf(1e6, 1.0) == pytest.approx(1.328e-3)                         # all laminar: Blasius
    assert sp._cf(1e6, 1e-9) == pytest.approx(0.072 * 1e6**-0.2, rel=1e-3)     # all turbulent
    assert sp._cf(1e6, 1.0) < sp._cf(1e6, 0.5) < sp._cf(1e6, 1e-9)
    for r in ae["rows"]:
        total = sum(r["cd0"].values()) + r["cdi"]
        assert r["braced"]["cd"] == pytest.approx(total)
        assert r["braced"]["l_over_d"] == pytest.approx(r["cl"] / total)
        assert r["unbraced"]["l_over_d"] > r["braced"]["l_over_d"]
        assert 0.03 < r["cd0"]["braces"] / total < 0.15                        # the paper has them at 8 % of the drag
    assert ae["area_m2"] == pytest.approx(1.6, abs=0.01) and ae["ar"] == pytest.approx(14.4, abs=0.1)


def test_the_cut_list_has_every_tube(s, res):
    tubes = {r["item"]: r for r in res["bom"] if r["mass_g"] is not None}
    assert set(tubes) == {"centre spar", "rear spar", "brace tube", "jury strut", "wing joiner"}
    sp_ = sp.strut_points(s)
    assert tubes["brace tube"]["cut_mm"] == pytest.approx(np.linalg.norm(sp_["wing"] - sp_["root"]) - 2 * s.strut.seat_mm)
    assert tubes["brace tube"]["qty"] == 2 and tubes["jury strut"]["cut_mm"] > 2 * s.fitting.socket_mm
    assert sum(r["item"].startswith("ring bulkhead") for r in res["bom"]) == len(s.bulkhead)


def test_the_belly_flat_takes_the_pane_and_ends_ahead_of_the_tail_cone(s, res):
    nf, nd = res["nadir"], s.nadir
    r = float(sp.myring_r(s.fuselage, nf["xa_mm"]))
    assert math.sqrt(r**2 - nf["za_mm"] ** 2) == pytest.approx(nf["pane_mm"] / 2 + nd.margin_mm)
    assert nf["from_mm"] < nd.x_mm[0] and nd.x_mm[1] < nf["to_mm"] < nd.recovery_from_mm
    assert 0 < nf["tilt_deg"] < 15


def test_only_the_package_s_own_numbers_fail(res):
    assert sp.failed(res) == ["tail cone meets the spinner at the firewall", "battery holds what it weighs"]


def test_params_scad_is_whole_and_used(s, res):
    text = sp.params_scad(s, res)
    names = re.findall(r"^(\w+) = .*;$", text, flags=re.M)
    assert len(names) == len([ln for ln in text.splitlines() if ln and not ln.startswith("//")])
    assert text.count("[") == text.count("]")
    scad = "".join(f.read_text() for f in sp.SCAD.glob("*.scad"))
    assert [n for n in names if not re.search(rf"\b{n}\b", scad)] == []


@pytest.mark.skipif(not shutil.which("openscad"), reason="OpenSCAD is not installed")
@pytest.mark.parametrize("part", ["tube_end", "wing_fork", "root_fork", "jury_collar", "end_rib", "nadir_belly"])
def test_the_parts_build_in_openscad(res, tmp_path, part):
    sp.export(res, tmp_path)
    out = tmp_path / f"{part}.stl"
    file, extra = (part, []) if part in ("end_rib", "nadir_belly") else ("brace_fittings", ["-D", f'part="{part}"'])
    done = subprocess.run(["openscad", *extra, "-o", str(out), str(tmp_path / "scad" / f"{file}.scad")],
                          capture_output=True, text=True, timeout=600)
    assert done.returncode == 0 and "WARNING" not in done.stderr and out.stat().st_size > 1000
