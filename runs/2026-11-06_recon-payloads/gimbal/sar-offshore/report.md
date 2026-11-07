# Recon sar-offshore: MOB 10 km astern, sea state 4, 20 kn wind

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission sar-offshore`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | search, 63.8 km of track planned |
| Take-off mass | 2.73 kg (battery 1.27, shell 0.24, spar 0.044, fixed 1.18) |
| Span / area / aspect ratio | 2.02 m / 0.278 m² / 14.7 |
| Root / tip chord | 13.7 / 13.7 cm (tip Re 150,000) |
| Spar tube, root / tip | r 5.4 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.2 m/s, 0.60, 10.1 |
| Stall speed (sea level) | 11.7 m/s (limit 12) |
| Task power / endurance | 96 W / 127 min |
| Mission time estimate (+20% reserve) | 106 min |
| Printed panels (220 x 220 x 250 mm bed) | 10, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.73 | 1.27 | 170 / 169 | 90% | 99 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.5 min after launch |
| Pod reached | 90% (goal 90%); goal at 106.0 min |
| Time on task | 98.5 min |
| Search plan | 49 m track spacing, effective sweep width 148 m, 2 pattern pass(es) |
| Flight time / distance | 107.4 min / 73.2 km |
| Battery left at recovery | 16% |
| Mean power, max bank | 95 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

