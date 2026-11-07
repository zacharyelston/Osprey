# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.5 km of track planned |
| Take-off mass | 1.32 kg (battery 0.16, shell 0.16, spar 0.020, fixed 0.98) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.4 |
| Root / tip chord | 44.1 / 13.1 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.9 m/s, 0.41, 8.7 |
| Stall speed (sea level) | 11.0 m/s (limit 12) |
| Task power / endurance | 62 W / 25 min |
| Mission time estimate (+20% reserve) | 21 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.32 | 0.16 | 21 / 21 | 90% | 16 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.6 min after launch |
| Pod reached | 90% (goal 90%); goal at 20.3 min |
| Time on task | 15.7 min |
| Search plan | 32 m track spacing, effective sweep width 99 m, 1 pattern pass(es) |
| Flight time / distance | 21.2 min / 16.8 km |
| Battery left at recovery | 18% |
| Mean power, max bank | 59 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

