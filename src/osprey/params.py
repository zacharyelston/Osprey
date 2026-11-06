"""Load the TOML design files into attribute-access namespaces."""

from __future__ import annotations

import tomllib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "design"
OUT = ROOT / "out"

SCENARIOS = tuple(sorted(f.stem for f in (DESIGN / "scenarios").glob("*.toml")))
RIGS = tuple(sorted(f.stem for f in (DESIGN / "rigs").glob("*.toml")))


def ns(obj):
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: ns(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [ns(v) for v in obj]
    return obj


def _toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_rig(name: str) -> dict:
    """A rig's [rig] table and its stations, following `include` chains."""
    raw = _toml(DESIGN / "rigs" / f"{name}.toml")
    rig = raw["rig"]
    stations = list(raw.get("station", []))
    if inc := rig.get("include"):
        stations = load_rig(inc)["station"] + stations
    ids = [s["id"] for s in stations]
    if len(ids) != len(set(ids)):
        raise ValueError(f"rig {name}: duplicate station ids in {ids}")
    return {"rig": rig, "station": stations}


def load(scenario: str = "coastal-watch", rig: str | None = None) -> SimpleNamespace:
    """Everything one scenario needs: boat, sea, atmosphere, cameras, targets,
    the rig its scenario names (or `rig`), and the scenario itself."""
    sc = _toml(DESIGN / "scenarios" / f"{scenario}.toml")
    boat = _toml(DESIGN / "boat.toml")
    sea = _toml(DESIGN / "sea.toml")
    tg = _toml(DESIGN / "targets.toml")
    cams = _toml(DESIGN / "cameras.toml")["camera"]
    r = load_rig(rig or sc["scenario"]["rig"])
    for s in r["station"]:
        if s["camera"] not in cams:
            raise ValueError(f"station {s['id']}: unknown camera {s['camera']!r}")
    state = sc["scenario"]["sea_state"]
    return ns({
        **boat,
        "sea": {**sea["sea"][state], "state": state},
        "atmosphere": sea["atmosphere"],
        "camera": cams,
        "target_class": tg["target"],
        "johnson": tg["johnson"],
        "rig": r["rig"],
        "station": r["station"],
        "scenario": sc["scenario"],
        "requirement": sc.get("requirement", {}),
        "target": sc.get("target", []),
        "dock": sc.get("dock", {}),
        "render": sc.get("render", {}),
    })
