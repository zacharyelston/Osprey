# Recon inspect-vessel: Identify a vessel 5 km off on a crossing course, from a 200 m standoff

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission inspect-vessel`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | inspect, 2.5 km of track planned |
| Take-off mass | 1.51 kg (battery 0.15, shell 0.14, spar 0.027, fixed 1.19) |
| Span / area / aspect ratio | 1.40 m / 0.168 m² / 11.7 |
| Root / tip chord | 14.3 / 13.2 cm (tip Re 203,966) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 22.9 m/s, 0.28, 4.7 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 152 W / 9 min |
| Mission time estimate (+20% reserve) | 7 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.53 | 0.16 | 14 / 22 | 100% | 4 |
| 2 | 0.65 | 1.51 | 0.15 | 15 / 23 | 100% | 3 |
| 3 | 0.63 | 1.51 | 0.15 | 17 / 32 | 100% | 2 |
| 4 | 0.52 | 1.51 | 0.15 | 16 / 29 | 100% | 2 |
| 5 | 0.54 | 1.51 | 0.15 | 15 / 25 | 100% | 3 |
| 6 | 0.60 | 1.51 | 0.15 | 16 / 29 | 100% | 2 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 3.2 min after launch |
| Orbit done reached | 100% (goal 100%); goal at 5.2 min |
| Time on task | 2.0 min |
| Inspection | 200 m standoff (207 m slant); 2.1 mm focal needed of 30 mm (gimbal); 37 px across; resolves it |
| Flight time / distance | 12.4 min / 9.8 km |
| Battery left at recovery | 34% |
| Mean power, max bank | 76 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

