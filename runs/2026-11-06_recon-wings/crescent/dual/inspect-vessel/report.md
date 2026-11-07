# Recon inspect-vessel: Identify a vessel 5 km off on a crossing course, from a 200 m standoff

Generated 2026-11-06 at unknown by `uv run osprey recon --mission inspect-vessel`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | inspect, 2.5 km of track planned |
| Take-off mass | 1.53 kg (battery 0.15, shell 0.15, spar 0.027, fixed 1.21) |
| Span / area / aspect ratio | 1.40 m / 0.171 m² / 11.5 |
| Root / tip chord | 15.7 / 15.0 cm (tip Re 194,174) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 19.1 m/s, 0.40, 7.7 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 90 W / 16 min |
| Mission time estimate (+20% reserve) | 9 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.54 | 0.15 | 13 / 21 | 100% | 4 |
| 2 | 0.65 | 1.53 | 0.15 | 14 / 22 | 100% | 3 |
| 3 | 0.63 | 1.53 | 0.15 | 14 / 22 | 100% | 3 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 3.2 min after launch |
| Orbit done reached | 100% (goal 100%); goal at 5.9 min |
| Time on task | 2.7 min |
| Inspection | 200 m standoff (207 m slant); 2.1 mm focal needed of 30 mm (inboard PTZ eye); 37 px across; resolves it |
| Flight time / distance | 12.0 min / 9.7 km |
| Battery left at recovery | 42% |
| Mean power, max bank | 70 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

