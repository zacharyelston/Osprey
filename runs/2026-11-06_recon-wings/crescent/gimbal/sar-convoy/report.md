# Recon sar-convoy: Search 5 km astern while the boat sails on, sea state 3, 15 kn wind

Generated 2026-11-06 at unknown by `uv run osprey recon --mission sar-convoy`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 19.2 km of track planned |
| Take-off mass | 1.56 kg (battery 0.33, shell 0.15, spar 0.029, fixed 1.05) |
| Span / area / aspect ratio | 1.48 m / 0.174 m² / 12.6 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,703) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.53, 10.2 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 63 W / 51 min |
| Mission time estimate (+20% reserve) | 43 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.56 | 0.33 | 46 / 44 | 90% | 16 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 4.0 min after launch |
| Pod reached | 90% (goal 90%); goal at 20.3 min |
| Time on task | 16.4 min |
| Search plan | 40 m track spacing, effective sweep width 123 m, 2 pattern pass(es) |
| Flight time / distance | 48.6 min / 31.9 km |
| Battery left at recovery | 14% |
| Mean power, max bank | 56 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

