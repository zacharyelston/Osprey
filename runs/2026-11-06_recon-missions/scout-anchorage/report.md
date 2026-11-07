# Recon scout-anchorage: Scout an anchorage 8 km ahead: image the bay for moorings, rocks and debris

Generated 2026-11-06 at 7c146a0 by `uv run osprey recon --mission scout-anchorage`. Screening-level models; REF inputs in `design/recon/`.

## Sized airframe (OpenMDAO + OpenAeroStruct, SLSQP)

Optimizer converged: **yes**

| Quantity | Value |
|---|---|
| Task | survey, 10.7 km of track planned |
| Take-off mass | 1.58 kg (battery 0.23, shell 0.14, spar 0.022, fixed 1.18) |
| Span / area / aspect ratio | 1.20 m / 0.163 m² / 8.8 |
| Root / tip chord | 13.6 / 13.6 cm (tip Re 150,000) |
| Spar tube, root / tip | r 4.0 / 4.0 mm, wall 0.50 / 0.50 mm |
| Task speed, CL, L/D | 16.4 m/s, 0.58, 6.5 |
| Stall speed (sea level) | 11.6 m/s (limit 12) |
| Task power / endurance | 88 W / 26 min |
| Mission time estimate (+20% reserve) | 21 min |
| Printed panels (220 x 220 x 250 mm bed) | 6, chord fits: yes |

![planform](planform.png)

### Calibrating the mission-time model against the flight sim

Each round sizes the airframe, flies it with an unlimited battery, and scales the optimizer's mission-time model by the energy the flight really used.

| Round | Time factor | Mass (kg) | Battery (kg) | Flown / estimated energy (Wh) | Progress flown | Task flown (min) |
|---|---|---|---|---|---|---|
| 1 | 1.00 | 1.68 | 0.33 | 32 / 44 | 98% | 10 |
| 2 | 0.72 | 1.58 | 0.23 | 31 / 43 | 98% | 11 |

## Flown through the mission (3-DOF point mass)

Outcome: **recovered**; left the task because: goal

| Quantity | Value |
|---|---|
| On scene | 7.1 min after launch |
| Area imaged reached | 98% (goal 98%); goal at 17.7 min |
| Time on task | 10.6 min |
| Survey | 11 legs, 71 m swath at 53 m spacing; ground sample 1.7 cm |
| Pixels across each target | lobster buoy 17.2 px, debris log 22.9 px, kayak 51.6 px |
| Flight time / distance | 24.4 min / 20.9 km |
| Battery left at recovery | 17% |
| Mean power, max bank | 76 W, 35 deg |

![track](track.png)

![timeline](timeline.png)

