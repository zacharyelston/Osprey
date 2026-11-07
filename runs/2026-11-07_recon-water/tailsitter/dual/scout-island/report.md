# Recon scout-island: From anchor, map 1.5 km of island shore for a landing, wildlife and hazards

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission scout-island`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 13.9 km of track planned |
| Take-off mass | 1.72 kg (battery 0.24, shell 0.18, spar 0.021, fixed 1.28) |
| Span / area / aspect ratio | 1.10 m / 0.201 m² / 6.0 |
| Root / tip chord | 44.1 / 12.6 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.7 m/s, 0.44, 6.9 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 111 W / 19 min |
| Mission time estimate (+20% reserve) | 16 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.82 | 0.27 | 29 / 33 | 98% | 14 |
| 2 | 0.88 | 1.73 | 0.24 | 30 / 34 | 98% | 13 |
| 3 | 0.88 | 1.72 | 0.24 | 30 / 34 | 98% | 13 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 1.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 15.2 min |
| Time on task | 13.3 min |
| Survey | 8 legs, 173 m swath at 138 m spacing; ground sample 2.1 cm (two side PTZs, turned down) |
| Pixels across each target | person in water 11.7 px, kayak 42.2 px, debris log 18.8 px |
| Flight time / distance | 16.6 min / 15.8 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 107 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

