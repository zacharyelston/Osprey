# mob on spreader-pairs: check report

Generated 2026-11-06 at unknown by `uv run osprey calc --scenario mob --rig spreader-pairs`. Screening-level models; REF inputs in `design/`.

**Result:** 4 FAIL, 3 WARN, 38 PASS


## Motion

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Roll about the 8 deg heel, rms / max | 1.6 / 4.3 deg |  | ss3, Hs 0.9 m, Tp 5.0 s, waves 120 deg off the bow |
| info | Pitch rms / max | 1.0 / 2.9 deg |  |  |
| info | Angular rate at the mounts, p95 / max | 5.7 / 9.4 deg/s |  | the same for every camera on a rigid hull |
| pass | Acceleration at top (18.9 m), p95 | 0.43 g | 0.5 g | sets the mount, connector and gimbal-motor ratings |
| info | Speed of top through the air, p95 | 1.9 m/s |  | parallax for near targets; adds to apparent wind on the housing |

## Stabilization

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | top: blur p95 at 200 mm, 1 ms | 0.01 px | 1 px | worst of 8 horizon bearings |
| pass | top: pointing jitter rms vs half-FOV at max zoom | 16 urad | 6399 urad | inner stage saturated 0% of the time |
| pass | top-down: blur p95 at 120 mm, 1 ms | 0.82 px | 1 px | worst of 8 horizon bearings |
| pass | top-down: pointing jitter rms vs half-FOV at max zoom | 2563 urad | 7732 urad | no fast stage |
| pass | lo-port-fwd: blur p95 at 4 mm, 1 ms | 0.19 px | 1 px | worst of 8 horizon bearings |
| pass | lo-port-fwd: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 254998 urad | no fast stage |
| pass | lo-port-aft: blur p95 at 4 mm, 1 ms | 0.19 px | 1 px | worst of 8 horizon bearings |
| pass | lo-port-aft: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 254998 urad | no fast stage |
| pass | lo-stbd-fwd: blur p95 at 4 mm, 1 ms | 0.19 px | 1 px | worst of 8 horizon bearings |
| pass | lo-stbd-fwd: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 254998 urad | no fast stage |
| pass | lo-stbd-aft: blur p95 at 4 mm, 1 ms | 0.19 px | 1 px | worst of 8 horizon bearings |
| pass | lo-stbd-aft: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 254998 urad | no fast stage |
| pass | hi-port-fwd: blur p95 at 8 mm, 1 ms | 0.37 px | 1 px | worst of 8 horizon bearings |
| pass | hi-port-fwd: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 149173 urad | no fast stage |
| pass | hi-port-aft: blur p95 at 8 mm, 1 ms | 0.37 px | 1 px | worst of 8 horizon bearings |
| pass | hi-port-aft: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 149173 urad | no fast stage |
| pass | hi-stbd-fwd: blur p95 at 8 mm, 1 ms | 0.37 px | 1 px | worst of 8 horizon bearings |
| pass | hi-stbd-fwd: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 149173 urad | no fast stage |
| pass | hi-stbd-aft: blur p95 at 8 mm, 1 ms | 0.37 px | 1 px | worst of 8 horizon bearings |
| pass | hi-stbd-aft: pointing jitter rms vs half-FOV at max zoom | 45360 urad | 149173 urad | no fast stage |

## Reach

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Detect person in water | 2,044 m (top, waves) | >= 1,000 m | same camera at deck height (2.5 m): 249 m |

## Ranging

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Horizon-dip range, top, at 1 km | +/- 12 m (1.2%) |  | refraction bias 3 m for dk = 0.04 |
| info | Horizon-dip range, top, at 2 km | +/- 24 m (1.2%) |  | refraction bias 10 m for dk = 0.04 |
| info | Horizon-dip range, top, at 5 km | +/- 65 m (1.3%) |  | refraction bias 54 m for dk = 0.04 |
| info | Group stereo top+lo-port-fwd, 11.4 m vertical baseline, at 2 km | +/- 76 m (3.8%) |  | relative orientation 50 urad from the shared horizon; a flexing rig without it: mrad |

## Coverage

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Horizon seen by at least one camera (main, heel 8 deg) | 100.0% | >= 95% |  |
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
| pass | Shutter sync error x mount rate, p95 (PTP) | 0.10 urad | 50 urad | with software timestamps (2000 us): 200 urad |

## Pairs

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | lo pair (lo-port+lo-stbd): baseline and mast flex between them | 2.70 m, 0 urad |  | same height: the mast's fore-aft bending moves both together |
| pass | lo pair (lo-port+lo-stbd): stereo range at 30 m, camera clocks / hardware sync | +/- 0.10 / 0.07 m | 1.5 m | 2 ms between frames at 5.7 deg/s costs 200 urad; hardware-synced shutters 0.1 urad |
| WARN | lo pair (lo-port+lo-stbd): stereo range at 200 m, camera clocks / hardware sync | +/- 4.38 / 3.23 m | 10 m | 2 ms between frames at 5.7 deg/s costs 200 urad; hardware-synced shutters 0.1 urad |
| **FAIL** | lo pair (lo-port+lo-stbd): stereo range at 1000 m, camera clocks / hardware sync | +/- 109.51 / 80.72 m | 50 m | 2 ms between frames at 5.7 deg/s costs 200 urad; hardware-synced shutters 0.1 urad |
| info | hi pair (hi-port+hi-stbd): baseline and mast flex between them | 1.90 m, 0 urad |  | same height: the mast's fore-aft bending moves both together |
| pass | hi pair (hi-port+hi-stbd): stereo range at 30 m, camera clocks / hardware sync | +/- 0.11 / 0.06 m | 1.5 m | 2 ms between frames at 5.7 deg/s costs 200 urad; hardware-synced shutters 0.1 urad |
| WARN | hi pair (hi-port+hi-stbd): stereo range at 200 m, camera clocks / hardware sync | +/- 4.88 / 2.47 m | 10 m | 2 ms between frames at 5.7 deg/s costs 200 urad; hardware-synced shutters 0.1 urad |
| **FAIL** | hi pair (hi-port+hi-stbd): stereo range at 1000 m, camera clocks / hardware sync | +/- 121.93 / 61.72 m | 50 m | 2 ms between frames at 5.7 deg/s costs 200 urad; hardware-synced shutters 0.1 urad |

## Pod timing

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | Accelerometer-only tilt error at top, p95 | 22.9 deg |  | specific force vs true vertical (roll p95 11 deg): accelerometers alone are not an attitude sensor aloft, the gyros are |

## Figures

![motion.png](motion.png)
![coverage.png](coverage.png)
![reach.png](reach.png)
