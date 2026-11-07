"""Osprey Recon: search theory, the 3-DOF flight sim and the OpenMDAO sizing."""
import math
import warnings
from dataclasses import replace
from pathlib import Path

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
        assert p.mission.name == m and p.mission.boat_mode in ("return", "approach", "sail", "hold")
        assert p.mission.kind in ("search", "survey", "inspect", "escort")
    assert {load(m).mission.kind for m in MISSIONS} == {"search", "survey", "inspect", "escort"}


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
    assert s["outcome"] == "recovered" and s["left_search_because"] == "goal"
    assert s["pod"] >= p.mission.search_pod


def test_a_short_battery_calls_bingo_and_still_gets_home():
    p = load("sar-datum")
    ac = _ac(energy_j=50 * 3600.0 * 0.5)
    r = flight.simulate(p, ac)
    assert r["outcome"] == "recovered"
    assert r["why"] in ("bingo", "goal")


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


def test_survey_images_the_site_straight_down():
    p = load("scout-anchorage")
    r = flight.simulate(p, _ac())
    s = flight.summary(p, _ac(), r)
    assert s["kind"] == "survey" and s["outcome"] == "recovered" and s["goal_met"]
    assert s["gsd_cm"] == pytest.approx(p.mission.survey_alt_m * 1.55e-6 / 8e-3 * 100, rel=1e-6)
    assert all(px > 10 for px in s["px_across"].values())       # every hazard class well resolved


def test_inspection_orbits_a_moving_vessel():
    p = load("inspect-vessel")
    r = flight.simulate(p, _ac())
    s = flight.summary(p, _ac(), r)
    assert s["kind"] == "inspect" and s["goal_met"] and s["resolves"]
    task = r["task"]
    on = r["phase"] == "task"
    d = np.hypot(r["x"][on] - [task.where(t)[0] for t in r["t"][on]],
                 r["y"][on] - [task.where(t)[1] for t in r["t"][on]])
    assert np.median(d) == pytest.approx(p.mission.standoff_m, rel=0.35)


def test_bingo_uses_the_real_way_home():
    """Regression: bingo once assumed wind and boat dead against the way home,
    and turned the drone round on arrival at a vessel it was sent to inspect."""
    p = load("inspect-vessel")
    ac = _ac(energy_j=40 * 3600.0 * 0.8)
    s = flight.summary(p, ac, flight.simulate(p, ac))
    assert s["outcome"] == "recovered" and s["goal_met"]


def test_one_bird_is_the_lightest_that_does_everything():
    from osprey.recon import fleet

    p_small, small = _kept("sar-datum")
    _, big = _kept("sar-offshore")
    missions = ["sar-datum", "inspect-vessel"]
    M = fleet.capability({"small": small, "big": big}, missions)
    best = fleet.one_bird(M, {"small": small, "big": big})
    assert best in ("small", "big")
    assert all(fleet.ok(s) for s in M[best].values())


KEPT = tuple(sorted(d.name for d in (Path(__file__).resolve().parents[1] / "runs/2026-11-06_recon-payloads/gimbal").iterdir()
                    if (d / "design.json").exists()))


def test_side_eyes_split_the_search_and_the_belly_fills_the_gap():
    from osprey.recon.params import payload_kg

    g, d = load("sar-datum"), load("sar-datum", payload="dual")
    sg, sd = search.sweep(g, 80.0), search.sweep(d, 80.0)
    left, right, belly = sd.rects
    assert left[2] > 0 > right[3]                         # one strip each side of the track
    assert belly[2] < 0 < belly[3] and belly[3] >= left[2] - 1e-9   # the belly covers the gap between them
    assert sd.width_eff_m > 3 * sg.width_eff_m
    assert payload_kg(d) > payload_kg(g)                  # two PTZs and a fisheye weigh more than one gimbal


def test_side_eyes_survey_two_strips_at_the_same_pixels():
    from osprey.recon import tasks

    g, d = load("scout-anchorage"), load("scout-anchorage", payload="dual")
    tg, td = tasks.build(g, np.zeros(2)), tasks.build(d, np.zeros(2))
    assert td.info()["swath_m"] == pytest.approx(2 * tg.info()["swath_m"])
    assert td.info()["gsd_cm"] == pytest.approx(tg.info()["gsd_cm"])
    assert len(td.pattern) < len(tg.pattern)


def test_inboard_eye_inspects_round_the_orbit():
    p = load("inspect-vessel", payload="dual")
    r = flight.simulate(p, _ac())
    s = flight.summary(p, _ac(), r)
    assert s["camera"] == "inboard PTZ eye" and s["goal_met"] and s["resolves"]


def test_escort_circles_the_sailing_boat_for_its_time():
    p = load("escort-flanks")
    r = flight.simulate(p, _ac())
    s = flight.summary(p, _ac(), r)
    assert s["kind"] == "escort" and s["outcome"] == "recovered" and s["goal_met"]
    assert s["task_s"] == pytest.approx(p.mission.escort_min * 60, abs=5)
    on = r["phase"] == "task"
    d = np.hypot(r["x"][on] - r["boat_x"][on], r["y"][on] - r["boat_y"][on])
    assert np.median(d) == pytest.approx(p.mission.escort_radius_m, rel=0.3)


def test_bingo_credits_a_boat_closing_on_the_drone():
    """Regression: bingo once ignored a boat sailing toward the site being
    surveyed and turned the drone home 30 s into the survey."""
    p = load("scout-anchorage", payload="dual")
    ac = _ac(energy_j=0.17 * 200 * 3600 * 0.8)
    s = flight.summary(p, ac, flight.simulate(p, ac))
    assert s["left_task_because"] != "bingo" or s["progress"] > 0.5


def _kept(m="sar-offshore"):
    import json
    from pathlib import Path

    d = json.loads((Path(__file__).resolve().parents[1] / "runs/2026-11-06_recon-payloads/gimbal" / m / "design.json")
                   .read_text())
    return load(m), d


def test_bird_meshes_are_closed_and_face_outward():
    from osprey.recon import geometry

    p, d = _kept()
    parts = geometry.build(p, d)
    for q in parts:
        v, f = q.verts, q.faces
        vol = np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6
        assert vol > 0, q.name                                   # outward winding: renderers cull back faces
    panels = [q for q in parts if q.name.startswith("panel_")]
    assert len(panels) == d["print_panels"]
    lo, hi = geometry.bounds(parts)
    assert hi[1] - lo[1] == pytest.approx(d["span_m"], rel=0.02)


def test_tail_respects_its_chord_floor():
    from osprey.recon import geometry

    for m in KEPT:
        p, d = _kept(m)
        t = geometry.tail_size(p, d)
        assert t["ch"] >= p.geometry.tail_chord_min_m and t["cv"] >= p.geometry.tail_chord_min_m


def test_bird_scene_compiles():
    import mujoco

    from osprey.recon import geometry, render

    p, d = _kept("sar-datum")
    a, b = render._drone_xml("bird", geometry.build(p, d), np.zeros(3), render._quat())
    xml = render._world("studio", a, b, render._cam("c", [2, 2, 2], [0, 0, 0]), 64, 48)
    m = mujoco.MjModel.from_xml_string(xml)
    assert m.nmesh == len(geometry.build(p, d))


def test_blended_wing_is_trimmed_stable_and_deep_enough():
    p = load("sar-datum", airframe="bwb")
    d = sizing.optimize(p)
    assert d["converged"] and d["airframe"] == "bwb"
    assert abs(d["cm_trim"]) < 1e-3                                      # trimmed at task speed
    assert d["static_margin"] >= p.stability.static_margin_min - 1e-4
    assert d["root_depth_m"] >= p.volume.root_depth_min_m - 1e-4
    assert d["print_panels"] == 0                                       # moulded, not printed


def test_plug_halves_are_closed_and_match_the_design(tmp_path):
    from osprey.recon import geometry, plug

    p = load("sar-datum", airframe="bwb")
    d = sizing.optimize(p)
    info = plug.export(p, d, tmp_path)
    assert {f.name for f in tmp_path.iterdir()} >= {"oml.stl", "plug_upper.stl", "plug_lower.stl", "sections.csv"}
    assert info["span_mm"] == pytest.approx(d["span_m"] * 1000)
    assert info["root_depth_mm"] == pytest.approx(d["root_depth_m"] * 1000, rel=0.02)
    for half in ("upper", "lower"):
        rings = geometry.bwb_surface(p, d, half=half)
        v, f = geometry.loft(rings[: len(rings) // 2])
        vol = np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6
        assert vol > 0                                                 # closed and wound outward


def test_altitude_buys_the_wake_and_the_mast_lens_buys_the_boat():
    from osprey.recon import awareness

    rows = {r["eye"]: r for r in awareness.table("ss3", 15.0)}
    mast = rows["Masthead long PTZ (18.9 m, 200 mm)"]
    drone = rows["Drone gimbal at 120 m (30 mm)"]
    assert drone["skiff_wake:detect"][0] > 2 * mast["skiff_wake:detect"][0]
    assert mast["skiff:recognize"][0] > drone["skiff:recognize"][0]
    assert mast["skiff_wake:detect"][1] == "waves"


def test_crescent_curves_its_leading_edge_and_prints():
    p = load("sar-offshore", airframe="crescent")
    d = sizing.optimize(p)
    assert d["converged"] and d["airframe"] == "crescent"
    assert abs(d["cm_trim"]) < 1e-3 and d["static_margin"] >= p.stability.static_margin_min - 1e-4
    le = np.array(d["le_x_m"])[::-1]                 # root to tip
    steps = np.diff(le)
    assert steps[-1] > steps[0] > -1e-6              # sweep grows toward the tips: a crescent
    assert d["print_panels"] > 0 and d["print_chord_ok"]
    assert d["le_z_m"][0] > d["le_z_m"][-1]          # the tips curve up


WINGS = Path(__file__).resolve().parents[1] / "runs/2026-11-06_recon-wings"


def _wing(airframe):
    import json

    return (load("sar-offshore", airframe=airframe),
            json.loads((WINGS / airframe / "gimbal/sar-offshore/design.json").read_text()))


def _area(P):
    return 0.5 * float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))


@pytest.mark.parametrize("airframe", ["bwb", "crescent"])
def test_ladder_frame_slots_pair_up_and_nothing_clashes(airframe):
    from osprey.recon import frame

    p, d = _wing(airframe)
    t = p.frame.thickness_mm + p.frame.clearance_mm
    for side in ("upper", "lower"):
        parts, info = frame.build(p, d, side)
        ribs = [q for q in parts if q.kind == "rib"]
        stringers = [q for q in parts if q.kind == "stringer"]
        base = info["base_z_mm"]
        assert all(abs(q.outline[:, 1].min() - base) < 1e-6 for q in parts)    # all stand on the table
        n_rib_slots = sum(len(q.slots) for q in ribs)
        assert n_rib_slots == sum(len(q.slots) for q in stringers) == info["joints"] > 0
        for s in stringers:
            ox, oy = s.origin
            ux, uy = s.direction
            assert len(s.slots) >= 1                                           # every run is slotted in somewhere
            for r in ribs:
                a = (r.origin[1] - oy) / uy
                if not 0 < a < s.size[0]:
                    continue
                x = ox + a * ux
                lo, hi = r.outline[:, 0].min(), r.outline[:, 0].max()
                mine = [hd for sa, hd in s.slots if abs(sa - a) < 1e-6]
                if not lo - t < x < hi + t:
                    continue                                                   # passes beyond the rib's ends
                assert mine, f"{s.name} runs through {r.name} with no slot"
                theirs = [hd for sx, hd in r.slots if abs(sx - x) < 1e-6]
                assert len(theirs) == 1
                # the two half-depth slots meet: together they are the part's full height there
                h = theirs[0] + mine[0]
                assert theirs[0] == pytest.approx(h / 2, rel=1e-6)
                assert h > 0
        # the slot widths: the sheet plus clearance, widened by the crossing angle
        for s in stringers:
            wd = t / abs(s.direction[1])
            assert wd >= t


@pytest.mark.parametrize("airframe", ["bwb", "crescent"])
def test_ladder_frame_parts_are_simple_and_solid(airframe):
    from osprey.recon import frame

    p, d = _wing(airframe)
    for q in frame.build(p, d, "upper")[0]:
        A = abs(_area(q.outline))
        tri = frame.triangulate(q.outline)
        assert sum(abs(_area(q.outline[k])) for k in tri) == pytest.approx(A, rel=1e-6)
        v, f = frame.solid(q, p.frame.thickness_mm)
        vol = np.einsum("ij,ij->i", v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]])).sum() / 6 * 1e9
        assert vol == pytest.approx(A * p.frame.thickness_mm, rel=1e-6)    # closed and wound outward


def test_ladder_frame_layout_files(tmp_path):
    from osprey.recon import frame

    p, d = _wing("bwb")
    info = frame.export(p, d, tmp_path)
    W, H = p.frame.sheet_mm
    n_cut = 0
    for k in range(1, info["sheets"] + 1):
        txt = (tmp_path / f"frame_sheet{k}.dxf").read_text().split("\n")
        pairs = list(zip(txt[0::2], txt[1::2]))
        assert pairs[-1] == ("0", "EOF")
        polys = [i for i, pr in enumerate(pairs) if pr == ("0", "POLYLINE")]
        layers = [pairs[i + 1][1] for i in polys]
        assert layers.count("SHEET") == 1
        n_cut += layers.count("CUT")
        xs = [float(v) for c, v in pairs if c == "10"]
        ys = [float(v) for c, v in pairs if c == "20"]
        assert min(xs) >= 0 and max(xs) <= W and min(ys) >= 0 and max(ys) <= H     # on the sheet
        assert (tmp_path / f"frame_sheet{k}.svg").exists()
    assert n_cut == info["parts"] == sum(len(v) for v in info["frames"].values())
    for sheet in info["nest"]:                                                 # no two parts overlap
        boxes = [(frame.placed(q, x, y, tn).min(0), frame.placed(q, x, y, tn).max(0)) for q, x, y, tn in sheet]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                (a0, a1), (b0, b1) = boxes[i], boxes[j]
                assert (a1 <= b0).any() or (b1 <= a0).any()
    md = (tmp_path / "frame.md").read_text()
    assert md.count("| R") + md.count("| S") >= info["parts"]


def test_buoyancy_integral_is_exact_on_a_box_and_a_sphere():
    from osprey.recon import geometry, water

    v = np.array([[x, y, z] for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)], float)
    f = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    V, cx, pts = water._below([(v + [0.3, 0, 0], f)], 0.1)
    assert V == pytest.approx(0.6) and cx == pytest.approx(0.3)
    assert np.ptp(pts[:, 0]) == pytest.approx(1.0)                         # the waterplane spans the box
    vs, fs = geometry._sphere([0.2, 0, 0], 1.0, 40)
    V, cx, _ = water._below([(vs, fs)], 0.0)
    assert V == pytest.approx(2 / 3 * math.pi, rel=0.02) and cx == pytest.approx(0.2, abs=1e-9)


def test_a_bird_floats_with_its_buoyancy_under_its_weight():
    from osprey.recon import geometry, water

    p, d = _wing("bwb")
    fl = water.afloat(p, d)
    assert fl["displaced_l"] == pytest.approx((d["mass_total_kg"] + p.water.kit_kg) / p.water.density_kgm3 * 1e3)
    assert fl["reserve"] > 1
    sealed = [(water._pitch(q.verts, np.array(fl["cg"]), math.radians(fl["trim_deg"])), q.faces)
              for q in geometry.build(p, d) if q.kind in water.SEALED]
    V, cbx, _ = water._below(sealed, fl["waterline_z"])
    assert V * 1e3 == pytest.approx(fl["displaced_l"], rel=1e-3)
    assert abs(cbx) < 2e-3                                                 # buoyancy straight under the CG


def test_water_takeoff_and_landing_loads_move_the_right_way():
    from osprey.recon import water

    p, d = _wing("bwb")
    light, heavy = water.takeoff(p, d, 2.0), water.takeoff(p, d, 2.6)
    assert light["gets_off"] and heavy["run_m"] > light["run_m"] and heavy["margin_min"] < light["margin_min"]
    assert water.resistance(p, p.water.hump_speed_frac) == pytest.approx(p.water.r_hump)
    n20 = water.impact_factor(p, 12.0, 2.0)
    # FAR 23.527 by hand: 0.012 x (12 m/s in knots)^2 / (tan(20 deg)^(2/3) x (2 kg in lb)^(1/3))
    assert n20 == pytest.approx(0.012 * (12 / 0.514444) ** 2 / (math.tan(math.radians(20)) ** (2 / 3)
                                                              * (2 / 0.453592) ** (1 / 3)))
    p.water.deadrise_deg = 30.0
    assert water.impact_factor(p, 12.0, 2.0) < n20                        # a sharper V lands softer


def test_the_float_kit_goes_into_the_sizing():
    bare, wet = load("sar-offshore", airframe="bwb"), load("sar-offshore", airframe="bwb", water=True)
    assert wet.body.mass_kg == pytest.approx(bare.body.mass_kg + bare.water.kit_kg)
    assert wet.body.cda_m2 == pytest.approx(bare.body.cda_m2 + bare.water.kit_cda_m2)
    assert wet.water.kit_aboard and not bare.water.kit_aboard
