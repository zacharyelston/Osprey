# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.5 km of track planned |
| Take-off mass | 1.39 kg (battery 0.17, shell 0.14, spar 0.027, fixed 1.05) |
| Span / area / aspect ratio | 1.40 m / 0.165 m² / 11.9 |
| Root / tip chord | 13.8 / 13.8 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.1 m/s, 0.53, 9.8 |
| Stall speed (sea level) | 11.6 m/s (limit 12) |
| Task power / endurance | 58 W / 29 min |
| Mission time estimate (+20% reserve) | 24 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.38 | 0.16 | 23 / 21 | 90% | 20 |
| 2 | 1.10 | 1.39 | 0.17 | 23 / 21 | 90% | 20 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.2 min after launch |
| Pod reached | 90% (goal 90%); goal at 24.2 min |
| Time on task | 20.0 min |
| Search plan | 32 m track spacing, effective sweep width 99 m, 2 pattern pass(es) |
| Flight time / distance | 24.5 min / 18.9 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 57 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

