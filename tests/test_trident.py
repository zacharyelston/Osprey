"""The Trident: three modules round a core, sized and floated (trident.py)."""

import math

import numpy as np
import pytest

from osprey import trident
from osprey.recon import water


@pytest.fixture(scope="module")
def found():
    return trident.size("found")


def test_its_sealed_bodies_hold_the_volume_they_should():
    c = trident.params("balanced")
    lay = trident.layout(c)
    named = dict(trident.meshes(c))
    core = math.pi * lay["r_core"] ** 2 * lay["core_l"]
    bay = math.pi * c["bay_r_m"] ** 2 * c["bay_m"]
    assert core + bay < water._below([named["envelope"]], 1e3)[0] < core + bay + math.pi * lay["r_core"] ** 2 * c["nose_m"]
    foot = math.pi * c["foot_r_m"] ** 2 * c["foot_l_m"]
    assert 0.8 * foot < water._below([named["foot 1"]], 1e3)[0] < foot
    wing = 0.685 * c["wing_t_over_c"] * c["wing_chord_m"] ** 2 * lay["panel_span"]
    assert water._below([named["wing 1"]], 1e3)[0] == pytest.approx(wing, rel=0.05)


def test_hover_power_grows_as_the_weight_to_the_one_and_a_half():
    c = trident.params()
    assert trident.hover_kw(c, 2000) / trident.hover_kw(c, 1000) == pytest.approx(2**1.5)
    small = dict(c, prop_d_m=c["prop_d_m"] / 2)
    assert trident.hover_kw(small, 1000) == pytest.approx(2 * trident.hover_kw(c, 1000))


def test_the_weight_closes_and_cargo_flies_the_same_airframe(found):
    assert found["ok"] and sum(found["parts"].values()) == pytest.approx(found["mass_kg"], rel=1e-5)
    cargo = trident.cargo(found)
    assert cargo["mass_kg"] == pytest.approx(found["mass_kg"])
    assert cargo["useful_kg"] > found["useful_kg"]                 # the crew's kit comes out too
    assert trident.cargo(found, 25.0)["useful_kg"] > cargo["useful_kg"] > trident.cargo(found, 100.0)["useful_kg"]
    assert trident.size("found", 100.0)["mass_kg"] > found["mass_kg"]


def test_as_sketched_it_cant_fly_and_balancing_the_module_ring_puts_the_wing_on_the_cg(found):
    sketch, balanced = trident.size("sketch"), trident.size("balanced")
    assert sketch["static_margin"] < -1.0                           # the wing far ahead of the CG
    for r in (balanced, found):
        assert r["static_margin"] == pytest.approx(r["params"]["static_margin"], abs=1e-3)
        assert r["layout"]["z_prop"] < sketch["layout"]["z_prop"] - 1.5
    assert balanced["mass_kg"] < sketch["mass_kg"]


def test_upright_and_inverted_it_has_no_arm(found):
    c = found["params"]
    ms = [m for _, m in trident.meshes(c)]
    cg = np.array([0.0, 0.0, found["zg_m"]])
    need = found["mass_kg"] / c["water_density_kgm3"]
    for psi in (0.0, math.pi / 3):
        assert abs(trident.gz(ms, cg, need, 0.0, psi)) < 1e-3
        assert abs(trident.gz(ms, cg, need, math.pi, psi)) < 1e-3


def test_the_found_layout_always_comes_back_and_float_feet_spoil_it(found):
    a = trident.afloat(found)
    assert a["rights"] and a["gm_m"] > 3 and a["props_clear_m"] > 0.5
    assert trident.afloat(trident.cargo(found))["rights"]
    feet = trident.size("found", feet=(0.20, 1.00))
    f = trident.afloat(feet)
    assert f["feet_share"] > 0.2 and not f["rights"]               # the feet's buoyancy at the tail holds it over
    sketch = trident.afloat(trident.size("sketch"))
    assert sketch["gm_m"] < 0 and not sketch["rights"]


def test_a_thin_sandwich_at_the_same_outside_beats_the_thick_foam_and_the_hdpe_lattice(found):
    hull = {h: trident.one(("crewed", "found", {"hull": h}, True)) for h in ("glass_foam", "lattice", "sandwich")}
    assert hull["glass_foam"]["mass_kg"] == pytest.approx(found["mass_kg"])
    sand, lat = hull["sandwich"], hull["lattice"]
    assert sand["mass_kg"] < found["mass_kg"] - 20 and sand["rights"] and sand["unsinkable"] > 1.5
    assert sand["layout"]["r_core"] == pytest.approx(found["layout"]["r_core"])        # the same outside
    assert sand["layout"]["inside_w_m"] > found["layout"]["inside_w_m"] + 0.25           # the room back inside
    assert lat["mass_kg"] > found["mass_kg"] + 150 and not lat["rights"]
