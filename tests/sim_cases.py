"""The sims run on the kept designs, reduced to the numbers worth comparing: what the Python sims gave is
kept in tests/data/sim_reference.json, and the tests hold the Rust sims to it.

    uv run python tests/sim_cases.py      # rewrite the reference from the sims as they are now
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/data/sim_reference.json"


def _design(path: Path) -> dict:
    return json.loads(path.read_text())


def _clean(x):
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return x
    if isinstance(x, (int, float)) or hasattr(x, "item"):
        v = float(x)
        return v if math.isfinite(v) else str(v)
    return str(x)


def flights():
    from osprey.recon import flight
    from osprey.recon.params import MISSIONS, load

    keep = ("outcome", "left_task_because", "progress", "flight_time_s", "on_scene_s", "task_s", "distance_km",
            "energy_left_frac", "bank_max_deg", "power_mean_w", "passes")
    for airframe, root in (("twin-boom", "runs/2026-11-06_recon-payloads"), ("tailsitter", "runs/2026-11-07_recon-water/tailsitter")):
        for pl in ("gimbal", "dual"):
            if airframe == "tailsitter" and pl == "dual":
                continue
            for mn in MISSIONS:
                kw = {"airframe": "tailsitter"} if airframe == "tailsitter" else {}
                p = load(mn, payload=pl, **kw)
                d = _design(ROOT / root / pl / mn / "design.json")
                ac = flight.Aircraft.from_design(p, d)
                r = flight.simulate(p, ac)
                s = flight.summary(p, ac, r)
                yield f"flight/{airframe}/{pl}/{mn}", {k: s[k] for k in keep if k in s} | {"steps": len(r["t"])}


def takeoffs():
    from osprey.recon import water
    from osprey.recon.params import load

    for pl in ("gimbal", "dual"):
        p = load("sar-offshore", payload=pl)
        d = _design(ROOT / "runs/2026-11-06_recon-payloads" / pl / "sar-offshore/design.json")
        yield f"takeoff/{pl}", water.takeoff(p, d, d["mass_total_kg"] + p.water.kit_kg)


def launches():
    from osprey.recon import tailsitter
    from osprey.recon.params import load

    for pl in ("gimbal", "dual"):
        p = load("sar-offshore", payload=pl, airframe="tailsitter")
        d = _design(ROOT / "runs/2026-11-07_recon-water/tailsitter" / pl / "sar-offshore/design.json")
        r = tailsitter.launch(p, d)
        yield f"launch/{pl}", {k: v for k, v in r.items() if k != "track"} | {"track_points": len(r["track"]),
                                                                             "track_end": list(r["track"][-1])}


def cyclones():
    from osprey.recon import cyclone, cyclone_modes
    from osprey.recon.params import load

    for pl in ("gimbal", "dual"):
        p = load("sar-offshore", payload=pl)
        d = _design(ROOT / "runs/2026-11-07_recon-cyclone-modes" / pl / "cyclone.json")["design"]
        cy, md = cyclone.inputs(), cyclone_modes.inputs()
        m = cyclone.mass(p, d, cy)
        yield f"spin_up/{pl}", cyclone.spin_up(p, d, cy, m)
        mg = cyclone_modes.Manager(p, d, cy, md, m)
        yield f"pitch_over/{pl}", cyclone_modes.pitch(p, d, cy, md, m, mg.tr["v_range_ms"], up=False)
        yield f"pitch_up/{pl}", cyclone_modes.pitch(p, d, cy, md, m, mg.v4, up=True)


def cases() -> dict:
    out = {}
    for gen in (flights, takeoffs, launches, cyclones):
        for k, v in gen():
            out[k] = _clean(v)
    return out


if __name__ == "__main__":
    REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE.write_text(json.dumps(cases(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {REFERENCE}")
