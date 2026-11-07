# Recon sar-offshore: MOB 10 km astern, sea state 4, 20 kn wind

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission sar-offshore`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 63.8 km of track planned |
| Take-off mass | 2.96 kg (battery 1.38, shell 0.31, spar 0.053, fixed 1.22) |
| Span / area / aspect ratio | 1.81 m / 0.347 m² / 9.4 |
| Root / tip chord | 44.1 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 7.1 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.50, 11.2 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 106 W / 121 min |
| Mission time estimate (+20% reserve) | 101 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.92 | 1.39 | 178 / 180 | 90% | 93 |
| 2 | 0.99 | 2.96 | 1.38 | 179 / 181 | 90% | 93 |
| 3 | 0.99 | 2.96 | 1.38 | 179 / 181 | 90% | 93 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.3 min after launch |
| Pod reached | 90% (goal 90%); goal at 100.3 min |
| Time on task | 93.0 min |
| Search plan | 49 m track spacing, effective sweep width 148 m, 2 pattern pass(es) |
| Flight time / distance | 101.8 min / 73.1 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 105 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

