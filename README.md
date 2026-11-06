# Osprey: mast-mounted multi-camera vision for sailboats

Models, simulations and synthetic camera data for a masthead vision system:
spotting and inspection from height, plus a look-down view that guides
docking and the AI pilot. See [docs/architecture.md](docs/architecture.md).

Status: screening models with REF inputs. Results are written up as runs land
in [runs/](runs/README.md).

## Quickstart

```bash
uv sync
uv run pytest
uv run osprey calc --scenario coastal-watch           # PASS/WARN/FAIL checks + figures
uv run osprey sim --scenario mob                      # looking-group timeline
uv run osprey render --scenario docking --rig mast5-spreaders   # RGB, depth, class masks, poses
uv run osprey sweep --workers 8                       # every scenario x rig
```

Long sweeps and GPU renders go to the ML hosts:
[docs/remote-simulation.md](docs/remote-simulation.md).

## Layout

| Path | What |
|---|---|
| `design/boat.toml` | Reference 40 ft sloop: hull, mast, sail plan, motion responses |
| `design/sea.toml` | Sea states, refraction, visibility |
| `design/cameras.toml` | Camera classes: long-zoom PTZ, mid-zoom PTZ, fixed wide, interior dome |
| `design/targets.toml` | Target classes and Johnson criteria |
| `design/rigs/` | `mast5` (1 top + 4 around the mast), `mast5-spreaders`, `whole-boat` |
| `design/scenarios/` | `coastal-watch`, `mob`, `docking` |
| `src/osprey/` | `frames`, `motion`, `optics`, `stabilize`, `occlusion`, `rig`, `tasking`, `calcs`, `figures`, `render/scene`, `cli` |
