# Recon sar-offshore: MOB 10 km astern, sea state 4, 20 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-offshore`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 13.7 km of track planned |
| Take-off mass | 1.64 kg (battery 0.24, shell 0.16, spar 0.030, fixed 1.21) |
| Span / area / aspect ratio | 1.54 m / 0.182 m² / 13.1 |
| Root / tip chord | 14.3 / 13.5 cm (tip Re 151,358) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.54, 10.5 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 68 W / 34 min |
| Mission time estimate (+20% reserve) | 29 min |
| Printed panels (220 x 220 x 250 mm bed) | 8, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.85 | 0.43 | 33 / 57 | 90% | 13 |
| 2 | 0.59 | 1.64 | 0.24 | 32 / 55 | 90% | 13 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.3 min after launch |
| Pod reached | 90% (goal 90%); goal at 20.1 min |
| Time on task | 12.8 min |
| Search plan | 226 m track spacing, effective sweep width 688 m, 2 pattern pass(es) |
| Flight time / distance | 28.5 min / 22.9 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 68 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

