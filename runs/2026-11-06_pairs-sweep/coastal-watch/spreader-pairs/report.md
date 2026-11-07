# coastal-watch on spreader-pairs: check report

Generated 2026-11-06 at unknown by `uv run osprey calc --scenario coastal-watch --rig spreader-pairs`. Screening-level models; REF inputs in `design/`.

**Result:** 4 FAIL, 12 WARN, 32 PASS


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
| WARN | top-down: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | top-down: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| pass | lo-port-fwd: blur p95 at 4 mm, 1 ms | 0.36 px | 1 px | worst of 8 horizon bearings |
| pass | lo-port-fwd: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 254998 urad | no fast stage |
| pass | lo-port-aft: blur p95 at 4 mm, 1 ms | 0.36 px | 1 px | worst of 8 horizon bearings |
| pass | lo-port-aft: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 254998 urad | no fast stage |
| pass | lo-stbd-fwd: blur p95 at 4 mm, 1 ms | 0.36 px | 1 px | worst of 8 horizon bearings |
| pass | lo-stbd-fwd: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 254998 urad | no fast stage |
| pass | lo-stbd-aft: blur p95 at 4 mm, 1 ms | 0.36 px | 1 px | worst of 8 horizon bearings |
| pass | lo-stbd-aft: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 254998 urad | no fast stage |
| pass | hi-port-fwd: blur p95 at 8 mm, 1 ms | 0.72 px | 1 px | worst of 8 horizon bearings |
| WARN | hi-port-fwd: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 149173 urad | no fast stage |
| pass | hi-port-aft: blur p95 at 8 mm, 1 ms | 0.72 px | 1 px | worst of 8 horizon bearings |
| WARN | hi-port-aft: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 149173 urad | no fast stage |
| pass | hi-stbd-fwd: blur p95 at 8 mm, 1 ms | 0.72 px | 1 px | worst of 8 horizon bearings |
| WARN | hi-stbd-fwd: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 149173 urad | no fast stage |
| pass | hi-stbd-aft: blur p95 at 8 mm, 1 ms | 0.72 px | 1 px | worst of 8 horizon bearings |
| WARN | hi-stbd-aft: pointing jitter rms vs half-FOV at max zoom | 101334 urad | 149173 urad | no fast stage |

## Reach

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| WARN | Detect person in water | 793 m (top, waves) | >= 1,000 m | same camera at deck height (2.5 m): 100 m |
| pass | Detect lobster buoy | 1,180 m (top, waves) | >= 500 m | same camera at deck height (2.5 m): 143 m |
| pass | Detect sailboat 30ft | 11,487 m (top, atmosphere) | >= 8,000 m | same camera at deck height (2.5 m): 11,487 m |
| WARN | Detect ship | 11,487 m (top, atmosphere) | >= 15,000 m | same camera at deck height (2.5 m): 11,487 m |

## Ranging

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Horizon-dip range, top, at 1 km | +/- 25 m (2.5%) |  | refraction bias 3 m for dk = 0.04 |
| info | Horizon-dip range, top, at 2 km | +/- 51 m (2.5%) |  | refraction bias 10 m for dk = 0.04 |
| info | Horizon-dip range, top, at 5 km | +/- 138 m (2.8%) |  | refraction bias 54 m for dk = 0.04 |
| info | Group stereo top+lo-port-fwd, 11.4 m vertical baseline, at 2 km | +/- 76 m (3.8%) |  | relative orientation 50 urad from the shared horizon; a flexing rig without it: mrad |

## Coverage

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Horizon seen by at least one camera (main+jib, heel 15 deg) | 100.0% | >= 98% |  |
| info | Horizon seen without top | 100.0% |  | what is left when the masthead PTZ is busy in a group |
| info | Horizon seen by two or more cameras | 100.0% |  | where a looking group of 2+ is possible |

## Mass aloft

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| WARN | Mass on the mast / masthead equivalent | 10.3 / 7.7 kg | 4 kg eq | equivalent = same heeling moment at the truck; cameras and pod electronics, no brackets or cable |
| info | Of which pod SOCs, IMUs and housings (masthead equivalent) | 1.7 kg |  | 0.92 kg a pod |

## Pod power

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| **FAIL** | top: peak draw at the PoE port | 81.4 W | 71.3 W | over 802.3bt Type 4: needs a second cable or local power |
| pass | lo-port-fwd: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | lo-port-aft: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | lo-stbd-fwd: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | lo-stbd-aft: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | hi-port-fwd: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | hi-port-aft: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | hi-stbd-fwd: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| pass | hi-stbd-aft: peak draw at the PoE port | 8.0 W | 802.3af | needs 802.3af |
| info | Whole system from the house bank, watch / active | 10.3 / 13.1 A |  | 130 / 165 W at 12.6 V; watch = top working, other PTZs parked |
| **FAIL** | Energy per day underway | 259 Ah | 120 Ah | 20 h watch, 4 h active |

## Pod network

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | 4 mounts without a pod computer | lo-port, lo-stbd, hi-port, hi-stbd |  | each camera encodes itself: detection runs on compressed streams at the pilot computer |
| info | top: raw sensor rate vs one gigabit link | 5,972 Mb/s | 1,000 Mb/s | 6.0x the link: frames must be encoded, and searched, on the pod |
| pass | top: encoded streams on its link | 40 Mb/s | 700 Mb/s | H.265 at 0.08 bit/px, 30 fps |
| pass | All pods on the switch uplink to the pilot | 199 Mb/s | 700 Mb/s |  |
| pass | top: SOC encoder load | 498 Mpx/s | 750 Mpx/s | Jetson Orin NX 16 GB class (dense INT8) |
| pass | top: detection on full-resolution frames | 3.3 TOPS | 20.0 TOPS | 10 fps, 20 GOP/Mpx, 40% of the NPU |

## Pod timing

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Shutter sync error x mount rate, p95 (PTP) | 0.18 urad | 50 urad | with software timestamps (2000 us): 367 urad |

## Pairs

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | lo pair (lo-port+lo-stbd): baseline and mast flex between them | 2.70 m, 0 urad |  | same height: the mast's fore-aft bending moves both together |
| pass | lo pair (lo-port+lo-stbd): stereo range at 30 m, camera clocks / hardware sync | +/- 0.14 / 0.07 m | 1.5 m | 2 ms between frames at 10.5 deg/s costs 367 urad; hardware-synced shutters 0.2 urad |
| WARN | lo pair (lo-port+lo-stbd): stereo range at 200 m, camera clocks / hardware sync | +/- 6.32 / 3.23 m | 10 m | 2 ms between frames at 10.5 deg/s costs 367 urad; hardware-synced shutters 0.2 urad |
| **FAIL** | lo pair (lo-port+lo-stbd): stereo range at 1000 m, camera clocks / hardware sync | +/- 158.09 / 80.72 m | 50 m | 2 ms between frames at 10.5 deg/s costs 367 urad; hardware-synced shutters 0.2 urad |
| info | hi pair (hi-port+hi-stbd): baseline and mast flex between them | 1.90 m, 0 urad |  | same height: the mast's fore-aft bending moves both together |
| pass | hi pair (hi-port+hi-stbd): stereo range at 30 m, camera clocks / hardware sync | +/- 0.18 / 0.06 m | 1.5 m | 2 ms between frames at 10.5 deg/s costs 367 urad; hardware-synced shutters 0.2 urad |
| WARN | hi pair (hi-port+hi-stbd): stereo range at 200 m, camera clocks / hardware sync | +/- 8.11 / 2.47 m | 10 m | 2 ms between frames at 10.5 deg/s costs 367 urad; hardware-synced shutters 0.2 urad |
| **FAIL** | hi pair (hi-port+hi-stbd): stereo range at 1000 m, camera clocks / hardware sync | +/- 202.78 / 61.72 m | 50 m | 2 ms between frames at 10.5 deg/s costs 367 urad; hardware-synced shutters 0.2 urad |

## Pod timing

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Accelerometer-only tilt error at top, p95 | 27.7 deg |  | specific force vs true vertical (roll p95 22 deg): accelerometers alone are not an attitude sensor aloft, the gyros are |

## Figures

![motion.png](motion.png)
![coverage.png](coverage.png)
![reach.png](reach.png)
