# Recon escort-flanks: Watch the beams for 45 min, circling the boat at 1.5 km as it sails

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission escort-flanks`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | escort, 48.6 km of track planned |
| Take-off mass | 2.13 kg (battery 0.59, shell 0.18, spar 0.028, fixed 1.34) |
| Span / area / aspect ratio | 1.54 m / 0.206 m² / 11.5 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.1 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.60, 8.1 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 99 W / 57 min |
| Mission time estimate (+20% reserve) | 47 min |
| Printed panels (220 x 220 x 250 mm bed) | 8, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.51 | 0.92 | 81 / 123 | 100% | 45 |
| 2 | 0.66 | 2.13 | 0.59 | 78 / 119 | 100% | 45 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 0.0 min after launch |
| Time on station reached | 100% (goal 100%); goal at 45.0 min |
| Time on task | 45.0 min |
| Escort | 45 min circling the boat at 1.5 km; watches the beams out to 6.7 km for a sailboat 30ft |
| Flight time / distance | 47.1 min / 39.1 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 100 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

