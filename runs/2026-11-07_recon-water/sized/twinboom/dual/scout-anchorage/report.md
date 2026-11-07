# Recon scout-anchorage: Scout an anchorage 8 km ahead: image the bay for moorings, rocks and debris

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission scout-anchorage`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 6.1 km of track planned |
| Take-off mass | 1.87 kg (battery 0.23, shell 0.16, spar 0.025, fixed 1.46) |
| Span / area / aspect ratio | 1.36 m / 0.181 m² / 10.1 |
| Root / tip chord | 13.4 / 13.4 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.6 m/s, 0.60, 6.6 |
| Stall speed (sea level) | 12.0 m/s (limit 12) |
| Task power / endurance | 106 W / 21 min |
| Mission time estimate (+20% reserve) | 18 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.99 | 0.33 | 31 / 45 | 98% | 6 |
| 2 | 0.70 | 1.87 | 0.23 | 31 / 44 | 98% | 6 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 6.9 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 13.1 min |
| Time on task | 6.2 min |
| Survey | 6 legs, 141 m swath at 106 m spacing; ground sample 1.7 cm (two side PTZs, turned down) |
| Pixels across each target | lobster buoy 17.2 px, debris log 22.9 px, kayak 51.6 px |
| Flight time / distance | 20.7 min / 17.7 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 89 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

