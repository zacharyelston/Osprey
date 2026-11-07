"""Load a Recon mission with everything it needs: the airframe, the sea and
atmosphere, the gimbal camera and the target classes."""

from __future__ import annotations

from types import SimpleNamespace

from osprey.params import DESIGN, _toml, ns

RECON = DESIGN / "recon"
MISSIONS = tuple(sorted(f.stem for f in (RECON / "missions").glob("*.toml")))
PAYLOADS = ("gimbal",) + tuple(sorted(f.stem for f in (RECON / "payloads").glob("*.toml")))
AIRFRAMES = ("twinboom",) + tuple(sorted(f.stem for f in (RECON / "airframes").glob("*.toml")))


def _merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def load(mission: str = "sar-datum", payload: str = "gimbal", airframe: str = "twinboom",
         water: bool = False) -> SimpleNamespace:
    """A mission, with the twin-boom airframe (the default) or a variant from
    design/recon/airframes, carrying the gimbal (the default) or a payload
    variant from design/recon/payloads. water=True puts the float kit aboard:
    its mass and drag join the body's, so the sizing carries them."""
    m = _toml(RECON / "missions" / f"{mission}.toml")["mission"]
    af = _toml(RECON / "airframe.toml")
    af["layout"].setdefault("kind", "twinboom")
    if airframe != "twinboom":
        over = _toml(RECON / "airframes" / f"{airframe}.toml")
        base = over.get("layout", {}).get("base")
        if base:                                       # a variant of a variant: the tailsitter on the blended wing
            af = _merge(af, _toml(RECON / "airframes" / f"{base}.toml"))
        af = _merge(af, over)
    if payload != "gimbal":
        af = _merge(af, _toml(RECON / "payloads" / f"{payload}.toml"))
    af["payload"].setdefault("layout", "gimbal")
    af["water"]["kit_aboard"] = water
    if water:
        af["body"]["mass_kg"] += af["water"]["kit_kg"]
        af["body"]["cda_m2"] += af["water"]["kit_cda_m2"]
    sea = _toml(DESIGN / "sea.toml")
    tg = _toml(DESIGN / "targets.toml")
    cams = _toml(DESIGN / "cameras.toml")["camera"]
    return ns({
        **af,
        "mission": m,
        "sea": {**sea["sea"][m["sea_state"]], "state": m["sea_state"]},
        "atmosphere": sea["atmosphere"],
        "camera": cams[af["payload"]["camera"]],
        "belly": cams.get(af["payload"].get("belly", ""), None),
        "target": tg["target"].get(m.get("target", "person_in_water")),
        "targets": tg["target"],
        "johnson": tg["johnson"],
    })


def payload_kg(p) -> float:
    """What the cameras weigh: the gimbal, or the fore/aft pair, belly camera and mount."""
    pl = p.payload
    if pl.layout == "dual":
        return 2 * p.camera.mass_kg + (p.belly.mass_kg if p.belly else 0.0) + pl.mount_kg
    return p.camera.mass_kg


def payload_w(p) -> float:
    pl = p.payload
    if pl.layout == "dual":
        return 2 * p.camera.power_w[1] + (p.belly.power_w[1] if p.belly else 0.0)
    return p.camera.power_w[1]
