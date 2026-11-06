"""Load a Recon mission with everything it needs: the airframe, the sea and
atmosphere, the search camera and the target class."""

from __future__ import annotations

from types import SimpleNamespace

from osprey.params import DESIGN, _toml, ns

RECON = DESIGN / "recon"
MISSIONS = tuple(sorted(f.stem for f in (RECON / "missions").glob("*.toml")))


def load(mission: str = "sar-datum") -> SimpleNamespace:
    m = _toml(RECON / "missions" / f"{mission}.toml")["mission"]
    af = _toml(RECON / "airframe.toml")
    sea = _toml(DESIGN / "sea.toml")
    tg = _toml(DESIGN / "targets.toml")
    cams = _toml(DESIGN / "cameras.toml")["camera"]
    return ns({
        **af,
        "mission": m,
        "sea": {**sea["sea"][m["sea_state"]], "state": m["sea_state"]},
        "atmosphere": sea["atmosphere"],
        "camera": cams[af["payload"]["camera"]],
        "target": tg["target"][m["target"]],
        "johnson": tg["johnson"],
    })
