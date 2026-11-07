# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.5 km of track planned |
| Take-off mass | 1.60 kg (battery 0.26, shell 0.14, spar 0.022, fixed 1.18) |
| Span / area / aspect ratio | 1.20 m / 0.161 m² / 8.9 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.5 m/s, 0.59, 6.5 |
| Stall speed (sea level) | 11.8 m/s (limit 12) |
| Task power / endurance | 90 W / 28 min |
| Mission time estimate (+20% reserve) | 23 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.58 | 0.24 | 34 / 31 | 90% | 20 |
| 2 | 1.09 | 1.60 | 0.26 | 34 / 32 | 90% | 19 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.2 min after launch |
| Pod reached | 90% (goal 90%); goal at 23.5 min |
| Time on task | 19.3 min |
| Search plan | 32 m track spacing, effective sweep width 99 m, 2 pattern pass(es) |
| Flight time / distance | 23.8 min / 18.9 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 87 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

