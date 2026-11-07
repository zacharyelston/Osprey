# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.5 km of track planned |
| Take-off mass | 1.53 kg (battery 0.24, shell 0.16, spar 0.020, fixed 1.11) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.4 |
| Root / tip chord | 44.1 / 12.7 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.4 m/s, 0.44, 6.5 |
| Stall speed (sea level) | 11.9 m/s (limit 12) |
| Task power / endurance | 100 W / 22 min |
| Mission time estimate (+20% reserve) | 18 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.65 | 0.28 | 31 / 35 | 90% | 14 |
| 2 | 0.89 | 1.54 | 0.24 | 30 / 33 | 90% | 14 |
| 3 | 0.90 | 1.53 | 0.24 | 30 / 33 | 90% | 15 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.1 min after launch |
| Pod reached | 90% (goal 90%); goal at 18.7 min |
| Time on task | 14.6 min |
| Search plan | 32 m track spacing, effective sweep width 99 m, 1 pattern pass(es) |
| Flight time / distance | 19.0 min / 16.0 km |
| Battery left at recovery | 16% |
| Mean power, max bank | 95 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

