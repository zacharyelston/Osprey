# Recon sar-datum: MOB 3 km astern, sea state 3, 15 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-datum`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 2.2 km of track planned |
| Take-off mass | 1.47 kg (battery 0.15, shell 0.16, spar 0.019, fixed 1.14) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.4 |
| Root / tip chord | 44.1 / 13.1 cm (tip Re 260,258) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 29.4 m/s, 0.15, 4.0 |
| Stall speed (sea level) | 11.6 m/s (limit 12) |
| Task power / endurance | 221 W / 7 min |
| Mission time estimate (+20% reserve) | 3 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.47 | 0.15 | 9 / 20 | 90% | 1 |
| 2 | 0.50 | 1.47 | 0.15 | 9 / 19 | 90% | 1 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.1 min after launch |
| Pod reached | 90% (goal 90%); goal at 4.9 min |
| Time on task | 0.8 min |
| Search plan | 195 m track spacing, effective sweep width 596 m, 1 pattern pass(es) |
| Flight time / distance | 6.9 min / 5.7 km |
| Battery left at recovery | 63% |
| Mean power, max bank | 78 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

