# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 2.2 km of track planned |
| Take-off mass | 1.78 kg (battery 0.15, shell 0.15, spar 0.022, fixed 1.46) |
| Span / area / aspect ratio | 1.20 m / 0.172 m² / 8.4 |
| Root / tip chord | 14.3 / 14.3 cm (tip Re 200,757) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 20.7 m/s, 0.39, 4.4 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 174 W / 8 min |
| Mission time estimate (+20% reserve) | 4 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.78 | 0.15 | 11 / 20 | 90% | 1 |
| 2 | 0.57 | 1.78 | 0.15 | 12 / 23 | 90% | 1 |
| 3 | 0.52 | 1.78 | 0.15 | 12 / 23 | 90% | 1 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 5.2 min |
| Time on task | 1.1 min |
| Search plan | 195 m track spacing, effective sweep width 596 m, 1 pattern pass(es) |
| Flight time / distance | 7.0 min / 5.6 km |
| Battery left at recovery | 50% |
| Mean power, max bank | 101 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

