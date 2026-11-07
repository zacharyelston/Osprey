# Recon escort-flanks: Watch the beams for 45 min, circling the boat at 1.5 km as it sails

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission escort-flanks`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | escort, 48.6 km of track planned |
| Take-off mass | 1.98 kg (battery 0.60, shell 0.21, spar 0.027, fixed 1.14) |
| Span / area / aspect ratio | 1.25 m / 0.232 m² / 6.8 |
| Root / tip chord | 44.1 / 13.0 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.6 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.2 m/s, 0.47, 8.1 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 102 W / 55 min |
| Mission time estimate (+20% reserve) | 46 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.40 | 0.93 | 79 / 120 | 100% | 45 |
| 2 | 0.66 | 2.00 | 0.59 | 78 / 116 | 100% | 45 |
| 3 | 0.67 | 1.98 | 0.60 | 78 / 115 | 100% | 45 |
| 4 | 0.67 | 1.98 | 0.60 | 79 / 116 | 100% | 45 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 0.0 min after launch |
| Time on station reached | 100% (goal 100%); goal at 45.0 min |
| Time on task | 45.0 min |
| Escort | 45 min circling the boat at 1.5 km; watches the beams out to 6.7 km for a sailboat 30ft |
| Flight time / distance | 46.2 min / 40.1 km |
| Battery left at recovery | 16% |
| Mean power, max bank | 102 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

