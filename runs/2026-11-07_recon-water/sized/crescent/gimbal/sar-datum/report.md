# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.5 km of track planned |
| Take-off mass | 1.57 kg (battery 0.20, shell 0.15, spar 0.028, fixed 1.19) |
| Span / area / aspect ratio | 1.45 m / 0.175 m² / 12.0 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.6 m/s, 0.53, 8.7 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 71 W / 28 min |
| Mission time estimate (+20% reserve) | 23 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.55 | 0.19 | 27 / 25 | 90% | 19 |
| 2 | 1.09 | 1.57 | 0.20 | 27 / 25 | 90% | 19 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 23.2 min |
| Time on task | 19.2 min |
| Search plan | 32 m track spacing, effective sweep width 99 m, 2 pattern pass(es) |
| Flight time / distance | 23.6 min / 19.0 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 69 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

