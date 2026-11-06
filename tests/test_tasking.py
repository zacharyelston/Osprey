"""Looking groups: the reserve rule, group sizes and the calc checks."""
import numpy as np

from osprey import calcs, occlusion, tasking
from osprey.params import load
from osprey.rig import stations


def _short(p, seconds=30):
    p.scenario.duration_s = seconds
    return p


def test_reserve_always_watches_and_mob_takes_the_max_group():
    p = _short(load("mob"))
    out = tasking.Sim(p).run()
    s = tasking.summary(out)
    assert s["always_watch"]
    groups = [len(r["group"]) for r in out["tasks"]["mob"]]
    assert max(groups) <= p.rig.max_group
    assert max(groups) >= 3                       # every camera that can see it, but the reserve
    assert all(len(r["group"]) + sum(len(o["group"]) for k, rows in out["tasks"].items() if k != "mob"
                                     for o in rows if o["t"] == r["t"]) <= 5 - p.rig.reserve
               for r in out["tasks"]["mob"])


def test_min_groups_stop_once_the_need_is_met():
    p = _short(load("coastal-watch"), 20)
    out = tasking.Sim(p).run()
    for rows in out["tasks"].values():
        for r in rows:
            assert len(r["group"]) <= p.rig.max_group


def test_spreader_tips_see_past_the_leeward_sails():
    """On mast brackets every lower camera is blind to leeward; on the spreader
    tips the leeward one is not (the finding that made mast5-spreaders)."""
    for rig, want in (("mast5", False), ("mast5-spreaders", True)):
        p = load("coastal-watch", rig=rig)
        sts = [s for s in stations(p) if "exterior" in s.zones and s.id != "top"]
        cov, mask = calcs.coverage(p, sts, occlusion.build(p))
        az = np.arange(0, 360, 1.0)
        lee = (az > 280) & (az < 330)             # starboard bow sector, body azimuth
        assert bool(mask[:, lee].any(0).all()) is want


def test_calc_runs_and_grades():
    p = load("docking")
    checks = calcs.run(p)
    assert {c.status for c in checks} <= {"PASS", "WARN", "FAIL", "INFO"}
    groups = {c.group for c in checks}
    assert {"Motion", "Stabilization", "Coverage", "Mass aloft", "Docking"} <= groups
