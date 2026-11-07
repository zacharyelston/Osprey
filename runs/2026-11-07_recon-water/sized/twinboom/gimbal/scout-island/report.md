# Recon scout-island: From anchor, map 1.5 km of island shore for a landing, wildlife and hazards

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission scout-island`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 25.3 km of track planned |
| Take-off mass | 1.84 kg (battery 0.36, shell 0.15, spar 0.024, fixed 1.30) |
| Span / area / aspect ratio | 1.33 m / 0.178 m² / 10.0 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.7 m/s, 0.60, 6.5 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 101 W / 34 min |
| Mission time estimate (+20% reserve) | 29 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.89 | 0.41 | 48 / 54 | 98% | 26 |
| 2 | 0.89 | 1.84 | 0.36 | 48 / 55 | 98% | 26 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 1.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 27.4 min |
| Time on task | 25.5 min |
| Survey | 15 legs, 86 m swath at 69 m spacing; ground sample 2.1 cm (gimbal) |
| Pixels across each target | person in water 11.7 px, kayak 42.2 px, debris log 18.8 px |
| Flight time / distance | 29.2 min / 26.3 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 99 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

