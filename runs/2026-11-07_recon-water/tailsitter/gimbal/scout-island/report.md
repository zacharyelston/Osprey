# Recon scout-island: From anchor, map 1.5 km of island shore for a landing, wildlife and hazards

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission scout-island`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 25.3 km of track planned |
| Take-off mass | 1.68 kg (battery 0.36, shell 0.18, spar 0.021, fixed 1.12) |
| Span / area / aspect ratio | 1.09 m / 0.200 m² / 5.9 |
| Root / tip chord | 44.1 / 12.9 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.3 m/s, 0.45, 7.1 |
| Stall speed (sea level) | 11.9 m/s (limit 12) |
| Task power / endurance | 100 W / 33 min |
| Mission time estimate (+20% reserve) | 28 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.80 | 0.40 | 46 / 52 | 98% | 25 |
| 2 | 0.90 | 1.68 | 0.36 | 46 / 51 | 98% | 25 |
| 3 | 0.90 | 1.68 | 0.36 | 46 / 51 | 98% | 25 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 1.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 26.5 min |
| Time on task | 24.5 min |
| Survey | 15 legs, 86 m swath at 69 m spacing; ground sample 2.1 cm (gimbal) |
| Pixels across each target | person in water 11.7 px, kayak 42.2 px, debris log 18.8 px |
| Flight time / distance | 28.4 min / 26.5 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 98 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

