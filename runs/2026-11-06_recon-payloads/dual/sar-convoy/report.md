# Recon sar-convoy: Search 5 km astern while the boat sails on, sea state 3, 15 kn wind

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission sar-convoy`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 3.5 km of track planned |
| Take-off mass | 1.80 kg (battery 0.28, shell 0.15, spar 0.024, fixed 1.34) |
| Span / area / aspect ratio | 1.30 m / 0.174 m² / 9.7 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.60, 7.1 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 97 W / 28 min |
| Mission time estimate (+20% reserve) | 23 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.75 | 0.24 | 38 / 32 | 90% | 3 |
| 2 | 1.19 | 1.80 | 0.28 | 38 / 32 | 90% | 3 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 6.9 min |
| Time on task | 2.9 min |
| Search plan | 221 m track spacing, effective sweep width 674 m, 2 pattern pass(es) |
| Flight time / distance | 27.5 min / 17.2 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 83 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

