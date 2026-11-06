# coastal-watch on mast5-spreaders: check report

Generated 2026-11-06 at unknown by `uv run osprey calc --scenario coastal-watch --rig mast5-spreaders`. Screening-level models; REF inputs in `design/`.

**Result:** 0 FAIL, 12 WARN, 5 PASS


## Motion

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Roll about the 15 deg heel, rms / max | 4.4 / 17.4 deg |  | ss4, Hs 1.9 m, Tp 7.0 s, waves 60 deg off the bow |
| info | Pitch rms / max | 1.4 / 5.1 deg |  |  |
| info | Angular rate at the mounts, p95 / max | 10.5 / 20.2 deg/s |  | the same for every camera on a rigid hull |
| WARN | Acceleration at top (18.9 m), p95 | 0.54 g | 0.5 g | sets the mount, connector and gimbal-motor ratings |
| info | Speed of top through the air, p95 | 3.5 m/s |  | parallax for near targets; adds to apparent wind on the housing |

## Stabilization

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | top: blur p95 at 200 mm, 1 ms | 0.03 px | 1 px | worst of 8 horizon bearings |
| pass | top: pointing jitter rms vs half-FOV at max zoom | 18 urad | 6399 urad | inner stage saturated 0% of the time |
| WARN | fwd: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | fwd: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | port: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | port: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | stbd: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | stbd: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | aft: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | aft: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |

## Reach

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| WARN | Detect person in water | 792 m (top, waves) | >= 1,000 m | same camera at deck height (2.5 m): 100 m |
| pass | Detect lobster buoy | 1,178 m (top, waves) | >= 500 m | same camera at deck height (2.5 m): 143 m |
| pass | Detect sailboat 30ft | 11,487 m (top, atmosphere) | >= 8,000 m | same camera at deck height (2.5 m): 11,487 m |
| WARN | Detect ship | 11,487 m (top, atmosphere) | >= 15,000 m | same camera at deck height (2.5 m): 11,487 m |

## Ranging

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Horizon-dip range, top, at 1 km | +/- 25 m (2.5%) |  | refraction bias 3 m for dk = 0.04 |
| info | Horizon-dip range, top, at 2 km | +/- 51 m (2.6%) |  | refraction bias 10 m for dk = 0.04 |
| info | Horizon-dip range, top, at 5 km | +/- 138 m (2.8%) |  | refraction bias 54 m for dk = 0.04 |
| info | Group stereo top+aft, 16.2 m vertical baseline, at 2 km | +/- 12 m (0.6%) |  | relative orientation 50 urad from the shared horizon; a flexing rig without it: mrad |

## Coverage

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Horizon seen by at least one camera (main+jib, heel 15 deg) | 100.0% | >= 98% |  |
| info | Horizon seen without top | 100.0% |  | what is left when the masthead PTZ is busy in a group |
| info | Horizon seen by two or more cameras | 100.0% |  | where a looking group of 2+ is possible |

## Mass aloft

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| WARN | Camera mass on the mast / masthead equivalent | 7.2 / 5.1 kg | 4 kg eq | equivalent = same heeling moment at the truck; cameras only, no brackets or cable |

## Figures

![motion.png](motion.png)
![coverage.png](coverage.png)
![reach.png](reach.png)
