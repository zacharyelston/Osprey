# Recon scout-anchorage: Scout an anchorage 8 km ahead: image the bay for moorings, rocks and debris

Generated 2026-11-07 at cc958a0 by `uv run osprey recon --mission scout-anchorage`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 6.1 km of track planned |
| Take-off mass | 1.72 kg (battery 0.24, shell 0.18, spar 0.021, fixed 1.28) |
| Span / area / aspect ratio | 1.10 m / 0.202 m² / 6.0 |
| Root / tip chord | 44.1 / 12.8 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.3 m/s, 0.46, 7.2 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 105 W / 20 min |
| Mission time estimate (+20% reserve) | 17 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.90 | 0.34 | 31 / 43 | 98% | 6 |
| 2 | 0.72 | 1.75 | 0.25 | 30 / 43 | 98% | 6 |
| 3 | 0.71 | 1.72 | 0.24 | 30 / 42 | 98% | 6 |
| 4 | 0.71 | 1.72 | 0.24 | 30 / 42 | 98% | 6 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 6.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 12.9 min |
| Time on task | 6.0 min |
| Survey | 6 legs, 141 m swath at 106 m spacing; ground sample 1.7 cm (two side PTZs, turned down) |
| Pixels across each target | lobster buoy 17.2 px, debris log 22.9 px, kayak 51.6 px |
| Flight time / distance | 19.9 min / 17.9 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 91 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

