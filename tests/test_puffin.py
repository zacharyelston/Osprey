"""The spar Puffin: righting curves and the battery on a screw (recon/puffin.py)."""

import math
import re
from pathlib import Path

import numpy as np
import pytest

from osprey.recon import puffin, water

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def layouts():
    return {n: puffin.one(n) for n in puffin.inputs()["layouts"]}


def test_upright_it_floats_on_what_it_weighs_and_level_or_inverted_has_no_arm():
    c = puffin.layout("screw")
    meshes, _, m, cg = puffin.build(c, c["float_x_m"])
    need = m / c["water_density_kgm3"]
    ms = puffin._posed(meshes, cg, puffin.UPRIGHT)
    h = puffin._level(ms, need)
    assert water._below(ms, h)[0] == pytest.approx(need, rel=1e-4)
    # Upright and nose-down, the hull is a body of revolution about the vertical through the CG: no arm either way.
    for axis in ("belly", "wingtip"):
        assert abs(puffin.gz(meshes, cg, need, axis, 0.0)) < 2e-3
        assert abs(puffin.gz(meshes, cg, need, axis, math.pi)) < 2e-3


def test_as_drawn_it_settles_flat_but_the_spar_always_bobs_back(layouts):
    a, b, s = layouts["as_drawn"], layouts["ballast"], layouts["screw"]
    assert not a["rights"] and a["gz15_m"] < 0                 # tipped 15°, it falls further
    assert b["rights"] and s["rights"]
    for r in (b, s):
        assert all(x > 0 for x in r["gz_belly_m"][1:-1]) and all(x > 0 for x in r["gz_wingtip_m"][1:-1])
        assert r["props_clear_m"] > 0.25 and r["waterline_m"] > 0.4    # deep draft, the props clear
    assert s["mass_kg"] < b["mass_kg"] - 0.9                        # the screw replaces the kilogram of ballast


def test_the_screw_puts_the_flight_cg_on_the_wing(layouts):
    c = puffin.layout("screw")
    s = layouts["screw"]
    cg = puffin.build(c, s["flight_battery_x_m"])[3][0]
    assert cg == pytest.approx(puffin.flight_cg_target(c), abs=1e-9)
    assert s["travel_m"] == pytest.approx(s["flight_battery_x_m"] - c["float_x_m"])
    assert 0.3 < s["travel_m"] < 0.8
    # A fixed layout's wing is slid to its CG instead.
    b = puffin.balance_wing(puffin.layout("ballast"), 0.10)
    assert puffin.build(b, 0.10)[3][0] == pytest.approx(puffin.flight_cg_target(b), abs=1e-6)


def test_a_heavier_dome_payload_weakens_the_righting():
    light, heavy = puffin.one("screw", payload_kg=0.3), puffin.one("screw", payload_kg=1.0)
    assert heavy["gz15_m"] < light["gz15_m"]
    assert heavy["travel_m"] < light["travel_m"]                    # less battery moment needed to balance it


def test_the_onshape_feature_draws_each_layout_where_the_model_puts_it(layouts):
    fs = (ROOT / "design/recon/onshape/spar-puffin.fs").read_text()
    for key, name in (("AS_DRAWN", "as_drawn"), ("FIXED_BALLAST", "ballast"), ("SCREW", "screw")):
        line = re.search(rf"PuffinLayout\.{key} : \{{([^}}]*)\}}", fs).group(1)
        num = lambda k: float(re.search(rf'"{k}" : ([0-9.]+)', line).group(1))
        r = layouts[name]
        assert num("wingLE") == pytest.approx(r["wing_le_m"], abs=0.002)
        assert num("water") == pytest.approx(r["waterline_m"], abs=0.002)
        if name == "screw":
            assert re.search(r'"battery" : definition\.flying \? ([0-9.]+) : ([0-9.]+)', line).groups() == \
                (f"{r['flight_battery_x_m']:.3f}", f"{r['battery_x_m']:.2f}")
        else:
            assert num("battery") == pytest.approx(r["battery_x_m"], abs=0.002)
    c = puffin.inputs()["craft"]
    assert f'"girth" : {c["diameter_m"]:.2f} * meter' in fs and f'"span" : {c["span_m"]:.1f} * meter' in fs
