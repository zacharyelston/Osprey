# Recon escort-flanks: Watch the beams for 45 min, circling the boat at 1.5 km as it sails

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission escort-flanks`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | escort, 48.6 km of track planned |
| Take-off mass | 2.22 kg (battery 0.64, shell 0.23, spar 0.030, fixed 1.32) |
| Span / area / aspect ratio | 1.40 m / 0.260 m² / 7.6 |
| Root / tip chord | 44.1 / 13.2 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.5 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.9 m/s, 0.49, 9.0 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 105 W / 56 min |
| Mission time estimate (+20% reserve) | 47 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.65 | 0.99 | 84 / 128 | 100% | 45 |
| 2 | 0.66 | 2.25 | 0.63 | 82 / 124 | 100% | 45 |
| 3 | 0.66 | 2.22 | 0.64 | 82 / 123 | 100% | 45 |
| 4 | 0.66 | 2.22 | 0.64 | 82 / 123 | 100% | 45 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 0.0 min after launch |
| Time on station reached | 100% (goal 100%); goal at 45.0 min |
| Time on task | 45.0 min |
| Escort | 45 min circling the boat at 1.5 km; watches the beams out to 6.7 km for a sailboat 30ft |
| Flight time / distance | 46.7 min / 39.5 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 105 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

