# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 2.2 km of track planned |
| Take-off mass | 1.69 kg (battery 0.15, shell 0.16, spar 0.027, fixed 1.35) |
| Span / area / aspect ratio | 1.40 m / 0.188 m² / 10.4 |
| Root / tip chord | 11.7 / 11.5 cm (tip Re 181,317) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 23.4 m/s, 0.27, 4.9 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 169 W / 9 min |
| Mission time estimate (+20% reserve) | 3 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.69 | 0.15 | 10 / 20 | 90% | 1 |
| 2 | 0.50 | 1.69 | 0.15 | 9 / 19 | 90% | 1 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 5.0 min |
| Time on task | 1.0 min |
| Search plan | 195 m track spacing, effective sweep width 596 m, 1 pattern pass(es) |
| Flight time / distance | 6.9 min / 5.6 km |
| Battery left at recovery | 61% |
| Mean power, max bank | 82 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

