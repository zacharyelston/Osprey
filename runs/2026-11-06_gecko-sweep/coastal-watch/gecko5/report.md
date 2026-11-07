# coastal-watch on gecko5: check report

Generated 2026-11-06 at unknown by `uv run osprey calc --scenario coastal-watch --rig gecko5`. Screening-level models; REF inputs in `design/`.

**Result:** 4 FAIL, 21 WARN, 16 PASS


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
| WARN | fwd: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | fwd: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | fwd-down: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | fwd-down: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | port: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | port: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | port-down: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | port-down: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | stbd: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | stbd: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | stbd-down: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | stbd-down: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | aft: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | aft: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |
| WARN | aft-down: blur p95 at 120 mm, 1 ms | 1.01 px | 1 px | worst of 8 horizon bearings |
| WARN | aft-down: pointing jitter rms vs half-FOV at max zoom | 4987 urad | 7732 urad | no fast stage |

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
| info | Group stereo top+aft-down, 16.6 m vertical baseline, at 2 km | +/- 12 m (0.6%) |  | relative orientation 50 urad from the shared horizon; a flexing rig without it: mrad |

## Coverage

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Horizon seen by at least one camera (main+jib, heel 15 deg) | 100.0% | >= 98% |  |
| info | Horizon seen without top | 100.0% |  | what is left when the masthead PTZ is busy in a group |
| info | Horizon seen by two or more cameras | 100.0% |  | where a looking group of 2+ is possible |
| pass | Horizon inside a watch sector, unblocked | 100.0% | >= 98% | every bearing has a camera sweeping it |
| info | Horizon inside two or more watch sectors | 100.0% |  | overlap: a camera can leave its sector for a group while a neighbour keeps the watch |

## Mass aloft

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| **FAIL** | Mass on the mast / masthead equivalent | 17.8 / 11.9 kg | 4 kg eq | equivalent = same heeling moment at the truck; cameras and pod electronics, no brackets or cable |
| info | Of which pod SOCs, IMUs and housings (masthead equivalent) | 3.0 kg |  | 0.92 kg a pod |

## Pod power

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| **FAIL** | top: peak draw at the PoE port | 81.4 W | 71.3 W | over 802.3bt Type 4: needs a second cable or local power |
| pass | fwd: peak draw at the PoE port | 68.1 W | 802.3bt Type 4 | needs 802.3bt Type 4 |
| pass | port: peak draw at the PoE port | 68.1 W | 802.3bt Type 4 | needs 802.3bt Type 4 |
| pass | stbd: peak draw at the PoE port | 68.1 W | 802.3bt Type 4 | needs 802.3bt Type 4 |
| pass | aft: peak draw at the PoE port | 68.1 W | 802.3bt Type 4 | needs 802.3bt Type 4 |
| info | Whole system from the house bank, watch / active | 12.7 / 31.9 A |  | 160 / 402 W at 12.6 V; watch = top working, other PTZs parked |
| **FAIL** | Energy per day underway | 381 Ah | 120 Ah | 20 h watch, 4 h active |

## Pod network

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| info | top: raw sensor rate vs one gigabit link | 5,972 Mb/s | 1,000 Mb/s | 6.0x the link: frames must be encoded, and searched, on the pod |
| pass | top: encoded streams on its link | 40 Mb/s | 700 Mb/s | H.265 at 0.08 bit/px, 30 fps |
| pass | All pods on the switch uplink to the pilot | 199 Mb/s | 700 Mb/s |  |
| pass | top: SOC encoder load | 498 Mpx/s | 750 Mpx/s | Jetson Orin NX 16 GB class (dense INT8) |
| pass | top: detection on full-resolution frames | 3.3 TOPS | 20.0 TOPS | 10 fps, 20 GOP/Mpx, 40% of the NPU |

## Pod timing

| | Check | Value | Limit | Note |
|---|---|---|---|---|
| pass | Shutter sync error x mount rate, p95 (PTP) | 0.18 urad | 50 urad | with software timestamps (2000 us): 367 urad |
| **FAIL** | Mast flex between top and aft pods, p95, no IMU | 846 urad | 50 urad | 2.4 Hz bending; horizon fixes at 5 Hz cannot follow it |
| pass | Relative orientation with pod gyros between horizon fixes | 57 urad | 100 urad | 50 urad horizon fix (+) 28 urad gyro drift over 0.2 s, two pods |
| info | Stereo top+aft at 2 km (16.2 m baseline), no IMU / with | +/- 221 / 14 m |  | what the pod gyros buy a looking group |
| info | Accelerometer-only tilt error at top, p95 | 27.7 deg |  | specific force vs true vertical (roll p95 22 deg): accelerometers alone are not an attitude sensor aloft, the gyros are |

## Figures

![motion.png](motion.png)
![coverage.png](coverage.png)
![reach.png](reach.png)
