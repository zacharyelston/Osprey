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


def _pod_stations(pod: dict, kit: dict) -> list[dict]:
    """A pod's two cameras as stations.

    Vertical kits (gecko): the upper camera keeps the pod's id and the lower
    one is <id>-down. A lower PTZ serves the same zones as the upper; a fixed
    down-looking camera (a fisheye) serves the near zone only.

    Horizontal kits (a back-to-back dual mount): <id>-fwd faces the bow and
    <id>-aft the stern, each along_dx_m from the mount centre."""
    x, y, z = pod["pos_m"]
    common = {"face_az_deg": pod["face_az_deg"], "on_mast": pod["on_mast"], "pod": pod["id"],
              "sector_deg": pod.get("sector_deg", 360.0)}
    if kit.get("layout") == "horizontal":
        dx = kit["along_dx_m"]
        zones = pod.get("zones", ["exterior", "deck"])
        return [{**common, "id": f"{pod['id']}-{end}", "camera": pod[end], "pos_m": [x + sign * dx, y, z],
                 "face_az_deg": az, "zones": zones}
                for end, sign, az in (("fwd", 1, 0.0), ("aft", -1, 180.0))]
    return [
        {"id": pod["id"], "camera": pod["up"], "pos_m": [x, y, z + kit["up_dz_m"]],
         "zones": pod.get("zones", ["exterior", "deck"]), **common},
        {"id": f"{pod['id']}-down", "camera": pod["down"], "pos_m": [x, y, z + kit["down_dz_m"]],
         "zones": pod.get("down_zones", ["near", "deck"] if pod["down"].startswith("fisheye")
                          else pod.get("zones", ["exterior", "deck"])), **common},
    ]


def load_rig(name: str) -> dict:
    """A rig's [rig] table, its stations and its pods, following `include`
    chains. Each pod adds its two cameras to the stations."""
    raw = _toml(DESIGN / "rigs" / f"{name}.toml")
    rig = raw["rig"]
    stations = list(raw.get("station", []))
    pods = list(raw.get("pod", []))
    kits = _toml(DESIGN / "electronics.toml")["kit"]
    for pod in pods:
        if pod["kit"] not in kits:
            raise ValueError(f"pod {pod['id']}: unknown kit {pod['kit']!r}")
        stations += _pod_stations(pod, kits[pod["kit"]])
    if inc := rig.get("include"):
        base = load_rig(inc)
        stations, pods = base["station"] + stations, base["pod"] + pods
    ids = [s["id"] for s in stations]
    if len(ids) != len(set(ids)):
        raise ValueError(f"rig {name}: duplicate station ids in {ids}")
    return {"rig": rig, "station": stations, "pod": pods}


def load(scenario: str = "coastal-watch", rig: str | None = None) -> SimpleNamespace:
    """Everything one scenario needs: boat, sea, atmosphere, cameras, targets,
    pod electronics, the rig its scenario names (or `rig`), and the scenario."""
    sc = _toml(DESIGN / "scenarios" / f"{scenario}.toml")
    boat = _toml(DESIGN / "boat.toml")
    sea = _toml(DESIGN / "sea.toml")
    tg = _toml(DESIGN / "targets.toml")
    el = _toml(DESIGN / "electronics.toml")
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
        "pod": r["pod"],
        "electronics": el,
        "scenario": sc["scenario"],
        "requirement": sc.get("requirement", {}),
        "target": sc.get("target", []),
        "dock": sc.get("dock", {}),
        "render": sc.get("render", {}),
    })
