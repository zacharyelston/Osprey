# Recon sar-convoy: Search 5 km astern while the boat sails on, sea state 3, 15 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-convoy`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 19.2 km of track planned |
| Take-off mass | 1.48 kg (battery 0.31, shell 0.16, spar 0.022, fixed 0.98) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.4 |
| Root / tip chord | 44.1 / 13.1 cm (tip Re 158,185) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.9 m/s, 0.41, 9.0 |
| Stall speed (sea level) | 11.7 m/s (limit 12) |
| Task power / endurance | 69 W / 44 min |
| Mission time estimate (+20% reserve) | 36 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.49 | 0.33 | 42 / 44 | 90% | 14 |
| 2 | 0.96 | 1.48 | 0.31 | 42 / 44 | 90% | 14 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.1 min after launch |
| Pod reached | 90% (goal 90%); goal at 18.4 min |
| Time on task | 14.4 min |
| Search plan | 40 m track spacing, effective sweep width 123 m, 2 pattern pass(es) |
| Flight time / distance | 39.2 min / 30.2 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 64 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

