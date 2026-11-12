"""The Trident in Blender: export a sized layout's sealed bodies and numbers, and have Blender build the scene.

The sealed bodies (the envelope, the wing panels, any float-feet) go across exactly as trident.meshes gives them,
the same meshes the flotation and MuJoCo runs use; blender/build_trident.py draws the rest from the numbers.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

from osprey import trident

SCRIPT = Path(__file__).parent / "blender" / "build_trident.py"
MAC_APP = Path("/Applications/Blender.app/Contents/MacOS/Blender")


def export(o: Path, layout_name: str = "found", **over) -> dict:
    """Size the layout and write meshes.npz (each body's vertices and faces) and trident.json to `o`."""
    r = trident.size(layout_name, **over)
    c = r["params"]
    o.mkdir(parents=True, exist_ok=True)
    arrs = {}
    for name, (v, f) in trident.meshes(c):
        k = name.replace(" ", "_")
        arrs[f"{k}_v"], arrs[f"{k}_f"] = np.asarray(v, float), np.asarray(f, np.int64)
    np.savez(o / "meshes.npz", **arrs)
    plain = (bool, int, float, str)
    doc = {"layout_name": layout_name, "mass_kg": r["mass_kg"], "zg_m": r["zg_m"],
           "params": {k: v for k, v in c.items() if isinstance(v, plain)},
           "layout": {k: v for k, v in r["layout"].items() if isinstance(v, plain)}}
    (o / "trident.json").write_text(json.dumps(doc, indent=1))
    return doc


def blender() -> str | None:
    """Blender's executable: $BLENDER, then `blender` on the path, then the macOS app."""
    for b in (os.environ.get("BLENDER"), shutil.which("blender"), MAC_APP if MAC_APP.exists() else None):
        if b:
            return str(b)
    return None


def build(o: Path, render: bool = True, exe: str | None = None) -> Path:
    """Run Blender headless on the export in `o`: trident.blend, and with `render` three views as PNGs."""
    exe = exe or blender()
    if not exe:
        raise FileNotFoundError("Blender not found: install it (brew install --cask blender) or set $BLENDER")
    out = o / "trident.blend"
    cmd = [exe, "--background", "--factory-startup", "--python", str(SCRIPT), "--", str(o), str(out)]
    subprocess.run(cmd + ([str(o)] if render else []), check=True, capture_output=True, text=True)
    return out
