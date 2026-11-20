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
    assert sp.failed(res) == ["tail cone meets the spinner at the firewall", "tail volumes", "battery holds what it weighs"]


@pytest.fixture(scope="module")
def twin():
    return sp.run("twin")


def test_the_twin_has_its_props_on_the_wing_and_a_tail_that_is_big_enough(s, twin):
    t = sp.inputs("twin")
    assert "twin" in sp.VARIANTS and t.pods.count == 2 and t.tail.kind == "v" and t.propulsion.layout == "pods"
    assert sp.failed(twin) == ["battery holds what it weighs"]                 # no stinger, and the tail volumes are met
    assert twin["tail"]["vh"] >= t.tail.vh_target and twin["tail"]["vv"] >= t.tail.vv_target
    # A pod's weight on the wing at the brace takes load off the brace in the pull-up, for its lift.
    pull = sp.cases(t)[0][0]
    no_pods = sp.inputs("twin")
    no_pods.pods.count = 0
    assert twin["analysis"]["cases"][pull]["brace_axial_n"] < sp.analyse(no_pods)["cases"][pull]["brace_axial_n"]
    b = twin["balance"]
    assert 0 < b["battery_aft_mm"] < b["travel_mm"]
    assert sp.balance(sp.inputs())["battery_aft_mm"] == 0                      # the pusher against itself
    assert all("pods" in r["cd0"] for r in twin["aero"]["rows"])


def test_front_back_and_both(twin):
    t = sp.inputs("twin")
    rows = {r["layout"]: r for r in twin["pod_sweep"]}
    assert list(rows) == ["front", "back", "both"] and t.pods.layout == "both"
    f, b, pp = rows["front"], rows["back"], rows["both"]
    assert (f["motors"], b["motors"], pp["motors"]) == (2, 2, 4)
    assert pp["length_mm"] > 2 * f["length_mm"] and pp["kg"] > f["kg"] and pp["auw_kg"] > f["auw_kg"]
    assert pp["auw_kg"] == pytest.approx(t.mass.auw_kg)                        # the design file's weight is the push-pull's
    assert pp["motor_w"] < 0.6 * f["motor_w"]                                  # four share what two did
    assert pp["eff"] < b["eff"] < f["eff"]                                     # the installation's losses
    assert f["battery_aft_mm"] > pp["battery_aft_mm"] > b["battery_aft_mm"] > 0   # a back prop's weight is further aft
    assert pp["sink_ms"] > f["sink_ms"]                                        # the long pods' skin, and their weight
    # One motor out: two motors lose half the thrust and the tail cannot hold the yaw; four lose a quarter and it can.
    assert f["out_thrust_frac"] == 0.5 and pp["out_thrust_frac"] == 0.75
    assert pp["out_yaw_nm"] == pytest.approx(f["out_yaw_nm"] / 2, rel=0.08)
    assert not f["tail_ok"] and not b["tail_ok"] and pp["tail_ok"]
    assert pp["out_climb_ms"] > f["out_climb_ms"] > 0
    for r in rows.values():
        c = sp.climb(sp.with_pods(t, r["layout"]))
        assert c["thrust_n"] * t.climb.speed_ms == pytest.approx(c["shaft_w"] * c["eff"])
        assert r["used"] < 1.0 and 0 < r["ideal"] < 1


@pytest.fixture(scope="module")
def boom():
    return sp.run("boom")


def test_the_boom_carries_its_tail_on_the_pods_and_its_pusher_between_them(boom):
    b = sp.inputs("boom")
    tl, bm = boom["tail"], boom["booms"]
    assert "boom" in sp.VARIANTS and sp.has_pusher(b) and b.pods.count == 2 and tl["kind"] == "boom"
    y = sp.strut_points(b)["y"]
    assert y == pytest.approx(b.wing.center_span_mm / 2) and bm["y_mm"] == y   # braces, pods and booms at the panels' joint
    assert tl["span_mm"] == pytest.approx(2 * y)
    assert tl["vh"] == pytest.approx(b.tail.vh_target, rel=1e-3) and tl["vv"] == pytest.approx(b.tail.vv_target, rel=1e-3)
    assert tl["chord_mm"] >= b.tail.h_chord_min_mm
    assert tl["le_x_mm"] >= b.fuselage.truncate_mm + b.tail.prop_clear_mm      # the tailplane is behind the pusher's disc
    assert y - b.propulsion.center_prop_in * 25.4 / 2 > b.boom.od_mm           # and the disc is between the booms
    assert bm["to_x_mm"] == pytest.approx(tl["le_x_mm"] + tl["chord_mm"]) and bm["used"] < 1
    q = 0.5 * b.flight.rho_kgm3 * (b.flight.stall_clean_ms * 2) ** 2
    assert bm["sigma_mpa"] == pytest.approx(q * tl["sh_m2"] / 2 * bm["lever_mm"] * 12.5 / sp.section(b.boom)[1], rel=1e-6)
    c = sp.climb(b)
    assert c["motors"] == 3 and len(c["tubes"]) == 3 and c["tubes"][-1]["prop_in"] == b.propulsion.center_prop_in
    assert sum(t_["motor_w"] * t_["motors"] for t_ in c["tubes"]) == pytest.approx(c["shaft_w"])
    assert c["out_thrust_frac"] == pytest.approx(2 / 3) and c["out_tail_cl"] < b.climb.tail_cl_max
    assert boom["length_sweep"] == []                                          # its tail is not on the body
    assert "tail cone meets the spinner at the firewall" not in sp.failed(boom)   # cut where the cubic meets it
    assert abs(boom["balance"]["battery_aft_mm"]) < boom["balance"]["travel_mm"]
    assert {i[0] for i in boom["balance"]["items"]} == {"tail", "pods", "pusher", "booms"}
    assert boom["balance"]["delta_kg"] == pytest.approx(b.mass.auw_kg - sp.inputs().mass.auw_kg, abs=0.15)
    assert all("booms" in r["cd0"] for r in boom["aero"]["rows"])


def test_how_long_the_body_can_be(s, res, twin):
    f = s.fuselage
    assert res["max_length_m"] == pytest.approx((f.nose_mm + f.mid_mm + 3 * f.radius_mm / math.tan(math.radians(11))) / 1e3)
    rows = [r for r in res["length_sweep"] if r["sized"]]
    assert [r["ok"] for r in rows] == [r["length_m"] <= res["max_length_m"] for r in rows]
    assert all(r["swells"] == (not r["ok"]) for r in rows)                     # past the limit the cubic bulges
    assert all(a["tail_m2"] > b["tail_m2"] and a["body_m2"] < b["body_m2"] for a, b in zip(rows[:-1], rows[1:]))
    assert all(r["vh"] >= s.tail.vh_target - 1e-9 and r["vv"] >= s.tail.vv_target - 1e-9 for r in rows)
    best = min((r for r in rows if r["ok"]), key=lambda r: r["sink_ms"])
    assert 1.8 <= best["length_m"] <= 2.4                                      # a short body pays in tail, a long one in skin
    assert best["sink_ms"] < rows[0]["sink_ms"] and best["sink_ms"] < rows[-1]["sink_ms"]
    assert rows[0]["slope_deg"] > f.tail_angle_deg + 3 and best["slope_deg"] < f.tail_angle_deg + 0.5
    as_designed = twin["length_sweep"][0]
    assert not as_designed["sized"] and as_designed["length_m"] == 2.0


def test_how_long_the_wing_can_be(res):
    rows = res["span_sweep"]
    assert rows[0]["ok"] and not rows[-1]["ok"]
    assert all(a["used"] < b["used"] for a, b in zip(rows[:-1], rows[1:]))
    assert rows[2]["sink_ms"] < rows[0]["sink_ms"]                             # a longer wing sinks slower, to a point
    assert "brace" in next(r for r in rows if not r["ok"])["limit"]


def test_params_scad_is_whole_and_used(s, res):
    text = sp.params_scad(s, res)
    names = re.findall(r"^(\w+) = .*;$", text, flags=re.M)
    assert len(names) == len([ln for ln in text.splitlines() if ln and not ln.startswith("//")])
    assert text.count("[") == text.count("]")
    scad = "".join(f.read_text() for f in sp.SCAD.glob("*.scad"))
    assert [n for n in names if not re.search(rf"\b{n}\b", scad)] == []


@pytest.mark.skipif(not shutil.which("openscad"), reason="OpenSCAD is not installed")
@pytest.mark.parametrize("part", ["tube_end", "wing_fork", "root_fork", "jury_collar", "end_rib", "nadir_belly"])
def test_the_parts_build_in_openscad(res, twin, boom, tmp_path, part):
    sp.export({"wing_fork": twin, "root_fork": boom}.get(part, res), tmp_path)
    out = tmp_path / f"{part}.stl"
    file, extra = (part, []) if part in ("end_rib", "nadir_belly") else ("brace_fittings", ["-D", f'part="{part}"'])
    done = subprocess.run(["openscad", *extra, "-o", str(out), str(tmp_path / "scad" / f"{file}.scad")],
                          capture_output=True, text=True, timeout=600)
    assert done.returncode == 0 and "WARNING" not in done.stderr and out.stat().st_size > 1000
