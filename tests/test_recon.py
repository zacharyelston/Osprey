"""Osprey Recon: search theory, the 3-DOF flight sim and the OpenMDAO sizing."""
import math
import warnings
from dataclasses import replace

import numpy as np
import pytest

from osprey.recon import flight, search, sizing
from osprey.recon.params import MISSIONS, load

warnings.filterwarnings("ignore", module="openaerostruct")


def _ac(**kw):
    base = dict(mass_kg=1.6, S_m2=0.15, span_m=1.2, cd0=0.08, k=0.03, cl_max=1.15, eta_prop=0.62,
                eta_motor=0.85, p_aux_w=14.0, energy_j=1e9, p_shaft_max_w=400.0, v_search=16.6,
                bank_max_rad=math.radians(35))
    return flight.Aircraft(**{**base, **kw})


def test_every_mission_loads():
    for m in MISSIONS:
        p = load(m)
        assert p.mission.name == m and p.mission.boat_mode in ("return", "sail")


def test_sweep_is_wider_higher_and_the_drone_sees_past_the_waves():
    p = load("sar-offshore")
    lo, hi = search.sweep(p, 40.0), search.sweep(p, 120.0)
    assert hi.width_eff_m > lo.width_eff_m > 0
    assert hi.p_vis > 0.9                       # steep look: crests hide almost nothing
    assert search.sweep(p, 5000.0).p_pass == 0  # too high to resolve a person at all


def test_plan_reaches_the_goal_at_least_cost():
    p = load("sar-datum")
    sw = search.sweep(p, p.mission.search_alt_m)
    pl = search.plan(sw, p.mission.datum_sigma_m, 0.9)
    assert pl.pod >= 0.9
    assert pl.coverage > 1.5                   # one pass (C = 1) can never reach 90 %
    assert pl.spacing_m == pytest.approx(sw.width_eff_m / pl.coverage)


def test_expanding_square_grows_to_the_half_size():
    pts = search.expanding_square(50.0, 400.0)
    legs = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    assert legs[0] == pytest.approx(50) and legs[2] == pytest.approx(100)
    assert np.abs(pts).max() >= 400


def test_grid_only_finds_what_the_footprint_covers():
    p = load("sar-datum")
    sw = search.sweep(p, 80.0)
    g = search.Grid(np.zeros(2), np.zeros(2), 150.0)
    g.look(np.array([0.0, -sw.near_m - 10]), 0.0, 0.0, 10.0, 15.0, sw)     # datum just ahead
    assert 0 < g.pod < 1
    far = search.Grid(np.zeros(2), np.zeros(2), 150.0)
    far.look(np.array([5000.0, 5000.0]), 0.0, 0.0, 10.0, 15.0, sw)
    assert far.pod == 0


def test_crosswind_transit_crabs_into_the_wind():
    """Regression: the crab angle once had its sign backwards and the drone
    swung a kilometre downwind on the way out."""
    p = load("sar-datum")                       # 15 kn from the east, datum due south
    r = flight.simulate(p, _ac())
    out = r["phase"] == "outbound"
    assert np.abs(r["x"][out]).max() < 150


def test_unlimited_battery_finds_and_comes_home():
    p = load("sar-datum")
    r = flight.simulate(p, _ac())
    s = flight.summary(p, _ac(), r)
    assert s["outcome"] == "recovered" and s["left_search_because"] == "pod"
    assert s["pod"] >= p.mission.search_pod


def test_a_short_battery_calls_bingo_and_still_gets_home():
    p = load("sar-datum")
    ac = _ac(energy_j=50 * 3600.0 * 0.5)
    r = flight.simulate(p, ac)
    assert r["outcome"] == "recovered"
    assert r["why"] in ("bingo", "pod")


def test_sizing_derivatives_through_the_span():
    """Regression: abs() in the shell-mass component killed the complex step."""
    prob, _ = sizing.build(load("sar-datum"))
    prob.run_model()
    d = prob.check_totals(of=["total.mass"], wrt=["wing.geometry.span"], method="fd", out_stream=None)
    v = d[("total.mass", "wing.geometry.span")]
    fd = np.asarray(v["J_fd"]).ravel()[0]
    an = np.asarray(v.get("J_rev", v.get("J_fwd"))).ravel()[0]
    assert an == pytest.approx(fd, rel=1e-3)


def test_sized_design_meets_its_constraints():
    p = load("sar-datum")
    d = sizing.optimize(p)
    assert d["converged"]
    assert d["v_stall_ms"] <= p.limits.stall_speed_max_ms + 1e-3
    assert d["re_tip"] >= p.wing.re_min * 0.999
    assert d["root_chord_m"] >= d["tip_chord_m"] - 1e-6
    assert d["print_chord_ok"] and d["failure"] <= 1e-6
    assert d["endurance_margin"] >= -1e-6
    ac = replace(flight.Aircraft.from_design(p, d))
    assert ac.v_stall(0.0) == pytest.approx(d["v_stall_ms"], rel=0.02)
