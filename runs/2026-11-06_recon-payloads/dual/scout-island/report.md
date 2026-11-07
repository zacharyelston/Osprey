# Recon scout-island: From anchor, map 1.5 km of island shore for a landing, wildlife and hazards

Generated 2026-11-06 at 7f1236d by `uv run osprey recon --mission scout-island`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 13.9 km of track planned |
| Take-off mass | 1.71 kg (battery 0.21, shell 0.14, spar 0.023, fixed 1.34) |
| Span / area / aspect ratio | 1.24 m / 0.165 m² / 9.2 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.60, 6.8 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 96 W / 21 min |
| Mission time estimate (+20% reserve) | 17 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.75 | 0.24 | 28 / 32 | 98% | 14 |
| 2 | 0.87 | 1.71 | 0.21 | 27 / 32 | 98% | 14 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 1.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 16.1 min |
| Time on task | 14.2 min |
| Survey | 8 legs, 173 m swath at 138 m spacing; ground sample 2.1 cm (two side PTZs, turned down) |
| Pixels across each target | person in water 11.7 px, kayak 42.2 px, debris log 18.8 px |
| Flight time / distance | 17.6 min / 15.8 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 94 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

