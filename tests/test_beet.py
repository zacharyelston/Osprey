"""The Beet: a flying buoy, sized and floated (beet.py)."""

import math

import pytest

from osprey import beet
from osprey.recon import water


def test_a_revolved_outline_holds_the_volume_it_should():
    mesh = beet.revolve([(0.0, 0.0), (1.0, 0.0), (1.0, 2.0), (0.0, 2.0)], n=96)
    assert water._below([mesh], 10.0)[0] == pytest.approx(2 * math.pi, rel=0.01)
    assert water._below([mesh], 1.0)[0] == pytest.approx(math.pi, rel=0.01)


def test_momentum_theory_puts_an_r44_near_its_rating():
    k = beet.r44()
    assert 0.8 * k["mcp_kw"] < k["hover_kw"] < k["takeoff_kw"]


def test_at_a_fixed_disc_loading_hover_power_grows_with_weight_alone():
    c = beet.case("beet-4")
    assert beet.hover_kw(c, 2000) / 2000 == pytest.approx(beet.hover_kw(c, 1000) / 1000)


def test_every_way_of_powering_the_beet_4_closes_and_the_turbine_is_lightest():
    m = {p: beet.size("beet-4", p) for p in beet.inputs()["power"]}
    assert all(r["ok"] for r in m.values())
    assert m["turbine"]["mass_kg"] < m["turbogen"]["mass_kg"] < m["gen-hover"]["mass_kg"] < m["battery-hop"]["mass_kg"]


def test_the_genset_buys_time_at_the_top_and_the_battery_does_not():
    gen = [beet.size("beet-4", "gen-hover", view_min=t)["mass_kg"] for t in (5, 15)]
    bat = [beet.size("beet-4", "battery-hop", view_min=t)["mass_kg"] for t in (5, 15)]
    assert gen[1] == pytest.approx(gen[0])
    assert bat[1] > 2 * bat[0]


def test_the_disc_floats_stiff_and_shallow_but_stays_upside_down_once_over():
    r = beet.one(("beet-4", "gen-hover", {}, True))
    tube_top = beet.inputs()["geometry"]["tube_bottom_m"] + beet.inputs()["geometry"]["tube_d_m"]
    assert 0 < r["waterline_m"] < tube_top
    assert r["gm_m"] > 3                                    # a disc: very stiff
    assert abs(r["gz_m"][0]) < 1e-3 and abs(r["gz_m"][-1]) < 2e-2
    assert r["gz_m"][2] > 0.3                               # 20 degrees over, it comes back hard
    assert not r["rights"] and 60 <= r["vanishes_deg"] <= 90
