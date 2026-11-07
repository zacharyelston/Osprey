"""One bird, many jobs: fly every sized airframe through every mission.

Each mission sizes its own airframe, but a crew will own one drone. The
capability matrix flies each design through every mission in the 3-DOF sim.
A cell succeeds when the drone gets back aboard with the task's goal met.
The lightest design that succeeds everywhere is the one to build.
"""

from __future__ import annotations

from osprey.recon import flight
from osprey.recon.params import load


def ok(s: dict) -> bool:
    return s["outcome"] == "recovered" and s["goal_met"]


def capability(designs: dict[str, dict], missions: list[str], payload: str = "gimbal") -> dict[str, dict[str, dict]]:
    out = {}
    for dn, d in designs.items():
        out[dn] = {}
        for mn in missions:
            p = load(mn, payload=payload)
            ac = flight.Aircraft.from_design(p, d)
            out[dn][mn] = flight.summary(p, ac, flight.simulate(p, ac))
    return out


def one_bird(matrix: dict[str, dict[str, dict]], designs: dict[str, dict]) -> str | None:
    """The lightest design that does every mission."""
    good = [dn for dn, row in matrix.items() if all(ok(s) for s in row.values())]
    return min(good, key=lambda dn: designs[dn]["mass_total_kg"]) if good else None
