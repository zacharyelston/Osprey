# Recon scout-anchorage: Scout an anchorage 8 km ahead: image the bay for moorings, rocks and debris

Generated 2026-11-07 at d01834a by `uv run osprey recon --mission scout-anchorage`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 10.7 km of track planned |
| Take-off mass | 1.46 kg (battery 0.20, shell 0.16, spar 0.019, fixed 1.08) |
| Span / area / aspect ratio | 1.00 m / 0.184 m² / 5.4 |
| Root / tip chord | 44.1 / 12.8 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 17.4 m/s, 0.43, 7.5 |
| Stall speed (sea level) | 11.6 m/s (limit 12) |
| Task power / endurance | 77 W / 24 min |
| Mission time estimate (+20% reserve) | 20 min |
| Printed panels (220 x 220 x 250 mm bed) | 0, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.53 | 0.27 | 26 / 36 | 98% | 10 |
| 2 | 0.73 | 1.46 | 0.20 | 26 / 36 | 98% | 10 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.1 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 17.0 min |
| Time on task | 9.9 min |
| Survey | 11 legs, 71 m swath at 53 m spacing; ground sample 1.7 cm (gimbal) |
| Pixels across each target | lobster buoy 17.2 px, debris log 22.9 px, kayak 51.6 px |
| Flight time / distance | 23.0 min / 21.2 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 68 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

