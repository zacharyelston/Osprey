# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 2.2 km of track planned |
| Take-off mass | 1.61 kg (battery 0.15, shell 0.17, spar 0.019, fixed 1.27) |
| Span / area / aspect ratio | 1.00 m / 0.189 m² / 5.3 |
| Root / tip chord | 44.1 / 15.1 cm (tip Re 284,444) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 27.9 m/s, 0.18, 3.1 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 320 W / 4 min |
| Mission time estimate (+20% reserve) | 3 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.69 | 0.15 | 11 / 18 | 90% | 1 |
| 2 | 0.61 | 1.62 | 0.15 | 12 / 26 | 90% | 1 |
| 3 | 0.50 | 1.61 | 0.15 | 13 / 30 | 90% | 1 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 4.8 min |
| Time on task | 0.8 min |
| Search plan | 195 m track spacing, effective sweep width 596 m, 1 pattern pass(es) |
| Flight time / distance | 6.8 min / 5.7 km |
| Battery left at recovery | 42% |
| Mean power, max bank | 110 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

