# Recon sar-convoy: Search 5 km astern while the boat sails on, sea state 3, 15 kn wind

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission sar-convoy`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 3.5 km of track planned |
| Take-off mass | 1.64 kg (battery 0.21, shell 0.17, spar 0.022, fixed 1.24) |
| Span / area / aspect ratio | 1.05 m / 0.192 m² / 5.7 |
| Root / tip chord | 44.1 / 12.4 cm (tip Re 150,588) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 18.0 m/s, 0.42, 8.0 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 87 W / 23 min |
| Mission time estimate (+20% reserve) | 19 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.62 | 0.19 | 28 / 25 | 90% | 3 |
| 2 | 1.10 | 1.64 | 0.21 | 28 / 25 | 90% | 3 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 6.6 min |
| Time on task | 2.6 min |
| Search plan | 221 m track spacing, effective sweep width 674 m, 2 pattern pass(es) |
| Flight time / distance | 21.5 min / 16.1 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 77 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

