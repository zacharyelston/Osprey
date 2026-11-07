# Recon scout-island: From anchor, map 1.5 km of island shore for a landing, wildlife and hazards

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission scout-island`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 13.9 km of track planned |
| Take-off mass | 1.60 kg (battery 0.17, shell 0.17, spar 0.020, fixed 1.24) |
| Span / area / aspect ratio | 1.02 m / 0.188 m² / 5.6 |
| Root / tip chord | 44.1 / 12.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 18.0 m/s, 0.43, 7.7 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 88 W / 19 min |
| Mission time estimate (+20% reserve) | 16 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.63 | 0.20 | 23 / 26 | 98% | 13 |
| 2 | 0.89 | 1.60 | 0.17 | 23 / 26 | 98% | 13 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 1.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 15.0 min |
| Time on task | 13.1 min |
| Survey | 8 legs, 173 m swath at 138 m spacing; ground sample 2.1 cm (two side PTZs, turned down) |
| Pixels across each target | person in water 11.7 px, kayak 42.2 px, debris log 18.8 px |
| Flight time / distance | 16.4 min / 15.8 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 85 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

