"""The Rust sims (sim/) against what the Python sims they replaced gave on the kept designs."""

import json

import pytest

from sim_cases import REFERENCE, cases


def _close(a, b, path):
    if isinstance(a, float) and isinstance(b, float):
        assert b == pytest.approx(a, rel=1e-9, abs=1e-12), path
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _close(x, y, f"{path}[{i}]")
    else:
        assert a == b, path


def test_rust_sims_match_the_python_reference():
    ref = json.loads(REFERENCE.read_text())
    new = cases()
    assert sorted(new) == sorted(ref)
    for k, fields in ref.items():
        for f, a in fields.items():
            _close(a, new[k][f], f"{k}.{f}")
