# Recon escort-flanks: Watch the beams for 45 min, circling the boat at 1.5 km as it sails

Generated 2026-11-06 at unknown by `uv run osprey recon --mission escort-flanks`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | escort, 48.6 km of track planned |
| Take-off mass | 1.80 kg (battery 0.45, shell 0.19, spar 0.025, fixed 1.14) |
| Span / area / aspect ratio | 1.15 m / 0.211 m² / 6.2 |
| Root / tip chord | 44.1 / 13.2 cm (tip Re 160,359) |
| Spar tube, root / tip | r 4.1 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 18.0 m/s, 0.43, 10.0 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 78 W / 55 min |
| Mission time estimate (+20% reserve) | 46 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 2.02 | 0.64 | 61 / 85 | 100% | 45 |
| 2 | 0.72 | 1.80 | 0.45 | 61 / 82 | 100% | 45 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 0.0 min after launch |
| Time on station reached | 100% (goal 100%); goal at 45.0 min |
| Time on task | 45.0 min |
| Escort | 45 min circling the boat at 1.5 km; watches the beams out to 6.7 km for a sailboat 30ft |
| Flight time / distance | 46.7 min / 43.3 km |
| Battery left at recovery | 15% |
| Mean power, max bank | 78 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

