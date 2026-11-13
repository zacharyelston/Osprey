"""The Trident in Blender (trident_blend.py, blender/build_trident.py)."""

import json
import subprocess

import numpy as np
import pytest

from osprey import trident
from osprey import trident_blend as tb


def test_the_export_carries_the_models_sealed_bodies_and_numbers_unchanged(tmp_path):
    doc = tb.export(tmp_path)
    c = trident.params("found")
    want = dict(trident.meshes(trident.size("found")["params"]))
    got = np.load(tmp_path / "meshes.npz")
    assert {k[:-2].replace("_", " ") for k in got.files} == set(want)
    for name, (v, f) in want.items():
        k = name.replace(" ", "_")
        assert np.array_equal(got[f"{k}_v"], v) and np.array_equal(got[f"{k}_f"], f)
    back = json.loads((tmp_path / "trident.json").read_text())
    assert back == doc and back["params"]["prop_d_m"] == c["prop_d_m"]
    assert back["layout"]["across_m"] == pytest.approx(2 * back["layout"]["arm"] + c["prop_d_m"])


@pytest.mark.skipif(tb.blender() is None, reason="Blender isn't installed")
def test_blender_builds_it_to_the_models_dimensions(tmp_path):
    doc = tb.export(tmp_path)
    blend = tb.build(tmp_path, render=False)
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import bpy, json, math, sys\n"
        "from mathutils import Vector\n"
        "obs = bpy.data.objects\n"
        "pts = lambda n: [o.matrix_world @ Vector(c) for o in obs if o.type == 'MESH' and o.name.startswith(n)"
        " for c in o.bound_box]\n"
        "disc = [math.hypot(*(o.matrix_world @ v.co)[:2]) for o in obs if o.name.endswith('disc') for v in o.data.vertices]\n"
        "print('PROBE' + json.dumps({'nose': max(p.z for p in pts('envelope')), 'tip': max(p.x for p in pts('wing 1')),"
        " 'pads': min(p.z for p in pts('pad')), 'props': max(disc)}))\n")
    run = subprocess.run([tb.blender(), "--background", str(blend), "--python", str(probe)],
                         capture_output=True, text=True, check=True)
    got = json.loads(next(ln for ln in run.stdout.splitlines() if ln.startswith("PROBE"))[5:])
    lay, c = doc["layout"], doc["params"]
    assert got["nose"] == pytest.approx(lay["z_nose"], abs=1e-3)
    assert got["tip"] == pytest.approx(lay["r_tip"], abs=1e-3)
    assert got["pads"] == pytest.approx(c["foot_bottom_m"], abs=1e-3)
    assert got["props"] == pytest.approx(lay["arm"] + c["prop_d_m"] / 2, abs=1e-3)
